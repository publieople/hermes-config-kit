---
name: windows-autostart-admin
description: Auto-launch a Windows desktop script or program with admin privileges at user logon. Covers the three viable mechanisms (Task Scheduler RunLevel=Highest, startup-folder shortcut, AHK self-elevate), the .lnk RunAs-flag pitfall, and how 3rd-party launchers (Quicker, Power Automate, etc.) fit into the picture. Use when a user reports "works when I double-click it but doesn't start at boot", "startup shortcut silently fails", or wants to add a logon-time admin task.
---

# Windows 开机自动启动 + 管理员权限

User 报告的典型症状:**手动双击能跑,开机后无反应**。根因 90% 是 logon session 的受限 token + 启动机制自身没拿到 RunAs 上下文。

## 先看证据,再选方案

永远不要凭记忆给方案。先跑诊断脚本(见 `references/diag-autostart.ps1`)确认三件事:

1. **.lnk 的 RunAs 标志位**(LinkFlags byte 0x14, mask `0x8000`)— 如果是 False 而 GUI 显示勾了"以管理员运行",**这就是 Win32 Shell UI 的 bug**:UAC=从不通知时写 .lnk 会清掉 RunAs 位。这条直接决定走不走启动文件夹。
2. **Application 日志最近 24h 内 AutoHotKey/脚本名相关 Error/Warning** — 确认脚本是否真的尝试启动过。
3. **Get-ScheduledTask | Where Name matches** — 看有没有遗留的计划任务(用户可能改了方案忘了清旧的)。
4. **Defender Operational 日志** EventId 1116/1117/1121/1129 — 看是不是被 SmartScreen/Defender 静默拦了。

诊断前不要给方案。

## 方案对比

| 方案 | 适用场景 | 优点 | 坑 |
|------|----------|------|-----|
| **任务计划程序 `RunLevel=Highest` + AtLogOn + 30s 延迟** | 通用,任何脚本/exe | 不依赖 .lnk 标志位;LastRunResult 可观测;触发时机精确 | 引入一个新概念(任务计划) |
| **启动文件夹 .lnk + 脚本自提权(`if !A_IsAdmin Run *RunAs`)** | 用户已经习惯启动文件夹心智模型;脚本可控 | 改动只 1 行 AHK | UAC=从不通知时 .lnk 的 RunAs 标志会被 Win32 UI 清掉(见 pitfall),所以**只能靠脚本自提权**,不能靠 .lnk |
| **3rd-party launcher(Quicker 等)的"以管理员运行"动作** | 用户已经在用 Quicker/同类工具,且 Quicker 自启已设 | UI 友好;权限管理统一;多动作复用 | Quicker 自启本身还是要走 注册表 Run / 任务计划,**它替代不了底层的开机调度**,只是把"提权"这件事外包 |

## 核心 Pitfall

### .lnk 的 RunAs 标志位(UAC=从不通知时静默丢失)

**症状**:用户在快捷方式属性里勾了"以管理员身份运行",桌面图标右下角出现盾牌图标(这是 UI 反馈),但实际 .lnk 文件里 `LinkFlags` 的 `0x8000` 位是 False。

**根因**:Win32 Shell UI 在某些 UAC 配置下(尤其是"不通知"那一档)写入 .lnk 时不会持久化 RunAs 标志位。手动双击能跑,因为 explorer.exe 当前 user session 有完整 token,.lnk 启动子进程时 ShellExecuteEx 走默认路径;但 logon session 下 explorer token 受限,.lnk 不带 RunAs 就拿不到管理员权限,被系统静默吞。

**诊断**:

```powershell
$lnk = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\foo.lnk"
$bytes = [IO.File]::ReadAllBytes($lnk)
$flags = [BitConverter]::ToUInt32($bytes, 0x14)
[bool]($flags -band 0x8000)  # False = RunAs 位没写进去
```

**修复**:不要去调 .lnk 标志位(Win32 UI bug 重现性差),直接换路径:

- 走任务计划程序 RunLevel=Highest
- 或让脚本自提权(参考 AHK 的 `if !A_IsAdmin Run *RunAs "A_ScriptFullPath"`)

### 启动文件夹 vs 注册表 HKCU\...\Run

两者行为相似但**注册表 HKCU 路径不会写 .lnk,直接是 exe/script 路径**,没有 RunAs 标志位的坑。如果用户坚持用注册表 Run,这条路在 UAC=从不通知配置下**比启动文件夹 .lnk 更可靠**。

```reg
[HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run]
"AHK-replace"="\"C:\\Program Files\\AutoHotKey\\replace.ahk\""
```

注意:AHK .ahk 文件走注册表 Run 同样要靠 `if !A_IsAdmin` 自提权,因为 explorer 拉这个进程时 token 是受限的。

## Quicker / Power Automate 这类工具的真相

**它们不是开机调度器**。它们能"开机自动跑某个动作",前提是自己已经被某种调度机制拉起来了:

| Quicker 自启的底层方式 | 是否有 RunAs 标志位 bug |
|------------------------|--------------------------|
| 注册表 Run HKCU | 无 |
| 任务计划 | 无 |
| 启动文件夹 .lnk | **有**(同上) |

所以如果用户已经在用 Quicker 且自启走的是注册表 Run,**Quicker 内部的"以管理员运行"动作可以直接解决提权问题**,比改 AHK 脚本自提权更优雅。但**不要向用户断言 Quicker 没法做开机调度**—— 先搜文档 / 查官方 QA 再说。

## 工作流(下次直接照抄)

1. 加载本 skill,加载 `references/diag-autostart.ps1`
2. 问用户:UAC 设置在哪个档?手动双击能跑吗?
3. 让用户跑诊断脚本(或代理跑),把四项结果贴回来
4. 根据 RunAs 位 + 用户对方案 1/2/3 的偏好,给一个具体可执行方案
5. **不要同时给三个方案让人选**。给最匹配的一个 + 一句话说明为什么不是另外两个

## Verification

任何方案落地后,验证步骤必须包括:

```powershell
# 方案 1 验证
Get-ScheduledTaskInfo -TaskName "AHK-replace" | Select LastRunTime, LastTaskResult
# LastTaskResult = 0 才是成功

# 方案 2 验证(AHK 自提权)
# 脚本启动后,看 tray icon 是否有盾牌 → 有 = 提权成功
# 或 AHK: A_IsAdmin 返回 1
```

如果 LastTaskResult != 0,查 [MS Learn Task Scheduler error codes](https://learn.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-error-and-success-constants)。

## 关联

- 诊断脚本: `references/diag-autostart.ps1`
- 已知 Win32 UI bug 行为: `references/lnk-runas-flag-bug.md`