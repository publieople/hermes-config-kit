# windows crate 0.62.2 API 速查（实测于 BootKeeper M0-M2）

源码位置：`~/.cargo/registry/src/index.crates.io-*/windows-0.62.2/src/Windows/Win32/`
**写代码前先读对应 mod.rs 确认签名**——文档/直觉经常和实际封装不一样。

## Feature 门控对照

| 要用的 API | 需要的 feature |
|---|---|
| Task Scheduler COM (`ITaskService` 等) | `Win32_System_TaskScheduler` + `Win32_System_Com` + `Win32_System_Variant` + `Win32_System_Ole` |
| `WINTRUST_DATA` / `WINTRUST_FILE_INFO` | `Win32_Security_WinTrust` + **`Win32_Security_Cryptography`**（没有这个 struct 都找不到！） |
| `WinVerifyTrust` | `Win32_Security_WinTrust` |
| `SHGetFolderPathW` | `Win32_UI_Shell` |
| `MessageBoxW` / `SW_HIDE` | `Win32_UI_WindowsAndMessaging` |
| `WaitForSingleObject` | `Win32_System_Threading` |
| `CloseHandle` / `HWND` / `HANDLE` / `INVALID_HANDLE_VALUE` | `Win32_Foundation` |

## Task Scheduler COM（高级封装，非 raw）

```rust
// 类名是 CLSID_CTaskScheduler，不是 TaskSchedulerClass
let service: ITaskService = unsafe {
    CoCreateInstance(&CLSID_CTaskScheduler, None, CLSCTX_INPROC_SERVER)
}?;

// Connect 要 4 个 &VARIANT（传 VARIANT::default()）
let none = VARIANT::default();
unsafe { service.Connect(&none, &none, &none, &none) }?;

// GetFolder 要 &BSTR，不是 &HSTRING
let root: ITaskFolder = unsafe { service.GetFolder(&BSTR::from("\\")) }?;

// 集合不是迭代器：Count() + get_Item(&VARIANT)
let tasks = unsafe { root.GetTasks(1) }?;   // TASK_ENUM_HIDDEN = 1
let count = unsafe { tasks.Count() }?;       // -> i32
for i in 1..=count {
    let v = VARIANT::from(i);
    let task = unsafe { tasks.get_Item(&v) }?;
}

// IActionCollection::Count 是 (&mut i32) 指针形式（和 IRegisteredTaskCollection 不同！）
let mut n = 0i32;
unsafe { actions.Count(&mut n) }?;
let action = unsafe { actions.get_Item(1) }?;  // 这里 get_Item 直接吃 i32

// IExecAction::Path 是 out-param（*mut BSTR）
let exec = action.cast::<IExecAction>()?;       // 需要 use windows::core::Interface;
let mut path = BSTR::new();
unsafe { exec.Path(&mut path) }?;
```

## WinVerifyTrust（签名校验）

```rust
let mut file_info = WINTRUST_FILE_INFO {          // 必须 mut！
    cbStruct: size_of::<WINTRUST_FILE_INFO>() as u32,
    pcwszFilePath: PCWSTR(wide.as_ptr()),         // PCWSTR 不是 PWSTR
    hFile: INVALID_HANDLE_VALUE,
    pgKnownSubject: null_mut(),
};
let mut data = WINTRUST_DATA {
    cbStruct: size_of::<WINTRUST_DATA>() as u32,
    dwUIChoice: WTD_UI_NONE,
    fdwRevocationChecks: WTD_REVOKE_NONE,
    dwUnionChoice: WTD_CHOICE_FILE,
    ..Default::default()                          // union 成员 zeroed
};
data.Anonymous.pFile = &mut file_info;            // 取地址！不是 *pFile = ...
let mut action = WINTRUST_ACTION_GENERIC_VERIFY_V2;
let result = unsafe {
    WinVerifyTrust(
        HWND(INVALID_HANDLE_VALUE.0 as *mut _),   // HWND 包装
        &mut action,                              // *mut GUID
        (&mut data as *mut WINTRUST_DATA).cast::<c_void>(),  // pwvtdata 是 *mut c_void
    )
};
// result == 0 有效；0x800B0100u32 as i32 = TRUST_E_NOSIGNATURE
```

## ShellExecuteW 提权（runas）

```rust
// 6 参数函数形式，返回 HINSTANCE；不是 SHELLEXECUTEINFOW 结构体版
let hinst = unsafe {
    ShellExecuteW(
        None,                                    // hwnd Option<HWND>
        &HSTRING::from("runas"),                 // verb
        &HSTRING::from(helper_path),             // file
        &HSTRING::from(params),                  // parameters
        &HSTRING::from(dir),                     // directory
        SW_HIDE,                                 // 在 WindowsAndMessaging 里
    )
};
if hinst.0 as isize <= 32 { /* 错误码 */ }
```

## SHGetFolderPathW

```rust
let mut buf = [0u16; 260];
unsafe { SHGetFolderPathW(None, csidl | 0x8000, None, 0, &mut buf) }?;
// 0x8000 = CSIDL_FLAG_CREATE；csidl 是 i32
```

## 其他

- `let Ok(x) = (unsafe { f() }) else { ... }` — let-else 配 unsafe 要括号，否则 E0658。
- `winreg::RegValue { bytes, .. } = value;` 用 let 解构（clippy 会建议），值本身是 REG_SZ 的原始 bytes。
- 交叉编译 `cargo check --target x86_64-pc-windows-msvc` 能过但 `cargo build`（bin）会卡在 `link.exe not found`——不是代码错，CI 有 MSVC 就能链。

## 实测修复记录（CI 真机抓到的 bug）

1. `*data.Anonymous.pFile = file_info` → null deref → `STATUS_STACK_BUFFER_OVERRUN` (0xc0000409)。修：`data.Anonymous.pFile = &mut file_info`。
2. 交叉编译看不出运行时崩溃——必须 windows-latest runner 跑真实枚举/验签才能暴露。
