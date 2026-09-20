# Markdown 转图片插件（astrbot_plugin_nobrowser_markdown_to_pic）

基于 pillowmd 实现，支持指令 `md2img` 和 LLM 响应自动转换。

## 正则检测问题（v1.2.0 / v1.4.0）

代码默认正则在 `main.py` L26-28，实际生效的是这一套（不是 `_conf_schema.json` 里的）。共 3 个问题：

### 🔴 表格正则 `\|[^\n]*\|` 过于宽泛

没有 `^`/`$` 锚定，会匹配**任何含管道符的行**——即使不是 Markdown 表格。"今天天气不错 | 适合出去玩"也会被误判为 md 内容触发转图。

### 🟡 `***` 分割线要求至少 4 个星号

`^\s*\*\*\*+\s*$` = `*`×3 + `+`（至少再一个）= 至少 4 个 `*`。标准 Markdown 水平线 `***`（3 个星号）会被漏掉。

### 🟡 代码默认值与 `_conf_schema.json` 不一致

`_conf_schema.json` 里的默认正则和代码里的**完全不同**——JSON 版要求代码块必须有 `\n` 包裹、各模式加了 `$` 锚定和分组括号。用户在 WebUI 点"重置为默认"后行为和代码默认不一致。

## 自定义样式

pillowmd 的 `LoadMarkdownStyles` 同时支持 `.json` 和 `.yml` 格式（优先 json，找不到则用 yml）。

每个样式目录结构：
```
<样式名>/
├── setting.json (或 .yml)
├── elements.json (或 .yml)
├── imgs/           # 图片资源
└── cover.png       # 可选：预览图
```

### 已安装的样式

来源：<https://github.com/Monody-S/CustomMarkdownImage/tree/main/styles>

存放到：`~/astrbot/data/styles/`

| 样式 | 格式 | 大小 |
|------|------|------|
| 独角兽gif | json | 556K |
| 经典 | yml | 28K |
| 朴素米黄 | yml | 60K |
| 夏日冲浪 | json + fonts | 20M |

### WebUI 配置

在插件设置中把 `style_path` 填为样式绝对路径，例如：

```
/home/po/astrbot/data/styles/经典
```

切样式改这个路径即可，不需要重启插件。

### 安装新样式

```bash
# 克隆仓库稀疏检出 styles 目录
git clone --depth 1 --filter=blob:none --sparse <repo-url> /tmp/styles-tmp
cd /tmp/styles-tmp
git sparse-checkout set styles
git checkout

# 复制到 AstrBot 数据目录
mkdir -p ~/astrbot/data/styles
cp -r styles/<样式名> ~/astrbot/data/styles/
```

pillowmd v0.7.3 安装路径：
```
/home/po/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/pillowmd/
```

## Emoji 渲染

默认字体（smSans/yahei/unifont）**不含 emoji 字形**，emoji 会显示为方框占位符。

### 原理

pillowmd 的 `MixFont` 类支持 `secondFonts` 备用字体列表：主字体找不到某字符时，自动遍历备用字体查找字形。

### 解决方案

1. **复制支持 emoji 的字体**到 pillowmd 字体目录：

```bash
# Windows 的 Segoe UI Emoji（WSL 下从 /mnt/c/Windows/Fonts/seguiemj.ttf 获取）
FONT_DIR=/home/po/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/pillowmd/data/fonts
cp /mnt/c/Windows/Fonts/seguiemj.ttf "$FONT_DIR/"
```

FreeType ≥ 2.10 支持 CBDT/CBLC 彩色 emoji 格式。

2. **在样式 setting 中添加 `secondFonts`**（emoji 字体放最前面优先匹配）：

```yml
# YML 样式
secondFonts: ["seguiemj.ttf", "yahei.ttf", "unifont.ttf"]
```

```json
// JSON 样式
"secondFonts": ["seguiemj.ttf"]
```

如果样式没有 `secondFonts` 字段，直接在 `setting` 末尾新增即可。

### ⚠️ 限制

- **必须配置 `style_path`** 指向自定义样式才能用 emoji。不填走默认渲染 `MdToImage()`，默认字体不含 emoji 字形。
- 彩色 emoji 取决于 FreeType 版本和字体格式。Segoe UI Emoji 在 FreeType 2.14 下测试通过。
- PIL/Pillow 不支持所有彩色 emoji 格式（如 COLRv1），部分 emoji 可能显示为黑白轮廓。
