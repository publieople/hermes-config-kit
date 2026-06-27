# Tauri v2 Manual Scaffold Templates

When `pnpm create tauri-app` is slow (proxy/WSL/network), build the project from these templates.

## File Checklist (creation order)

```
project/
├── package.json          # 1. Frontend deps
├── vite.config.js        # 2. Vite config with multi-page
├── src/
│   ├── index.html        # 3. Main page
│   ├── settings.html     # 4. Settings page (optional)
│   ├── main.js           # 5. App logic
│   ├── renderer.js       # 6. Markdown renderer
│   └── style.css         # 7. Styles
├── public/               # 8. PWA static files
│   ├── manifest.json
│   ├── sw.js
│   └── icons/
├── src-tauri/
│   ├── Cargo.toml        # 9. Rust deps
│   ├── tauri.conf.json   # 10. App config
│   ├── build.rs          # 11. Build script
│   ├── capabilities/
│   │   └── default.json  # 12. Permissions
│   ├── icons/            # 13. App icons (RGBA PNG)
│   └── src/
│       ├── main.rs       # 14. Entry point
│       ├── tray.rs       # 15. System tray
│       ├── commands.rs   # 16. Tauri commands
│       └── config.rs     # 17. Settings
├── CLAUDE.md             # 18. Project context
└── .gitignore            # 19. Git ignores
```

## Commands After File Creation

```bash
pnpm install
pnpm approve-builds esbuild  # if pnpm warns about ignored builds
pnpm build                   # verify frontend
cd src-tauri && cargo check  # verify Rust
git init && git add -A && git commit -m "init"
```

## Key Templates

### package.json (Vanilla JS + Tauri v2)
```json
{
  "name": "myapp",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "tauri": "tauri"
  },
  "dependencies": {
    "@tauri-apps/api": "^2",
    "@tauri-apps/plugin-clipboard-manager": "^2",
    "@tauri-apps/plugin-global-shortcut": "^2",
    "marked": "^15",
    "highlight.js": "^11"
  },
  "devDependencies": {
    "vite": "^6"
  }
}
```

### vite.config.js (multi-page)
```js
import { defineConfig } from 'vite';
import { resolve } from 'path';

const root = resolve(__dirname, 'src');

export default defineConfig({
  root: 'src',
  publicDir: '../public',
  build: {
    target: 'es2020',
    outDir: '../dist',
    emptyOutDir: true,
    rollupOptions: {
      input: [resolve(root, 'index.html'), resolve(root, 'settings.html')],
    },
  },
  server: { host: '127.0.0.1', port: 1420, strictPort: true },
  clearScreen: false,
});
```

### src-tauri/Cargo.toml
```toml
[package]
name = "myapp"
version = "0.1.0"
edition = "2021"

[dependencies]
tauri = { version = "2", features = ["tray-icon"] }
tauri-plugin-clipboard-manager = "2"
tauri-plugin-global-shortcut = "2"
tauri-plugin-single-instance = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
dirs = "6"

[build-dependencies]
tauri-build = { version = "2", features = [] }
```

### src-tauri/tauri.conf.json
```json
{
  "productName": "MyApp", "version": "0.1.0",
  "identifier": "com.example.myapp",
  "build": {
    "frontendDist": "../dist",
    "devUrl": "http://127.0.0.1:1420",
    "beforeDevCommand": "pnpm dev",
    "beforeBuildCommand": "pnpm build"
  },
  "app": {
    "windows": [{
      "title": "MyApp", "width": 800, "height": 600,
      "center": true, "visible": false, "resizable": true, "decorations": true
    }],
    "withGlobalTauri": true,
    "trayIcon": { "iconPath": "icons/icon.png", "iconAsTemplate": true }
  },
  "bundle": {
    "active": true, "targets": "all",
    "icon": ["icons/32x32.png","icons/128x128.png","icons/128x128@2x.png","icons/icon.icns","icons/icon.ico"]
  }
}
```

### src-tauri/capabilities/default.json
```json
{
  "identifier": "default", "description": "Default permissions",
  "windows": ["main"],
  "permissions": ["core:default", "clipboard-manager:default", "global-shortcut:default"]
}
```

### src-tauri/build.rs
```rust
fn main() { tauri_build::build() }
```

### src-tauri/src/main.rs (working skeleton)
```rust
use tauri::Manager;
mod commands; mod config; mod tray;

fn main() {
    let mut builder = tauri::Builder::default()
        .plugin(tauri_plugin_clipboard_manager::init());

    #[cfg(desktop)]
    {
        builder = builder.plugin(tauri_plugin_global_shortcut::Builder::new()
            .with_handler(|_app, _shortcut, event| {
                if event.state() == tauri_plugin_global_shortcut::ShortcutState::Pressed {}
            }).build());
        builder = builder.plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            let _ = app.get_webview_window("main").expect("no main window").set_focus();
        }));
    }

    builder.invoke_handler(tauri::generate_handler![commands::get_clipboard_text])
        .setup(|app| {
            #[cfg(desktop)] {
                use tauri_plugin_global_shortcut::{Code,GlobalShortcutExt,Modifiers,Shortcut};
                app.global_shortcut().register(
                    Shortcut::new(Some(Modifiers::CONTROL|Modifiers::SHIFT), Code::KeyM)
                )?;
            }
            let _tray = tray::create_tray(app.handle())?;
            config::ensure_config_dir()?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

## Pitfalls

- **Icon must be RGBA** (color type 6 PNG), not RGB — `generate_context!()` panics otherwise
- **npm 11 on Arch** has devDependencies bug — use `pnpm` instead
- **Vite `root: 'src'`** means `publicDir` must be `'../public'`, `outDir` must be `'../dist'`
- **Tauri `frontendDist: "../dist"`** is relative to src-tauri/
