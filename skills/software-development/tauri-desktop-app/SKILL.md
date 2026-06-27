---
name: tauri-desktop-app
description: Tauri v2 桌面/移动应用开发 — 项目搭建、插件配置、架构模式、跨平台适配
tags: [tauri, rust, desktop, android, pwa, cross-platform]
trigger: tauri|tauri v2|桌面应用|Tauri plugin|system tray|global shortcut|clipboard
category: software-development
---

# Tauri v2 桌面应用开发

## 核心理念

- **Spec 先行**：开发前先写 proposal → design → tasks，Comet 工作流驱动
- **复用优先**：先搜现成 Tauri 插件，不自己造轮子
- **文档驱动**：每个 Tauri API 调用都验证官方 v2 文档

## 项目启动

```bash
pnpm create tauri-app        # 选 vanilla JS + Vite
cd <project>
cargo install tauri-cli --locked  # Tauri CLI（如未安装）
```

## 前端选型决策树

```
复杂度评估
├── 单页面 + 少量交互  → Vanilla JS + Vite（本 Skill 默认）
├── 多页面 + 状态管理  → React/Preact
├── 响应式优先          → Solid/Svelte
└── 用户已有 React 栈   → React + Vite
```

对 Markdown 预览器这类"一个 textarea + 一个渲染 div"的应用，框架是过度工程。

## Tauri v2 插件矩阵

| 插件 | Cargo Crate | npm Package | 用途 | 备注 |
|------|------------|-------------|------|------|
| clipboard-manager | `tauri-plugin-clipboard-manager` | `@tauri-apps/plugin-clipboard-manager` | 读写剪贴板 | `readText()` / `writeText()` |
| global-shortcut | `tauri-plugin-global-shortcut` | `@tauri-apps/plugin-global-shortcut` | 全局热键 | `register('Ctrl+Shift+M', handler)` |
| single-instance | `tauri-plugin-single-instance` | — (Rust only) | 单实例 | 重复启动 → 聚焦已有窗口 |
| autostart | `tauri-plugin-autostart` | `@tauri-apps/plugin-autostart` | 开机自启 | `enable()` / `disable()` / `isEnabled()` |

### 系统托盘

用 Tauri 内置 `TrayIcon` API（**不需要插件**）：

```rust
use tauri::tray::{TrayIconBuilder, TrayIconEvent};
use tauri::menu::{Menu, MenuItem};

let menu = Menu::with_items(app, &[
    &MenuItem::with_id(app, "show", "显示/隐藏", true, None::<&str>)?,
    &MenuItem::with_id(app, "settings", "设置", true, None::<&str>)?,
    &MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?,
])?;

TrayIconBuilder::new()
    .icon(app.default_window_icon().unwrap().clone())
    .tooltip("App Title")
    .menu(&menu)
    .on_menu_event(|app, event| match event.id.as_ref() {
        "show" => { /* toggle window */ }
        "settings" => { /* open settings */ }
        "quit" => app.exit(0),
        _ => {}
    })
    .on_tray_icon_event(|tray, event| {
        if let TrayIconEvent::Click { .. } = event {
            // toggle window visibility
        }
    })
    .build(app)?;
```

### 窗口管理

```rust
// 获取窗口
let window = app.get_webview_window("main").unwrap();

// 显隐切换
if window.is_visible().unwrap_or(false) {
    window.hide().unwrap();
} else {
    window.show().unwrap();
    window.set_focus().unwrap();
}
```

### 安装命令

```bash
# Rust 侧
cd src-tauri
cargo add tauri-plugin-clipboard-manager
cargo add tauri-plugin-global-shortcut
cargo add tauri-plugin-single-instance
cargo add tauri-plugin-autostart

# JS 侧
pnpm add @tauri-apps/plugin-clipboard-manager
pnpm add @tauri-apps/plugin-global-shortcut
pnpm add @tauri-apps/plugin-autostart
```

## 能力配置 (capabilities/default.json)

```json
{
  "identifier": "default",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "clipboard-manager:allow-read-text",
    "clipboard-manager:allow-write-text",
    "global-shortcut:allow-register",
    "global-shortcut:allow-unregister",
    "autostart:allow-enable",
    "autostart:allow-disable",
    "autostart:allow-is-enabled"
  ]
}
```

## Android 端

> 📚 完整研究见 `references/android-clipboard-research.md`

### 剪贴板监听

参见 `references/android-clipboard-research.md`。

关键结论：
- 小窗前台时 `ClipboardManager.OnPrimaryClipChangedListener` **正常工作**，不需要 Shizuku
- 后台监听在 Android 10+ 被彻底禁止
- PWA 用 `visibilitychange` 事件 + `navigator.clipboard.readText()`

### Tauri Android 初始化

```bash
rustup target add aarch64-linux-android
# 需要 Android Studio + SDK + NDK 27+
pnpm tauri android init
pnpm tauri android dev
pnpm tauri android build
```

## 多端代码共享策略

```
项目根/
├── src/              # 共享前端（Vanilla JS + Vite）
│   ├── index.html
│   ├── main.js       # Tauri API → 桌面/Android 自动注入
│   ├── renderer.js   # Markdown 渲染（marked.js + highlight.js）
│   └── style.css
├── src-tauri/        # Rust 后端（桌面 + Android 共用）
│   ├── src/
│   │   ├── main.rs   # 插件注册、setup hook
│   │   ├── tray.rs   # 系统托盘（#[cfg(desktop)]）
│   │   ├── commands.rs
│   │   └── config.rs
│   └── tauri.conf.json
├── manifest.json     # PWA manifest（独立于 Tauri）
└── sw.js             # Service Worker（PWA 专属）
```

**关键**：前端代码完全不区分平台。`window.__TAURI__` 存在时走 Tauri API，否则走 Web Clipboard API。

## 常见坑

1. **global-shortcut 在 Linux/WSL 开发时可能不灵** — 正常现象，Windows 打包后生效
2. **Android 构建需要特定 NDK 版本** — 查最新 Tauri Android 文档
3. **PWA 的 `navigator.clipboard` 需要 HTTPS 或 localhost** — GitHub Pages 天然 HTTPS
4. **WSL2 下 Tauri dev 需要 `sudo pacman -S xdotool webkit2gtk-4.1`**
5. **Windows 交叉编译从 WSL2** — 推荐直接用 Windows 侧 Rust 构建，或 CI
6. **npm 11 的 devDependencies bug** — 如果受影响，全部移到 dependencies

## 设置持久化

```rust
use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Clone)]
struct Settings {
    hotkey: String,
    theme: String,
    auto_start: bool,
}

// 存储路径
let config_dir = dirs::config_dir().unwrap().join("app-name");
let config_path = config_dir.join("config.json");
```

## 验证清单

- [ ] `pnpm tauri dev` 桌面端可运行
- [ ] 托盘图标右键菜单正常
- [ ] 热键注册成功，可唤起窗口
- [ ] 剪贴板读取正常
- [ ] 设置保存/加载正常
- [ ] Android APK 可构建
- [ ] PWA 可安装
