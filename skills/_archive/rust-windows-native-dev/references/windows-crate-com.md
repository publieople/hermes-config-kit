# windows crate 0.62.2 — COM API notes (from BootKeeper)

Verified against the crate's generated source in
`~/.cargo/registry/src/index.crates.io-*/windows-0.62.2/src/Windows/Win32/`.
**Always read the module's `mod.rs` in the registry cache before using an API** —
the high-level wrappers differ from the C signatures in surprising ways.

## Required features (this is where most "cannot find" errors come from)

| API family | Features |
|---|---|
| Task Scheduler | `Win32_System_TaskScheduler`, `Win32_System_Com`, `Win32_System_Variant`, `Win32_System_Ole` |
| WinVerifyTrust | `Win32_Security_WinTrust` **and** `Win32_Security_Cryptography` (WINTRUST_DATA struct is gated on Cryptography!) |
| SHGetFolderPathW | `Win32_UI_Shell`, `Win32_Foundation` |

Check available features: `crates.io/api/v1/crates/windows/<ver>` → `version.features` keys.

## Task Scheduler (COM)

```rust
use windows::core::BSTR;
use windows::Win32::System::Com::{CoCreateInstance, CLSCTX_INPROC_SERVER};
use windows::Win32::System::TaskScheduler::{
    CLSID_CTaskScheduler, ITaskFolder, ITaskService, IExecAction,
};
use windows::Win32::System::Variant::VARIANT;

let service: ITaskService =
    unsafe { CoCreateInstance(&CLSID_CTaskScheduler, None, CLSCTX_INPROC_SERVER) }?;
let none = VARIANT::default();
unsafe { service.Connect(&none, &none, &none, &none) }?;   // 4x &VARIANT, not NULL
let root: ITaskFolder = unsafe { service.GetFolder(&BSTR::from("\\")) }?;
let tasks = unsafe { root.GetTasks(1) }?;                   // TASK_ENUM_HIDDEN = 1
let count = unsafe { tasks.Count() }?;                      // returns Result<i32>
for i in 1..=count {
    let index = VARIANT::from(i);
    let task = unsafe { tasks.get_Item(&index) }?;          // get_Item takes &VARIANT!
    let name = unsafe { task.Name() }?.to_string();
}
```

Key differences from C API:
- `ITaskService::Connect` takes `&VARIANT` x4 — pass `VARIANT::default()` for all.
- `IRegisteredTaskCollection` is **not an iterator** — `Count()` + `get_Item(&VARIANT)`.
- `ITaskFolder::GetFolder` takes `&BSTR`, not `&HSTRING`.
- Class is `CLSID_CTaskScheduler` (COM class), NOT `TaskSchedulerClass`.

Resolving the command from a task's first action:

```rust
use windows::core::Interface;  // REQUIRED for .cast()

fn resolve_command(task: &IRegisteredTask) -> String {
    let def = unsafe { task.Definition() }.ok()?;
    let actions = unsafe { def.Actions() }.ok()?;
    let mut count = 0i32;
    unsafe { actions.Count(&mut count) }.ok()?;   // NOTE: out-param style!
    let action = unsafe { actions.get_Item(1) }.ok()?;  // get_Item takes i32 here!
    let exec = action.cast::<IExecAction>().ok()?;
    let mut path = BSTR::new();
    unsafe { exec.Path(&mut path) }.ok()?;        // out-param, returns Result<()>
    path.to_string()
}
```

Traps:
- `IActionCollection::Count(&mut i32) -> Result<()>` — out-param.
- `IActionCollection::get_Item(i32)` — plain i32, unlike the task collection's VARIANT.
- `IExecAction::Path(&mut BSTR) -> Result<()>` — out-param, returns `()`, NOT the path.

## WinVerifyTrust (Authenticode signature check)

```rust
use windows::core::PCWSTR;
use windows::Win32::Foundation::HWND;
use windows::Win32::Security::WinTrust::{
    WinVerifyTrust, WINTRUST_ACTION_GENERIC_VERIFY_V2, WINTRUST_DATA,
    WINTRUST_FILE_INFO, WTD_CHOICE_FILE, WTD_REVOKE_NONE, WTD_UI_NONE,
};

let wide: Vec<u16> = ...encode_wide()...;          // path + null terminator
let mut file_info = WINTRUST_FILE_INFO {           // MUST be mut (API writes it)
    cbStruct: size_of::<WINTRUST_FILE_INFO>() as u32,
    pcwszFilePath: PCWSTR(wide.as_ptr()),          // PCWSTR, not PWSTR!
    hFile: INVALID_HANDLE_VALUE,
    pgKnownSubject: null_mut(),
};
let mut data = WINTRUST_DATA {
    cbStruct: size_of::<WINTRUST_DATA>() as u32,
    dwUIChoice: WTD_UI_NONE,
    fdwRevocationChecks: WTD_REVOKE_NONE,
    dwUnionChoice: WTD_CHOICE_FILE,
    ..Default::default()
};
data.Anonymous.pFile = &mut file_info;             // ASSIGN the pointer. NEVER *ptr = x
let mut action = WINTRUST_ACTION_GENERIC_VERIFY_V2;
let result = unsafe {
    WinVerifyTrust(
        HWND(INVALID_HANDLE_VALUE.0 as *mut _),    // HWND wrapper
        &mut action,                               // *mut GUID
        (&mut data as *mut WINTRUST_DATA).cast::<core::ffi::c_void>(),  // *mut c_void!
    )
};
// 0 == valid; 0x800B0100 == no signature (compare as 0x800B0100u32 as i32)
```

The bug CI caught: writing `*data.Anonymous.pFile = file_info;` dereferences a
**null** union pointer (Default is zeroed) → null deref, `STATUS_STACK_BUFFER_OVERRUN`
on real Windows. The correct form assigns the address.

## winreg (registry)

```rust
use winreg::enums::{HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE, KEY_READ};
use winreg::RegKey;

let key = RegKey::predef(hive).open_subkey_with_flags(path, KEY_READ)?;
for (name, value) in key.enum_values().flatten() {
    let winreg::RegValue { bytes, .. } = value;
    let cmd = String::from_utf8_lossy(&bytes).to_string();
}
```

## SHGetFolderPathW (startup folder paths)

```rust
let hr = unsafe { SHGetFolderPathW(None, csidl | 0x8000, None, 0, &mut buf) };  // buf: [u16; 260]
// hwnd: Option<HWND>, csidl: i32, buf fixed 260 — CSIDL_FLAG_CREATE = 0x8000
```

## Rust syntax traps that bit during this work

- `let Ok(x) = (unsafe { f() }) else { ... };` — unsafe block inside let-else
  needs wrapping parens or it's a syntax error.
- Union field is `Anonymous`, not `u`.
- `0x800B0100` (HRESULT failure) doesn't fit i32 literal — cast: `0x800B0100u32 as i32`.
- `PWSTR` vs `PCWSTR` are distinct types — const API wants `PCWSTR`.

## CI pattern (real Windows validation)

```yaml
test-windows:
  runs-on: windows-latest          # REAL Windows: registry, Task Scheduler, WinVerifyTrust live
  steps:
    - uses: actions/checkout@v4
    - uses: dtolnay/rust-toolchain@stable
    - run: cargo test --workspace  # runs tests/windows_integration.rs (#![cfg(windows)])
    - run: cargo clippy --workspace --all-targets -- -D warnings
```

`windows-latest` runners always have the Task Scheduler service and system tasks
under `\Microsoft\Windows\...`, so enumeration integration tests get real data.
