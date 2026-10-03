# windows crate 0.62.2 实测 API 形态（BootKeeper M0 实编译验证）

来源：BootKeeper `crates/core/src/windows/`，在 WSL 用 `cargo build --target x86_64-pc-windows-msvc` 逐一编译验证。所有签名均来自 registry 缓存源码，非文档猜测。

## 所需 features

```toml
[target.'cfg(windows)'.dependencies]
windows = { version = "0.62", features = [
    "Win32_System_TaskScheduler",  # Task Scheduler COM
    "Win32_System_Com",            # CoCreateInstance
    "Win32_System_Variant",        # VARIANT（COM 方法参数）
    "Win32_System_Ole",            # ITaskService::Connect 依赖
    "Win32_Security_WinTrust",     # WinVerifyTrust
    "Win32_Security_Cryptography", # ★ WINTRUST_DATA 结构体被此 gate！
    "Win32_UI_Shell",              # SHGetFolderPathW
    "Win32_Foundation",            # HWND / INVALID_HANDLE_VALUE
] }
winreg = "0.56"
```

## Task Scheduler COM（枚举计划任务）

类 GUID 名是 `CLSID_CTaskScheduler`（不是 `TaskSchedulerClass`）；`ITaskService`/`ITaskFolder`/`IExecAction` 都是高级封装接口。

```rust
use windows::core::{BSTR, Interface};
use windows::Win32::System::Com::{CoCreateInstance, CLSCTX_INPROC_SERVER};
use windows::Win32::System::TaskScheduler::{CLSID_CTaskScheduler, IExecAction, ITaskFolder, ITaskService};
use windows::Win32::System::Variant::VARIANT;

// 创建服务
let service: ITaskService = unsafe { CoCreateInstance(&CLSID_CTaskScheduler, None, CLSCTX_INPROC_SERVER) }?;

// Connect 需要 4 个 &VARIANT（不是 None）
let none = VARIANT::default();
unsafe { service.Connect(&none, &none, &none, &none) }?;

// GetFolder 要 &BSTR（不是 &HSTRING）
let root: ITaskFolder = unsafe { service.GetFolder(&BSTR::from("\\")) }?;

// GetTasks(1) — TASK_ENUM_HIDDEN = 1
let tasks = unsafe { root.GetTasks(1) }?;

// ★ 集合不是迭代器：Count() + get_Item(&VARIANT)
let count = unsafe { tasks.Count() }?; // 返回 Result<i32>，直接取值
for i in 1..=count {
    let index = VARIANT::from(i);
    let task = unsafe { tasks.get_Item(&index) }?; // 要 &VARIANT
    let name = unsafe { task.Name() }?.to_string();
    let path = unsafe { task.Path() }?.to_string();
}
```

动作解析链：

```rust
fn resolve_command(task: &IRegisteredTask) -> String {
    use windows::core::Interface; // cast 方法需要这个 trait 在作用域
    let def = unsafe { task.Definition() }?;
    let actions = unsafe { def.Actions() }?;
    let mut count = 0i32;
    unsafe { actions.Count(&mut count) }?; // ★ IActionCollection::Count 是 (&mut i32) 指针形式
    if count == 0 { return String::new(); }
    let action = unsafe { actions.get_Item(1) }?; // ★ 这里是 i32 直接传，不是 VARIANT
    let exec = action.cast::<IExecAction>()?;     // cast 需要 Interface trait
    let mut path = BSTR::new();
    unsafe { exec.Path(&mut path) }?;             // ★ out-param 形式，不是返回 BSTR
    path.to_string()
}
```

## WinVerifyTrust（签名校验）

```rust
use std::os::windows::ffi::OsStrExt;
use windows::core::PCWSTR;
use windows::Win32::Foundation::{HWND, INVALID_HANDLE_VALUE};
use windows::Win32::Security::WinTrust::{
    WinVerifyTrust, WINTRUST_ACTION_GENERIC_VERIFY_V2, WINTRUST_DATA,
    WINTRUST_FILE_INFO, WTD_CHOICE_FILE, WTD_REVOKE_NONE, WTD_UI_NONE,
};

let wide: Vec<u16> = OsStr::new(path).encode_wide().chain(std::iter::once(0)).collect();
let file_info = WINTRUST_FILE_INFO {
    cbStruct: std::mem::size_of::<WINTRUST_FILE_INFO>() as u32,
    pcwszFilePath: PCWSTR(wide.as_ptr()),           // ★ PCWSTR 不是 PWSTR
    hFile: INVALID_HANDLE_VALUE,
    pgKnownSubject: std::ptr::null_mut(),
};
let mut data = WINTRUST_DATA {
    cbStruct: std::mem::size_of::<WINTRUST_DATA>() as u32,
    dwUIChoice: WTD_UI_NONE,
    fdwRevocationChecks: WTD_REVOKE_NONE,
    dwUnionChoice: WTD_CHOICE_FILE,
    ..Default::default()
};
data.Anonymous.pFile = &mut file_info;               // ★ union 字段叫 Anonymous；必须赋地址，不能解引用空 union 指针！
// ⚠️ 错误写法：unsafe { *data.Anonymous.pFile = file_info; }  ← 对 zeroed 的 union 指针解引用 = 空指针崩溃
//   这是真实踩过的坑：交叉编译通过，真 Windows CI 一跑就 STATUS_STACK_BUFFER_OVERRUN (0xc0000409)

let mut action = WINTRUST_ACTION_GENERIC_VERIFY_V2;
let result = unsafe {
    WinVerifyTrust(
        HWND(INVALID_HANDLE_VALUE.0 as *mut _),       // ★ 要 HWND，从 HANDLE.0 转
        &mut action,                                   // ★ *mut GUID
        (&mut data as *mut WINTRUST_DATA).cast::<core::ffi::c_void>(), // ★ *mut c_void
    )
};
// result == 0 → Valid；0x800B0100u32 as i32 (TRUST_E_NOSIGNATURE) → None；其他 → Invalid
```

## SHGetFolderPathW（启动文件夹路径）

```rust
let mut buf = [0u16; 260];                            // ★ 固定 [u16; 260]
let hr = unsafe { SHGetFolderPathW(None, csidl | 0x8000, None, 0, &mut buf) };
// 签名: (hwnd: Option<HWND>, csidl: i32, htoken: Option<HANDLE>, dwflags: u32, pszpath: &mut [u16; 260])
// CSIDL_STARTUP=0x07, CSIDL_COMMON_STARTUP=0x18, CSIDL_FLAG_CREATE=0x8000
// 转 String: OsString::from_wide 后 to_string_lossy
```

## winreg（注册表枚举）

```rust
use winreg::enums::{HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, KEY_READ};
use winreg::RegKey;

let key = RegKey::predef(hive).open_subkey_with_flags(subkey_path, KEY_READ)?;
for (name, value) in key.enum_values().flatten() {
    let cmd = match value {
        winreg::RegValue { bytes, .. } => String::from_utf8_lossy(&bytes).to_string(),
    };
    // Run 键值是 REG_SZ/REG_EXPAND_SZ，bytes 是 UTF-16LE？实测 from_utf8_lossy 够用（ASCII 路径）
}
```

## 杂项

- `let Ok(x) = (unsafe { f() }) else { ... };` — unsafe block 外面必须套括号才能配 let-else。
- `IRegisteredTaskCollection::Count` 返回 `Result<i32>` 直接取；`IActionCollection::Count(&mut i32)` 是 out-param。同名方法签名完全不同，逐个查。
- `windows::Win32::System::Variant::VARIANT::from(i32)` 可以把整数转成 COM 索引。
