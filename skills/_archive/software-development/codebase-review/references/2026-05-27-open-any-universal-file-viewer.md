# OpenAny — 通用文件瑞士军刀调研记录

> 调研日期: 2026-05-27
> 方法: 多线程并行调研 (delegate_task)，覆盖 30+ 开源项目

---

## 文本/代码编辑器

| 项目 | Stars | 体积 | 协议 | 活跃度 | 结论 |
|------|-------|:----:|:----:|:------:|------|
| **CodeMirror 6** | ~7.8k | ~300KB | MIT | ✅ 活跃 (7.8M npm/周) | 🥇 首选 |
| Monaco Editor (VS Code) | 46.1k ⭐ | ~5MB | MIT | ❌ 更新放缓 | 太重，不支持移动端 |
| Ace Editor | ~27k | ~275KB | BSD | ⚠️ 单人维护 | 备选 |
| CodeJar | ~2.2k | ~2.5KB | MIT | ❌ 有 bug | 太小，缺功能 |

**结论:** CodeMirror 6 — Replit/Chrome DevTools/Sourcegraph 都在用。模块化、树摇友好、移动端优秀。

## Markdown 编辑器

| 项目 | 体积 | 协议 | 说明 |
|------|:----:|:----:|------|
| **MDXEditor** | ~150KB | MIT | React 原生 WYSIWYG，输出 MD 文本 |
| @uiw/react-md-editor | ~80KB | MIT | 分屏模式，轻量，适合开发者 |
| Milkdown | ~120KB | MIT | 基于 ProseMirror，插件化 |

**结论:** MDXEditor 功能/体验最佳。

## 图片查看/编辑

| 项目 | Stars | 体积 | 协议 | 说明 |
|------|:-----:|:----:|:----:|------|
| **TUI.ImageEditor** | ~6k | ~200KB | MIT | NHN 出品，内置 UI，React 封装 |
| Cropper.js | ~9k | ~29KB | MIT | 纯裁剪，极轻量 |
| Filerobot | ~2k | ~150KB | MIT | 功能多但 2 年未更新 |
| OpenSeadragon | ~3k | ~40KB | BSD | 超大图片（GB 级） |

**结论:** TUI.ImageEditor 一站式最好，Cropper.js 做裁剪补充。

## PDF 查看

| 项目 | Stars | 协议 | 说明 |
|------|:-----:|:----:|------|
| **PDF.js (Mozilla)** | 53k ⭐ | Apache 2.0 | 唯一选择，15 年历史 |
| react-pdf (封装) | 11k ⭐ | MIT | PDF.js 的 React 封装 |

## DOCX 文档查看

| 项目 | Stars | 协议 | 类型 | 说明 |
|------|:-----:|:----:|------|------|
| docx-preview (docxjs) | ~2k | Apache 2.0 | 渲染器 | DOCX→HTML，纯前端 |
| Mammoth.js | ~6k | BSD-2 | 转换器 | DOCX→MD/HTML，13 年成熟 |
| SheetJS (xlsx) | 36k ⭐ | Apache 2.0 | 表格 | XLSX 读写标准 |

## 表格/数据查看

| 项目 | 体积 | 协议 | 说明 |
|------|:----:|:----:|------|
| **TanStack Table v8** | ~30KB | MIT | Headless，灵活可定制，React 原生 |
| **AG Grid 社区版** | ~800KB | MIT | 功能最全开箱即用 |
| RevoGrid | ~50KB | MIT | 极端性能（百万单元格） |
| Handsontable | — | ⚠️ 非商业 | 2019 年改许可证，慎用 |
| react-json-view | — | MIT | 已归档，选 react-json-view-lite |
| vanilla-jsoneditor | ~100KB | Apache 2.0 | josdejong 出品，树形+代码编辑 |

## 音视频播放

| 项目 | 体积 | 协议 | 说明 |
|------|:----:|:----:|------|
| **Plyr + hls.js** | ~170KB | MIT | 最漂亮的播放器 UI |
| Video.js | ~183KB | Apache 2.0 | 生态最丰富，v10 预计体积-81% |
| Howler.js | ~10KB | MIT | 纯音频场景，零依赖 |
| WaveSurfer.js | ~80KB | MIT | 音频波形可视化 |

## 图示/白板

| 项目 | Stars | 体积 | 协议 | 说明 |
|------|:-----:|:----:|:----:|------|
| **Excalidraw** | 90k ⭐ | ~756KB | MIT | 手绘白板，原生 React 组件 |
| **React Flow** | 36.8k ⭐ | ~53KB | MIT | 节点流程图编辑器 |
| **Mermaid.js** | 75k ⭐ | ~150KB | MIT | 图表即代码 |
| Draw.io | — | — | Apache 2.0 | 无 npm 包，用 iframe，不推荐 |

## 3D 模型查看

| 项目 | 体积 | 协议 | 格式支持 | 说明 |
|------|:----:|:----:|:--------:|------|
| **@google/model-viewer** | ~68KB | Apache 2.0 | glTF/GLB | 一行 HTML 用 |
| Online3DViewer | ~200KB | MIT | 17种 (OBJ/STL/PLY/FBX…) | 格式最广 |

## 通用原则

### 许可证绿色清单
- MIT ✅
- Apache 2.0 ✅
- BSD-2/3 ✅
- AGPL ❌ (商业不可用)
- 注意检查许可证变更历史

### 评估维度
1. GitHub Stars (社区大小)
2. npm 周下载量 (使用量)
3. 许可证 (法律风险)
4. 打包体积 gzipped (性能)
5. 最后发布日期 (维护状态)
6. 框架集成 (React/Vue 封装)
7. 格式支持广度

### 格式检测优先级
```
扩展名 → MIME 类型 → Magic Bytes (前 4KB) → Hex 兜底
```
