---
name: tauri-v2-development
description: Tauri v2 desktop + mobile app development — scaffolding, plugin ecosystem, architecture patterns, Android target, and cross-platform packaging. Use when building or planning a Tauri v2 project.
tags: [tauri, rust, desktop, mobile, android, cross-platform]
category: software-development
---

# Tauri v2 Development

## When to Use

- Starting a new Tauri v2 project (desktop or mobile)
- Figuring out which plugins are available for a Tauri feature
- Planning architecture for a Tauri app with Rust backend + web frontend
- Setting up Android build target for a Tauri project
- Deciding between Tauri plugins vs custom implementation

## Quick Start

```bash
# Scaffold a new project (pick one)
pnpm create tauri-app          # PNPM
npm create tauri-app@latest    # NPM
cargo install create-tauri-app --locked && cargo create-tauri-app  # Cargo

# Install Tauri CLI (if not already)
cargo install tauri-cli

# Dev mode
pnpm tauri dev

# Build
pnpm tauri build
```

## Plugin Ecosystem

Tauri v2 plugins are the primary way to access native platform features. Most are official, under `tauri-apps/plugins-workspace`.

| Plugin | npm package | Rust crate | Purpose |
|--------|------------|------------|---------|
| **System Tray** | built-in | `tauri::tray` | Tray icon, right-click menu, left-click handler |
| **Global Shortcut** | `@tauri-apps/plugin-global-shortcut` | `tauri-plugin-global-shortcut` | Register system-wide hotkeys |
| **Clipboard** | `@tauri-apps/plugin-clipboard-manager` | `tauri-plugin-clipboard-manager` | Read/write text to system clipboard |
| **Single Instance** | built-in | `tauri-plugin-single-instance` | Prevent duplicate app instances |
| **Autostart** | `@tauri-apps/plugin-autostart` | `tauri-plugin-autostart` | Launch app on system startup |
| **Shell** | `@tauri-apps/plugin-shell` | `tauri-plugin-shell` | Execute shell commands |

### Install a plugin

```bash
pnpm tauri add <plugin-name>   # Installs both npm + cargo deps
# OR manually:
cargo add tauri-plugin-<name>   # In src-tauri/
pnpm add @tauri-apps/plugin-<name>  # In frontend/
```

Then register in `src-tauri/src/lib.rs`:

```rust
tauri::Builder::default()
    .plugin(tauri_plugin_clipboard_manager::init())
    .plugin(tauri_plugin_global_shortcut::Builder::new().build())
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
```

And add permissions in `src-tauri/capabilities/default.json`:

```json
{
  "permissions": [
    "clipboard-manager:allow-read-text",
    "clipboard-manager:allow-write-text",
    "global-shortcut:allow-register",
    "autostart:allow-enable",
    "autostart:allow-disable"
  ]
}
```

## Architecture Patterns

### Recommended: Vanilla JS frontend + Rust backend

For simple apps (previewers, utilities, tools), skip React/Vue/Svelte. Use:

```
src/                  # Vanilla HTML/CSS/JS (no framework)
src-tauri/            # Rust backend
  src/
    main.rs           # Entry point: plugin init, setup hook
    tray.rs           # System tray logic
    commands.rs       # #[tauri::command] functions
    config.rs         # Settings persistence (serde + JSON)
  Cargo.toml
  tauri.conf.json
  capabilities/
    default.json       # Permission whitelist
```

### When to use React/Vue/etc

Only when the frontend has complex state management (forms, reactive data, routing). For a markdown previewer with a textarea and a render div, vanilla JS + Vite bundler is sufficient and keeps binary size small.

### Tauri CLI conventions

```bash
pnpm tauri dev          # Dev with hot reload
pnpm tauri build        # Production build
pnpm tauri android dev  # Android dev (requires Android Studio)
pnpm tauri android build # Android APK build
pnpm tauri icon <file>  # Generate all icon sizes
```

## Detailed API Gotchas (discovered in practice)

### global-shortcut: matches() takes (Modifiers, Code), NOT a string
```rust
// ❌ WRONG — compile error "expected 2 arguments"
shortcut.matches("Ctrl+Shift+M")

// ✅ CORRECT
use tauri_plugin_global_shortcut::{Code, Modifiers, Shortcut};
let target = Shortcut::new(Some(Modifiers::CONTROL | Modifiers::SHIFT), Code::KeyM);
shortcut == &target  // compare Shortcut values directly
```

### global-shortcut: plugin goes on Builder, NOT in setup()
```rust
// ❌ WRONG — setup() gives you App, not Builder; app.plugin() doesn't exist
builder.setup(|app| {
    app.plugin(tauri_plugin_global_shortcut::Builder::new()...)?;
})

// ✅ CORRECT — register handler on Builder, shortcut in setup
let mut builder = tauri::Builder::default()
    .plugin(tauri_plugin_global_shortcut::Builder::new()
        .with_handler(|_app, _shortcut, event| { ... })
        .build());

builder.setup(|app| {
    app.global_shortcut().register(shortcut)?;
    Ok(())
});
```

### autostart v2.5+: init() takes extra args AND `.autostart()` on AppHandle doesn't exist
```rust
// API changed in v2.5+. init() requires MacosLauncher + Option<Vec<&str>> args.
// Additionally, `app.autostart().enable()` does NOT compile — the AutostartExt
// trait path changed. Skip for MVP; implement in later phase with version-pinned docs.
// Workaround: use placeholder commands returning Ok(false) / Ok(()) for now.
```

### Emitter trait: must import explicitly for window.emit()
```rust
use tauri::Emitter;  // ← REQUIRED, or emit() won't resolve
window.emit("event-name", payload)?;
```

### Icon: must be RGBA (color type 6), not RGB
```rust
// generate_context!() panics with "icon is not RGBA" if PNG is color type 2 (RGB)
// Use color type 6 (RGBA) with alpha channel
// Quick RGBA PNG generator: see references/png-icon-generator.py
```

### Vite + Tauri multi-page: use flat array for rollupOptions.input
```js
// ✅ Preserves flat output: dist/index.html, dist/settings.html
rollupOptions: {
  input: [
    resolve(root, 'index.html'),
    resolve(root, 'settings.html'),
  ],
}
// ❌ Named entries create subdirectories: dist/main/index.html
```

### Vite `publicDir` when `root` is not project root
```js
// When root: 'src', the default publicDir becomes 'src/public'.
// To keep static assets at project-root/public/, set explicitly:
export default defineConfig({
  root: 'src',
  publicDir: '../public',   // ← REQUIRED when root ≠ '.'
  // ...
});
```

### Vite `base` for GitHub Pages subpath deployment
```js
// MUST set base when deploying to GH Pages at a subpath (e.g., /repo-name/):
export default defineConfig({
  base: '/repo-name/',   // affects all asset URLs, manifest links, SW paths
  // ...
});
// Without this, assets 404 because they resolve relative to root '/'.
```

### npm 11 Arch bug: devDependencies silently skipped

npm 11 on Arch Linux does not install devDependencies into `node_modules/`.
Workaround: use **pnpm** instead (preferred for all Tauri projects), or merge all deps into dependencies.

```bash
# ✅ Preferred: use pnpm
pnpm install

# ❌ npm 11 on Arch: devDeps silently missing, build fails
npm install
```

## Key Pitfalls

### 1. Permission must be explicitly added

Every Tauri plugin command needs explicit permission in `capabilities/default.json`. Missing permission = silent failure or runtime error. Check the plugin docs for exact permission strings.

### 2. Plugin registration order matters

Register plugins with `.plugin()` BEFORE `.setup()` in the builder chain. Some plugins need to be initialized before the setup hook runs.

### 3. Window management: hide vs close

Use `window.hide()` not `window.close()` for tray apps. Closing destroys the WebView; hiding preserves state. On app exit, explicitly call `app.exit(0)`.

### 4. System tray onActionEvent in Rust vs JS

Rust tray APIs use `TrayIconBuilder::on_menu_event()`. JS tray APIs use `Menu.new({ items: [{ action: fn }] })`. Choose one — don't mix. For a tray-heavy app, Rust side is cleaner since it has direct access to window handles.

### 5. Android clipboard: foreground-only without Shizuku

On Android, `ClipboardManager.OnPrimaryClipChangedListener` only fires when the app is in the foreground. For background monitoring, Shizuku (ADB-level privileged process) is required. See `references/tauri-android-clipboard.md` for details.

### 6. Single instance requires desktop cfg guard

```rust
#[cfg(desktop)]
{
    builder = builder.plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
        let _ = app.get_webview_window("main")
                   .expect("no main window")
                   .set_focus();
    }));
}
```

Mobile platforms don't need single-instance enforcement (OS handles it).

### 7. Window visibility state management

### 8. Android requires `[lib]` with `cdylib` in Cargo.toml

```
error: no library targets found in package `app-name`
```

Android builds (`tauri android build`) compile with `--lib` flag. Without `[lib]`, it fails. Fix:

```toml
# src-tauri/Cargo.toml
[lib]
name = "app-name"
crate-type = ["lib", "cdylib"]
```

Then move `run()` to `src/lib.rs`:
```rust
// src/lib.rs
pub fn run() { /* plugin setup, builder chain */ }

// src/main.rs
fn main() { app_name::run(); }
```

### 9. Entire tray module needs `#![cfg(desktop)]` for Android

```rust
// src-tauri/src/tray.rs — FIRST line:
#![cfg(desktop)]
```

And in lib.rs: `#[cfg(desktop)] mod tray;`

Without this, Android builds fail because `tauri::menu`, `tauri::tray`, `window.center()` etc. don't exist on mobile targets.

### 10. .ico must be valid ICO format (not PNG renamed)

```
error RC2175: resource file icon.ico is not in 3.00 format
```

Windows Resource Compiler validates .ico structure. Generate proper ICO (PNG data in ICO wrapper). See `references/icon-generation.md`.

### 11. `pnpm tauri android init` required before first Android build

```
Android Studio project directory .../gen/android doesn't exist
```

CI must run `pnpm tauri android init` before `pnpm tauri android build` on clean checkouts.

When toggling a preview window (show/hide via hotkey or tray):
- Track visibility in Rust state: `Mutex<bool>` or `AtomicBool`
- Use `window.is_visible()` to check current state
- Use `window.show()` / `window.hide()` plus `.set_focus()` when showing

## WSL2 Development Notes

- Tauri dev (`pnpm tauri dev`) works on WSL2 Linux, but plugins requiring native OS features (tray, global shortcut) may behave differently or not work
- Frontend dev and testing works fully in WSL2 — use `pnpm tauri dev` for quick UI iteration
- For full integration testing of Windows-specific features (tray, hotkeys), build and run on Windows natively
- `cargo tauri build` for Windows target requires `x86_64-pc-windows-msvc` target or cross-compilation via `mingw-w64`

## Reference Files

| File | Contents |
|------|----------|
| `references/scaffold-files.md` | Complete file templates for manual Tauri v2 project scaffolding |
| `references/tauri-plugins-reference.md` | Complete API reference for all major Tauri v2 plugins |
| `references/tauri-android-clipboard.md` | Android clipboard restriction history and approaches |
| `references/pwa-github-pages-deploy.md` | GitHub Pages PWA deployment workflow |
| `references/github-actions-build.md` | Multi-platform CI: Windows .msi + Android APK + Release |
| `references/icon-generation.md` | Programmatic icon generation (RGBA PNG, multi-size ICO) |

- Official docs: https://v2.tauri.app (always check before implementing plugin-specific code)
