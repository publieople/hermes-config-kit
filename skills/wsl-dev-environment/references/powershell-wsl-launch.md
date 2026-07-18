# PowerShell → WSL CLI 启动的 4 个连环坑

## 场景

Windows PowerShell 终端想直接敲 `hermes` / `claude` / `codex`，实际命令在 WSL 里装好了。

直觉写法：
```powershell
wsl hermes                  # 错：找不到命令
wsl -e bash -lc "hermes"    # 错：~ 解析成 /root / env 丢失 / 卡 fish welcome（见下）
```

## 四个坑逐一记录

### 坑 1：`wsl hermes` 报 "未找到命令"

原因：`wsl` 默认进入 WSL 默认登录用户的 PATH（`/usr/bin:/usr/local/bin` 等），不读 `.bashrc` 里的 `export PATH`，也不读 `~/.local/bin/env`。所有装在 `~/.local/bin/` 的 CLI（hermes / claude）都找不到。

验证：
```bash
wsl -e bash -c 'command -v hermes'    # exit 127，输出空
echo $PATH | tr ':' '\n' | grep local  # 没 ~/.local/bin
```

### 坑 2：`wsl -e bash -lc "~/.local/bin/hermes"` 报 "/root/.local/bin/hermes: 没有那个文件或目录"

原因：`wsl -e` 不带 `-u` 时用 `/etc/wsl.conf` 的 `default` 用户（默认 root）。`~` 在 bash -lc 字符串里被当前用户解析为 `$HOME`，root 的 `$HOME=/root`，所以 `~/.local/bin/hermes` → `/root/.local/bin/hermes`。

试过的修复（用户提的）：
```powershell
# 方案 A：切到 po 用户 — 但要 sudo 密码，且会丢 root 那边的 env（见坑 3）
function hermes { wsl -u po -e bash -lc "~/.local/bin/hermes $($args -join ' ')" }

# 方案 B：改 wsl.conf 让 default = po
# 要 sudo 写 /etc/wsl.conf，且之后 wsl hermes 能用但 root 那边方便度丢了
```

### 坑 3：`wsl -u po ...` 启动后报 "It looks like Hermes isn't configured yet -- no API keys or providers found"

原因：hermes 启动读一堆 env（`DEEPSEEK_API_KEY` / `BAILIAN_API_KEY` / `HTTPS_PROXY` / `HTTP_PROXY` / `NAPCAT_TOKEN` / `PYTHONPATH`…）。WSL root 登录 shell 里这些 env 是齐的（写在 `/etc/profile.d/` 或 root 的 `.bashrc`），但 `-u po` 切到 po 用户后 po 的 shell 没这些 export。

验证：
```bash
# 对比 env 差异
bash -lc 'env | grep -iE "api|key|proxy"'          # root：BAILIAN_API_KEY、DEEPSEEK_API_KEY、HTTPS_PROXY… 都在
sudo -u po bash -lc 'env | grep -iE "api|key|proxy"' # po：几乎全空，只有 MKLROOT
```

→ "我在 WSL 里都配好了" 是 root 用户视角，不是 po 用户视角。

### 坑 4：`wsl -e bash -lc "..."` 执行时先进入 fish / 卡在 PS1，等你退出才执行命令

**症状**：用户报告"PowerShell 敲 hermes 后会先进 WSL 的 fish，看到 welcome banner 和主题渲染，等我退出才进 hermes"。

**原因**：`bash -l` 让 bash 作为**登录 shell** 启动。bash 登录 shell 看到 stdin/stdout 是 TTY（PowerShell 传过来的就是）→ 进交互模式 → 先读 `.bash_profile` / `.profile`、打印 PS1 等用户输入 → 然后才把 `-c` 字符串作为命令执行。用户的默认登录 shell 是 fish 时，命令字符串被作为 fish 的内建命令跑（fish 看到 `HOME=/home/po /home/...` 这种语法也是支持的，但前面的 welcome 渲染和 PS1 占用已经发生了）。

**官方依据**（Microsoft WSL docs）：
> "The Linux command following `wsl` is handled like any command run in WSL. **Run as the WSL default user.**"
> `wsl -e` 跳过默认 Linux shell，但仍按你指定的 shell（bash）启动；加了 `-l` 它就走 login shell 路径。

**修复**：去掉 `-l`，用 `bash -c`：

```powershell
# ❌ 触发坑 4
function hermes { wsl -e bash -lc "/home/po/.hermes/hermes-agent/venv/bin/hermes $($args -join ' ')" }

# ✅ 不进登录 shell 模式，直接 exec
function hermes { wsl -e bash -c "/home/po/.hermes/hermes-agent/venv/bin/hermes $($args -join ' ')" }
```

**副作用**：`bash -c` 不读 `.bash_profile`，所以 root 登录 shell 里 export 的 env（API key / proxy）会丢。但 hermes 默认优先读 `~/.hermes/config.yaml` 里写死的 key，所以通常没事。如果报"未配置"，三种补 env 方法：

```powershell
# 方法 A：PowerShell env 透传（精细控制）
function hermes {
  $envArgs = @()
  foreach ($name in 'HTTPS_PROXY','HTTP_PROXY','BAILIAN_API_KEY','DEEPSEEK_API_KEY','NAPCAT_TOKEN') {
    if ($env:$name) { $envArgs += '--env', "$name=$($env:$name)" }
  }
  & wsl.exe @envArgs -e bash -c "HOME=/home/po /home/po/.hermes/hermes-agent/venv/bin/hermes $($args -join ' ')"
}

# 方法 B：WSLENV（全局生效，所有 wsl 命令）
$env:WSLENV = "HTTPS_PROXY/u:HTTP_PROXY/u:BAILIAN_API_KEY/u:DEEPSEEK_API_KEY/u:NAPCAT_TOKEN/u"

# 方法 C：让 wsl 默认 shell（root 的 fish）直接 exec hermes — `HOME=val cmd` 是 POSIX / fish / zsh 通用
function hermes { wsl HOME=/home/po /home/po/.hermes/hermes-agent/venv/bin/hermes $args }
```

方法 C 最简洁——一行，不启新 shell，fish 看到 `HOME=/home/po /home/...` 直接 exec hermes。**前提**：hermes config 里有 API key（默认行为）。

## 最终解法（推荐）

```powershell
function hermes { wsl -e bash -c "/home/po/.hermes/hermes-agent/venv/bin/hermes $($args -join ' ')" }
```

为什么这样对：
- root 的 env 全在（API key / proxy / NapCat token）
- hermes 跑在 po 的 venv 上（库 / skill / `~/.hermes/` 配置都是 po 那套）
- 绝对路径绕开 `~` 解析坑和 PATH 坑
- 不带 `-l` → bash 不进登录 shell → 不卡在 PS1 / fish welcome

**最简变体**：
```powershell
function hermes { wsl HOME=/home/po /home/po/.hermes/hermes-agent/venv/bin/hermes $args }
```

验证链路：
```powershell
wsl -e bash -c '/home/po/.hermes/hermes-agent/venv/bin/hermes --version'
# 期望：Hermes Agent v0.18.2 (2026.7.7.2) · upstream ...
# 不输出 version = 路径错了
# 输出 version 但启动仍报 no providers = 走 WSLENV 或 /etc/profile.d/ 方案
```

## 通用化

| 工具 | 装在哪 | PowerShell 函数 |
|---|---|---|
| hermes | `/home/po/.hermes/hermes-agent/venv/bin/hermes` | `wsl -e bash -c "/home/po/.hermes/hermes-agent/venv/bin/hermes $($args -join ' ')"` |
| claude code | `/home/po/.local/bin/claude`（uv tool 装） | `wsl -e bash -c "/home/po/.local/bin/claude $($args -join ' ')"` |
| codex | `/home/po/.npm-global/bin/codex` | `wsl -e bash -c "/home/po/.npm-global/bin/codex $($args -join ' ')"` |

**注意**：所有函数**都用 `-c`（去掉 `-l`）**，否则都触发坑 4。

## 根本修复（一次解决所有坑）

```bash
sudo tee /etc/profile.d/hermes-env.sh <<'EOF'
export PATH="$HOME/.local/bin:$PATH"
# 其他需要持久化的 env 在这里 export
EOF
```

之后 `wsl hermes` / `wsl claude` / `wsl codex` 任何用户登录都能直接用。要 sudo，用户自己跑。

## 给未来 agent 的提示

如果用户说"PowerShell 里 xxx 命令找不到"、"在 WSL 里能用，在 PowerShell 里不行"、或"PowerShell 启动 hermes 先卡在 fish 再进 hermes"，按这 4 坑顺序排查：

1. `wsl -e bash -c 'command -v <cmd>'` — 看 PATH 里有没有（坑 1）
2. 看错误路径是不是 `/root/...` — `~` 解析错了（坑 2）
3. 启动报 "no API keys / 未配置" — 切用户了（坑 3）或 `bash -c` 没读 `.bash_profile`（坑 4 副作用）
4. 启动先看到 fish welcome / PS1 才执行 — `bash -lc` 登录 shell 模式（坑 4）

**`wsl -u po` 不是好解**——丢了 root 那边的 env。如果用户说"我要 po 用户登录"，那是另外的需求（不是切换来跑 hermes）。

**修法的优先级**：
1. 函数去掉 `-l`，用 `-c`（避坑 4）
2. 用绝对路径（避坑 1 + 2）
3. 保持默认 root 用户（保 root 的 env）
4. 如果还报"未配置"→ WSLENV 透传或写 `/etc/profile.d/`