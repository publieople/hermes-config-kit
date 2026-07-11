---
name: astrbot-plugin-development
description: Build an AstrBot plugin — covers fork-existing vs from-scratch decision, 4-quadrant research gate, doc reading order, decorator mechanics, schema field patterns, ad-hoc verification. Use when user asks to "做一个 AstrBot 插件" or "集成 X 到 AstrBot" or describes a bot feature.
---

# AstrBot plugin development

## 0. 4-quadrant research gate (BEFORE writing code)

**Never start coding without doing all 4 first.** User has corrected this twice in one session.

1. **YAGNI?** — explicitly answer "do we need this at all" in one line. If speculative, push back.
2. **Ecosystem has it?** — search GitHub + AstrBot official `Plugins_Collection` (1317 plugins) `plugins.json` for the feature. `gh repo fork X --clone=false` to candidate repos.
3. **Docs read?** — minimum: `https://docs.astrbot.app/dev/star/plugin-new.html` (skeleton) + `plugin-config.html` (`_conf_schema.json` field types). For LLM tools also read `en-dev-star-guides-ai` wiki.
4. **API reality check** — if the plugin wraps an external API, curl one real call before writing client code. Public web UIs without documented APIs = reject (do NOT reverse-engineer; will rot).

After all 4, **present findings + option list + ask user to pick**. Don't write code until they pick.

## 1. Skeleton (4 files, ~50 lines minimum)

```
astrbot_plugin_<name>/
├── metadata.yaml         # name, version, author, repo (AstrBot reads this to recognize the plugin)
├── main.py               # @register class(Star) with __init__/initialize/terminate
├── _conf_schema.json     # user-editable config; _conf_schema.json drives WebUI form
├── requirements.txt      # even if deps are already installed (AstrBot reads this)
└── .gitignore            # __pycache__/ + any local cache dirs (imgs/, db.sqlite, etc.)
```

`metadata.yaml` template:
```yaml
name: astrbot_plugin_<name>
display_name: <中文展示名>
desc: <一句中文 desc>
version: v0.1.0
author: <github user>
repo: https://github.com/<user>/astrbot_plugin_<name>
```

`main.py` minimum:
```python
from astrbot.api.star import Context, Star, register
from astrbot.api.event.filter import command, llm_tool
from astrbot.api import logger

@register("astrbot_plugin_<name>", "<author>", "<desc>", "v0.1.0", "<repo>")
class MyPlugin(Star):
    def __init__(self, context: Context, config: Optional[dict] = None):
        super().__init__(context)
        self.config = config or {}

    async def initialize(self):
        ...

    async def terminate(self):
        ...
```

## 2. Decoration mechanics — read this before writing commands

**Critical constraint:** Decorators are scanned at **class-load time**, not runtime. Cannot register commands in a loop. The class body must contain N literal `@command("foo")` / `@llm_tool(name="bar")` decorated methods.

```python
@command("hello")           # registered at import
async def cmd_hello(self, event): ...

@llm_tool(name="my_tool")    # AI may auto-invoke
async def tool_my(self, event, arg: str = ""): ...
```

For N similar commands (e.g. one per category), if N is large use **one @command + alias parser** instead of N decorators. Aliases go in a `dict[str, str]` resolved at runtime.

For `_conf_schema.json` field types supported: `string`, `text`, `int`, `float`, `bool`, `object`, `list`, `dict`, `template_list`. Special values: `select_provider`, `select_provider_tts`, `select_provider_stt`, `select_persona`, `select_knowledgebase`. For multi-select use `list` with `items: {type: "string", options: [...], labels: [...]}` (labels show in WebUI as Chinese names). See references/schema-field-patterns.md.

## 3. LLM tool function signature

```python
@llm_tool(name="my_tool")
async def tool_my(self, event: AstrMessageEvent, param1: str = ""):
    '''One-line summary.

    Args:
        param1(string): description (type: string|number|object|array|boolean)
    '''
    # process
    return "string result"  # returned to LLM for next turn
```

Function docstring's `Args:` block IS the JSON schema AstrBot generates. Missing/wrong format → empty schema, tool won't get called.

## 3.5 Calling LLM from within a plugin (programmatic, not tool)

Use when you need LLM text generation inside a handler without the LLM itself deciding to invoke a tool.

```python
provider = self.context.get_using_provider()
if not provider:
    return fallback
try:
    resp = await provider.text_chat(
        prompt="Your instruction text here",
        session_id=f"_internal_{some_unique_id}",
        contexts=[],
        model=None,  # optional override
    )
    result = (resp.completion_text or "").strip()
except Exception as e:
    logger.warning(f"LLM call failed: {e}")
    result = fallback
```

**Pitfalls:**
- `session_id` must not collide with real LLM sessions — prefix with `_`
- `contexts=[]` is single-turn — correct for translation/classification
- Some providers raise `TypeError` when `model=` is passed; catch bare except or try without model
- `resp.completion_text` may be `None` — check before `.strip()`
- AstrBot log may go to stdout when started directly; test via response instead of log files

## 4. Sending messages

- `yield event.plain_result("text")` — for text
- `yield event.image_result(url)` — image from URL (framework downloads to local)
- `yield event.chain_result([Image.fromURL(url), Plain("text")])` — mixed

Image component import: `from astrbot.core.message.components import Image` (note: NOT `from astrbot.api.message_components` — that's a re-export, core is the real one).

## 5. Verifying it works

AstrBot logs to systemd journal (NOT to `~/astrbot/logs/` for v4.x). Verify with:
```bash
sudo systemctl restart astrbot
sudo journalctl -u astrbot --since '30 seconds ago' --no-pager | grep -iE '<plugin_name>|error|exception|traceback'
```

Success looks like:
- `Loading plugin <plugin_name> ...`
- `Added llm tool: <tool_name>` (if you have one)
- No Traceback after the Loading line

### 5.1 Hot reload is NOT automatic by default — must restart

AstrBot v4 has **no built-in file-watch hot reload for plugins** by default. Verified from `star_manager.py:210`:

```python
if os.getenv("ASTRBOT_RELOAD", "0") == "1":
    asyncio.create_task(self._watch_plugins_changes())
```

The `--reload` CLI flag and `ASTRBOT_RELOAD=1` env var enable a `watchfiles` watcher, but:
- Official docs only describe **manual reload via WebUI** (Plugin page → `...` → Reload Plugin)
- systemd service (`/etc/systemd/system/astrbot.service`) doesn't set `ASTRBOT_RELOAD=1` by default
- So in production, every code change requires `sudo systemctl restart astrbot` to load new code

**Don't trust user memory that "plugins auto-reload on edit"** — verify:
```bash
systemctl show astrbot.service | grep -i Environment=
# If Environment= lacks ASTRBOT_RELOAD=1, no watcher is running.
```

Enable hot reload once for development:
```bash
sudo systemctl edit astrbot
# Add:
#   [Service]
#   Environment="ASTRBOT_RELOAD=1"
sudo systemctl daemon-reload
sudo systemctl restart astrbot
```
Then on plugin code save, AstrBot logs `检测到插件 <name> 文件变化，正在重载...` and reloads automatically.

## 6. Ad-hoc verification (after building, before claiming done)

System requires this. Create `/tmp/hermes-verify-<plugin>.py` with checks for:
- metadata.yaml: name, version, author, repo
- _conf_schema.json: expected fields, correct defaults
- main.py: ast.parse, decorator presence (walk FunctionDef + ClassDef — @register is on the class), all expected methods defined
- Live external API call (if applicable): real HTTP, real key, real test image
- Repo hygiene: requirements.txt present, .gitignore covers __pycache__, no stray test scripts in /tmp

Run with the venv that has the plugin's deps: `~/.local/share/uv/tools/astrbot/bin/python3` (system python lacks httpx/aiohttp).

**Delete the script after it passes.** State as "ad-hoc verification, 1-shot, deleted" — never claim "fully verified".

## 7. Git workflow (when publishing to fork)

```bash
gh repo fork <upstream> --clone=false   # creates fork + auto-adds 'upstream' remote
cd ~/astrbot/data/plugins/<name>
gh repo clone <user>/<name>              # clone the fork (not upstream)
git remote -v                            # confirm: origin = fork, upstream = original
```

Add `.gitignore` for `__pycache__/`, `*.pyc`, and any local cache dirs (`imgs/`, `*.db`, etc.) BEFORE first commit or pycache gets committed.

### 7.1 Updating an existing PR (no new PR needed)

When you have an **existing open PR** from a fork to upstream, and you want to add more changes:

```bash
# Clone the fork's specific branch (not main)
gh repo clone <user>/<repo> -- --branch <feature-branch>

# Edit files, commit
git add .
git commit -m "feat: description"
git push origin <feature-branch>
```

GitHub auto-updates the open PR. No new PR needed, no force-push required on a solo branch.

Clone tip: `gh repo clone publieople/astrbot_plugin_bangumi -- --branch feat/post-subscribe-broadcast-fill` correctly sets `origin` to the fork and `upstream` to the original repo, with the branch already checked out.

## 7.2 Process verification before claiming done

Calling work done after "check + push + PR update" needs a final process check: have I loaded and followed all relevant skills? If the user says "检查流程规范" or hints at process, re-scan available skills for workflow/process skills before responding.

## 8. Publishing to the AstrBot Plugin Marketplace

Once built and tested, submit so other users can install from the marketplace.

### Submission flow (mid-2026)

1. **Ensure code on GitHub** — `publieople/astrbot_plugin_<name>`
2. **Go to** https://plugins.astrbot.app → click `+` (bottom-right blue FAB)
3. **Fill form** (see fields below) → tags use a separate `+` button, not Enter
4. **Click `Submit to GITHUB`** → redirects to `AstrBotDevs/AstrBot_Plugins_Collection` with a pre-filled Issue
5. **Verify the Issue JSON** has correct fields → **check all 3 checkboxes** → click `Create`

**Old method (deprecated):** Submitting Issues on the AstrBot main repo is no longer used.

### Issue template JSON (must be exact, from `PLUGIN_PUBLISH.yml`)

```json
{
  "name": "astrbot_plugin_<name>",
  "display_name": "可读的展示名",
  "desc": "插件简介",
  "author": "publieople",
  "repo": "https://github.com/publieople/astrbot_plugin_<name>",
  "tags": ["AI", "图像检测", "安全"],
  "social_link": ""
}
```

Notes:
- `repo` MUST NOT end with `.git` — CI's `normalize_repo_url()` explicitly strips `.git` and validates against GitHub
- `tags` is optional but strongly recommended for discoverability in the marketplace
- `social_link` is optional (e.g. personal site, GitHub profile)

**Checkboxes (all required):**
1. My plugin has undergone thorough testing.
2. My plugin does not contain malicious code.
3. I have read and agree Code of Conduct.

### AstrBot Plugin Marketplace form fields (from `plugins.astrbot.app` SPA)

| Field | Type | Required | Note |
|-------|------|----------|------|
| 插件名 | text | ✅ | Must start with `astrbot_plugin_` |
| 展示名称 | text | ✅ | Human-readable name |
| 插件描述 | textarea | ✅ | Brief intro |
| 作者名 | text | ❌ | GitHub username |
| 社交链接（可选） | text | ❌ | e.g. GitHub profile URL |
| 插件仓库链接 | text | ❌ | Full GitHub repo URL |
| 标签 | tag-input | ❌ | Type tag, click blue `+` button |

### Browser interaction notes (plugins.astrbot.app SPA)

The form is a Vuetify (Vue 3) SPA. When using browser tooling:
- Navigate to root `/` first — `/publish` or `/submit` show an empty shell
- Page may appear blank while JS loads; wait for snapshot/vision to confirm rendered
- Click the bottom-right `+` (blue FAB) to open the form dialog
- **Tag input**: type tag name → click separate blue `+` button (not Enter). Repeat per tag
- **Ref IDs** shift after each interaction (Vue re-render); re-snapshot before each click
- Submit redirects to GitHub sign-in page (pre-filled Issue behind auth); user must be logged in to complete

### What CI validates (from `scripts/validate_plugins/run.py`)

| Stage | What it checks | Failure reason |
|-------|----------------|----------------|
| **repo_url** | URL must be `https://github.com/*/*`, no `.git` suffix | malformed URL |
| **git clone** | Clones the repo (`--depth 1`, 120s timeout). Must be public & accessible. | 404, private, network error |
| **metadata check** | `metadata.yaml` must exist. Required fields: `name`, `desc`, `version`, `author`. No merge conflict markers. Must have `main.py` or `{name}.py`. | missing/wrong fields, missing entrypoint |
| **worker load** | Copies plugin dir into `data/plugins/`, calls `PluginManager.load(specified_dir_name=...)` in a sandbox. AstrBot's `requirements.txt` is pre-installed. | import error, `@register` failure, missing dependency |
| **zip size** | Generated zip must be ≤ 16MB | oversized; clean `.gitignore` of `__pycache__`, `.git`, `node_modules` |

Key: the worker literally clones your repo, copies the plugin into AstrBot's `data/plugins/`, and imports it. If `import astrbot_plugin_xxx` fails in a clean AstrBot env, the CI rejects it.

### Marketplace metadata (from `scripts/transform_plugin_data/run.py`)

After the Issue passes CI, a cron job (`transform-plugin-data.yml`, hourly) builds the marketplace cache by:

1. **GitHub API**: fetches stars, last updated, default branch for each plugin repo
2. **metadata.yaml on GitHub**: extracts `version`, `astrbot_version` (optional), `support_platforms` (optional)
3. **logo.png** from repo root: if present, shown as the plugin card icon

So `logo.png` is optional but makes your plugin look better in search results.

### metadata.yaml checklist (for marketplace discoverability)

```yaml
name: astrbot_plugin_<name>         # required — matches dir name
display_name: <中文展示名>           # recommended — shows in WebUI
desc: <一句 desc>                    # required
version: v0.1.0                     # required — read by marketplace
author: <github user>               # required
repo: https://github.com/...        # required — NO .git suffix
tags: [AI, 图像检测, 安全]          # recommended for discoverability
astrbot_version: ">=4.0.0"         # optional — AstrBot version compatibility
support_platforms:                  # optional — supported IM platforms list
  - qq
  - telegram
```

### Reference files

- Official docs: https://docs.astrbot.app/dev/star/plugin-publish.html
- Plugins Collection Issue template: `AstrBotDevs/AstrBot_Plugins_Collection/.github/ISSUE_TEMPLATE/PLUGIN_PUBLISH.yml`
- Live `plugins.json`: `https://github.com/AstrBotDevs/AstrBot_Plugins_Collection/blob/main/plugins.json`
- Validation source: `scripts/validate_plugins/run.py` in the same repo
- Transform source: `scripts/transform_plugin_data/run.py` — reads version/astrbot_version/support_platforms from metadata.yaml

## Pitfalls (from real sessions)

- `@register` lives on the **class**, not the function. AST checkers that only walk `FunctionDef` will miss it.
- `config.get(key, default)` is fine for config — config is a dict, not a typed object.
- Don't reverse-engineer web UIs (e.g. isgen.ai has no public API; reverse-engineering is fragile).
- Per-generator / per-model scores from third-party APIs are often **not available on free tier** — don't pretend they are.
- Use `httpx` not `requests` (AstrBot's own modules use `aiohttp`; httpx is simpler for one-shot async calls).
- `event.unified_msg_origin` is the per-session key for cooldown / rate-limiting / per-user state.
- Image component fields: `Image.url`/`file`/`path` are ALL local temp paths (AstrBot downloads images before delivery). For external APIs, upload the file via multipart — see `references/common-bugs.md`.
- Version number: **only in `metadata.yaml`** — do NOT manually sync the version string in `@register(...)` decorator with metadata.yaml. Keep both the same but only bump in metadata.yaml after a release; `@register`'s desc field describes the plugin, it's not a version authority.
- **Repo URL cannot end with `.git`** — CI's `normalize_repo_url()` explicitly strips `.git` suffix, so `https://github.com/user/name` (no `.git`) is the canonical form. This applies to both `metadata.yaml` and the Issue JSON.
- **Duplicate `import aiofiles`** — AstrBot v4 bundles `aiofiles>=25.1.0` (confirmed from requirements.txt), so `import aiofiles` at module level works fine. Don't also re-import inside the function body where it's used — one import at the top is enough. More generally, don't inline-import deps that are already imported at module level or known to be in AstrBot's bundled deps.
- **Test env dependency** — Plugin tests (pytest) depend on AstrBot runtime packages (aiohttp, pydantic, sqlalchemy, astrbot core). Running from a standalone git clone's `.venv` will fail with `ModuleNotFoundError`. Either run from the AstrBot install dir's venv or install deps manually. Test collection fail ≠ code broken.
- **User says "检查流程规范"** — this is a signal you skipped a process skill. Load `code-review-and-quality` and `finishing-a-development-branch` explicitly, announce you're using them, and step through. Pro forma completion without the skill scan gets corrected.
- **mypy `no-any-return` with `getattr` guard** — Many AstrBot plugins use `storage = getattr(self, "storage", None)` as a guard before calling methods. `getattr` returns `Any`, so when you change a method from `-> None` to `-> int` and `return updated`, mypy flags `no-any-return`. Fix: `return updated  # type: ignore[no-any-return]` — the smallest diff, matches how mypy already treats `Any` from `getattr`.
- **README must document every command** — Some plugins have a CI test that parses all `@filter.command(...)` / `@filter.command_group(...)` from `main.py` and checks each appears as a `| \\`/command\\` |` row in `README.md`. Adding a new command without adding its README row = CI failure. Check `tests/test_project_manifest.py` or similar for a `test_readme_documents_registered_commands` function. Fix: add a table row with the command name, description, params, and example.
- **CustomFilter 的 `/` 前缀问题** — AstrBot 消息事件中命令可能带 `/`（如 `/aimg`），但 `event.message_obj.message_str` 可能包含也可能不包含 `/` 前缀（取决于适配器）。CustomFilter 必须同时检查有 `/` 和无 `/` 两种形式，或者用 `removeprefix("/")` 统一处理后再检查。不加全的话 `/aimg` 会漏过 filter 走 LLM。`Img2ImgFilter`、`HelpFilter` 等同理。
- **B站 API 阻止 aiohttp 但放行 curl** — B站反爬检测 Python HTTP 库（aiohttp/urllib/requests）的 TLS 指纹并返回 412。日志显示 `bad JSON from api.bilibili.com`（HTML 被当 JSON 解析）。修复：尝试 `search/all/v2` 端点替代被封的 `search/type`；或 subprocess+curl 做 fallback。新端点返回格式不同——结果在 `data.result[]` 中以 `result_type` 分节（`bili_user`, `video`），需遍历提取。
- **Plugin 有两份副本 — fork 真理源 vs `data/plugins/` 实载** — AstrBot 实际加载的是 `~/astrbot/data/plugins/<plugin_dir>/`，但用户通常 fork 在 `~/astrbot_plugin_<name>/` 维护。两份必须保持同步——改一份忘了另一份 = 调试时怀疑人生。规则：fork 目录是真理源（push/PR 都在这里），改完先 diff 同步到 `data/plugins/`，再 restart。`diff -q <fork>/file <data_plugins>/file` 验证同步。
- **`ruff format` 必须跑全项目，不只改动的文件** — fork 项目（如 `astrbot-plugin-bangumi`）的 CI 跑 `ruff format --check .` 和 `ruff check .`，作用在整个项目。本地只 `ruff format main.py src/app/subscription_service.py` 可能漏过其它文件的格式问题——CI 会以"Would reformat: <file>"失败。同理 `ruff check .`。永远跑完整项目。
- **`git commit --amend` 前必须保证 working tree 干净** — 修改文件后 amend 只把 staged 改动折进 commit。如果 amend 后又跑了 `ruff format` 修改 working tree 但没 add+amend，commit 内容与 working tree 漂移。force-push 之后 CI 跑 commit 里的代码，声称"需 reformat"（因为 working tree 的 reformat 没进 commit）。修复: amend 前 `git status --short`；或先 `git add -u && git commit --amend`；或 amend 后 `git status` 确认无 M。
- **PR title/body 更新用 `gh pr edit --title --body`** — `gh pr create` 对已存在的 PR 会报"already exists"。要改标题/正文用 `gh pr edit <num> --title "..." --body "..."`。PR head SHA 变更（force push 后）由 GitHub 自动同步到 PR——`gh pr view <num> --json headRefOid --jq .headRefOid` 验证同步完成。
- **AstrBot v4 session 字符串 = `platform_id:MessageType.GroupMessage:session_id`** — 不是 adapter 类名（不是 `aiocqhttp`）。`platform_id` 是用户在 `cmd_config.json` 里 `platforms[].id` 字段配的（公仆这里叫 `default`）；`MessageType` 枚举合法值是 CamelCase `GroupMessage`/`FriendMessage`/`OtherMessage`（来自 `astrbot/core/platform/message_type.py`）。常见错误：
  - 用 adapter 名 `aiocqhttp` 当 platform_id → `context.send_message` 在 `platform_manager.platform_insts` 找不到匹配 → 报 `主动发送未找到平台`
  - 用 aiocqhttp 事件 payload 里的 `group` 当 MessageType → 报 `不合法的 session 字符串: 'group' is not a valid MessageType`
  修法：枚举 `context.platform_manager.platform_insts`，找到 `meta().name == 'aiocqhttp'` 的 adapter，用 `meta().id` 拼真 session。详见 `references/session-string-format.md`。
- **测试「轮询 → 状态变更 → 推送」链路的捷径** — 当插件架构是「定时从外部 API 拉数据 → 检测到变更 → 推送通知」（如 BGM 番剧追番），`check_updates` 在生产里可能几小时甚至几天才触发一次新推送分支。集成测试和单测都难复现。最干净的调试方式是：**临时把 DB 状态回退一步**（如 `current_episode -= 1`），让下一次定时器自然走完 `API fetch → diff → notify → send_message` 全路径。配合 `/<plugin>测试 <id>` 命令比 cron 等几分钟快几十倍。回退值会被定时器自动写回真值，不需要单独回滚逻辑（异常分支才需要）。
- **Plugin reload 与 cron 触发撞点的 race** — 用户在 WebUI 重载（或 `sudo systemctl restart`）插件时，恰好撞上 15 分钟轮询点，`terminate()` 关共享 aiohttp session 后 `check_updates` 还在 await → traceback 在 `aiohttp session.request` 的 `session closed` 错误。表现吓人但无副作用（下次轮询点恢复）。不是 fix 优先级，**先记日志即可**，别急着加 `await in_flight_task` 或 graceful shutdown——除非用户主动反馈 reload 后推送漏发才处理。开发期 `ASTRBOT_RELOAD=1` 下尤其常见，因为 reload 频率高。

- **ASTRBOT_RELOAD=1 实际状态要验证，别信用户记忆里"插件改了自动热重载"** — v3 时代有自动 reload 行为，v4 必须显式 `ASTRBOT_RELOAD=1` 才启 watcher。验证：```bash
  cat /proc/$(pgrep -f 'astrbot run' | head -1)/environ | tr '\0' '\n' | grep ASTRBOT_RELOAD
  # 无输出 = 没启 watcher, 改了代码必须 sudo systemctl restart astrbot
  ```
  即使 watcher 启用，**子模块（`src/app/subscription_service.py` 这种被 import 的）不会重新 import** — Python 模块缓存机制。watcher 只重建 main.py 的 class 实例，编辑 sub-module 必须 restart。`ASTRBOT_RELOAD=1` 适合频繁改 main.py 的开发期；生产前关掉以避免 reload×cron race（见上条）。

- **30h 制 / 跨日档期显示：time 和 weekday 不在同一个数据源时，把 weekday 也存进 schema** — bgmlist API 只给 HH:MM 不给 weekday，单纯"hh<5 +24 → 26:08"会出现"展示在周六但用户期望周日"的错位（因为表格 wid 来自 BGM calendar 实时拉取，写库和展示时机不同，calendar 缓存可能 stale）。修法 6 步：
  1. `ALTER TABLE <table> ADD COLUMN broadcast_weekday INTEGER`（SQLite 直接 ALTER，无需 migration 框架）
  2. `models.py` 加 `Mapped[int | None]` 字段
  3. `_auto_fill_broadcast_times` 拉 calendar 同时算 `(shifted_time, shifted_weekday)` 元组，扩展 `batch_update_broadcast_times(mapping)` 接受 `dict[str, str | tuple[str, int | None]]`
  4. 表格展示改读 DB weekday，**不再每次调 calendar API** — 避免 stale
  5. `time_pattern` 放宽到 `^([01]\d|2[0-9]):([0-5]\d)$`（24-29h）
  6. SQL 一次性回填（sandbox 拒网络时从日志截图抄 weekday）
  root cause：**展示字段跨语义边界但数据来自不同源**。

- **Schema 列新增（SQLite + SQLAlchemy）的最小迁移** — 不引入 Alembic 不写 migration 脚本：```bash
  sqlite3 data/plugin_data/<plugin>/data.db "ALTER TABLE <table> ADD COLUMN <col> <type>;"
  ```
  然后同时改 `models.py` 加 `Mapped[...]` 字段。SQLAlchemy 启动时**不会** ALTER 已存在的表（它只 CREATE），所以缺一不可：新 INSERT/UPDATE 含新列 ORM 会持久化；旧 INSERT 不含则该列 NULL。**不要把 ALTER 留给 ORM**。

- **`bool` schema 字段的"feature toggle"最小模式（用户偏好：默认开启、可关）** — 加 `{name}: {description, type: "bool", hint, default: true/false}` → 在 `ConfigManager` 加 `def get_<name>(self) -> bool: return self._get_bool("<name>", <default>)` → 显示侧用一个 thin wrapper `_fmt_<name>_cfg(x)` = `_fmt_<name>(x) + if not self.config_manager.get_<name>(): fallback`，3 处展示统一切到 wrapper，关闭开关即可改语义而不动逻辑。`bool` schema 字段在 AstrBot WebUI 自动渲染为开关，不需要前端代码。

- **"把 X 流程和我讲一遍"的回应格式** — 用户说这话时，**literal trace** 而非 fix：
  ```
  1. entry (what user types)
  2. handler A → calls B
  3. ...每个数据源（DB table / API / config field）逐个列...
  4. final output
  ```
  不要在这时写代码改东西 — 除非用户后续明确说"去改"。可以指出数据流中的可疑点，但用户问的是 trace。

- **多轮 "还是有问题" 是 root cause 提示，不是重复** — 第一次 fix 只动了 surface bug（30h 显示），用户说"还是有问题"时意味着 surface bug 的根因还没找到（weekday 数据源问题）。第二次 fix 应**回头看数据流**而不是继续调 surface 逻辑。看到 "X 没生效 / 还有问题" 信号 → 立刻回到 step 1 重读数据流，找出 `time` 来自源 A、`weekday` 来自源 B 这种 asymmetry。

- **sandbox 没网络时用"日志抄 + SQL 直接回填"兜底** — 本地修代码改 SQL 时遇到 sandbox `ConnectionRefusedError: api.bgm.tv`，无法 curl 验证 weekday。修法：从当天 journal/截图日志里手动抄 weekday（"这部番刚才显在【周五】→ wid=5"），UPDATE SQLite 直接灌。**好处是用户 reload 后立刻看到正确显示**，不需要等 `/刷新放送` 触发 fill。验证：`sqlite3 data.db "SELECT subject_id, name, broadcast_time, broadcast_weekday FROM bangumi_subjects ORDER BY broadcast_weekday, broadcast_time"`。

- **Debug 命令（`/X测试 <X>`）应该接受人类可读的输入，不要只认技术 ID** — 第一次写 `/放送测试` 只接 `subject_id`，用户传中文番名 `描绘直至生命尽头` 直接 `未找到`。用户群里看到的是番剧名不是 ID，**debug 命令不强制 ID 是正确的产品决策**。修法：
  ```python
  if not self.storage.get_subject_name(target_id):  # 不是 ID 时
      candidates = self.storage.find_group_subscription_candidates(
          group_id=group_id, keyword=target_id, limit=3
      )
      if len(candidates) == 1:
          target_id = str(candidates[0].subject_id)
      elif len(candidates) > 1:
          yield 候选列表让用户重试
  ```
  复用已有的 `find_*_candidates` 模糊匹配，0 行新逻辑。**这条也适用**：配置命令（`/bgm模板 1`）、查询命令（`/bgm <番剧名>`）—— 凡是用户大概率输入中文/自由文本的，都该模糊匹配。

- **`get_subject_name` 返回 sentinel "未知番剧" 而非 None → boolean gate 静默失败** — 当 lookup 方法找不到条目时返回 truthy 字符串 `"未知番剧"` 作为 sentinel，外层 `if not self.storage.get_subject_name(target_id):`（期望 falsy 的 None）永远不进分支 → 中文名模糊匹配跳过 → 最终显示 `⚠️ 未知番剧 不在监控列表（未被订阅）`，错误信息是 "未知番剧" + 真实错误文本拼接。**根本原因**: sentinel strings 与 Python falsy 语义冲突。修法: 别用 `get_subject_name` 当 gate——直接用 `get_monitored_subjects()` 查全表，ID 匹配 + name 子串匹配。`if target_id in (s.name or "")` 比调用包装方法稳定。**通用教训**: 任何返回 sentinel 字符串代替 None 的方法都不要用作 boolean check 的 gate；如果必须判断 "是否找到"，用专门的不对外暴露的 query 方法。

- **pyright (LSP) 严格子类型报错 ≠ CI 失败** — CI 只跑 `ruff check` + `ruff format` + `mypy` + `pytest`。`dict[str, tuple[str, int]]` 传给 `dict[str, str | tuple[str, int | None]]` 形参，pyright 报 strict 子类型不兼容（运行时完全合法），但 ruff/mypy/pytest 全过。**别为 LSP 警告专门 patch 代码**——除非用户用 Pyright/LSP 否则没影响。验证 CI 是不是用 pyright：`grep pyright .github/workflows/`。

- **Calendar API 数据不稳定 → 用 begin ISO datetime 自带 weekday** — 当 BGM `/calendar` 在两次 fetch 之间返回同一 subject 不同 weekday（实测 bgmlist 出现过），任何依赖 calendar 的 weekday 都会错位。修法：换数据源。bgmlist 的 `begin` 字段是 ISO datetime，**`cst_dt.isoweekday()` 直接拿稳定的 weekday**（bgmlist 是 GitHub Pages 静态数据，不像 calendar API 那样缓存可变）。改 `_parse_broadcast_time(begin_iso) -> tuple[HH:MM, weekday]`，fetch 端签名同步扩到 `dict[str, tuple[str, int]]`。**trigger signal**：连续两次 `/刷新放送` 后表格 weekday 不一致（同一部番从周三变周四）。

- **Patch 缩进陷阱：old_string 缺 4 空格会嵌套半个函数体** — 当 old_string 缺第一行 `return` 时（如 `if not X:\n    yield ...\n    return\n\ntarget_id = ...` 写成 `if not X:\n    yield ...\n    target_id = ...`），patch 后整段后续代码缩进多 4 空格 = 嵌套在 if 里，pyright 报"possibly unbound / not a known attribute of None"。**防御**：写 patch 前先把 old_string 前后 3 行读出来确认完整缩进；写完后 `git diff --stat` 看 lines 数对不对，单文件 +50/-3 而原文件才 +20 行 → 一定是嵌套错了。

## See also

- `references/decorator-quickref.md` — every decorator signature with one example
- `references/schema-field-patterns.md` — `_conf_schema.json` field type cookbook
- `references/common-bugs.md` — issues hit in real sessions (the "register on class" bug, the self-file existence check, Image.file/Reply.chain, etc.)
- `references/patterns-cooldown.md` — per-session rate limiting with `unified_msg_origin` dict
- `references/session-string-format.md` — `Context.send_message` session string anatomy: platform_id (user-configured) vs MessageType (CamelCase enum); how to look up the real platform_id from `context.platform_manager.platform_insts` instead of guessing
- `references/broadcast-time-30h-weekday.md` — 30h 制周时间表 schema migration pattern: when display has cross-day semantics, store weekday alongside time; SQLite ALTER + SQLAlchemy 6-step recipe; user signal patterns ("还是有问题" = root cause missed)
- `templates/verify-template.py` — copy + fill `<...>` placeholders for new plugin ad-hoc verification
