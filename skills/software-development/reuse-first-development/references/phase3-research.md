# open-any Phase 3 Research Results (2026-06-20)

## 背景

在 Phase 2 完成后（8 handlers, 182 tests, 零 lint），SPEC.md 列出 5 个 Open Questions。
用户确认 ABC 三个方向都需要做。按 reuse-first-development 方法论逐一调研。

---

## A. 补齐盲区

### A1. PDF 查看

| 候选 | 大小 | 浏览器 | 维护 | 结论 |
|------|------|--------|------|------|
| `react-pdf` | ~50KB | ✅ | ✅ 活跃 | ✅ **选用** |
| `pdfjs-dist` 原生 | 1MB | ✅ | ✅ Mozilla 维护 | 太重, 无 React 封装 |
| 原生 `<iframe>` | 0 | ✅ | ✅ 内置 | 太简陋 |
| Nutrient SDK | 大 | ✅ | 商业 | 付费, 不需要 |

**决策**: `react-pdf` v9 + `pdfjs-dist` worker 走 CDN（避免 1MB 打包进 bundle）。

### A2. 压缩包浏览

| 候选 | 大小 | ZIP | TAR | GZIP | 结论 |
|------|------|-----|-----|------|------|
| `fflate` | 30KB (+3KB ZIP) | ✅ | ❌ | ✅ | ✅ **选用** |
| `JSZip` | 94KB | ✅ | ❌ | ❌ | 更大, API 更友好但慢 |
| `libarchive.js` | 大 | ✅ | ✅ | ✅ | 太重型 |

**决策**: `fflate` — 解压 ZIP→列出文件→点开预览。TAR 和 GZ 用 fflate 的 gzip/deflate 流 + 自解析 TAR header（TAR 格式极简单）。

### A3. 音视频预览

| 候选 | 大小 | 格式支持 | 结论 |
|------|------|----------|------|
| 原生 `<video>` / `<audio>` | 0 | MP4/WebM/OGG/MP3/WAV | ✅ **选用** |
| `video.js` | 16KB | 同上 + HLS/DASH | 不需要额外格式 |
| `plyr` | 10KB | 同上 | UI 更好但不必要 |

**决策**: 零依赖。浏览器原生控件覆盖 99% 场景。

---

## B. 工程加固

### B1. CI/CD

**决策**: GitHub Actions 标准流程

```yaml
# .github/workflows/ci.yml
on: [push, pull_request]
jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run lint
      - run: npm test
      - run: npm run build
```

### B2. 集成测试

**决策**: Vitest + `@testing-library/react` + `jsdom`

- Vitest 已配, 只需加 `environment: 'jsdom'` 配置
- `@testing-library/react` 测试 handler 组件渲染
- `@testing-library/user-event` 模拟用户交互

### B3. PWA 离线验证

**决策**: Chrome DevTools 手动验证, 无需额外工具。

---

## C. 体验打磨

### C1. 主题切换

| 候选 | 大小 | 依赖 | 结论 |
|------|------|------|------|
| TW v4 `dark:` variant + Zustand | 0 | 0 | ✅ **选用** |
| `next-themes` | 3KB | Next.js | Vite 不支持 |

**实现**: `@custom-variant dark` 在 CSS, Zustand store 存偏好, `document.documentElement.classList.toggle('dark')`, localStorage 持久化。

### C2. 国际化

| 候选 | 大小 | 生态 | 结论 |
|------|------|------|------|
| `react-i18next` | ~5KB gzip | 2.5M 周下载 | ✅ **选用** |
| `@nanostores/i18n` | 1KB | 小众 | 生态太弱 |
| `next-intl` | 4KB | Next.js 专用 | 非 Next 项目 |
| `react-intl` | 14KB | FormatJS 官方 | 更重, API 更繁琐 |

**决策**: `react-i18next` — hooks API (`useTranslation`), 命名空间, 支持插值/复数, 社区最大。

### C3. 快捷键

| 候选 | 大小 | 下载量 | 结论 |
|------|------|--------|------|
| `react-hotkeys-hook` | <3KB | 2.5M/周 | ✅ **选用** |
| `hotkeys-js` | 3.8KB | 非 React 原生 | 需手动绑定 |
| `mousetrap` | 1.5KB | 不维护 | 已停止更新 |

**决策**: `react-hotkeys-hook` v4 — 一行 `useHotkeys('ctrl+s', save)`, 支持组合键/序列/作用域。

---

## 汇总

| 序号 | 任务 | 依赖 | Bundle 影响 |
|------|------|------|-------------|
| A1 | PDF handler | `react-pdf` + `pdfjs-dist` | +50KB (worker CDN) |
| A2 | Archive handler | `fflate` | +30KB |
| A3 | Audio/Video handler | 无 | 0 |
| B1 | CI | 无 | 0 |
| B2 | 集成测试 | `@testing-library/react` + `jsdom` | dev only |
| B3 | PWA 验证 | 无 | 0 |
| C1 | 主题切换 | 无 | 0 |
| C2 | i18n | `react-i18next` + `i18next` | +10KB |
| C3 | 快捷键 | `react-hotkeys-hook` | +3KB |

**总计**: 新增 7 个运行时依赖, 净增 bundle <100KB。
