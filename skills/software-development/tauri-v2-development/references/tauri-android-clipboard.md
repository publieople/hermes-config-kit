# Android Clipboard Handling in Tauri v2

## Summary

Android clipboard access is heavily restricted since Android 10. This reference covers what's possible at each permission level.

---

## Clipboard Access Levels

| Method | Background? | Requires | Notes |
|--------|------------|----------|-------|
| `navigator.clipboard.readText()` (WebView/PWA) | ❌ Foreground only | None | Must be from user-initiated context |
| `ClipboardManager.getPrimaryClip()` (Android API) | ❌ Foreground only | None | Standard Android API |
| `ClipboardManager.OnPrimaryClipChangedListener` | ⚠️ Only when app is in foreground | None | Listener works in foreground service IF app visible |
| Shizuku-privileged clipboard read | ✅ Background | Shizuku installed + authorized | Proxies through shell UID |
| Root | ✅ Background | Root access | Full system access |

---

## Android Clipboard Restriction History

| Version | Change |
|---------|--------|
| **Android 9- (API < 29)** | Any app could read clipboard in background |
| **Android 10 (API 29)** | Background clipboard access blocked. Only foreground app can read. `READ_CLIPBOARD_IN_BACKGROUND` permission exists but is `protectionLevel=signature` (system-only) |
| **Android 12 (API 31)** | Toast notification on every clipboard read: "App pasted from clipboard" |
| **Android 13 (API 33)** | `EXTRA_IS_SENSITIVE` flag for clipboard data. Privacy setting toggle for clipboard access warnings |
| **Android 14-16** | No relaxation. Foreground services tightened further. Google Issue #137878823 for background clipboard permission — unresolved for 5+ years |

---

## The Foreground Listener Approach (Recommended for MDClipView)

When an Android app is in the foreground (including split-screen/multi-window/popup view), `ClipboardManager.OnPrimaryClipChangedListener` works normally:

```kotlin
val clipboardManager = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
clipboardManager.addPrimaryClipChangedListener {
    val clip = clipboardManager.primaryClip
    if (clip != null && clip.itemCount > 0) {
        val text = clip.getItemAt(0).text?.toString() ?: ""
        // Send to Tauri frontend via plugin bridge
    }
}
```

This means: **if the app is running in a small window (Android popup view mode), clipboard changes are detected automatically.** No Shizuku needed for this use case.

---

## Tauri v2 Android Plugin Architecture

To expose Android clipboard to the Tauri frontend:

```
Android App (Tauri v2)
├── Kotlin Plugin
│   extends app.tauri.plugin.Plugin
│   annotated @TauriPlugin
│   └── ClipboardListener
│       └── OnPrimaryClipChanged → invoke("clipboard_changed", text)
│
├── Rust Backend
│   └── Receives plugin event → emits to WebView
│
└── WebView Frontend
    └── Listens for "clipboard-changed" event → renders markdown
```

### Kotlin Plugin Template

```kotlin
@TauriPlugin
class ClipboardPlugin(private val rust: Rust) : Plugin(rust) {
    private lateinit var clipboardManager: ClipboardManager
    
    override fun load(webView: WebView) {
        clipboardManager = webView.context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        clipboardManager.addPrimaryClipChangedListener {
            val text = clipboardManager.primaryClip?.getItemAt(0)?.text?.toString() ?: return@addPrimaryClipChangedListener
            rust.invoke("clipboard_changed", text)
        }
    }
}
```

---

## Shizuku Background Monitoring

For true background clipboard monitoring (detecting clipboard changes even when app is not visible):

### How Shizuku Works

Shizuku starts a privileged process running as `shell` UID (same as ADB). When an app uses Shizuku API to read clipboard, the call is proxied through this privileged process, bypassing the foreground-only restriction.

### Shizuku Setup (Octoclip Pattern)

1. User installs Shizuku app
2. User activates Shizuku service (via wireless debugging or ADB)
3. App requests Shizuku authorization
4. App uses Shizuku API to register clipboard listener
5. Clipboard changes detected in background → app notified

### Shizuku API Integration

```kotlin
// Check Shizuku availability
if (Shizuku.pingBinder()) {
    // Request permission
    if (Shizuku.checkSelfPermission() == PackageManager.PERMISSION_GRANTED) {
        // Use Shizuku to execute privileged operations
        val process = Runtime.getRuntime().exec("sh")
        // ... clipboard monitoring through privileged process
    }
}
```

### Limitations

- Not all users have Shizuku installed
- Google Play may reject apps that depend on Shizuku
- Consider: distribute APK via GitHub Releases instead of Play Store
- Octoclip and Tasker both use this pattern successfully

---

## PWA Clipboard Limitations

PWAs on Android cannot:
- Monitor clipboard in background (Service Workers don't have clipboard API access — W3C issue #458)
- Read clipboard without user interaction

PWA clipboard strategy:
- Use `visibilitychange` event: when user switches to the PWA, auto-read clipboard
- Fallback: "Paste" button that calls `navigator.clipboard.readText()`
- Store last-rendered text to avoid duplicate renders

```js
let lastText = '';
document.addEventListener('visibilitychange', async () => {
    if (document.visibilityState === 'visible') {
        try {
            const text = await navigator.clipboard.readText();
            if (text && text !== lastText) {
                lastText = text;
                renderMarkdown(text);
            }
        } catch (e) {
            // Clipboard read requires user gesture on some browsers
        }
    }
});
```
