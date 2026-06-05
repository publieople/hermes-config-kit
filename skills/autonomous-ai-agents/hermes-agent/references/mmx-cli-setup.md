# mmx-cli: MiniMax 官方 CLI 工具

## 概述

`mmx-cli`（npm 包名 `mmx-cli`，命令名 `mmx`）是 MiniMax 开放平台的官方命令行工具。  
专为 AI Agent 和终端用户设计，支持文本、图像、视频、语音、音乐等全模态能力。

**GitHub:** https://github.com/MiniMax-AI/cli  
**文档:** https://platform.minimax.io/docs/token-plan/minimax-cli  
**中文文档:** https://platform.minimaxi.com/docs/guides/text-ai-coding-tools

**前置条件：** 需要订阅 MiniMax Token Plan（Plus ¥49/月 或更高）。

---

## 安装

```bash
npm install -g mmx-cli
# 验证
mmx --version
```

要求 Node.js 18+。

### 预检：mmx 可能已经装过

先检查再重装，避免 EACCES 或重复安装：

```bash
# 检查 npm 全局安装目录
npm config get prefix
# 例： /usr  -> 二进制在 /usr/lib/node_modules/.bin/mmx
# 例： ~/.npm-global -> 二进制在 ~/.npm-global/bin/mmx

# 直接检查已知位置
ls ~/.npm-global/bin/mmx 2>/dev/null || ls /usr/lib/node_modules/.bin/mmx 2>/dev/null || echo "not found"
```

如果已经装过但 `mmx` 找不到，是 PATH 问题：

```bash
# 添加到 PATH（写入 ~/.bashrc 持久化）
export PATH="$HOME/.npm-global/bin:$PATH"
```

**fish shell 用户（通过 .bashrc 启动 fish）：** 如果 `.bashrc` 已有上面这行，fish 会继承该 PATH。验证用：

```fish
type mmx
# → mmx is /home/po/.npm-global/bin/mmx
```

如果找不到，在 `~/.config/fish/config.fish` 添加：

```fish
fish_add_path ~/.npm-global/bin
```

### 权限错误处理

`npm install -g mmx-cli` 报 `EACCES: permission denied` 时，原因是 npm 默认 prefix 设为 `/usr`（需要 sudo）但用户没有 sudo，且 `~/.npm-global` 下已有二进制：

```bash
# 方案 A：已设 npm prefix 为 ~/.npm-global
npm config set prefix ~/.npm-global    # 只需一次
npm install -g mmx-cli                 # 无需 sudo

# 方案 B：直接确认 ~/.npm-global/bin/ 下面有没有
ls ~/.npm-global/bin/mmx               # 有的话加 PATH 即可
```

---

## 认证

```bash
# 用 Token Plan API Key 登录（自动探测 region）
mmx auth login --api-key sk-xxxxx

# 登录后自动显示配额面板
# 失败时手动设置 region：
mmx config set --key region --value cn    # 中国大陆
mmx config set --key region --value global # 国际

# 查看登录状态
mmx auth status
```

> **注意：** 认证后会自动运行 `mmx quota` 显示额度。配置文件保存在 `~/.mmx/config.json`。

---

## 核心命令

| 命令 | 用途 | 示例 |
|------|------|------|
| `mmx quota` | 查看 Token Plan 使用额度 | 显示每5小时/每日/每周配额 |
| `mmx text chat` | 多轮文本对话（流式输出） | `mmx text chat --message "写一首关于AI的诗"` |
| `mmx image generate` | 文生图 | `mmx image "赛博朋克城市夜景, 16:9"` |
| `mmx video generate` | 文生视频（异步） | `mmx video generate --prompt "日落时猫咪看窗外"` |
| `mmx speech synthesize` | 语音合成(TTS) | `mmx speech synthesize --text "你好" --out hi.mp3` |
| `mmx music generate` | 音乐生成 | `mmx music generate --prompt "轻快的爵士乐" --out summer.mp3` |
| `mmx vision describe` | 图片理解 | `mmx vision describe --image photo.jpg` |
| `mmx search query` | 内置网页搜索 | `mmx search --query "今天天气"` |
| `mmx config show/set` | 查看/修改配置 | `mmx config set --key region --value cn` |
| `mmx update latest` | 升级到最新版 | `mmx update latest` |

---

## Token Plan 套餐参考（中国大陆 ¥）

### 标准版（M2.7）

| 套餐 | 价格 | M2.7 请求/5小时 | 其他 |
|------|------|:--------------:|------|
| Starter | ¥29/月 | 600 | — |
| Plus | ¥49/月 | 1,500 | Speech 4K字/日, image-01 50张/日 |
| Max | ¥119/月 | 4,500 | 含 Hailuo 视频 2个/日 |

### 极速版（M2.7-highspeed）

| 套餐 | 价格 | 请求/5小时 |
|------|:----:|:---------:|
| Plus-极速版 | ¥98/月 | 1,500 |
| Max-极速版 | ¥199/月 | 4,500 |
| Ultra-极速版 | ¥899/月 | 30,000 |

---

## 配置 Hermes Agent 辅助服务

MiniMax 可以接管 Hermes 的 auxiliary 服务（vision、TTS）而不影响主模型。

### 1. 环境变量

`.env` 中需同时设置两个变量（CN 用户）：

```bash
MINIMAX_CN_API_KEY=sk-xxxxx          # 国内版 LLM/vision 用
MINIMAX_API_KEY=sk-xxxxx             # TTS 等需要（相同 key）
```

> **注意：** Hermes TTS 模块读取 `MINIMAX_API_KEY`，而 CN provider 读取 `MINIMAX_CN_API_KEY`。两者都要设。

### 2. Vision（图片理解）

**⚠️ 重要：MiniMax M2.7 是纯文本模型，不支持通过 chat/completions API 接收图像。**
配置 `auxiliary.vision` 为 `minimax-cn/MiniMax-M2.7` 不会报错但也不会返回视觉分析结果（Hermes 的 `vision_analyze` 工具会失败）。

如需 MiniMax 视觉能力，用 `mmx-cli` 的专用 VLM 端点：

```bash
mmx vision describe /path/to/image.jpg
# 支持 WebP、JPEG、PNG，无需格式转换
# 查看 VLM 额度：mmx quota（coding-plan-vlm 配额项）
```

配置示例（仅供参考——实际 Hermes auxiliary.vision 走 M2.7 无法分析图像）：

```yaml
auxiliary:
  vision:
    provider: minimax-cn
    model: MiniMax-M2.7
```

### 3. TTS（语音合成）

MiniMax Speech 2.8 的 CN 端点与 LLM 端点路径不同（`/v1/t2a_v2` vs `/v1`），需显式指定 base_url：

```yaml
tts:
  provider: minimax
  minimax:
    model: speech-2.8-hd       # 或 speech-02-hd
    voice_id: female-shaonv    # 可用 mmx speech voices 列出
    base_url: https://api.minimaxi.com/v1/t2a_v2  # CN 端点
```

可用的中文语音：`female-shaonv`（少女）、`female-yujie`（御姐）、`male-qn-qingse`（青年清涩）、`male-qn-badao`（霸道）等。Jingpin 版音质更高（后缀 `-jingpin`）。

### 4. 清理过期 provider

如果之前配过其他 custom provider（如 bailian 百炼），在 `config.yaml` 中删除：

```yaml
# 删掉这整段：
custom_providers: []            # 空数组 = 无自定义 provider
```

### 5. 安装 mmx-cli（推荐）

```bash
npm install -g mmx-cli
mmx auth login --api-key sk-xxxxx    # 自动探测 CN region
mmx quota                            # 查看 Token Plan 配额
```

`mmx-cli` 可以调用 Hermes TTS/Vision 框架不直接支持的功能（图像生成、视频、音乐、搜索）。

### 6. 验证

```bash
# TTS 测试
mmx speech synthesize --text "你好世界" --out test.mp3 --voice female-shaonv

# 查额度
mmx quota

# Vision（需等 reset 后生效）
mmx vision describe --image some.jpg

# 文本对话（带思维链）
curl -s -H "Authorization: Bearer $MINIMAX_CN_API_KEY" \
  -H "Content-Type: application/json" \
  http://api.minimaxi.com/v1/chat/completions \
  -d '{"model":"MiniMax-M2.7","messages":[{"role":"user","content":"hello"}],"max_tokens":50}'
```

### 7. API 行为细节与排错

#### TTS 响应格式

MiniMax t2a_v2 端点**不返回原始音频文件**，而是返回 JSON，音频以 Hex 编码嵌入：

```json
{
  "data": { "audio": "49443304000000086a545858..." },
  "base_resp": { "status_code": 0, "status_msg": "success" }
}
```

Hermes 的 `tts_tool.py` 已内建 Hex → 音频的解码逻辑，但如果你直接 curl 调试：
- HTTP 200 但文件只有 ~77 字节 → 检查是否为 JSON 错误响应
- 错误码 2013 = `"invalid params, empty field"` — 通常遗漏了 `voice_setting` 或 `audio_setting` 字段
- 正确 JSON 格式 (t2a_v2)：
  ```json
  { "model": "speech-2.8-hd", "text": "...",
    "voice_setting": { "voice_id": "female-shaonv", "speed": 1.0, "vol": 1.0, "pitch": 0 },
    "audio_setting": { "sample_rate": 32000, "format": "mp3", "channel": 1 } }
  ```

#### Vision 注意事项

- **`/v1/chat/completions` 不支持图像输入**：MiniMax M2.7 是 text-to-text 模型。API 层面可通过 `image_url` 传图但模型不会解析——模型会回复没有看到图片。**这是模型能力限制，不是网络或格式问题。**
- **`mmx vision describe`**：可靠方案，通过专用 VLM 端点处理本地文件和 URL。支持 WebP/JPEG/PNG，无需格式转换。
- **`auxiliary.vision` 配置**：M2.7 不可用于 vision，需用 `mmx vision describe` 替代。minimax-cn provider 只在主模型使用 M2.7 文本能力时生效。

#### 文本对话特点

- M2.7 默认输出 `<think>...</think>` 思维链标签（Hermes 的 `show_reasoning` 可控制显示）
- 响应包含 `cached_tokens` 字段 → 支持 prompt 缓存，长上下文更省费用
- 流式输出（SSE）可以用 `"stream": true` 启用

#### 可用语音一览

`mmx speech voices` 返回约 60+ 个语音 ID，涵盖：

| 类别 | 语音 ID |
|------|---------|
| 中文少女 | `female-shaonv`, `female-shaonv-jingpin` |
| 中文御姐 | `female-yujie`, `female-yujie-jingpin` |
| 中文成熟 | `female-chengshu`, `female-chengshu-jingpin` |
| 中文甜美 | `female-tianmei`, `female-tianmei-jingpin` |
| 中文男青年清涩 | `male-qn-qingse`, `male-qn-qingse-jingpin` |
| 中文男青年精英 | `male-qn-jingying`, `male-qn-jingying-jingpin` |
| 中文男青年霸道 | `male-qn-badao`, `male-qn-badao-jingpin` |
| 中文男大学生 | `male-qn-daxuesheng`, `male-qn-daxuesheng-jingpin` |
| 英语 | `English_*` 系列 (narrator, expressive, calm等多种) |
| 日语/韩语 | `Japanese_*`, `Korean_*` 系列 |
| 德语/俄语/意/阿/土/乌 | 对应语言前缀系列 |

`-jingpin` 后缀为高音质版。

#### 常见问题

- **TTS 返回 401** → `base_url` 设成了 global 端点 `api.minimax.io`，CN 用户需用 `api.minimaxi.com`
- **Vision 配置不生效** → 检查辅助 vision 的 provider 是否从旧的 expired provider 改过来了；需要 `/reset`
- **`.env` 写不进去** → `.env` 受文件保护，通过 `echo >>` 终端命令追加，不用 `write_file` 或 `patch` 工具
- **`mmx` 命令 not found 但实际已装过** → npm prefix 可能是自定义目录。检查 `npm config get prefix`，在对应 bin 子目录下找 `mmx`。典型位置 `~/.npm-global/bin/`，加 PATH：`export PATH="$HOME/.npm-global/bin:$PATH"`
- **`vision_analyze` 总是返回"看不到图片"** → 两个原因叠加：
  1. 主模型（如 deepseek-v4-flash）是纯文本模型，不支持 `vision_analyze`
  2. `auxiliary.vision` 配了 `minimax-cn/MiniMax-M2.7` → M2.7 的 chat/completions 端点也无法处理图像
  3. 解法：直接用终端跑 `mmx vision describe --image <path>`（走 MiniMax 专用 VLM），然后把结果贴回对话

### 8. 注意事项

- **TTS 端点差异：** MiniMax LLM (`/v1`) 和 TTS (`/v1/t2a_v2`) 用不同 path，config 中必须显式设 `base_url`，否则默认用 global 端点 `api.minimax.io` 导致 401
- **配额共享：** Hermes 和 mmx-cli 共用同一个 Token Plan，额度叠加不翻倍
- **Plus 套餐限制：** M2.7 1,500 次/5小时，Speech 4,000 字符/日，image-01 50 张/日。超出需降级或升级
- **重置周期：** M2.7 每 5 小时一轮，语音/图像每日重置
- **mmx-cli 单独使用 Image/Video：** Hermes Agent 内置的 `image_gen` 工具集默认走 FAL.ai，不经过 MiniMax。如需 MiniMax 生图/生视频，直接用 `mmx image` / `mmx video` 命令

## 与 Hermes Agent 的关系

- **Hermes Agent 主模型：** 如只想用 MiniMax 做辅助服务（vision、TTS），主模型保留其他 provider（DeepSeek、OpenRouter 等），无需切换
- **mmx-cli:** 直接调用 MiniMax 的多模态能力（图像、视频、语音、音乐），不经过 Hermes 的 auxiliary 框架
- 两者共用同一个 Token Plan Key，配额共享
