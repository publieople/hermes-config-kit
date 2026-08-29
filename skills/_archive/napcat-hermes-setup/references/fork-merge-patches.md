# Fork 合并后的补丁

合并 MoeOver/main（PR #17917）后，以下 2 个文件因冲突被 resolve 为 HEAD，
需手动加回 NapCat 集成代码。

## gateway/run.py

### Adapter 创建代码（在 `Platform.QQBOT` 块和 `Platform.YUANBAO` 块之间）

```python
        elif platform == Platform.NAPCAT:
            from gateway.platforms.napcat import NapCatAdapter, check_napcat_requirements
            if not check_napcat_requirements():
                logger.warning("NapCat: aiohttp not installed")
                return None
            return NapCatAdapter(config)
```

### _UPDATE_ALLOWED_PLATFORMS（~10835 行）

在 `Platform.QQBOT` 后加 `Platform.NAPCAT`：

```python
        Platform.FEISHU, Platform.WECOM, Platform.WECOM_CALLBACK, Platform.WEIXIN,
        Platform.BLUEBUBBLES, Platform.QQBOT, Platform.NAPCAT, Platform.LOCAL,
```

## hermes_cli/gateway.py

### _setup_napcat() 函数（在 `_setup_qqbot()` 和 `_setup_signal()` 之间）

完整代码见 [`references/napcat-setup-function.md`](napcat-setup-function.md)。

### _PLATFORMS dict 条目（~5647 行）

```python
        "qqbot": _setup_qqbot,
        "napcat": _setup_napcat,
```

## MoeOver merge 带来的完整文件列表

这些文件在 merge 中无冲突，已自动合并：

| 文件 | 内容 |
|------|------|
| `gateway/platforms/napcat.py` | NapCat 平台适配器（1250 行） |
| `gateway/config.py` | Platform.NAPCAT + 平台启用逻辑 |
| `tools/napcat_tool.py` | napcat_call 工具（212 行） |
| `tools/send_message_tool.py` | NapCat 消息发送支持 |
| `toolsets.py` | napcat toolset 注册 |
| `hermes_cli/setup.py` | `hermes setup` 交互式配置 |
| `hermes_cli/config.py` | 平台配置入口 |
| `skills/messaging/napcat/SKILL.md` | QQ 群聊人格 |
| `tests/gateway/test_napcat.py` | 798 行测试 |
| `tests/tools/test_napcat_tool.py` | 工具测试 |
| `website/docs/.../napcat.md` | 文档 |

## gateway/authz_mixin.py

**这是最隐蔽的隐藏坑**。即使前 3 个文件都修好了，`NAPCAT_ALLOW_ALL_USERS=true` 也不会生效。

### platform_env_map（~157 行，QQBOT 之后）

```python
            Platform.QQBOT: "QQ_ALLOWED_USERS",
            Platform.NAPCAT: "NAPCAT_ALLOW_FROM",   # ← 加这行
            Platform.YUANBAO: "YUANBAO_ALLOWED_USERS",
```

### platform_allow_all_map（~183 行，QQBOT 之后）

```python
            Platform.QQBOT: "QQ_ALLOW_ALL_USERS",
            Platform.NAPCAT: "NAPCAT_ALLOW_ALL_USERS",   # ← 加这行
            Platform.YUANBAO: "YUANBAO_ALLOW_ALL_USERS",
```

**症状**（缺失时）：Gateway 日志持续报 `Unauthorized user: 2631792752 (人民公仆) on napcat`，所有 QQ 消息被静默丢弃。

## 冲突文件（手动解决）

这些文件合并时有冲突，resolve 为 HEAD（最新官方代码），然后手动补回 NapCat 部分：

| 文件 | 原因 |
|------|------|
| `gateway/run.py` | MoeOver 落后于上游，NapCat adapter 代码被移除 |
| `hermes_cli/gateway.py` | `_setup_napcat()` 函数被移除 |
| `gateway/platforms/base.py` | media extraction 实现差异（保留 HEAD） |
| `tests/gateway/test_platform_base.py` | 测试差异（保留 HEAD） |
| `website/sidebars.ts` | 导航差异（保留 HEAD） |

### 冲突解决命令

```bash
# 合并（非交互模式，接受自动合并）
git merge moeover/main --no-edit

# 非 NapCat 专属文件 → 保留 HEAD
git checkout --ours gateway/platforms/base.py tests/gateway/test_platform_base.py website/sidebars.ts
git add gateway/platforms/base.py tests/gateway/test_platform_base.py website/sidebars.ts

# NapCat 需要集成的文件 → 保留 HEAD 后手动补回 NapCat 部分
git checkout --ours gateway/run.py hermes_cli/gateway.py
git add gateway/run.py hermes_cli/gateway.py
# 然后手动加回：adapter 创建代码、_UPDATE_ALLOWED_PLATFORMS、_setup_napcat()、_PLATFORMS dict

# 提交合并
git commit -m "Merge moeover/main: NapCat/OneBot 11 platform support"
```

## 验证

### 基础验证（Gateway 启动）

```bash
grep -a -E 'napcat|Gateway running with' /home/po/.hermes/logs/gateway.log | tail -5
# 应看到：✓ napcat connected + Gateway running with 3 platform(s)
```

### 功能验证（合并后必查清单）

合并后这些自定义功能会丢失，必须逐一确认：

| 功能 | 检查方式 | 修复位置 |
|------|---------|---------|
| **`_active_runner` 已赋值** | `grep '_active_runner = runner' gateway/run.py` 应有结果 | `gateway/run.py` start_gateway() ~15713 行 |
| **`napcat_call` 工具可用** | 发图 @bot，检查 agent.log 是否有 `napcat_call` 调用 | `tools/napcat_tool.py` + `gateway/run.py` |
| NAPCAT_MODEL 按渠道模型 | `grep '{PLATFORM}_MODEL' gateway/run.py` 应在 ~2712 行找到 | `gateway/run.py` _resolve_session_agent_runtime() |
| QQ 跳过 Mem0 | `grep skip_memory gateway/run.py` 应找到 `_napcat` | `gateway/run.py` ~16803 行 |
| 中文反注入威胁扫描 | `tools/threat_patterns.py` 是否包含 `cn_` 模式 | `tools/threat_patterns.py` |
| NAPCAT_CONTEXT_MODE 群聊上下文 | napcat.py 是否有 `_add_group_context` + `_drain_group_context` | `gateway/platforms/napcat.py` |
| `_strip_self_mention` 前导检测 | napcat.py 是否有 `seen_text` 变量 | `gateway/platforms/napcat.py` |
| authz 映射 | `grep NAPCAT authz_mixin.py` 应有 2 处 | `gateway/authz_mixin.py` |

## 执行记录（2026-06-10 实操）

### 第一次（更新后修复，16:10-16:30）

1. `hermes update` 后 NapCat 断连（ECONNREFUSED 8646）
2. 发现 `gateway/platforms/napcat.py` 被删除，Platform 枚举里 NAPCAT 被移除
3. 从 git 历史恢复 napcat.py：`git show 41ac6ab0d:gateway/platforms/napcat.py > gateway/platforms/napcat.py`
4. 手动补丁 config.py（枚举 + 平台启用）、run.py（adapter + _UPDATE_ALLOWED_PLATFORMS）
5. 重启后出现 `Unauthorized user` → 发现 authz_mixin.py 没有 NAPCAT 映射
6. 补 authz_mixin.py → 重启 → 正常

### 第二次（Fork 合并，16:35-16:50）

1. `gh repo fork NousResearch/hermes-agent --fork-name hermes-agent --clone=false`
2. `git merge moeover/main --no-edit` → 5 个文件冲突
3. 解决冲突后提交 → push 到 fork（force push 首次）
4. 补丁：run.py adapter、hermes_cli/gateway.py setup、authz_mixin.py
5. 重启 → `Unauthorized user` 消失

### 第三次（按渠道模型 + 上下文模式，18:00-18:50）

1. 加 `{PLATFORM}_MODEL` 通用机制到 `gateway/run.py` _resolve_session_agent_runtime()
2. 加 `NAPCAT_CONTEXT_MODE` 到 napcat.py（_add_group_context/_drain_group_context）
3. 在 `.env` 中设 `NAPCAT_CONTEXT_MODE=true`
4. GitHub push 失败（网络：github.com 443 via 127.0.0.1 拒绝连接）
5. 本地 commit 已保存，待网络恢复后 push

### 第四次（_active_runner + _strip_self_mention 前导检测，23:00-23:25）

**发现 `napcat_call` 工具完全不可用** — `tools/napcat_tool.py` 通过 `gateway.run._active_runner` 获取 NapCat adapter，但这个模块级变量从未被赋值（始终为 None）。图片识别功能因此从未工作过。

修复（`gateway/run.py`）：
```python
# 模块级变量声明（~68 行）
_active_runner: Optional[Any] = None

# start_gateway() 中赋值（~15713 行）
runner = GatewayRunner(config)
global _active_runner
_active_runner = runner
```

**`_strip_self_mention` 前导 @bot 检测** — QQ 在 reply 链中自动插入不可见 @bot 段，旧代码不区分位置，所有消息都被判定为 mentioned。修复：加 `seen_text` 追踪，只有消息**开头**的 @bot 算主动提及。详见 SKILL.md 群聊上下文机制章节。
