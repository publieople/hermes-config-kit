# GitHub Actions: Multi-Platform Tauri Build

```yaml
name: Build
on:
  push:
    tags: ['v*']
  workflow_dispatch:
permissions:
  contents: write

jobs:
  windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v3
        with: { version: 11 }
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: pnpm }
      - uses: dtolnay/rust-toolchain@stable
        with: { targets: x86_64-pc-windows-msvc }
      - name: Install WiX Toolset
        run: dotnet tool install --global wix --version 5.0.2
      - run: pnpm install --frozen-lockfile
      - name: Build Tauri (Windows)
        run: pnpm tauri build --bundles msi
      - uses: actions/upload-artifact@v4
        with:
          name: app-windows
          path: src-tauri/target/release/bundle/msi/*.msi

  android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v3
        with: { version: 11 }
      - uses: actions/setup-node@v4
        with: { node-version: 22, cache: pnpm }
      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: >-
            aarch64-linux-android,
            armv7-linux-androideabi,
            i686-linux-android,
            x86_64-linux-android
      - uses: android-actions/setup-android@v3
        with:
          packages: 'platforms;android-34 build-tools;34.0.0 ndk;27.0.12077973 cmake;3.22.1'
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: 17 }
      - name: Install Linux deps
        run: sudo apt-get install -y -qq libwebkit2gtk-4.1-dev libxdo-dev libssl-dev
      - run: pnpm install --frozen-lockfile
      - name: Build Tauri (Android)
        run: |
          export ANDROID_HOME=$ANDROID_SDK_ROOT
          export NDK_HOME=$ANDROID_SDK_ROOT/ndk/27.0.12077973
          pnpm tauri android init
          pnpm tauri android build
      - uses: actions/upload-artifact@v4
        with:
          name: app-android
          path: src-tauri/gen/android/app/build/outputs/apk/release/*.apk

  release:
    if: startsWith(github.ref, 'refs/tags/v')
    needs: [windows, android]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with: { pattern: app-*, merge-multiple: true }
      - uses: softprops/action-gh-release@v2
        with:
          files: '*.msi\n*.apk'
          generate_release_notes: true
```

Common failures:
- `frozen-lockfile` error → use `--no-frozen-lockfile` if lockfile may be stale
- `.ico` not in 3.00 format → generate valid ICO
- `no library targets` → add `[lib]` with cdylib to Cargo.toml
- `unresolved imports tauri::menu, tauri::tray` → add `#![cfg(desktop)]` to tray.rs
