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
| `向群组 <id> 发送《xxx》更新通知失败: 不合法的 session 字符串: 'group' is not a valid MessageType` | **session 字符串拼错，MessageType 必须 CamelCase** — 详见 §5 |

### 5. 通知推到群失败：`'group' is not a valid MessageType` (2026-07-10)

**症状**：日志持续刷
```
向群组 707942526 发送《xxx》更新通知失败: 不合法的 session 字符串: 'group' is not a valid MessageType
```
番剧更新检测正常（API 请求 + "有更新: N -> M" 都出现），但**群里始终收不到通知**。订阅服务把异常吞进 `except Exception` 静默走 fallthrough，无重试无日志告警，群里只能干等。

**根因**：`src/app/subscription_service.py` 的 `_resolve_notification_session()` 把 raw QQ 号拼成 `aiocqhttp:group:{id}`（小写 `group`）。AstrBot v4 的 `MessageType` 枚举合法值是 CamelCase `GroupMessage` / `FriendMessage`：

```python
# ~/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/astrbot/core/platform/message_type.py
class MessageType(Enum):
    GROUP_MESSAGE = "GroupMessage"
    FRIEND_MESSAGE = "FriendMessage"
```

`aiocqhttp` 适配器解析 session 时把第二段喂给 `MessageType()`，小写 `group` 不在枚举里直接 raise。**容易踩**因为 aiocqhttp 在 webhook event payload 里用的是小写 `message_type = "group"`（incoming 端 OK），但 outgoing `send_message()` 用的是 AstrBot 内部 CamelCase enum（两端反向不一致）。

**修复**（不是一行——MessageType 修了还不够, platform_name 也写错了, 两步必须都改）:

```python
# src/app/subscription_service.py _resolve_notification_session
# 1. MessageType CamelCase (不是 aiocqhttp webhook event 的小写 "group")
# 2. platform_name 用 metadata.id 而不是硬编码 "aiocqhttp" (后者是 adapter
#    class 名, 不是用户在 cmd_config.json 里配置的 platform id; 公仆这里
#    默认是 "default", 硬编码 aiocqhttp 会触发 "未找到匹配平台" 警告)

class SubscriptionService:
    # 不再 @staticmethod — 需要 self.context
    def _resolve_notification_session(self, group_id: str) -> str:
        if group_id.count(":") >= 2:
            return group_id  # 已是完整 session
        if self.context is not None:
            try:
                for platform in self.context.platform_manager.platform_insts:
                    if platform.meta().name == "aiocqhttp":
                        return f"{platform.meta().id}:GroupMessage:{group_id}"
            except Exception:
                pass
        # 兜底: context 不可用时回退原 hardcoded 路径
        return f"aiocqhttp:GroupMessage:{group_id}"
```

**为什么必须 enumerate platform_manager** (踩了两轮才看清的根因):

AstrBot v4 `context.send_message()` 在 `core/star/context.py:533-536` 用 `platform.meta().id == session.platform_name` 找匹配 platform。platform.id 是用户在 cmd_config.json 配置的 (不是 adapter class 名)。`core/platform/sources/aiocqhttp/aiocqhttp_platform_adapter.py:48-52` 里 `id=cast(str, self.config.get("id"))` —— 直接读用户配置。

公仆的 cmd_config 里 aiocqhttp 的 `id` 字段是 `default` (看 AngelHeart 日志 `default:GroupMessage:923740990` 自证)。硬编码 `aiocqhttp:GroupMessage:xxx` 时:
- 第一轮 (MessageType 小写): 报 `'group' is not a valid MessageType` (session 解析失败)
- 第二轮 (MessageType 改对, platform_name 仍硬编码): 报 `AstrBot 主动发送未找到匹配平台: aiocqhttp:GroupMessage:xxx` (platform id 找不到匹配)
- 修完: 群里真收到推送

**复现+验证**（端到端, 不依赖真实新集数）:

```bash
# 1. 改两个副本 (AstrBot 加载副本 + fork 真理源), 保持同步
diff -q ~/astrbot/data/plugins/astrbot-plugin-bangumi-enhance/src/app/subscription_service.py \
        ~/astrbot_plugin_bangumi/src/app/subscription_service.py
# 两个都改完后必须 diff 为空

# 2. 重启 AstrBot (ASTRBOT_RELOAD=1 未启时, 热重载不会触发; main.py 以外的子模块
#    即使启了 watcher 也要手动 restart)
sudo systemctl restart astrbot

# 3. 端到端验证 — 不要傻等真实新集数 (可能几小时到几天才有), 用 /放送测试 命令
#    (见下方"调试命令"段)

# 4. 验证日志无失败
sudo journalctl -u astrbot --since "5 min ago" --no-pager | \
  grep -E "向群组.*更新通知成功|MessageType|未找到匹配平台"
# 期望: 不再有任何失败行
```

**预防**：自己写 plugin 时，凡是从 raw platform ID 拼 session 字符串的，先去 `astrbot/core/platform/message_type.py` 抄合法 enum 值再拼。**不要参考 aiocqhttp webhook event 的小写字段名**（那是 incoming 方向），outgoing `context.send_message()` 用的是 CamelCase。

**自检工具: `/放送测试` 调试命令** (公仆加的, 在 fork + data/plugins 两份 main.py 的 `refresh_broadcast` 之后):

```
/放送测试                       # 通用假消息, 只走 send_message 路径
/放送测试 <subject_id>          # 跑完整 check_updates 端到端
```

带 subject_id 时临时把该番 `current_episode` 减 1, 强制 `check_updates` 进入"有新集数"分支, 触发完整链路:
`get_latest_episode` (BGM API) → 比对 → `update_subject_episode` → `_notify_subscribers` → `_resolve_notification_session` (本次修复) → `_send_update_message` → `context.send_message`。

**为什么必须有这个命令** (公仆反复要求的痛点): 14 部番剧通常都已追到最新, 等真实新集数要几小时到几天。"修复是否生效"在生产路径上 5 小时内从未被触发过——`/放送测试 <id>` 一行就强制走一遍真生产路径。

```bash
# 在测试群里跑一次
/放送测试 622206    # 《尼古喵喵》

# 期望:
# 1. 群内立刻看到《尼古喵喵》更新通知卡片 (走完整路径)
# 2. bot 回到命令"✅ check_updates 完成"
# 3. journal 里看到 "番剧《尼古喵喵》有更新" + "向群组 923740990 发送《尼古喵喵》更新通知成功"
sudo journalctl -u astrbot --since "30 sec ago" --no-pager | \
  grep -E "尼古喵喵|未找到匹配平台|MessageType"
# 期望: 无 "未找到匹配平台" / 无 MessageType 报错
```

**约束**: 命令完成后 `update_subject_episode` 会把 current_episode 写回 BGM API 真实集数 (因为 `get_latest_episode` 比对会用真实最新值), 不需要手动恢复 DB。

**支持中/英文番剧名（不只是 ID）**：第一版只接 `subject_id`，用户传中文番名 `描绘直至生命尽头` 直接 `⚠️ 本地数据库未找到 subject_id=描绘直至生命尽头`。**修法**：参数解析层先 `get_subject_name(target_id)`，miss 时 fallback 到 `find_group_subscription_candidates(group_id, target_id, limit=3)`：
```python
if not self.storage.get_subject_name(target_id):
    candidates = self.storage.find_group_subscription_candidates(
        group_id=group_id, keyword=target_id, limit=3
    )
    if len(candidates) == 1:
        target_id = str(candidates[0].subject_id)
    elif len(candidates) > 1:
        # 列出来让用户选
```
**通用规则**：debug 命令、配置命令、查询命令的参数都该接受用户群里看到的自然语言输入（中文番名、用户别名），不要强制技术 ID。0 行新逻辑，复用已有的 `find_*_candidates` 模糊匹配。

**Patch 缩进陷阱**：patch `old_string` 缺第一行 `return` 时（如 `if not X:\n    yield ...\n    return\n\ntarget_id = ...`），后续代码会被多缩 4 空格 = 嵌套进 if 体内，pyright 报"possibly unbound / not a known attribute of None"。**防御**：patch 前先读 old_string 前后 3 行确认完整缩进；写完后 `git diff --stat` 看 lines 数对不对（单文件 +50/-3 但原文件只 +20 行 = 嵌套错了）。

**Patch 关联**：fork 测试 `tests/app/test_subscription_service.py:176` 也写死 `assert == "aiocqhttp:group:group"`，是 dead test，需要同步改 `GroupMessage`（不影响运行时，但是 CI 红灯）。

### §5.2 `/放送测试` 命令两种模式（公仆 fork 加的调试命令，PR #18 收录）

**两种用法，验证目标完全不同，不要混用**：

```
/放送测试                       # 仅验证 send_message 链路
/放送测试 <subject_id>          # 跑完整 check_updates 端到端
```

**无参模式 (`/放送测试`)**：直接调 `subscription_service._send_update_message()` 发一条字符串消息。**只覆盖**：
- `_resolve_notification_session` 拼 session
- `_send_update_message` → `context.send_message`

**不覆盖**：BGM API 拉取、`check_updates` 集数比对、`update_subject_episode` 写回。所以"群里看到假消息"≠"推送功能完全正常"。

**带 subject_id 模式 (`/放送测试 622206`)**：临时把 `current_episode` 减 1 → 调 `check_updates()` → 触发"有新集数"分支 → 走完整生产路径。**覆盖全链路**：
`get_latest_episode` (BGM API) → 比对 → `update_subject_episode` → `_notify_subscribers` → `_resolve_notification_session` (本次修复) → `_send_update_message` → `context.send_message`。

**用法步骤**：

```bash
# 1. 选一部本群已订阅的番 (DB 查 group_id=923740990 的 subscriptions)
/放送测试 622206    # 《尼古喵喵》, 本群已订阅

# 2. 期望:
#    a) bot 回到命令 "🔧 准备跑完整 check_updates 路径: 《尼古喵喵》 current_episode N → N-1"
#    b) 群内立刻看到《尼古喵喵》更新通知卡片 (走完整渲染+推送)
#    c) bot 回 "✅ check_updates 完成"
#    d) journal 里同时看到 "番剧《尼古喵喵》有更新" + "向群组 923740990 发送《尼古喵喵》更新通知成功"

# 3. 验证日志
sudo journalctl -u astrbot --since "30 sec ago" --no-pager | \
  grep -E "尼古喵喵|未找到匹配平台|MessageType"
# 期望: 无 "未找到匹配平台" / 无 MessageType 报错

# 4. DB 状态: update_subject_episode 会把 current_episode 写回真实最新值, 不需要手动恢复
sqlite3 /home/po/astrbot/data/plugin_data/astrbot_plugin_bangumi_enhance/data.db \
  "SELECT subject_id, name, current_episode FROM bangumi_subjects WHERE subject_id='622206'"
# 期望: current_episode 等于 BGM API 真实最新集数
```

**前置条件**：
- `<subject_id>` 必须在 `bangumi_subjects` 表里 (即已被任意群订阅过)
- `<subject_id>` 必须被**当前群**订阅（否则 `_notify_subscribers` 不会推到本群）
- 当前群必须有 aiocqhttp platform id（不要在没接 adapter 的环境跑）

**实现要点 (加命令时)**：
- 临时 `current_episode - 1` 用 `self.storage.update_subject_episode()`，同步写回 DB
- `check_updates` 是 async，等它跑完
- 异常分支把 `current_episode` 恢复回原值，避免污染数据
- 不需要 `_build_subscribable_subject` 或 bgm API 二次校验（不是新增订阅，是复用已订阅条目）

### §5.3 fork → 上游 PR 提交全流程 (publish 时的 CI 必坑，2026-07-10 实测)

适用：自己有 fork (`publieople/<repo>`)，改完想 PR 回上游 (`<upstream-owner>/<repo>`)，CI 卡住需要排查。

**结构假设**：
- 工作副本: `~/astrbot_plugin_bangumi/` (fork truth source)
- AstrBot 加载副本: `~/astrbot/data/plugins/astrbot-plugin-bangumi-enhance/` (跟 fork diff 为空)
- fork remote: `origin` → `https://github.com/publieople/astrbot_plugin_bangumi.git`
- upstream remote: `upstream` → `https://github.com/united-pooh/astrbot_plugin_bangumi.git`
- 工作分支: `feat/xxx` (跟上游 main 不一致，需要 PR)

**PR 提交步骤**:

```bash
# 1. 同步两个副本 (AstrBot 加载的副本可能因热重载/手动改偏离 fork)
diff -q ~/astrbot/data/plugins/astrbot-plugin-bangumi-enhance/main.py ~/astrbot_plugin_bangumi/main.py
diff -q ~/astrbot/data/plugins/astrbot-plugin-bangumi-enhance/src/app/subscription_service.py ~/astrbot_plugin_bangumi/src/app/subscription_service.py
# 两个都 diff 为空 → 同步

# 2. 在 fork 仓 commit + push
cd ~/astrbot_plugin_bangumi
git add main.py src/app/subscription_service.py
git -c user.name="publieople" -c user.email="publieople@outlook.com" commit -m "fix: ..."
git push origin feat/xxx

# 3. 在 upstream 仓提 PR (用 gh CLI, 需 gh 已认证)
gh pr create --repo <upstream-owner>/<repo> --base main \
  --head publieople:feat/xxx \
  --title "fix: <一句话>" \
  --body "## 根因 ..."
# 如果 gh 报 "pull request already exists", 说明这个 head 分支已经有 PR, 改 push 后自动更新 head SHA
```

**CI 失败的常见原因 + 修法**:

#### Ruff format check 失败（最常见）

**症状**: CI 日志 `Would reformat: <file>` 跑 `ruff format --check .`

**根因**: ruff 0.13+ 的 formatter 比旧版严格，CI 装的 ruff 版本跟你本地的可能不一致。

**修法**:
```bash
cd ~/astrbot_plugin_bangumi
uvx ruff format .          # 不要带 --check, 直接格式化
git diff                   # 确认改动符合预期
git add <files>
git -c user.name="..." -c user.email="..." commit --amend --no-edit
git push --force-with-lease origin feat/xxx   # amend 改写 SHA, 必须 force push
```

**坑**: force-push 后**还要再 amend 一次**才能把格式化的代码进 commit。第一次 amend 经常忘记把 working tree 的格式化 diff add 进去，导致 CI 仍报"Would reformat"。**完整流程**:
```bash
# 第一次 amend 漏了 working tree 改动 → CI 还 fail
uvx ruff format .
git diff  # 看到 working tree 还有 diff
git add <files>
git commit --amend --no-edit  # 第二次 amend
git push --force-with-lease origin feat/xxx
```

#### pytest 失败：旧 test 写死了 buggy 行为

**症状**: 你的修复改了某个常量/枚举值，但 fork 的 test 还 assert 旧值。CI 跑全套 pytest 时这个 dead test 红。

**例**: 本次 `tests/app/test_subscription_service.py:176` 写死 `assert == "aiocqhttp:group:group"`，修复后变成 `aiocqhttp:GroupMessage:group`。

**修法**:
```bash
# 同步改 fork 的 test 文件 (data/plugins/ 副本是 release 复刻, 不需要 test)
vim tests/app/test_subscription_service.py
# 改成新值
git add tests/app/test_subscription_service.py
git commit --amend --no-edit
git push --force-with-lease origin feat/xxx
```

**原则**: 修复代码的同时同步改 dead test，否则 PR 合不上游。这是 fork-only 的清理活，不要顺手改非 dead 的 test。

#### pytest 失败：新命令没在 README 登记

**症状**: `tests/test_project_manifest.py` 报错 `assert commands <= readme_commands`，列出你的新命令 (`Extra items in the left set: '放送测试'`)。

**根因**: 上游维护的 manifest test 用 AST 扫 main.py 的 `@command(...)` 装饰器，要求所有注册的 command 都在 README.md 的指令表里登记。

**修法**:
```bash
# 在 README.md 指令表加一行
echo '| `/放送测试` | (调试) 模拟一次推送... | `[subject_id]` | `/放送测试 622206` |' >> README.md
git add README.md
git commit --amend --no-edit
git push --force-with-lease origin feat/xxx
```

#### gh pr create 报 "pull request already exists"

**症状**: `gh pr create --head publieople:feat/xxx --repo <upstream>` 报
> a pull request for branch "publieople:feat/xxx" into branch "main" already exists

**原因**: 之前已经用这个 head 分支开过 PR。**不是错**，是 gh 提示。PR 的 head SHA 会自动跟随你后续的 force-push 更新。

**处理**:
```bash
# PR 已经在, 直接 force-push amend 后的 commit 即可
git push --force-with-lease origin feat/xxx
# 用 gh pr view --json headRefOid 确认 PR head 同步到新 SHA
gh pr view <N> --repo <upstream> --json headRefOid --jq .headRefOid
```

#### 等 CI 的循环

CI runner 起 run 大约 1-3 分钟，可以循环看:
```bash
for i in $(seq 1 20); do
  sleep 15
  s=$(gh pr checks <N> --repo <upstream> 2>&1)
  echo "--- $i ($(date +%H:%M:%S)) ---"; echo "$s"
  if echo "$s" | grep -q "pass"; then echo "✅ PASSED"; break; fi
  if echo "$s" | grep -qE "fail|failure"; then echo "❌ FAILED"; break; fi
done
```

#### 完整自检流程（push 前一次性跑完，避免多轮 force-push）

```bash
cd ~/astrbot_plugin_bangumi

# 1. ruff lint + format
uvx ruff check . && uvx ruff format --check .
# 失败 → uvx ruff format . 然后 commit amend

# 2. mypy (跟 CI 一致)
uvx --with mypy --with types-PyYAML mypy src main.py
# 失败 → 修代码, 不允许加 # type: ignore 绕过

# 3. pytest 单独跑 (不依赖 requirements.txt 重依赖)
uvx --with pyyaml --with pytest python -m pytest tests/test_project_manifest.py -q
# 失败 → README 加新命令登记

# 4. 看 git status 确认没遗漏 working tree 改动
git status --short
# 只剩 ?? (untracked) 是允许的, M (modified) 必须 add+amend

# 5. push
git push --force-with-lease origin feat/xxx
```

**关键原则**:
- **永远先在 fork 仓 amend + force-push**，不要在 AstrBot 加载副本改完直接 restart（下次又回到 fork，状态漂移）
- **force push 用 `--force-with-lease`**，不用 `--force`，避免覆盖别人的 push
- **PR head SHA 同步验证**: `gh pr view <N> --json headRefOid` 跟 `git rev-parse HEAD` 必须一致

### §5.1 修改完代码没生效（用户记忆里的"插件会热重载"是错觉）

**症状**：改完 `subscription_service.py`、看到 grep 验证文件确实改了，**但日志里仍然刷老报错** / **群里仍然没通知**。

**根因**：AstrBot 的 watcher 默认未启。`star_manager.py:210` 显式 `if os.getenv("ASTRBOT_RELOAD", "0") == "1"`，`astrbot run` 不传 `--reload` 也不设 env 时，文件监听 task 根本没创建。**改了文件不会自动 reload 进运行进程**。

**诊断**（别再凭印象走）：
```bash
# 进程是否启了 watcher
PID=$(pgrep -f 'astrbot run' | head -1)
tr '\0' '\n' < /proc/$PID/cmdline | grep -E 'reload|ASTRBOT'
# 空 = 没启
cat /proc/$PID/environ | tr '\0' '\n' | grep ASTRBOT_RELOAD
# 无输出 = env 没设

# 验证文件改了 vs 内存里还是旧的
grep -c "GroupMessage" ~/astrbot/data/plugins/astrbot-plugin-bangumi-enhance/src/app/subscription_service.py
# 0 = 文件没改成功；>=1 = 文件改了但没 reload
```

**修复**：走 `sudo systemctl restart astrbot`，别再找"reload 单个插件"的快捷方式——dashboard API 有 `POST /api/plugins/reload`，但要鉴权 (`require_plugin_scope`)，比 restart 麻烦；而且 `restart` 才能彻底清 Python `import` 缓存，watcher 即便启了也救不回子模块。详见主 SKILL.md §3.5。

**永久解决**：`sudo systemctl edit astrbot` 加 `Environment="ASTRBOT_RELOAD=1"`，之后改 main.py 会自动重建 class 实例；改二级 .py（如 subscription_service.py）仍要手动 restart（Python 模块缓存）。

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
**降级**：calendar API 拉取失败时按当日档写入（不 shift），日志 `WARNING`。不影响启动。

**⚠️ BGM `/calendar` API 周末期不稳定的坑（2026-07-10 实测）**：第一次实现用 `service.get_calendar()` 拿 weekday 但**同一个 subject 在不同时刻调 calendar API 返回的 weekday 可能不同**（公仆群里 617123 反复在周三/周四之间漂）。**根因**：BGM calendar 缓存 TTL + 内部排序逻辑不稳定，不适合作为 weekday 真值源。

**根治**：weekday 直接从 **bgmlist `begin` ISO datetime** 拿（`.astimezone(CST).isoweekday()`），bgmlist 数据稳定可重现。改动 `src/api/bgmlist.py:_parse_broadcast_time` 返回 `(HH:MM, weekday)` 元组，`_auto_fill_broadcast_times` 用 bgmlist weekday 而非 calendar weekday。**不要把 BGM calendar weekday 当成"准的"**——它在生产观察中持续漂移。

### weekday 持久化到 DB（2026-07-10）

**为什么需要**：表格渲染按 `(wid, broadcast_time)` 排序，wid 必须稳定可查。如果每次都临时计算（拉 calendar 或推算），calendar 不稳定 + 推算时机不同 → 同一次刷新看到的 weekday 可能跟 DB 写入时的 wid 不同，**导致刷新完表格里 wid 漂移**（公仆群里 617123 反复在周三/周四漂就是这个）。

**存储**：给 `bangumi_subjects` 表加 `broadcast_weekday INTEGER` 列：

```sql
ALTER TABLE bangumi_subjects ADD COLUMN broadcast_weekday INTEGER;
```

模型层 (`src/db/models.py:BangumiSubject`) 加字段；`repository.set_subject_broadcast_time()` 增加可选 `broadcast_weekday` 参数；`repository.batch_update_broadcast_times()` 接受 `dict[str, tuple[str, int]]` 形式同步写 time + weekday。

**读取**：新增 `repository.get_subscribed_subjects(group_id)` 返回 `list[BangumiSubject]`（含 weekday），`/放送时间` 无参表格直接遍历用 `s.broadcast_weekday` 排序，不再调 calendar API。

**手动设置**：`/放送时间 <番剧> HH:MM` 不带 weekday（保留用户手动设的时间，weekday 维持现状）。

### 表格排序的隐藏 bug（2026-07-10 实测）

**症状**：表格输出顺序错乱（3, 5, 4, 4, 4, 6）而不是按 weekday 升序（3, 4, 4, 4, 5, 6）。DB 数据完全正确，但显示顺序错。

**根因**：构建 `entries: list[tuple[int, str, str]]` 用了 `sort_key` 但**漏掉 `entries.sort(key=lambda e: e[0])`**。Python list append 后默认是插入顺序。

**修法**（一行）：
```python
entries.append((sort_key, day, line))
entries.sort(key=lambda e: e[0])  # ← 别漏
```

**预防**：每次构建 tuple-of-tuples 用于后续分组展示时，立刻 grep 自己 `entries.sort` 是否存在。`list.sort()` 不存在的 tuple 容器 = 默默保持插入序 = 显示"看起来对实际乱"。

### `uv.lock` 不要 commit

fork 历史里 `uv.lock` 一直未跟踪（`.gitignore` 不一定显式列，但 commit 历史里从未有 uv.lock 改动）。**改动后看到 `?? uv.lock` 保持 untracked**，不要 `git add uv.lock`——PR review 会问这个文件哪来的。

## 30h 制放送时间显示约定（公仆偏好，2026-07-10）
**规则**：`broadcast_time` 字段存储和显示**保留 30h 制原始格式**，**不要归一化到 24h**。

**为什么**：深夜档番剧（凌晨 0:00~5:00 播出）在 30h 制下记作 `24:00` ~ `29:59`，对应 24h 制的次日 `00:00` ~ `05:59`。归一化会丢"次日"语义，用户看到 `00:28` 无法判断是昨晚还是今早。`/放送时间` 命令输出必须保持 `24:28` 形式（不是 `00:28`）。

**实现要点** (`main.py:_fmt_time`):
- `00:00 ~ 23:59` → 原样显示
- `24:00 ~ 29:59` → 原样显示（已是 30h 制）
- `None` / 空 / 解析失败 → 显示 `未设置` 或回退原值

**坑**：自动归一化（或 git merge 引入的 `int(h)%24`）会让所有 30h 时间变 24h，**改一行要全链路验证**：DB 存储 / 显示输出 / 日志 / 推送通知消息体。

**排序行为**：`/放送时间` 排版用 `wid * 10000 + _time_to_min(bt)` 作 sort_key，`_time_to_min("24:28") = 24*60+28 = 1468`，周一 `24:28` 排序 key = `11468`，周二 `00:30` = `20030`，**24:28 自动排到 00:30 之前**（深夜档属于周一而非周二），不需要特殊处理。

### 30h 设置项 + 自动落库（公仆 fork，2026-07-10 PR #18 收录）

**两个改进点**：

**1. 用户可关闭 30h 制** (`_conf_schema.json` + `config_manager.get_broadcast_time_30h`):
```json
"broadcast_time_30h": {
  "description": "放送时间 30 小时制显示",
  "type": "bool",
  "hint": "启用后, 深夜档(00:00-05:59)会显示为 24:00-29:59 区分次日,例如 24:28 表示次日 00:28",
  "default": true
}
```
关闭后 `24:28` 回落 `00:28`（24h 制）。**实现**：UI 展示用 `_fmt_time_cfg(bt)` 而不是 `_fmt_time(bt)`，前者读 config 决定要不要回退。

**2. 自动把深夜档写入 DB**（`_auto_fill_broadcast_times` 增强）:

bgmlist API 给的是 `HH:MM`（无 weekday），BGM `/calendar` 给的是 `{weekday_id, items:[{id}]}`（无 HH:MM）。**两者都没有完整信息**。但组合起来能反推档期：

```python
# _auto_fill_broadcast_times 内, 在拿到 bgmlist_data 之后:
weekday_for: dict[str, int] = {}
for day in await self.service.get_calendar():
    wid = (day.get("weekday") or {}).get("id", 0)
    for item in day.get("items") or []:
        weekday_for[str(item.get("id"))] = wid

def _shift_late_night(hhmm: str, wid: int) -> tuple[str, int]:
    h, m = hhmm.split(":", 1)
    hh = int(h)
    if hh < 5 and wid > 0:
        # hh<5 视为前一日档期, hh+24 → 写入 24:28 这种形式
        return f"{hh + 24:02d}:{m}", wid - 1 or 7
    return hhmm, wid

# 对每部番:
raw = bgmlist_data.get(subject_id)
shifted, _ = _shift_late_night(raw, weekday_for.get(subject_id, 0))
to_update[subject_id] = shifted
```

**为什么 <5 是阈值**：05:00 之前的播出基本是深夜档（前一晚档期的尾巴），05:00 之后一般算"次日早晨"。公仆的"少女怪兽焦糖味"周五 00:28 → 入库 `24:28` → `/放送时间` 表格里显示在周四（wid=5 → wid=4）。

**手动兜底**：`/放送时间 <番剧> HH:MM` 接受的格式也从 `[01]\d|2[0-3]` 放宽到 `[01]\d|2[0-9]`，允许直接写 `24:28`（凌晨手动调时用）。**不要**改 `time_pattern` 时漏这个，会写不进 DB。

**降级**：calendar API 拉取失败时按当日档写入（不 shift），日志 `WARNING`。不影响启动。

**⚠️ BGM `/calendar` API 周末期不稳定的坑（2026-07-10 实测）**：第一次实现用 `service.get_calendar()` 拿 weekday 但**同一个 subject 在不同时刻调 calendar API 返回的 weekday 可能不同**（公仆群里 617123 反复在周三/周四之间漂）。**根因**：BGM calendar 缓存 TTL + 内部排序逻辑不稳定，不适合作为 weekday 真值源。

**根治**：weekday 直接从 **bgmlist `begin` ISO datetime** 拿（`.astimezone(CST).isoweekday()`），bgmlist 数据稳定可重现。改动 `src/api/bgmlist.py:_parse_broadcast_time` 返回 `(HH:MM, weekday)` 元组，`_auto_fill_broadcast_times` 用 bgmlist weekday 而非 calendar weekday。**不要把 BGM calendar weekday 当成"准的"**——它在生产观察中持续漂移。

### weekday 持久化到 DB（2026-07-10）

**为什么需要**：表格渲染按 `(wid, broadcast_time)` 排序，wid 必须稳定可查。如果每次都临时计算（拉 calendar 或推算），calendar 不稳定 + 推算时机不同 → 同一次刷新看到的 weekday 可能跟 DB 写入时的 wid 不同，**导致刷新完表格里 wid 漂移**（公仆群里 617123 反复在周三/周四漂就是这个）。

**存储**：给 `bangumi_subjects` 表加 `broadcast_weekday INTEGER` 列：

```sql
ALTER TABLE bangumi_subjects ADD COLUMN broadcast_weekday INTEGER;
```

模型层 (`src/db/models.py:BangumiSubject`) 加字段；`repository.set_subject_broadcast_time()` 增加可选 `broadcast_weekday` 参数；`repository.batch_update_broadcast_times()` 接受 `dict[str, tuple[str, int]]` 形式同步写 time + weekday。

**读取**：新增 `repository.get_subscribed_subjects(group_id)` 返回 `list[BangumiSubject]`（含 weekday），`/放送时间` 无参表格直接遍历用 `s.broadcast_weekday` 排序，不再调 calendar API。

**手动设置**：`/放送时间 <番剧> HH:MM` 不带 weekday（保留用户手动设的时间，weekday 维持现状）。

### 表格排序的隐藏 bug（2026-07-10 实测）

**症状**：表格输出顺序错乱（3, 5, 4, 4, 4, 6）而不是按 weekday 升序（3, 4, 4, 4, 5, 6）。DB 数据完全正确，但显示顺序错。

**根因**：构建 `entries: list[tuple[int, str, str]]` 用了 `sort_key` 但**漏掉 `entries.sort(key=lambda e: e[0])`**。Python list append 后默认是插入顺序。

**修法**（一行）：
```python
entries.append((sort_key, day, line))
entries.sort(key=lambda e: e[0])  # ← 别漏
```

**预防**：每次构建 tuple-of-tuples 用于后续分组展示时，立刻 grep 自己 `entries.sort` 是否存在。`list.sort()` 不存在的 tuple 容器 = 默默保持插入序 = 显示"看起来对实际乱"。

### `uv.lock` 不要 commit

fork 历史里 `uv.lock` 一直未跟踪（`.gitignore` 不一定显式列，但 commit 历史里从未有 uv.lock 改动）。**改动后看到 `?? uv.lock` 保持 untracked**，不要 `git add uv.lock`——PR review 会问这个文件哪来的。

## 30h 制放送时间显示约定（公仆偏好，2026-07-10）

`broadcast_time` 字段值在**推送通知消息体**里也被读出来展示（详见上文 "通知不包含放送时间" 段）。如果开了 30h 制但没跑 `_auto_fill_broadcast_times` 重新入库，推送消息里的 `⏰ 放送时间: 00:28` 仍是 24h 制——这是 DB 实际值，不是显示逻辑问题。**修复后跑一次 `/刷新放送` (overwrite=true) 让所有条目重写一遍**。

## `/放送时间` 重排后的行为（公仆 fork，2026-07-10）

**改动前**：按订阅顺序列出每部番 `HH:MM`，不便看一周节奏。

**改动后**：拉 BGM `/calendar` 拿到 weekday → 把本群订阅映射到 weekday → 按 `(weekday, broadcast_time)` 排序 → 输出分天分组表。

**输出格式**：
```
📺 本群订阅放送时间表:

【周一】
  XX (ID: 123) [22:00]
  YY (ID: 456) [24:28]      ← 深夜档用 30h 制

【周二】
  ZZ (ID: 789) [21:30]

【未排期】                   ← 已完结 / 不在当前 calendar 中
  AA (ID: 999) [未设置]
```

**降级**：calendar API 拉取失败时回退到原按订阅顺序展示，日志记 `WARNING`。不会因为 BGM 接口问题阻塞 `/放送时间`。

## 插件重载撞 cron 轮询的 traceback（2026-07-10 实测）

**症状**：用户在 WebUI 点 "重载插件" 时（**正好赶上** 15 分钟 cron 轮询点），journal 出现一段看似严重的 traceback：

```
[app.subscription_service:254] in check_updates
  File ".../subscription_service.py", line 254, in check_updates
    latest_episode = await self.service.get_latest_episode(...)
  ...
aiohttp client.py: session.request
  RuntimeError: Session is closed
```

**实际原因**：reload 流程 = 卸载旧 class → 触发 `terminate()` 关共享 aiohttp session → 加载新 class。但 `terminate()` **不等**正在飞的 `check_updates()` 跑完，新 session 创建前旧 session 已经关。

**是否要紧**：**不要紧**。下次 15 分钟轮询点恢复，下个 episode 拉取走新 session 即可。订阅无丢失、DB 一致。

**用户可见症状**："为什么重载插件会报错" → 解释清楚别让人误以为是 bug。

**避免**：在自己写插件的 `terminate()` 里 `await self.scheduler_manager.scheduler.shutdown(wait=True)` 等待 in-flight job。但**不要**为了这个改 upstream — 修法不直观，且代价是 reload 阻塞等 14 部 API 全跑完（>30 秒）。
