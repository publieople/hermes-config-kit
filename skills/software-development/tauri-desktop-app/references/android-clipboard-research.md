# Android 剪贴板访问研究

## 权限演进史

| Android 版本 | API | 变化 |
|---|---|---|
| ≤9 | ≤28 | 任意 App 可在后台监听剪贴板变化 |
| **10** | **29** | **🚫 后台禁止读剪贴板**。`READ_CLIPBOARD_IN_BACKGROUND` 权限存在但 `protectionLevel="signature"`，仅系统 App 可用 |
| 12 | 31 | 每次读剪贴板弹出 Toast："XX 应用从剪贴板粘贴了内容" |
| 13 | 33 | 敏感内容标记 `EXTRA_IS_SENSITIVE`，隐私设置中可开关剪贴板访问提示 |
| 14 | 34 | 前景服务类型严格要求，后台限制进一步收紧 |
| 15-16 | 35-36 | 无变化。Google Issue #137878823 要求开放后台剪贴板权限，五年未解决 |

## 当前（Android 16）的可行方案

### 方案对比

| 方案 | 前台读 | 后台监听 | 需要权限 | PWA 可用 |
|------|--------|---------|----------|---------|
| `ClipboardManager.getPrimaryClip()` | ✅ | ❌ | 无 | ❌ |
| `OnPrimaryClipChangedListener` | ✅ 前台时触发 | ❌ 后台不触发 | 无 | ❌ |
| Shizuku 代理 | ✅ | ✅ | Shizuku + 用户授权 | ❌ |
| AccessibilityService | ✅ | ✅ | 无障碍权限 | ❌ |
| PWA `navigator.clipboard.readText()` | ✅ | ❌ | HTTPS | ✅ |
| PWA `visibilitychange` + read | ✅ | ❌ | HTTPS | ✅ |

### 推荐策略

**小窗前台模式**（不依赖 Shizuku）：
- 当 App 在小窗/分屏前台运行时，`OnPrimaryClipChangedListener` 正常触发
- 适合"小窗开着，复制即渲染"的场景
- 不需要任何额外权限或 Shizuku

**PWA 降级方案**：
```js
document.addEventListener('visibilitychange', async () => {
  if (document.visibilityState === 'visible') {
    const text = await navigator.clipboard.readText();
    if (text !== lastRendered) renderMarkdown(text);
  }
});
```

**Shizuku 方案**（如需要真正后台监听）：
- 已证实可行：Octoclip 在生产中使用
- 原理：Shizuku 启动 shell UID 进程代理 ClipboardManager 调用
- 缺点：需要用户安装 Shizuku + 授权，Google Play 审查灰色地带

## 来源

- [Android Developers: Secure Clipboard Handling](https://developer.android.com/privacy-and-security/risks/secure-clipboard-handling)
- [Google Issue Tracker #137878823](https://issuetracker.google.com/issues/137878823)
- [Octoclip Docs: Background Monitoring with Shizuku](https://docs.octoclip.app/features/source/background-monitoring/android/shizuku.html)
- [Stack Overflow: Rooting android is the only way to access clipboard from background in Android 11?](https://stackoverflow.com/questions/77927971)
- [W3C Editing Issue #458: navigator.clipboard in Service Workers](https://github.com/w3c/editing/issues/458)
