# Bangumi 番剧订阅插件排障

> 插件: `astrbot_plugin_bangumi_enhance`  
> 配置: `/home/po/astrbot/data/config/astrbot_plugin_bangumi_enhance_config.json`

## 常见问题：订阅不推送更新

### 1. API 网络不通

`api.bgm.tv` 在国内直连经常超时。必须通过代理。

**检查**：
```bash
curl -v --connect-timeout 8 https://api.bgm.tv/v0/episodes 2>&1 | tail -5
# Connection timed out = 被墙
curl -x http://127.0.0.1:7890 https://api.bgm.tv/v0/episodes
# 有返回 = 代理可用
```

**插件配置** (`config.json`)：
```json
{
  "proxy_http": "127.0.0.1",
  "port": "7890"
}
```

### 2. 代理间歇性失败

日志中偶尔出现 `网络请求失败 (第 1 次): Cannot connect to host api.bgm.tv:443 ssl:default [None]`，通常是代理瞬断。重试机制会处理（max_retries=3）。

### 3. 没有新集数 ≠ 插件坏了

**先查数据库**确认当前状态：
```bash
python3 -c "
import sqlite3; conn = sqlite3.connect('/home/po/astrbot/data/plugin_data/astrbot_plugin_bangumi_enhance/data.db')
for r in conn.execute('SELECT subject_id, name, current_episode, updated_at, broadcast_time FROM bangumi_subjects'):
    print(r)
"
```

**再查 Bangumi API** 看实际最新集数：
```bash
curl -s -x http://127.0.0.1:7890 "https://api.bgm.tv/v0/episodes?subject_id=<id>&limit=50" | python3 -m json.tool | grep -E '"ep"|"airdate"|comment'
```

插件逻辑：`get_latest_episode()` 要求 `airdate ≤ 今天 AND comment > 0` 才触发通知。Bangumi 有时提前列出剧集（已有评论但 airdate 未到），此时不会推送，是正常行为。

### 4. 日志解读

| 日志 | 含义 |
|------|------|
| `开始更新 N 个番剧的集数信息` | 定时任务启动 |
| `Bangumi API请求 (尝试 1/3)` | 正常请求 |
| `网络请求失败 (第 X 次)` | 瞬时网络问题 |
| `番剧《xxx》有更新: N -> M` | 发现新集数 |
| `更新番剧《xxx》失败` | 持续失败，需要排查 |

## 通知不包含放送时间

`_notify_subscribers()` 原本在发更新通知时**不查询 `broadcast_time` 字段**，即使数据库已有值（来自 bgmlist API 自动填充或手动 `/放送时间` 设置），通知消息里也看不到放送时间。

**修复（v1.3.x）**：在 `src/app/subscription_service.py` 的 `_notify_subscribers` 方法开头添加：
```python
broadcast_time = self.storage.get_subject_broadcast_time(subject_id)
```
然后在通知文本/图片前插入 `⏰ 放送时间: HH:MM (CST)`。

**验证修复**：发送 `/放送时间` 查看已设置的 broadcast_time，下次该番剧更新时通知应包含放送时间信息。

## 放送时间自动获取机制

### 数据来源

Bangumi 官方 `/calendar` API **只返回周几播出的分组**，不含精确 `HH:MM`。精确的放送时间来自 **bgmlist.com**（开源项目 `wxt2005/bangumi-list-v3`）。

### 调用链路

```
bgmlist.com (/api/v1/bangumi/onair)
    → src/api/bgmlist.py :: fetch_onair_data()
        → 解析每个 item：sites[site="bangumi"].id 提取 subject_id，begin 字段（ISO 时间）→ CST HH:MM
    → main.py :: _auto_fill_broadcast_times()  [插件启动时调用]
        → repository.py :: batch_update_broadcast_times()
            → 只填充 broadcast_time 为空的条目，已有值的不覆盖
            → 写入 SQLite (BangumiSubject.broadcast_time)
```

### bgmlist API 格式

```json
{
  "items": [
    {
      "begin": "2026-04-06T14:00:00.000Z",
      "sites": [{"site": "bangumi", "id": "377130"}, ...]
    }
  ]
}
```

`_parse_broadcast_time("2026-04-06T14:00:00.000Z")` → `"22:00"`（CST ±0）。

### 触发时机

1. **启动时**：`_auto_fill_broadcast_times()` 调用一次，只填空的
2. **定时任务**：每 15 分钟 `check_updates`，配合 `broadcast_time` 精确触发（到时间附近才真正检查该番剧）
3. **手动**：`/放送时间 <番剧名> HH:MM` 设置，`/放送时间 <番剧名> 清空` 清除

### bgmlist API 不可达时的行为

- 跳过自动填充，不会阻塞启动
- `broadcast_time` 为空 = 通知触发退到整点检查（没有精确时间）
- 不抛异常，温和降级

### 缓存

- `CalendarService` 有 `_calendar_cache`（12 小时 TTL），但那是 Bangumi `/calendar` 的数据
- `fetch_onair_data()` 本身**无缓存**，每次调用都请求 bgmlist API
- 双重检查锁（`_calendar_cache_lock`）避免并发下重复请求
