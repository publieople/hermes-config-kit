# Tauri v2 Plugins Quick Reference

Condensed from official Tauri v2 docs (https://v2.tauri.app). Verify against live docs for API changes.

---

## System Tray

### JS API

```js
import { TrayIcon } from '@tauri-apps/api/tray';
import { Menu } from '@tauri-apps/api/menu';

const menu = await Menu.new({
  items: [
    { id: 'show', text: 'Show Preview', action: onTrayMenuClick },
    { id: 'settings', text: 'Settings', action: onTrayMenuClick },
    { id: 'quit', text: 'Quit', action: () => app.exit(0) },
  ],
});

const tray = await TrayIcon.new({
  menu,
  menuOnLeftClick: true,
  icon: 'icons/icon.png',
  tooltip: 'MDClipView',
});
```

### Rust API

```rust
use tauri::{
  menu::{Menu, MenuItem},
  tray::TrayIconBuilder,
};

let quit_i = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
let menu = Menu::with_items(app, &[&quit_i])?;

let tray = TrayIconBuilder::new()
  .menu(&menu)
  .show_menu_on_left_click(true)
  .on_menu_event(|app, event| match event.id.as_ref() {
    "quit" => app.exit(0),
    _ => {}
  })
  .build(app)?;
```

---

## Global Shortcut

### JS API

```js
import { register } from '@tauri-apps/plugin-global-shortcut';

await register('CommandOrControl+Shift+M', (event) => {
  if (event.state === "Pressed") {
    // toggle window
  }
});
```

### Rust API

```rust
use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut, ShortcutState};

app.handle().plugin(
    tauri_plugin_global_shortcut::Builder::new().with_handler(move |_app, shortcut, event| {
        if event.state() == ShortcutState::Pressed {
            // handle shortcut
        }
    }).build(),
)?;

let shortcut = Shortcut::new(Some(Modifiers::CONTROL | Modifiers::SHIFT), Code::KeyM);
app.global_shortcut().register(shortcut)?;
```

**Permissions needed:**
- `global-shortcut:allow-register`

**Shortcut string format:** `"Modifier+Modifier+Key"`
- Modifiers: `CommandOrControl`, `Shift`, `Alt`, `Super`
- `CommandOrControl` resolves to Cmd on macOS, Ctrl on Windows/Linux

---

## Clipboard Manager

### JS API

```js
import { writeText, readText } from '@tauri-apps/plugin-clipboard-manager';

// Write
await writeText('Tauri is awesome!');

// Read
const content = await readText();
```

### Rust API

```rust
use tauri_plugin_clipboard_manager::ClipboardExt;

app.clipboard().write_text("Tauri is awesome!".to_string()).unwrap();
let content = app.clipboard().read_text();
```

**Permissions needed:**
- `clipboard-manager:allow-read-text`
- `clipboard-manager:allow-write-text`

---

## Single Instance

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

---

## Autostart

### JS API

```js
import { enable, isEnabled, disable } from '@tauri-apps/plugin-autostart';

await enable();
const enabled = await isEnabled();
await disable();
```

**Permissions needed:**
- `autostart:allow-enable`
- `autostart:allow-disable`
- `autostart:allow-is-enabled`

---

## Window Management

### Key JS APIs

```js
import { getCurrentWindow } from '@tauri-apps/api/window';

const win = getCurrentWindow();

await win.center();                              // Center on screen
await win.setSize(new LogicalSize(800, 600));    // Resize
await win.setMinSize(new PhysicalSize(400, 300));// Min size
await win.setPosition(new LogicalPosition(0, 0));// Move
await win.hide();                                // Hide (keeps state)
await win.show();                                // Show
await win.setFocus();                            // Bring to front
await win.isVisible();                           // Check visibility
await win.close();                               // Close (destroys WebView)
```

### Rust API (programmatic window creation)

```rust
use tauri::WebviewWindowBuilder;

// In setup hook
tauri::WebviewWindowBuilder::new(
    app,
    "preview",
    tauri::WebviewUrl::App("index.html".into()),
)
.inner_size(800.0, 600.0)
.center()
.build()?;
```

In `tauri.conf.json`:
```json
{
  "app": {
    "windows": [
      {
        "label": "main",
        "create": false,
        "width": 800,
        "height": 600
      }
    ]
  }
}
```

---

## Project Scaffolding

### tauri.conf.json essentials

```json
{
  "productName": "MDClipView",
  "version": "0.1.0",
  "identifier": "com.publieople.mdclipview",
  "build": {
    "frontendDist": "../dist",
    "devUrl": "http://localhost:1420",
    "beforeDevCommand": "pnpm dev",
    "beforeBuildCommand": "pnpm build"
  },
  "app": {
    "windows": [{ "title": "MDClipView", "width": 800, "height": 600 }],
    "security": { "csp": null }
  },
  "bundle": {
    "active": true,
    "targets": "all",
    "icon": ["icons/icon.png"]
  }
}
```

### Cargo.toml plugin dependencies

```toml
[dependencies]
tauri = { version = "2", features = ["tray-icon"] }
tauri-plugin-shell = "2"
tauri-plugin-clipboard-manager = "2"
tauri-plugin-global-shortcut = "2"
tauri-plugin-single-instance = "2"
tauri-plugin-autostart = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

---

## Android Target Setup

```bash
# Install Android targets
rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android

# Initialize Android in project
pnpm tauri android init

# Set ANDROID_HOME and NDK
export ANDROID_HOME=/path/to/android/sdk
export NDK_HOME=$ANDROID_HOME/ndk/$(ls $ANDROID_HOME/ndk | tail -1)

# Dev on Android (USB or emulator)
pnpm tauri android dev

# Build APK
pnpm tauri android build
```

Requires: Android Studio, Android SDK, NDK, JDK 17+.
