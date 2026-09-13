# .lnk RunAs 标志位丢失问题(Win32 Shell UI bug)

## 现象

用户在快捷方式属性 → 快捷方式选项卡 → 高级 → "以管理员身份运行" 勾上了,
桌面图标右下角出现盾牌图标(UI 反馈正常)。

但实际上 .lnk 文件二进制里的 `LinkFlags` (offset 0x14, 4 bytes little-endian)
的 `0x8000` 位(RunAsUser)是 False。

## 触发条件

Win32 Shell 在以下 UAC 配置下写入 .lnk 时会清掉 RunAs 标志位:

- 通知设置 = "不通知"(滑块到最底)

其他档位下标志位正常持久化。

## 为什么手动能跑,开机不跑

| 触发方式 | explorer.exe 的 token | .lnk 带 RunAs 标志位 | 结果 |
|----------|------------------------|----------------------|------|
| 桌面双击 | 当前 user session,完整 token | False(标志位丢了) | ShellExecuteEx 默认以当前 token 启动,脚本能跑(如果脚本本身有自提权或不要 admin) |
| 启动文件夹 logon 时 | logon session,**受限 token** | False | ShellExecuteEx 拿不到 admin,被系统静默吞掉(无错误对话框,UAC=不通知) |

所以**手动跑=explorer 当前 session token 本身就够用**,根本不走 RunAs 标志;
**开机跑=explorer 受限 token + 没有 RunAs 标志 = 完全没提权路径**。

## 验证证据(2026-07-10,user=fzj)

用户的 `replace.lnk`:
- LinkFlags: 0x0000209B
- RunAsUser 0x8000: **False**
- TargetPath: `C:\Program Files\AutoHotKey\replace.ahk`
- WorkingDirectory: `C:\Program Files\AutoHotKey`

手动双击 AHK 起来且生效。
开机后无任何 Application 错误日志 → 脚本根本就没尝试启动过。

## 解法优先级

1. **任务计划程序 RunLevel=Highest**(推荐) — RunAs 是任务计划自己的设置,不走 .lnk
2. **脚本自提权** — AHK 例: `if !A_IsAdmin Run *RunAs "A_ScriptFullPath"`
3. **改用注册表 HKCU\...\Run**(不走 .lnk,没这个 bug) — 但同样要靠脚本自提权
4. ❌ 改 .lnk 的 LinkFlags 二进制位 — 不稳定,Win32 UI 重写 .lnk 时会再次清掉
5. ❌ 调高 UAC 到"总是通知" — 影响范围大,不推荐仅为这一件事动系统设置

## 已知关联引用

- MS Learn: [Task Scheduler error codes](https://learn.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-error-and-success-constants)
- IShellLinkW / IPersistFile 文档: [MS Learn Shell Links](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nn-shobjidl_core-ishelllinkw)