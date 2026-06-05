---
name: minimax-vision
description: 用户发送图片或要求看图时，使用 MiniMax mmx CLI 的 VLM 端点替代 vision_analyze 工具
---

# MiniMax Vision

## 触发条件

**只要满足以下任一条件就必须加载此 skill：**

- 用户发送了图片（飞书/Telegram/Discord 等平台发来的图片消息）
- 用户说"看这张图"、"看看这个"、"这是什么"、"帮我分析这个图片"等涉及图片的请求
- 用户引用了图片文件路径并要求分析
- 任何需要理解图像内容的场景

**⚠️ 优先级（强制规则）：** 只要涉及图片，**第一步就是加载本 skill 并执行 `mmx vision describe`**。禁止先尝试 `vision_analyze`、OCR、或其他图像转文本工具作为"前置探索"——那些都是弯路，浪费时间。

## 前提

- `mmx` CLI 安装在 `~/.npm-global/bin/mmx`
- 需要 export PATH：`export PATH="$HOME/.npm-global/bin:$PATH"`
- MiniMax Token Plan API Key 已通过 `mmx auth login` 认证

## 工作流

### 1. 定位图片

图片可能在以下位置（按优先级）：

**a) 用户消息中明确给出了文件路径** → 直接使用

**b) 用户在飞书/Telegram等平台发送了图片**
→ 检查缓存目录下的最近图片文件：
```bash
ls -t ~/.hermes/image_cache/ 2>/dev/null | head -5
```
取最新的图片文件（.jpg, .png, .webp）

**c) 用户粘贴了截图**
→ 同上，检查 image_cache 目录

### 2. 分析图片

```bash
export PATH="$HOME/.npm-global/bin:$PATH"
mmx vision describe --image <图片路径>
```

### 3. 返回结果

将 `mmx vision describe` 的 JSON 输出中的 `content` 字段内容呈现给用户。
如果 `base_resp.status_code != 0`，则输出错误信息。

## 常见路径

| 场景 | 路径模式 |
|------|---------|
| 飞书发图 | `~/.hermes/image_cache/img_*.jpg` |
| 缓存截图 | `~/.hermes/image_cache/*.png` |
| 浏览器截图 | `~/.hermes/cache/screenshots/browser_screenshot_*.png` |

## 示例

用户发了一张图片问"这是什么"：

```
# 1. 找图片
$ ls -t ~/.hermes/image_cache/ | head -1
img_abc123.jpg

# 2. 分析
$ export PATH="$HOME/.npm-global/bin:$PATH"
$ mmx vision describe --image ~/.hermes/image_cache/img_abc123.jpg

# 3. 将 content 字段返回给用户
```

## 注意事项

- **不要使用 `vision_analyze` 工具** — MiniMax 的 chat/completions API 不支持图像输入
- **不要用 auxiliary.vision 配置** — 当前模型是纯文本模型，配了也没用
- **PATH 问题** — mmx 在 `~/.npm-global/bin/` 下，必须手动 export PATH
- 如果 image_cache 下没有图片，尝试用 `find ~/.hermes/image_cache/ -name "*.jpg" -o -name "*.png" -o -name "*.webp" 2>/dev/null | head -5` 搜索

## 踩坑记录

- **不要在 MiniMax 之前尝试 vision_analyze -> OCR 链** — 当前主力模型无原生视觉，`vision_analyze` 靠辅助模型（通常也失败），OCR 会产生乱码且浪费时间装 tesseract。用户发图后的正确路径只有一条：加载本 skill -> `mmx vision describe`。
- **看了图没加载 skill** — 触发条件已在上面写明，但容易在执行中被忽略。用户发图后第一件事必须是加载本 skill，没有例外。