---
name: bangumi-subscription
description: 管理 Bangumi 番剧订阅 - 搜索、添加、移除、查看订阅
---

# Bangumi 番剧订阅管理

## 触发条件

用户说出以下关键词时加载本 skill：
- "订阅"、"取消订阅"、"订阅列表"、"追番"、"bangumi"
- 任何与番剧更新通知相关的请求

## 交互命令

### 1. 搜索并订阅番剧
用户说 `订阅 {番剧名}` 时：
1. 用搜索引擎搜索 `site:bgm.tv {番剧名} 2026` 获取条目ID，或者直接用 `web_extract` 访问 `https://bgm.tv/subject/` 前缀测试已知ID。
2. 获取 subject_id 后，用 `web_extract(urls=["https://api.bgm.tv/v0/subjects/{subject_id}"])` 验证条目，从中提取 `name_cn`（中文名）和 `total_episodes`（总话数）。
3. 执行终端命令添加订阅：
   ```
   python3 ~/.hermes/scripts/bangumi.py add {subject_id} "{中文名}"
   ```
4. 如果总话数已知，也一并更新：
   ```
   python3 ~/.hermes/scripts/bangumi.py update {subject_id} 0 {total_eps}
   ```
5. **查 yuc.wiki 确定放送时间**：用 web_extract 访问 `http://yuc.wiki/{YYYYMM}/`（当前季度），按星期分组找到该番，记录播出日和播出时间。
   - 如果时间为 "深夜" 或未标明具体时间，则默认设定为 21:00
   - 如果标明了具体时间（如 "22:45~" 或 "15:30~"），就用该时间
   - 注意 yuc.wiki 用的是 30小时制（24:00~30:00 表示第二天凌晨 0:00~6:00）
   - 番名模糊匹配（见下方常见匹配示例）
6. **创建 cron job**：根据 yuc.wiki 查到的播出日和时间，用 cronjob action='create' 创建定时任务。
   - 放送时间 23:00 以内：cron 设在放送时间之后 5~15 分钟（给电视台延迟留余量）
   - 放送时间在 24:00~30:00（即第二天凌晨）：cron 设在对应时间，注意 cron 用 24 小时制，30小时制转回正常时间（25:00 = 次日01:00）
   - cron 的 schedule 用 cron 表达式，如 `0 23 * * 5`（每周五23:00）
   - prompt 内容参考下方 cron job prompt 模板
   - 启用工具集：terminal, napcat, web
7. 回复用户：已订阅 [番剧名]，播出时间 [周X HH:MM]，有新话会通知

### 2. 取消订阅
用户说 `取消订阅 {ID或番名}` 时：
```
python3 ~/.hermes/scripts/bangumi.py remove {subject_id}
```
同时用 cronjob action='list' 找到对应的 cron job，然后 action='remove' 删除。

### 3. 查看订阅列表
用户说 `订阅列表` 时：
```
python3 ~/.hermes/scripts/bangumi.py list
```

### 4. 手动检查更新
用户说 `检查更新` 时，需要同时查 Bangumi API 的最新话数，比对已通知话数，有更新就手动推送并更新数据。

## 数据文件

- 订阅列表：`~/.hermes/bangumi_subscriptions.json`
- 管理脚本：`~/.hermes/scripts/bangumi.py`

## 定时任务

每部番单独创建 cron job，在各自的放送时间之后检查更新并推送通知，不统一检查。

### cron job prompt 模板

```
检查{番名}（subject_id: {id}）是否有新话更新。

1. 用 web_extract 访问 https://api.bgm.tv/v0/episodes?subject_id={id}&type=0&limit=20
2. 从返回的数据中找到最大 ep 值（使用 data 数组中每条记录的 ep 字段，NOT sort 字段），这就是最新话数
3. 用终端命令 python3 ~/.hermes/scripts/bangumi.py get {id} 查询当前已通知到第几话
4. 如果最新话数 > 已通知话数，且最新话的 airdate 不是未来日期，则：
   a. 用终端命令 python3 ~/.hermes/scripts/bangumi.py update {id} {最新话数} 更新已通知话数
   b. 用 send_message 发通知到本群，格式： "[番名] 第X话已更新，快去看看吧"
5. 如果最新话数 == 已通知话数，就什么都不做

注意：必须使用 ep 字段的值，不要用 sort 字段！
```

### 当前订阅定时任务

| 番剧 | 放送时间 | Job ID |
|------|---------|--------|
| 上伊那牡丹 | 每周五 23:00 | fd9f16d16460 |
| 女神异世界转生 勇者的肋骨 | 每周二 21:00（yuc.wiki: 深夜） | 5af15936ddbf |
| Re:0 第四季 丧失篇 | 每周三 22:45 | 3e43515c1a67 |
| 尖帽子的魔法工房 | 每周一 21:00（yuc.wiki: 深夜） | 381bb7fe1a24 |
| 杖与剑的魔剑谭 第二季 | 每周日 15:30 | 322455490fff |

## 数据来源

### 1. Bangumi API（检查话数）
- 通过 web_extract 访问 `https://api.bgm.tv/v0/episodes?subject_id={id}&type=0&limit=20`
- 获取最新话数：取 data 数组中每条记录的 `ep` 字段的最大值（**不要用 sort 字段**，因为多季番的 sort 值可能偏移）
- episode type=0 为主篇，只需要检查主篇

### 2. yuc.wiki（获取播出时间）
- 通过 web_extract 访问 `http://yuc.wiki/{YYYYMM}/`（按季度调整，如 202604 为2026年4月）
- 页面按星期几分组，每组内有番名、播出时间、首播日期、平台信息
- 播出时间格式：`{月/日} {HH:MM}~`（如 "4/10 23:00~"），或 "深夜"（未标明具体时间）
- 匹配方式：番剧名模糊匹配
- 常见匹配示例：
  - "上伊那牡丹，酒醉身姿似百合花般" → "上伊那牡丹 酒醉身姿似百合"
  - "女神异世界转生想成为什么 我 勇者的肋骨" → "请求女神让我 转生成勇者的肋骨"
  - "Re:从零开始的异世界生活 第四季 丧失篇" → "Re:从零开始的 异世界生活 第4期"
  - "尖帽子的魔法工房" → "尖帽子的魔法工坊"

## 30小时制

yuc.wiki 使用30小时制。第二天 00:00~06:00 的放送算前一天的 24:00~30:00。
转成正常时间：25:00 = 次日01:00，26:00 = 次日02:00，以此类推。
cron 时间也用转换后的正常时间。

## 注意事项

- 消息用纯文本，不要用 markdown
- Bangumi API 通过 web_extract 访问，terminal 里直连不通
- yuc.wiki 也只能通过 web_extract 访问
- episode type=0 为主篇，只需要检查主篇
- **必须用 ep 字段而非 sort 字段判断话数**，尤其注意多季番的 sort 可能从13+开始
- yuc.wiki 上标"深夜"的番没有具体时间，默认设 cron 为 21:00
