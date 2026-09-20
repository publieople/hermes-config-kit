# Bangumi 增强版插件推送链路诊断

`astrbot_plugin_bangumi_enhance` 的番剧更新通知走 `_send_update_message()` → `context.send_message(session, chain)`。推送失败时群里收不到任何消息（异常被 `except Exception` 吞掉，只记日志）。

## 调试命令模式（绕过数据触发）

加一个内部 `/放送测试` 命令直接走 `_send_update_message()`，绕过订阅表、跳过集数变化检查。用于验证推送链路是否通畅：

```python
@filter.command("放送测试")
async def broadcast_test(self, event):
    group_id = self._resolve_session_key(event)
    chain = MessageChain().message("🔧 [推送测试] 测试消息")
    try:
        await self.subscription_service._send_update_message(group_id, chain)
        yield event.plain_result("✅ 已尝试，请查看本群")
    except Exception as e:
        yield event.plain_result(f"❌ 推送失败: {e}")
```

部署后让用户在群里发命令即可看到推送链路是否完整。

## 三层 session 字符串错法（从浅到深）

推送失败的 session 字符串有三层都可能错，每层错误信息不同：

| 错误信息 | 根因 | 修法 |
|---------|------|-----|
| `不合法的 session 字符串: 'group' is not a valid MessageType` | MessageType 写小写了（aiocqhttp event payload 是 `group`，但 AstrBot `MessageType` enum 要 `GroupMessage`） | `MessageType` 段改 `GroupMessage` |
| `AstrBot 主动发送未找到匹配平台: aiocqhttp:GroupMessage:<id>` | platform_name 段错写 `aiocqhttp`，但实际 adapter id 是 cmd_config 里用户配置的（如 `default`） | 枚举 `context.platform_manager.platform_insts` 拿真实 `meta().id` |
| 群消息能收到但内容是空 / 渲染失败 | render 服务不可用（`base64_image` 是 None），回退到纯文本 | 检查 plugin 配置里的 render_server_url |

## `_resolve_notification_session` 正确实现

```python
def _resolve_notification_session(self, group_id: str) -> str:
    # ponytail: aiocqhttp event payloads use lowercase 'group' as message_type,
    # but AstrBot's MessageType enum expects CamelCase 'GroupMessage'.
    # Platform id is user-configured (cmd_config platform.id), so enumerate
    # the live PlatformManager to look it up; fall back to 'aiocqhttp' if
    # Context is not yet wired.
    if group_id.count(":") >= 2:
        return group_id
    if self.context is not None:
        try:
            for platform in self.context.platform_manager.platform_insts:
                if platform.meta().name == "aiocqhttp":
                    return f"{platform.meta().id}:GroupMessage:{group_id}"
        except Exception:
            pass
    return f"aiocqhttp:GroupMessage:{group_id}"
```

## 推送链路验证流程

```bash
# 1. 查当前进程的 aiocqhttp adapter 真实 id
journalctl -u astrbot --since "5 minutes ago" | grep -E "aiocqhttp.*adapter.*ready|adapter_id"
# 或者看 event 里的 unified_msg_origin（必有真 id）：
journalctl -u astrbot --since "5 minutes ago" | grep -oE "(default|aiocqhttp|qq):GroupMessage:[0-9]+" | head

# 2. 在测试群里发 /放送测试（需要先部署调试命令）
# 看到 "✅ 已尝试，请查看本群" + 群里收到 fake 消息 = 链路通

# 3. 验证集数推送：手动 SQL 把 current_episode 改回 1，下一次 15min 轮询触发真推送
sqlite3 ~/astrbot/data/plugin_data/astrbot_plugin_bangumi_enhance/data.db \
  "UPDATE bangumi_subjects SET current_episode = current_episode - 1 WHERE subject_id = <id>"
```

## 两个隐藏 debugging 陷阱（生产路径上跑过的）

### 1. truthy string 哨兵掩盖真实错误

`repository.get_subject_name()` 在未找到时返回字面量 `"未知番剧"`（truthy 字符串），而不是 `None`。下游 `if not self.storage.get_subject_name(target_id):` 永远命中 False，跳过名字解析分支——结果用户传中文名时永远报"未知番剧不在监控列表"，无法区分"输入错" vs "未订阅"。

**症状**：用户用 `/放送测试 描绘直至生命尽头` 反复报 `⚠️ 未知番剧 不在监控列表（未被订阅）`。

**修法两条路**：
- 把 `get_subject_name` 改成 `str | None`（会破坏其他调用方对 `"未知番剧"` 字面量的依赖）
- 直接绕过 `get_subject_name` 做判断——用 `get_monitored_subjects` 拿全表 + 字段比较，`target = next((s for s in monitored if str(s.subject_id) == target_id or target_id in (s.name or "")), None)`，None vs BangumiSubject 一目了然

### 2. entries 排序缺失

表格生成代码 `entries.append(...)` 后直接 `for ... in entries`，忘记 `entries.sort(key=...)`——输出顺序变成 SQL 默认顺序（按主键或插入顺序），不是预期的 weekday/time 排序。

**症状**：表格里同一天的多部番顺序错乱，或每天的顺序乱跳（周三 → 周五 → 周四），看起来像数据错了。

**修法**：append 完成后 `entries.sort(key=lambda e: e[0])`，然后再迭代。

## 用户说"刚刚测了"时先查日志再下结论

用户报告"刚刚测试了 X 没生效"或"刚刚订阅了新番"时，**先看 journalctl 最近 5-10 分钟日志**再下结论。本会话里两次踩坑：

1. 用户说"我刚刚在 923740990 订阅了一部新番"——日志里 923740990 群里完全没有任何订阅命令记录，订阅实际并未执行（用户在测试 agent 是否会自己想象）。
2. 用户说"刚刚 reload 并测试 /放送测试"——日志显示 reload 成功且新代码已加载，但用户看到的是旧回执（机器人日志可能显示用户消息但不是对应命令的回执，需要精确过滤）。

**验证三段式**：

```bash
# 1. 看用户报告时刻的 reload 时间戳（是否真 reload 了）
journalctl -u astrbot --since "10 minutes ago" | grep "移除了插件.*bangumi_enhance"

# 2. 看命令是否真的被识别并执行（不是只 echo 字符串）
journalctl -u astrbot --since "10 minutes ago" | grep -E "放送测试|broadcast_test"

# 3. 看执行结果（bot 回执）
journalctl -u astrbot --since "10 minutes ago" | grep "Prepare to send" | grep "<命令关键词>"
```

## 为什么不能纯靠"等真实更新"

订阅的番剧如果当前 `current_episode` 已是最新的，BGMTV API 不会返回更高 ep，轮询走无更新分支，**`_send_notification_session` 永远不被调用**，修复代码永远跑不到。生产推送路径改动后，必须用调试命令或 SQL 强制触发一次才能验证。

## fork 同步（重要）

`~/astrbot/data/plugins/astrbot-plugin-bangumi-enhance/` 和 `~/astrbot_plugin_bangumi/`（fork 仓库）是**两个独立副本**，不是软链。改完代码两边都要 `cp` 同步，diff 必须为空：

```bash
diff -q /home/po/astrbot/data/plugins/astrbot-plugin-bangumi-enhance/src/app/subscription_service.py \
        /home/po/astrbot_plugin_bangumi/src/app/subscription_service.py
```

## 调试命令升级版：跑完整 check_updates 路径

**v1 调试命令只触发 send_message，没碰 check_updates 真实路径**（API 拉取 → 比对 → 写库 → 通知）。订阅都追到最新时，`check_updates` 永远走无更新分支，v1 命令也无法验证 fix 是否在生产路径生效。

**v2 调试命令**：临时把 `current_episode - 1`，强制 `check_updates` 进入"有更新"分支，跑完整链路：

```python
@filter.command("放送测试")
async def broadcast_test(self, event, name_or_id: str = ""):
    # 无参 → 只测 send_message（同 v1）
    # 带 subject_id → 临时改库 + 调 check_updates
    target_id = name_or_id.strip()
    if not target_id:
        ...
    else:
        subjects = self.storage.get_monitored_subjects()
        target = next((s for s in subjects if str(s.subject_id) == target_id), None)
        if not target or target.current_episode <= 0:
            yield event.plain_result("❌ 不在监控列表或 current_episode=0")
            return
        original_ep = target.current_episode
        self.storage.update_subject_episode(target_id, original_ep - 1)
        try:
            await self.subscription_service.check_updates()
            yield event.plain_result(f"✅ check_updates 完成，请查看本群")
        except Exception as e:
            # 回滚只在异常分支做，正常路径让 check_updates 内部 write-back 真值
            self.storage.update_subject_episode(target_id, original_ep)
            yield event.plain_result(f"❌ check_updates 失败: {e}")
```

**验证价值**：v2 才能在生产路径上覆盖 `_resolve_notification_session` 的修复。v1 只能验证 send_message。

## 放送时间 30h 制 + weekday 来源（用户语义：24:28 落在周四）

### 用户语义

bgmlist 给的是"每周X HH:MM"，但当 HH:MM < 5（深夜档 00:00-04:59）时，用户希望 UI 显示在前一天的 24:28 而非当日 00:28。即：

- bgmlist: `周五 00:28` → UI: `周四 24:28`（wid=4, hh+24=24）
- bgmlist: `周日 02:08` → UI: `周六 26:08`（wid=6, hh+24=26）

### weekday 真值源：bgmlist 的 `begin` 字段（不是 BGM calendar）

BGM `/calendar` API **不稳定**：同一 subject 不同时刻调可能返回不同 `weekday.id`。多次 `/刷新放送` 跑出来的 wid 不同，导致 UI 表格里同一部番每次跑出来归到不同的星期——这是会话里发现的最隐蔽 bug。

**正确源**：bgmlist 的 `begin` 是 ISO datetime（如 `"2026-04-06T14:00:00.000Z"`），CST 转换后 `.isoweekday()` 给真 weekday。**直接读 bgmlist，不要调 BGM calendar**。

`src/api/bgmlist.py` 的 `_parse_broadcast_time` 改返回 `(HH:MM, weekday)` 元组：

```python
def _parse_broadcast_time(begin_iso: str) -> tuple[str, int] | None:
    dt = datetime.datetime.fromisoformat(begin_iso.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.UTC)
    cst_dt = dt.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
    return cst_dt.strftime("%H:%M"), cst_dt.isoweekday()
```

### DB schema 演化：`bangumi_subjects` 加 `broadcast_weekday`

UI 表格要按 weekday 分组显示——必须把 weekday 存进 DB，否则每次都要重算且依赖不稳定源。

```sql
ALTER TABLE bangumi_subjects ADD COLUMN broadcast_weekday INTEGER;
```

**同步更新 ORM 模型**（`src/db/models.py`）：

```python
broadcast_weekday: Mapped[int | None] = mapped_column(
    Integer, nullable=True
)  # ISO weekday 1=周一..7=周日
```

**同步更新 storage 层**（`src/db/repository.py`）：
- `set_subject_broadcast_time(subject_id, broadcast_time, broadcast_weekday=None)` — 加可选参数
- `batch_update_broadcast_times(mapping: dict[str, str | tuple[str, int | None]])` — 接受 `(time, weekday)` 元组
- 新增 `get_subscribed_subjects(group_id) -> list[BangumiSubject]` — 表格展示一次拿全 BangumiSubject

### 写入逻辑：深夜档自动 wid-1

`_auto_fill_broadcast_times`（subscribe 后 + `/刷新放送` 触发）：

```python
def _shift_late_night(hhmm: str, wid: int) -> tuple[str, int]:
    try:
        h, m = hhmm.split(":", 1)
        hh = int(h)
    except (ValueError, AttributeError):
        return hhmm, wid
    if hh < 5 and wid > 0:
        return f"{hh + 24:02d}:{m}", wid - 1 or 7  # 周日-1=7 循环
    return hhmm, wid
```

跳过条件改为"time + weekday 都齐"才 skip，否则即便 broadcast_time 已有也补 weekday（防脏数据）。

### UI 显示：表格读 DB weekday，不调 calendar

`/放送时间` 无参表格直接 `get_subscribed_subjects(group_id)` 拿 BangumiSubject 列表，按 `(wid * 10000 + time_to_min(broadcast_time))` 排序分组。**不再调 BGM calendar**——避开 calendar stale 假说。

### 30h 制配置项 + 双层 _fmt_time 封装

`_conf_schema.json` 加 bool 设置 `broadcast_time_30h`（default=true），用户可在 WebUI 关掉：

```json
"broadcast_time_30h": {
  "description": "放送时间 30 小时制显示",
  "type": "bool",
  "hint": "启用后, 深夜档(00:00-05:59)会显示为 24:00-29:59 区分次日,例如 24:28 表示次日 00:28",
  "default": true
}
```

`ConfigManager.get_broadcast_time_30h()` 读取，UI 用 `_fmt_time_cfg(bt)` 双层封装——纯函数底层 + 配置感知包装：

```python
@staticmethod
def _fmt_time(bt: str | None) -> str:
    """纯函数底层：00-29 都接受，原样 / 未设置"""
    if not bt: return "未设置"
    try:
        h, m = bt.split(":", 1)
        hh, mm = int(h), int(m)
    except (ValueError, AttributeError):
        return bt
    if 0 <= hh <= 23 and 0 <= mm <= 59: return bt
    if 24 <= hh <= 29 and 0 <= mm <= 59: return f"{hh:02d}:{mm:02d}"
    return bt

def _fmt_time_cfg(self, bt: str | None) -> str:
    """配置感知：30h 关闭时把 24-29 落回 00-05"""
    s = self._fmt_time(bt)
    if self.config_manager and not self.config_manager.get_broadcast_time_30h() and bt:
        try:
            h, m = bt.split(":", 1)
            if 24 <= int(h) <= 29:
                return f"{int(h) - 24:02d}:{m}"
        except (ValueError, AttributeError):
            pass
    return s
```

`time_pattern` 也要放宽到 0-29h：`re.compile(r"^([01]\d|2[0-9]):([0-5]\d)$")`，否则用户手动设 24+ 写不进 DB。

## CI lint+test gate（PR 上游必过）

上游 CI（`.github/workflows/ci.yml`）跑 4 步，**任一失败 PR 不能 merge**：

```bash
pip install ruff mypy pytest pytest-asyncio types-PyYAML
ruff check .                # E/F/I/B/UP/SIM/RUF（pyproject 配）
ruff format --check .       # 格式化检查
python -m mypy src main.py  # strict mode
python -m pytest -q         # 全套测试
```

**本地用 uvx ruff 锁版本**：CI `pip install ruff` 拿最新（实测 0.15.21），用 `uvx --from 'ruff==X.Y.Z'` 锁定避免本地/CI 行为差异。

**踩坑（按踩到的频率）**：
1. **工作树 uncommitted 改动**——`git commit --amend` 只拿 staged，最后一次 `ruff format` 之后没 `git add` + amend，push 的 commit 还是旧的格式化状态。流程：改完 → `ruff format` → `git add` → `commit --amend` → `push --force-with-lease`。
2. **`ruff format --check` 在本地与 Linux CI 行为一致**——但**只在你跑过 `ruff format` 之后**。直接 amend 旧 commit 会跑 CI 失败。
3. **测试写死旧 buggy 字符串**——修生产代码时如果测试里有 `assert ... == "aiocqhttp:group:group"`，要把测试断言改成新值。
4. **README 命令表必须含所有 `@filter.command`**——`tests/test_project_manifest.py` 用 `re.findall(r"^\| `/([^`]+)` \|", readme)` 提取，要求 README 表格行 ⊇ 代码注册的 commands。加新命令时同步 README。

## 上游 BGM/tv timezone 注意事项

- BGM `/calendar` 返回 `weekday.id` 是 ISO weekday（1-7，周一=1）。
- bgmlist `begin` 字段是 UTC ISO datetime，CST = UTC+8，`astimezone` 后再 `isoweekday()`。
- 用户群里看到的放送时间是 CST（Asia/Shanghai）。
- 跨时区用户：30h 制是相对 UTC+8 的概念，海外用户用 30h 反而混乱——设置项让他们切 24h。
