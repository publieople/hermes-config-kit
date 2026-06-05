# HyperFrames 视频渲染工作流

为每日科技简报等固定格式内容直接生成 MP4，无需录屏。一行命令出片。

## 环境配置

### 安装

```bash
cd /tmp/hf-test   # 或项目目录
npm install hyperframes --ignore-scripts  # 跳过 onnxruntime-node 下载
```

> **为什么 --ignore-scripts？** onnxruntime-node 的 postinstall 脚本会下载预编译二进制，在中国网络环境下（即使走 Clash 代理）返回 302 导致失败。Docker 模式不需要它。

### Docker 构建补丁（必做）

HyperFrames 的 Docker 构建流程中的 npm install 也会触发 onnxruntime 下载。修改模板永久修复：

```bash
sed -i 's/npm install -g hyperframes@${HYPERFRAMES_VERSION}$/npm install -g hyperframes@${HYPERFRAMES_VERSION} --ignore-scripts/' \
  node_modules/hyperframes/dist/docker/Dockerfile.render

sed -i 's/npm install -g hyperframes@${HYPERFRAMES_VERSION}$/npm install -g hyperframes@${HYPERFRAMES_VERSION} --ignore-scripts/' \
  node_modules/hyperframes/dist/cli.js
```

**注意**：`npm update hyperframes` 会覆盖 dist 文件，补丁丢失。更新后重打。

### WSL Docker 组权限

```bash
# 用户已在 docker 组但仍需：
sg docker -c "cd /project && ./node_modules/.bin/hyperframes render --docker ..."
```

## 内容调研（重要）

用户明确要求「不要瞎写」——每条新闻必须核实原始来源。

### 调研步骤

1. 搜索每条新闻的关键词 + 日期（如 `Anthropic Claude Opus 4.8 H轮 650亿美元 2026年5月`）
2. 至少访问 2-3 个独立来源交叉验证
3. 提取关键数据（金额、百分比、日期、人名、产品名）
4. 记录来源（官网/新华社/财联社/36氪等知名媒体）
5. 用 `web_extract` 处理原始页面，获取详细描述和引语
6. 优先使用一手来源（公司官网公告 > 媒体转载 > 自媒体评论）

### 内容格式

每条新闻 7-8 秒，包含：
- **标题**（加粗主信息）
- **一句话副标题**（核心亮点）
- **正文**（2-3 句，含具体数字加粗）
- **来源标注**（底部小字）

## 图片素材获取

用户明确要求真实新闻图片，不接受 SVG 示意图。

### 可行途径

| 途径 | 成功率 | 说明 |
|------|--------|------|
| 公司官网新闻稿 | ⭐⭐⭐ | 如 `anthropic.com`、`huawei.com`、`space.com` 通常有公开图片 CDN |
| 科技媒体配图 | ⭐⭐ | 36kr、IT之家可能有 CDN 但限制 curl |
| Wikimedia Commons | ⭐ | 404 比例高，备选 |
| jsdelivr CDN | ⭐ | 大部分新闻图标不可用 |

### 图片发现流程

1. **浏览器探索**：用 `browser_navigate` 打开新闻页面 → `browser_get_images` 列出所有图片 URL
2. **尝试下载**：`curl -x http://127.0.0.1:7890 -sL -o assets/name.jpg -w '%{http_code}' 'IMAGE_URL'`
3. **验证结果**：`file assets/name.jpg` — 必须输出 `JPEG image data` 或 `PNG image data`，不能是 `HTML document`（那是 404 页面）
4. **清理失败文件**：`rm -f assets/bad-file.jpg`

### 图片使用规范

- 图片放 `assets/` 目录，HTML 中用相对路径 `src="assets/name.jpg"`
- 每张图片套一层 `.img-overlay` 渐变遮罩，保证文字可读
- 图片尺寸建议：主图 ≥ 800×500，小图 ≥ 300×200

## HTML 合成要点

### 场景结构

```
.scene (composition container)
  ├── .grid-bg (背景网格)
  ├── .top-bar (顶部光条)
  ├── [scene 0: title] data-track-index="0"
  │     └── .title-wrap (图标 + 主标题 + 副标题 + 日期)
  ├── [scene 1-N: news] data-track-index="1..N"
  │     ├── .img-card (图片 + overlay)
  │     └── .info-panel (标签 + 标题 + 正文 + 来源)
  └── [scene N+1: end] data-track-index="N+1"
```

### 关键属性

- `data-composition-id` — 顶层 div 唯一 ID
- `data-track-index` — 每个场景唯一递增
- `class="clip"` — **必须**，控制可见性。少了场景会全程露脸。
- `data-start` + `data-duration` — 定义场景时间范围
- 所有 GSAP timeline 注册到 `window.__timelines["composition-id"]`

### 时间参考（5 条新闻）

- Title: 4.5s
- Per news: 7-8s
- End: 3s
- Total: ~45s
- timeline.set 对齐总时长：`tl.set({}, {}, totalSeconds)`

### GSAP 动画

每个场景使用 `tl.from` 对子元素做错峰 fade-in（每次间隔 0.1-0.15s）：
```js
tl.from(".img-card", { opacity: 0, x: -20, duration: 0.45, ease: "power3.out" }, t);
tl.from(".cat-tag", { opacity: 0, y: -8, duration: 0.25, ease: "power2.out" }, t + 0.1);
tl.from(".hline", { opacity: 0, x: 15, duration: 0.35, ease: "power3.out" }, t + 0.2);
// ...
```

## Docker 渲染

### 首次运行（构建镜像，~2 分钟）

```bash
sg docker -c "cd /project && ./node_modules/.bin/hyperframes render --docker --output renders/output.mp4"
```

首次会下载 ~420MB apt 包 + Chrome + npm 依赖。后续缓存命中。

### 后续运行（~1 分钟）

同命令，Docker 层全部 CACHED。

### 检查内容

渲染完成后用 snapshot 检查画面：

```bash
mkdir -p snapshots
./node_modules/.bin/hyperframes snapshot . --at 0.5,5.5,12.5,20.5 --describe false
```

## 样式规范

- 背景：深蓝黑 `radial-gradient(ellipse at 50% 0%, #0f1729 0%, #060a17 100%)`
- 网格：`rgba(99,102,241,0.03)` 60px 间距
- 顶部光条：`linear-gradient(90deg, #6366f1, #a78bfa, #34d399)` 3px 高
- 图片卡片：圆角 14px + 底部渐变 overlay
- 内容面板：左 620px 起始，宽度 1220px
- 分类标签颜色：
  - AI → `#818cf8` 蓝
  - 航天 → `#f87171` 红
  - 芯片 → `#fbbf24` 黄
  - 云服务 → `#c084fc` 紫
  - 硬件 → `#34d399` 绿
- 字体：`font-family: 'Inter', Arial, sans-serif`（Docker Chrome 有 Inter）
- 进度点：底部右侧点状导航，当前场景放大为条形 (`width: 28px; border-radius: 4px`)

## 已知限制

- **Docker Chrome 无中文/日文字体**：font-family 中的 `PingFang SC`、`Noto Sans SC` 会 fallback。中文显示正常但非最佳。
- **内联图片**：`<img src="assets/name.jpg">` 而非 CSS background-image。HyperFrames 在 Docker 中将这些文件复制到容器内工作目录。
- **GSAP 样式冲突**：不要同时使用 CSS `transform: translate(-50%, ...%)` 和 GSAP `y` 动画——GSAP 会覆盖完整的 CSS transform，导致居中失效。改用 GSAP 的 `xPercent: -50` 和 `yPercent: -50`。
- **无网络音频/视频**：Docker 中无网络。所有资源必须在构建时拷贝进去。
- **onnxruntime-node**：`--ignore-scripts` 跳过后，node_modules 中的 onnxruntime 是空的。Docker 模式不依赖它。
