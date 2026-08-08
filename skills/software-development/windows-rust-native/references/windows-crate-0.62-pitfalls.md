# windows crate 0.62 完整坑位（BootKeeper M0–M2 实战实录）

写于 2026-08-02，Rust 1.96 + windows 0.62.2 + winreg 0.56 实测。所有条目都是编译错误或真机崩溃换来的。

## 1. Feature gate 是编译期硬门槛

缺失 feature 报 `unresolved import` / `cannot find X in Win32`。按功能查：

| 功能 | 需要的 features |
|---|---|
| Task Scheduler COM | `Win32_System_TaskScheduler` + `Win32_System_Com` + `Win32_System_Variant` + `Win32_System_Ole` |
| WinVerifyTrust | `Win32_Security_WinTrust` + **`Win32_Security_Cryptography`** |
| SHGetFolderPathW | `Win32_UI_Shell` + `Win32_Foundation` |
| MessageBoxW | `Win32_UI_WindowsAndMessaging` |
| WaitForSingleObject | `Win32_System_Threading` |
| ShellExecuteW | `Win32_UI_Shell` |

**最阴的**：`WINTRUST_DATA` 结构体本身 gate 在 `Win32_Security_Cryptography` 下，不是 `Win32_Security_WinTrust`。只开 WinTrust feature，import WINTRUST_DATA 会 `unresolved import`，但 WinVerifyTrust 函数本体在。

## 2. COM 接口是高级封装

windows crate 的 COM 接口（ITaskService 等）是生成的高级绑定，不是裸 vtbl：
- `CoCreateInstance(&CLSID_X, None, CLSCTX_INPROC_SERVER)` 直接返回 `Result<ITaskService>`
- 方法签名已经是"人类友好"版本，但**全是 unsafe fn** → 调用必须包 `unsafe { }`
- `let...else` 配 unsafe block 要括号：`let Ok(x) = (unsafe { f() }) else { ... };`

**例外**：给 union 字段赋值（`data.Anonymous.pFile = &mut x`）不是 unsafe——赋值本身安全，解引用才需要 unsafe。第一个版本写成 `*data.Anonymous.pFile = x`（解引用空指针赋值）真机直接崩，改 `= &mut x` 正确且不需要 unsafe 块。

## 3. 常见类型/函数签名差异（0.62 与直觉不同）

| 项 | 0.62 签名 | 直觉陷阱 |
|---|---|---|
| `ShellExecuteW` | 6 参数 free function | 文档常见 SHELLEXECUTEINFOW 结构体版本；0.62 是简单 6 参版，返回 HINSTANCE（<=32 为错误码） |
| `WinVerifyTrust` | `(HWND, *mut GUID, *mut c_void)` | pwvtdata 是 `*mut c_void`，需 `(&mut data as *mut WINTRUST_DATA).cast::<c_void>()`；action 是 `*mut GUID` 要 `let mut` |
| `WinVerifyTrust` 返回值 | `i32` | `0x800B0100` 超 i32 范围，比较要 `0x800B0100u32 as i32` |
| `SHGetFolderPathW` | `(Option<HWND>, i32, Option<HANDLE>, u32, &mut [u16;260])` | 缓冲数组固定 `[u16; 260]`；csidl 是 `i32`；CSIDL_FLAG_CREATE = `0x8000`（或 `0x8000u32`） |
| `HWND` | `HWND(pub *mut c_void)` | 从 INVALID_HANDLE_VALUE 转：`HWND(INVALID_HANDLE_VALUE.0 as *mut _)` |
| `CloseHandle` | `Win32::Foundation` | 不在 `System::Threading` |
| `MESSAGEBOX_RESULT` | newtype | `ret == IDYES` 而不是 `ret == 6` |
| `VARIANT_BOOL` | `VARIANT_BOOL(i16)` | `true` = `-1`，`false` = `0` |

## 4. COM 集合接口：Count + get_Item，不是迭代器

```
IRegisteredTaskCollection::Count() -> Result<i32>
IRegisteredTaskCollection::get_Item(&VARIANT) -> Result<IRegisteredTask>
```
- 索引从 1 开始（COM 惯例）
- `get_Item` 收 `&VARIANT`，构造 `VARIANT::from(i)`
- 不要幻想 `for task in tasks` — 编译错误 `IRegisteredTaskCollection is not an iterator`

`IActionCollection` 不同：
- `Count(&mut i32) -> Result<()>` — 指针形式！
- `get_Item(i32) -> Result<IAction>` — 直接传值

## 5. Task Scheduler 枚举模式

```rust
let service: ITaskService = unsafe { CoCreateInstance(&CLSID_CTaskScheduler, None, CLSCTX_INPROC_SERVER) }?;
let none = VARIANT::default();
unsafe { service.Connect(&none, &none, &none, &none) }?;
let root: ITaskFolder = unsafe { service.GetFolder(&BSTR::from("\\")) }?;
let tasks = unsafe { root.GetTasks(1) }?;  // 1 = TASK_ENUM_HIDDEN
let count = unsafe { tasks.Count() }?;
for i in 1..=count {
    let task = unsafe { tasks.get_Item(&VARIANT::from(i)) }?;
    let name = unsafe { task.Name() }?.to_string();
}
```

任务操作：
- 启停：`task.SetEnabled(VARIANT_BOOL(if enabled { -1 } else { 0 }))`
- 删除：`folder.DeleteTask(&BSTR::from(name), 0)`
- `ITaskFolder::GetFolder` 支持嵌套路径（`\Microsoft\Windows`），root 是 `\`

## 6. WinVerifyTrust 正确写法

```rust
let mut file_info = WINTRUST_FILE_INFO {
    cbStruct: size_of::<WINTRUST_FILE_INFO>() as u32,
    pcwszFilePath: PCWSTR(wide.as_ptr()),   // PCWSTR 不是 PWSTR！
    hFile: INVALID_HANDLE_VALUE,
    pgKnownSubject: null_mut(),
};
let mut data = WINTRUST_DATA { cbStruct: ..., dwUIChoice: WTD_UI_NONE, fdwRevocationChecks: WTD_REVOKE_NONE, dwUnionChoice: WTD_CHOICE_FILE, ..Default::default() };
data.Anonymous.pFile = &mut file_info;      // ← 赋值，不是解引用！
let mut action = WINTRUST_ACTION_GENERIC_VERIFY_V2;
let result = unsafe { WinVerifyTrust(HWND(INVALID_HANDLE_VALUE.0 as *mut _), &mut action, (&mut data as *mut WINTRUST_DATA).cast::<c_void>()) };
// 0 = valid, 0x800B0100u32 as i32 = no signature, else invalid
```

## 7. 集成测试（真机跑，#[cfg(windows)]）

`crates/core/tests/windows_integration.rs` 里 `#![cfg(windows)]` — Linux 上 0 测试，Windows runner 上真跑。枚举测试只断言"不 panic + 字段非空"，不断言数量（CI 机器注册表可能是空的）。

## 7.5 注册表值是 UTF-16LE —— 豆腐块（tofu）bug

REG_SZ / REG_EXPAND_SZ 值在 Windows 里是 **UTF-16LE 编码，带结尾 null**。用 `String::from_utf8_lossy(&bytes)` 误解码 → UI（WebView2/表格）渲染成方块 □，复制出来"方块消失"（剪贴板存的是原始字符，粘贴到别的字体正常）。

```rust
use winreg::enums::RegType;

pub fn decode_reg_value_bytes(vtype: RegType, bytes: &[u8]) -> String {
    match vtype {
        RegType::REG_SZ | RegType::REG_EXPAND_SZ => {
            let mut units: Vec<u16> = bytes
                .chunks_exact(2)
                .map(|c| u16::from_le_bytes([c[0], c[1]]))
                .collect();
            while units.last() == Some(&0) { units.pop(); }  // 剥结尾 null
            String::from_utf16_lossy(&units)
        }
        _ => String::from_utf8_lossy(bytes).to_string(),
    }
}
```

**坑**：`enum_values()` 返回的 value NAME 已经是正常 String，只有 value BYTES 需要解码。**grep 所有 `from_utf8_lossy` 的调用点**（枚举 + 快照创建都可能有），不是只修看到的那一处。这个 bug 交叉编译 + 单测全绿，真机 GUI 才暴露——又是"必须真机验证"的例子。

## 8. 交叉编译 vs 真机

| 验证方式 | 能验证 | 不能验证 |
|---|---|---|
| `cargo check --target x86_64-pc-windows-msvc` | API 签名、feature、类型 | 链接、运行时行为、真机 API 调用 |
| CI windows-latest `cargo test` | 全部（真注册表/任务计划/签名） | — |

经验：本地 WSL 交叉编译通过 ≠ Windows 能跑。第一个 WINTRUST_DATA 版本交叉编译+clippy 全绿，真机直接 stack buffer overrun。**每个 Windows-native crate 都要配真机 CI。**
