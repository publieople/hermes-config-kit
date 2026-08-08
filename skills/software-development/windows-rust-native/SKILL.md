---
name: windows-rust-native
description: 写直接调 Win32/COM 的 Rust 代码前加载（windows crate、注册表、任务计划、签名）。
category: software-development
tags: [windows, rust, win32, com, winreg, wintrust, task-scheduler, cross-compile, ci]
---

# Windows Rust 原生开发（windows crate 0.62）

直接调 Win32 API / COM 的 Rust 代码。不覆盖 Tauri（见 tauri-v2-development）。

## 触发条件

- 枚举/读写注册表（Run 键、启动项）
- Task Scheduler（计划任务）COM 调用
- WinVerifyTrust 签名校验
- 任何 `windows` crate 的 `Win32_*` feature 使用
- 需要在 WSL 验证 Windows 代码（交叉编译检查）
- 为 Windows 代码配真机 CI

## 平台依赖隔离（Linux 也能测纯逻辑）

```toml
# Cargo.toml — 平台依赖放 target 段，Linux 编译不拉 Windows 库
[dependencies]
serde = "1"

[target.'cfg(windows)'.dependencies]
winreg = "0.56"
windows = { version = "0.62", features = [...] }
```

`#[cfg(windows)]` 门控的模块在 Linux 上编译时整个跳过 → 纯逻辑（规则引擎、快照、模型）在 Linux 跑单测，Windows 代码只真机验证。

## 交叉编译检查（无 Windows 机器时的 API 验证）

```bash
rustup target add x86_64-pc-windows-msvc
cargo check --target x86_64-pc-windows-msvc -p <crate>   # 验证 API 用法对错
cargo clippy --target x86_64-pc-windows-msvc --workspace --all-targets
```

**关键限制**：`cargo check` 不需要链接器，能验证所有 API 签名用法。但 **bin（非 lib）`cargo build` 需要 link.exe** — WSL 没有 MSVC 链接器，报 `linker link.exe not found`。所以本地只跑 `cargo check`，真链接靠 CI 的 windows runner。

## windows crate 0.62 核心 API 模式

详细坑位表见 `references/windows-crate-0.62-pitfalls.md`。高频要点：

### COM 接口是高级封装，不是 raw 绑定
- `CoCreateInstance(&CLSID_X, None, CLSCTX_INPROC_SERVER)` 返回强类型接口，直接 `.Method()` 调用
- 方法返回值是 `windows_core::Result<T>`，用 `.map_err(|e| ...)?` 处理
- **所有 COM 调用是 unsafe** — 必须包 `unsafe { }` 块（赋值给 union 字段不需要 unsafe，调用方法需要）

### 常用 Win32 函数签名差异（0.62 与旧版/文档不同）
| 函数 | 0.62 签名 | 注意 |
|---|---|---|
| `ShellExecuteW` | 6 参数（hwnd, operation, file, params, dir, nShowCmd） | **不是** SHELLEXECUTEINFOW 结构体版本 |
| `WinVerifyTrust` | `(HWND, *mut GUID, *mut c_void)` | pwvtdata 是 `*mut c_void`，要 cast |
| `SHGetFolderPathW` | `(Option<HWND>, i32, Option<HANDLE>, u32, &mut [u16;260])` | 缓冲固定 260 |
| `SHGetFolderPathW` csidl | `i32`，CSIDL_FLAG_CREATE 是 `0x8000` | |
| `CloseHandle` | 在 `Win32::Foundation` | 不在 Threading |

### COM 集合接口不是迭代器
`IRegisteredTaskCollection` 用 `Count()` + `get_Item(&VARIANT)`，不是 for 循环。
`IActionCollection::Count` 是 `(&mut i32)` 指针形式，`get_Item(i32)` 直接传值。

### 必需 feature（缺了编译报 unresolved import）
- TaskScheduler COM → `Win32_System_TaskScheduler` + `Win32_System_Com` + `Win32_System_Variant` + `Win32_System_Ole`
- WinVerifyTrust → `Win32_Security_WinTrust` + **`Win32_Security_Cryptography`**（WINTRUST_DATA 结构体 gate 在这）
- SHGetFolderPathW → `Win32_UI_Shell` + `Win32_Foundation`
- MessageBoxW → `Win32_UI_WindowsAndMessaging`
- WaitForSingleObject → `Win32_System_Threading`

## 真机 CI（windows-latest = 真 Windows）

```yaml
test-windows:
  runs-on: windows-latest
  steps:
    - uses: actions/checkout@v4
    - uses: dtolnay/rust-toolchain@stable
    - run: cargo test --workspace
    - run: cargo clippy --workspace --all-targets -- -D warnings
```

**核心价值**：交叉编译只验证"能编译"，真机跑才验证"真的能跑"。本会话 CI 抓到一个交叉编译完全看不出的空指针解引用（WINTRUST_DATA union 初始化）——`*data.Anonymous.pFile = x` 在真机直接 `STATUS_STACK_BUFFER_OVERRUN`，改成 `data.Anonymous.pFile = &mut x` 才过。**Windows 代码必须配真机 CI，别信交叉编译。**

## 提权进程数据共享：ProgramData，不是 AppData

**核心坑**：GUI/CLI 是普通权限，helper 是管理员（ShellExecuteW runas）。管理员进程的 `%APPDATA%` 解析到 `C:\Windows\System32\config\systemprofile\AppData\Roaming`，与普通用户的 `C:\Users\<name>\AppData\Roaming` 不同。请求/结果文件和快照目录如果用 `%APPDATA%`，GUI 写了 helper 读不到。

**修法**：统一用 `%ProgramData%\BootKeeper`（`std::env::var("ProgramData")`）。ProgramData 是所有用户和管理员都能读写的系统共享目录。预留 `BOOTKEEPER_DATA` 环境变量覆盖以兼容测试/定制。

```rust
fn data_root() -> PathBuf {
    if let Ok(p) = std::env::var("BOOTKEEPER_DATA") { return PathBuf::from(p); }
    let base = std::env::var("ProgramData").unwrap_or("C:\\ProgramData".into());
    PathBuf::from(base).join("BootKeeper")
}
```

## 注册表位置：存真实路径，不用显示缩写

**核心坑**：枚举器存 `HKCU\...\Run` 作为 location（显示缩写），写操作解这个 location 找 registry key 时把 `...\` 当字面量剥掉 → 打开 `HKCU\Run` 而非 `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run` → 值查找 NotFound → 禁用/启用/删除静默失败。

**修法**：枚举器的 location 字段存真实路径 `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run`（或 HKLM 等价）。`parse_hive_and_key` 只做 hive 剥离 + 真实路径解析，不依赖 `...\` 缩略。所有 CLI/GUI/MCP 的默认位置同步改为真实路径。**写完必须加集成测试**：真注册表写值 → 禁用 → 再枚举找 `.disabled` → 启用 → 验证往返。

## SCManager 枚举 Windows 服务

```rust
use windows::Win32::System::Services::{
    OpenSCManagerW, EnumServicesStatusW, OpenServiceW, QueryServiceConfigW,
    SERVICE_WIN32, SERVICE_STATE_ALL, SERVICE_AUTO_START,
    SC_MANAGER_ENUMERATE_SERVICE, CloseServiceHandle,
};
```

**要点**：
- `EnumServicesStatusW` 8 个参数：scm, service_type (SERVICE_WIN32), state (SERVICE_STATE_ALL), buf ptr, buf size, &mut needed, &mut count, resume (None)
- 第一次调用 buf=0 → 获取所需大小 → 第二次调用传实际缓冲
- `QueryServiceConfigW` 同理：两次调用模式（None→获取大小，Some→填数据）
- 参数都传值，**不是引用**（`scm` 不是 `&scm`，`svc` 不是 `&svc`）
- Cargo.toml 需要 `"Win32_System_Services"` feature

## 参考文件

- `references/windows-crate-0.62-pitfalls.md` — windows crate 0.62 完整坑位（COM 接口形态、feature gate、类型签名、注册表 UTF-16LE 解码）
