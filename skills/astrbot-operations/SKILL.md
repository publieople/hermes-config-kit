---
name: astrbot-operations
description: AstrBot 运营维护 — 进程管理、插件热重载、人格系统、知识库集成、常见故障排查
---

# AstrBot 运维指南

## 进程管理

**AstrBot 通过 systemd 管理（非用户手动启动）**：
```bash
sudo systemctl status astrbot      # 查看状态
sudo systemctl restart astrbot     # 重启
sudo systemctl stop astrbot        # 停止
```

日志输出到 systemd journal，非日志文件：
```bash
sudo journalctl -u astrbot --no-pager -n 100
sudo journalctl -u astrbot --no-pager --since "1:06"
```

WebUI: `http://localhost:6185`，用户名 `Publieople`，密码 `Fzj103415422`。

## 版本升级

AstrBot 通过 `uv` 部署，**不支持在 WebUI 里直接升级**。WebUI 升级只更新前端 dist 文件，Core 版本不变会导致版本错配。

```bash
# 通过代理升级时需加大超时（默认 30s 不够），大包走清华镜像
env UV_HTTP_TIMEOUT=300 UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple uv tool upgrade astrbot --python 3.12
```

升级后如果 WebUI 和 Core 版本不一致：删除 `data/dist` 目录后重启。
```bash
sudo systemctl stop astrbot
rm -rf /home/po/astrbot/data/dist
sudo systemctl start astrbot
```

**注意**：升级后首次启动可能弹出 `Install dashboard? [Y/n]:` 交互式提示。先手动跑一次 `echo "y" | astrbot run` 让 dashboard 装完，然后再用 systemd 启动。

## 插件管理

**AstrBot 支持热重载，新插件放到 `data/plugins/` 后无需重启。** 不要 kill 进程。

插件目录: `/home/po/astrbot/data/plugins/`

### 通过 CLI 安装（推荐）

```bash
cd /home/po/astrbot
# 搜索插件
astrbot plug search bangumi
# 用 marketplace 名称安装（注意：可能与 GitHub repo 名不同）
astrbot plug install astrbot-plugin-bangumi-enhance
# 从 GitHub URL 安装
astrbot plug install https://github.com/united-pooh/astrbot_plugin_bangumi
```

**注意**：命令是 `astrbot plug`（不是 `plugin`）。marketplace 上的插件名用连字符（`astrbot-plugin-bangumi-enhance`），可能不同于 GitHub repo 名（`astrbot_plugin_bangumi`）。

### 手动 git clone

```bash
cd /home/po/astrbot/data/plugins
git clone <repo-url>  # 需要代理: export https_proxy=http://127.0.0.1:7890
```

### 插件加载失败

如果插件加载失败，通过 API 重载:
```
POST /api/plugin/reload-failed  {"dir_name": "astrbot_plugin_xxx"}
```

## 人格系统（Persona）

**生效链路**：
1. 用户在 WebUI 保存人格 → 存入 AstrBot DB
2. 群消息到达 → `self_learning` 插件 `get_persona_id()` 选择人格
3. `MemoryProcessor` 加载人格提示词 → 注入 LLM system prompt
4. LLM 按人格生成回复

**关键坑**：`self_learning` 插件有自己的人格选择逻辑，可能会覆盖 WebUI 中手动切换的人格。日志中看到 `最终使用人格: XXX` 才是实际生效的人格。如果切换了人格但群里没变，检查 `self_learning` 覆盖。

通过 API 查看人格列表：
```
GET /api/persona/list  (Authorization: Bearer <token>)
```

## 知识库集成

配置在 `/home/po/astrbot/data/cmd_config.json`:
- `kb_names: ["盒武器"]` — 使用的知识库列表
- `kb_agentic_mode: true` — 让 LLM 可主动调用 KB 工具（推荐）
- `kb_fusion_top_k: 20` / `kb_final_top_k: 5` — 检索参数

**盒武器知识库**: `kb_id=c0ca81b9-f1f0-4479-9ce8-f6c3017958cf`，Embedding: SiliconFlow `BAAI/bge-m3`。

注意：`embedding_dimensions` 对 `bge-m3` 应设为 `0`（硅基流动不支持该参数）。

## 添加 OpenAI 兼容模型提供商

AstrBot 支持通过 OpenAI 兼容 API 接入自定义模型（如 OpenCode Zen 免费模型）。

### 配置方式

在 WebUI `设置 → 大语言模型 → 添加模型源`，或直接编辑 `data/config/abconf_*.json`：

#### provider_sources 添加源

```json
{
  "provider": "opencode",
  "type": "openai_chat_completion",
  "api_base": "https://opencode.ai/zen/v1",
  "key": [""],       // ⚠️ OPENCODE 免费模型特例：见下方 Auth 坑章节，正确配置是 key: []（空数组）
  "id": "opencode",
  "enable": true
}
```

#### provider 添加模型（可选，预览模型时自动创建）

```json
{
  "id": "opencode/deepseek-v4-flash-free",
  "enable": true,
  "provider_source_id": "opencode",
  "model": "deepseek-v4-flash-free",
  "modalities": ["text"],
  "custom_extra_body": {},
  "max_context_tokens": 20000,  // 免费模型通常20k
  "reasoning": false
}
```

### OpenCode Zen 免费模型

| 模型名 | 上下文 | 说明 |
|--------|--------|------|
| `deepseek-v4-flash-free` | ~20K | 通用编程 |
| `big-pickle` | ~20K | OpenCode 官方免费 |
| `minimax-m2.5-free` | ~32K | 科大讯飞 |
| `mimo-v2.5-free` | ~20K | 小米开源 |
| `nemotron-3-ultra-free` | ~20K | NVIDIA |
| `north-mini-code-free` | ~20K | 知乎开源 |

### Auth 关键行为

**OpenCode Zen 免费模型 `POST /v1/chat/completions` 的行为：**
- **不传 `Authorization` header → 200 OK**（返回 `cost":"0"`）
- 传了任何非空 `Authorization` header → 401 `Invalid API key.` 或 403 `error code: 1010`
- 免费的 `/v1/models` 列表不需要 auth（可以用来确认模型存在）

**AstrBot 的 `openai_source.py`（第 360 行，v4.26.2）：**
```python
self.chosen_api_key = self.api_keys[0] if len(self.api_keys) > 0 else None
```
- `key: []` → `chosen_api_key = None` → SDK 不发 `Authorization` header → ✅
- `key: ["***"]` → `chosen_api_key = "***"` → SDK 发 `Bearer ***` → ❌ 401
- `key: [""]` → `chosen_api_key = ""` → 新版 OpenAI SDK 不接受空字符串，抛错

**新版 OpenAI SDK 不允许 `api_key=None` 或 `api_key=""`**，会直接报 `Missing credentials` 错误。需要在 `~/.config/astrbot/` 或系统层面设 `OPENAI_API_KEY` 环境变量为任意值绕过去。详见 [references/opencode-auth-debug.md](references/opencode-auth-debug.md)。

### 注意事项

- **`api_base` 必须 `/v1` 结尾**：`https://opencode.ai/zen/v1`（不是 `zen`）
- **免费模型上下文窗口小**（20K-32K），日常对话够用但长文本会截断
- **无速率保证**：免费 tier 有隐式限速，超限等待即可
- **可用模型列表**：`curl https://opencode.ai/zen/v1/models`
- **不传敏感代码**：免费 tier 数据可能用于改进服务

## 常见故障

### WSL PYTHONPATH 污染

Hermes Agent 设置 `PYTHONPATH=/home/po/.hermes/hermes-agent` 全局环境变量，
WSL 中每个 Python 进程都继承此路径。症状：
- `pip install` 产生 `hermes-agent requires xxx` 版本冲突警告
- `uv pip install --python` 安装到错误位置
- Python 进程加载 hermes-agent 依赖导致版本冲突

**修复**：启动任何 Python 命令前 `unset PYTHONPATH`。
在 systemd service 或启动脚本中也应主动 unset。

详见 references: [配置文件陷阱](references/config-file-hazards.md) | [人格系统详解](references/persona-flow.md) | [音乐插件坑](references/music-plugin.md) | [Bangumi 番剧订阅](references/bangumi-plugin.md) | [IndexTTS/CosyVoice2 部署](references/indextts-setup.md) | [CosyVoice2 部署](references/cosyvoice2-setup.md) | [TTS 模型选型](references/tts-model-selection.md) | [GPT-SoVITS Docker 部署](references/gpt-sovits-setup.md)

**1. LLM API 挂死导致 bot 不回复**
症状：进程在跑但日志不再更新，10+ 分钟无新消息。
原因：LLM API 连接进入 CLOSE-WAIT 阻塞消息处理管线。
修复：`sudo systemctl restart astrbot`

**2. 插件热加载后不生效**
症状：插件目录有文件但未出现在已安装列表。
修复：调用 `POST /api/plugin/reload-failed {"dir_name":"xxx"}`

**3. systemd 下插件文件修改不生效**
症状：手动改了 plugins 目录下的 .py 文件，WebUI 也点了热重载但行为不变。
原因：systemd 管理的 AstrBot 进程跑的是内存中的代码。热重载通知运行中的进程重新加载模块，但 `@filter.command` generator 可能不会重新绑定。
修复：`sudo systemctl restart astrbot`。验证：看日志是否有对应代码路径的新日志行。

**3. 人格切换不生效**
症状：WebUI 切了人格但群内语气未变。
原因：`self_learning` 动态覆盖了选择。查看日志确认实际人格。

**4. openpyxl 兼容性**
Python 3.12+/3.14 上 `Fill()` 报错。用 zipfile + xml.etree 直接解析 xlsx。

**5. TTS 语音合成（本地 GPU 模式）**
详见 references/indextts-setup.md 和 references/cosyvoice2-setup.md。

**部署原则**：
- TTS 模型以**独立 FastAPI 服务**运行，AstrBot 插件只做 HTTP 客户端
- 模型依赖复杂时，优先用 Docker 或 conda，不要死磕 uv/pip 环境
- 遇到依赖卡住时，**先评估替代方案的总成本**（换模型、换部署方式），不要在一棵树上反复试

**6. 升级后 dashboard 交互提示**

v4.25→v4.26 升级后，首次 `astrbot run` 可能弹出 `Install dashboard? [Y/n]:` 交互式提示。
systemd 环境下无法交互，导致反复崩溃（`auto-restart` 死循环）。

修复：先手动跑一次 `echo "y" | astrbot run` 让 dashboard 装完，然后 `sudo systemctl restart astrbot`。

## TTS 语音合成提供商配置

AstrBot WebUI 内置多个 TTS 提供商。选型前**先查文档/源代码**，不凭记忆猜 API。

### 内置提供商速查

| 提供商 | 本地/API | 日语 | 声音克隆 | 费用 | 适用场景 |
|--------|---------|------|---------|------|---------|
| **GSV TTS(本地)** | 本地 | ✅ | ✅ | 免费 | 7z整合包一键部署，GPU~4GB |
| **FishAudio TTS(API)** | 云端 | ✅ | ✅ | 免费额度 | 零部署，注册就有额度 |
| **Edge TTS** | 免费 | ✅ | ❌ | 免费 | 不需要克隆时首选 |
| **阿里云百炼 TTS(API)** | 云端 | ✅ | ✅ | 免费额度 | CosyVoice/Qwen3-TTS |
| **MiniMax TTS(API)** | 云端 | ✅ | ✅ | 付费 | 商业级 |
| **火山引擎 TTS(API)** | 云端 | ✅ | ✅ | 付费 | 字节跳动模型 |
| **Azure TTS** | 云端 | ✅ | ❌ | 付费 | 微软标准 |
| **ElevenLabs TTS(API)** | 云端 | ✅ | ✅ | 💰贵 | 效果最好但最贵 |

### GSV TTS(本地) — GPT-SoVITS 部署

AstrBot 的 GSV TTS(本地) 连接到 GPT-SoVITS 标准 API（`GET /tts` 端点），默认 `http://127.0.0.1:9880`。

**部署前必须查官方文档**（README + api.py 参数），不凭记忆猜命令。

**Docker 部署（推荐）：** 镜像内置模型，免模型下载和依赖安装。详见 [GPT-SoVITS Docker 部署](references/gpt-sovits-setup.md)。

关键坑：
- 镜像预装模型在 `/workspace/models/pretrained_models/`，但 config 指向的 `GPT_SoVITS/pretrained_models/` 是空目录——需删目录后 `ln -s` 建立软链
- `ref_audio_path` 是容器内路径，用 `-v` 挂载宿主机目录到容器
- Docker compose 有多个 service 定义（含 Lite 版多了 ASR/UVR5 目录挂载），`docker compose up` 会校验全部 service 的 volume 是否存在——用 `docker run` 绕过

**AstrBot 源码路径**（排查参数时查阅）：
```
/home/po/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/astrbot/core/provider/sources/gsv_selfhosted_source.py
```

关键配置字段：`api_base`（默认 `http://127.0.0.1:9880`）、`gpt_weights_path`、`sovits_weights_path`、`gsv_default_parms`（传给 `/tts` 的额外参数，键名自动去掉 `gsv_` 前缀）。

### GSV TTS 配置参数详解

AstrBot 的 GSV TTS(本地) 提供商源码路径：
```
/home/po/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/astrbot/core/provider/sources/gsv_selfhosted_source.py
```

**API 端点：** `GET /tts`（标准 GPT-SoVITS API）。

**已知坑：**

1. **`.lower()` 问题**：GSV 提供商会把 `default_params` 的所有值 `str(value).lower()`，所以 `ref_audio_path` 中的路径会被转小写。容器内的路径必须兼容小写，或建立小写软链。
   - 例如：Docker 内实际路径 `/workspace/GPT-SoVITS/reference_audio/xxx.wav`
   - 被 `.lower()` 变成 `/workspace/gpt-sovits/reference_audio/xxx.wav`
   - 解决：容器内 `ln -s /workspace/GPT-SoVITS /workspace/gpt-sovits`

2. **参考音频时长**：GPT-SoVITS API 要求参考音频 3~10 秒。超出会返回 `"Reference audio is outside the 3-10 second range"`。

3. **参考音频文本**：`prompt_text` 越准确，声音克隆效果越好。不确定内容时用 whisper 转写：
   ```bash
   python3 -c "
   import whisper
   m = whisper.load_model('small')
   r = m.transcribe('path/to/audio.wav', language='ja')
   print(r['text'].strip())
   "
   ```

4. **跨语言合成**：日语参考音频 + `text_lang=zh` 可输出中文，反之亦然。GPT-SoVITS 支持跨语言零样本克隆。

**GSV 默认参数（在 WebUI 中填写）：**

```json
{
  "ref_audio_path": "/workspace/gpt-sovits/reference_audio/千早爱音.wav",
  "prompt_text": "あのー、もう始まってる？んっ、じゃあ改めてこんにちは、アノンです",
  "prompt_lang": "ja",
  "text_lang": "zh",
  "text_split_method": "cut0",
  "media_type": "wav"
}
```

**注意：** 参数字段在 WebUI 中显示为带 `gsv_` 前缀（如 `gsv_ref_audio_path`），但源码中会自动去掉前缀。填不带前缀的键名。

### GSV TTS 上下文配置项说明

| WebUI 显示字段 | 实际 key | 说明 |
|--------------|---------|------|
| 参考音频文件路径 | `ref_audio_path` | 容器内绝对路径（会被 `.lower()`） |
| 参考音频文本 | `prompt_text` | 参考音频的台词内容 |
| 参考音频文本语言 | `prompt_lang` | `zh` / `ja` / `en` |
| 文本语言 | `text_lang` | 要合成的输出语言 |
| 切分文本的方法 | `text_split_method` | `cut0` 不切（短句用）|
| 输出媒体的类型 | `media_type` | `wav` / `ogg` / `aac` |
| 语音播放速度 | `speed_factor` | 1.0 = 原速 |
| 生成语音的多样性 | `top_k` | 默认 15 |
| 核采样的阈值 | `top_p` | 默认 1 |
| 生成语音的随机性 | `temperature` | 默认 1 |

### 部署前查文档铁律

**用户对此要求严格：任何不熟悉的工具/框架/部署流程，必须先查阅官方文档再给用户命令。**

这是用户在对话中多次纠正的行为（"你查一下文档再说"、"你看完完整文档再说"）。正确的流程：

1. 用户问「怎么配置X」→ 先找 X 的官方文档/README → 理解后再给出步骤
2. **不要凭记忆或猜测**写配置文件路径、API 参数、命令行参数
3. 不确定的直接查文档或 man page，不要"我觉得应该是这样"
4. 如果文档不完整，先读源码确认

### 本地 TTS 部署原则

- 模型以独立 FastAPI 服务运行，AstrBot 插件只做 HTTP 客户端
- 依赖复杂时优先 Docker 或 conda，不在 venv/pip 上死磕
- 遇依赖卡住先评估替代方案——换模型/换部署方式比修依赖更快
- 网络慢时用镜像（`pypi.tuna.tsinghua.edu.cn`）+ 设 `UV_HTTP_TIMEOUT=300`
- WSL 的 PYTHONPATH 污染全局，启动任何 Python 前 `unset PYTHONPATH`

## 插件页面（Plugin Pages）开发

AstrBot 支持在 WebUI 中内嵌自定义页面。HTML 文件放入 `pages/<page_name>/index.html`，WebUI 自动扫描。

**开发铁律：先读官方文档 https://docs.astrbot.app/dev/star/guides/plugin-pages.html，不猜 API。**

### API 存在的坑

以下 API 在 v4.x 中**不存在**，不要用：
- `filter.on_message()` — 用 `@filter.event_message_type(EventMessageType.ALL)` 代替
- `filter.on_llm_response()` — 不存在
- `EventMessageType` 的导入路径：`from astrbot.api.event.filter import EventMessageType`，不是 `astrbot.api.event`
- 语音消息没有独立事件类型，通过检查 `message_obj.message` 中的 `Record` component 识别
- 新增 `pages/` 目录后必须**重启 AstrBot**（热重载扫描不到新目录）
- 插件页面在 iframe 中运行，不支持文件上传

### 注册 Web API 的正确格式

`register_web_api` 的 route 参数格式是 `f"/{PLUGIN_NAME}/endpoint"`，**不是** `/plugin-page/{PLUGIN_NAME}/xxx`。

```python
from astrbot.api.web import json_response, error_response, request
PLUGIN_NAME = "astrbot_plugin_xxx"
context.register_web_api(f"/{PLUGIN_NAME}/voices", handler, ["GET"], "List")
# request.query.get("limit", 20, type=int)  — query 参数
# await request.json(default={})             — POST body
# json_response({"data": ...}) / error_response("message")
```

前端（`pages/xxx/index.html`）用 bridge SDK：
```javascript
const bridge = window.AstrBotPluginPage;  // 自动注入，no import needed
const data = await bridge.apiGet("endpoint", { limit: 20 });
const result = await bridge.apiPost("endpoint", { key: "val" });
```

**注意**：Bridge 侧的 endpoint **不带插件名前缀**——bridge 自动加。后端注册了 `/{PLUGIN_NAME}/voices`，前端调 `bridge.apiGet("voices")`。
