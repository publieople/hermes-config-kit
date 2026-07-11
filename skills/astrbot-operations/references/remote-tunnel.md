# 远程服务隧道 — ComfyUI 实战

源会话：2026-07-07，AstrBot + SSH 隧道 + ComfyUI 配置

## 场景

AstrBot 在 WSL 中运行，ComfyUI 在无公网 IP 的实验室服务器上，通过 FRP 暴露 SSH 端口到公网。

## SSH 隧道 systemd service

写入 `/etc/systemd/system/comfyui-tunnel.service`：

```ini
[Unit]
Description=SSH Tunnel to ComfyUI Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=po
ExecStart=/usr/bin/ssh -p 35043 -N -L 8188:127.0.0.1:8188 -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes po@3722d01e5a6f.ofalias.com
ExecStop=/usr/bin/pkill -f "ssh.*3722d01e5a6f.*8188"
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

特性：
- `Type=simple` 不加 `-f`，让 systemd 直接控制 SSH 进程（不是 `Type=forking`）
- `-o ExitOnForwardFailure=yes` 防止 SSH 进程挂起在失效的转发上（systemd 自动重启）
- `ServerAliveInterval=30` 防止 NAT 超时断开

使用前确认 SSH 密钥无密码：
```bash
ssh -o BatchMode=yes -p 35043 po@3722d01e5a6f.ofalias.com "echo OK"
```

## AstrBot 插件选择

有两个可用的 ComfyUI 插件，根据偏好选择：

### 选项 1：工作流式 LLM 驱动（需改节点，更可控）

插件：`cjxzdzh/astrbot_plugin_comfyui`（v1.0.1，⭐10）

**AstrBot WebUI → 插件 → astrbot_plugin_comfyui → 设置**：

| 字段 | 值 | 说明 |
|------|-----|------|
| `server_ip` | `127.0.0.1:8188` | SSH 隧道后的本地地址 |
| `webui_host` | `0.0.0.0` | 管理页允许局域网访问 |
| `webui_port` | `6187` | 默认 |

**ComfyUI 服务端自定义节点**（必须）：
```bash
cd /path/to/ComfyUI/custom_nodes
git clone https://github.com/chrisgoringe/cg-use-everywhere          # Simple String
git clone https://github.com/Acly/comfyui-tooling-nodes              # ETN_LoadImageBase64
git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite    # VHS_LoadVideo（可选）
```

**工作流文件名约定**：`工作流名+文本N+图片M+视频K.json`
- 工作流内文本入口用 **Simple String**，图片入口用 **ETN_LoadImageBase64**
- 上传后为每个工作流写说明文字，LLM 据此选择工作流

**LLM 工具**：通过 LLM Tool 直接调用（comfyui_execute / list_workflows / query_wait），干净可控。

#### ⚠️ cg-use-everywhere v7+ 移除了 Simple String

**`Simple String` 节点在 cg-use-everywhere v7（2025-09-10）中被移除。** 新 clone 的版本是 v7.x，搜不到 Simple String 节点。

**修复**：回退到最后包含 Simple String 的提交：
```bash
cd /data/comfy/ComfyUI/custom_nodes/cg-use-everywhere
git checkout f2a0c34679404794ae7fb9b626abcb5921f6a485
```
验证：
```bash
grep -r 'class.*SimpleString\|Simple String' --include='*.py' --include='*.js' .
# 应看到 SimpleString 类定义 + NODE_CLASS_MAPPINGS 注册
```

**无替代方案**：cg-use-everywhere 作者在讨论中确认没有给 Simple String 做替代。cjxzdzh 插件硬编码 `class_type == "Simple String"`。

### 选项 2：简易 LLM 驱动（填节点 ID，不改工作流）

插件：`lumingya/astrbot_plugin_comfyui_pro`（v2.0，⭐14）

**优势**：不需要改工作流节点类型，直接导入 ComfyUI 导出的 API JSON，填 Input/Output 节点 ID 即可。

**AstrBot WebUI → 插件 → astrbot_plugin_comfyui_pro → 设置**：

| 字段 | 值 | 说明 |
|------|-----|------|
| `Server Address` | `127.0.0.1:8188` | SSH 隧道后的本地地址 |
| `JSON File` | 选已放入的工作流文件 | ComfyUI 导出（API Format）的 .json |
| `Input Node ID` | 接收提示词的 CLIP Text Encode 节点 ID | 开开发者模式可见 |
| `Output Node ID` | Save Image / Preview Image 节点 ID | 同上 |

**工作流放哪**：`data/plugin_data/astrbot_plugin_comfyui_pro/workflow/`

**重载**：放好工作流后，重载插件 → 刷新浏览器 → 再重载，下拉菜单才会出现新工作流。

**LLM 触发**：不是通过 LLM Tool，而是从 LLM 回复中正则提取 `<draw>...</draw>` 标签。默认 system prompt 已配置好，不需要额外设置。

**命令**（给管理员用的）：
| 命令 | 说明 |
|------|------|
| `/comfy_ls` | 列出工作流 |
| `/comfy_use <序号>` | 切换工作流 |
| `/comfy_lock on\|off` | 锁定/解锁（仅管理员） |
| `/画图 <提示词>` | 直接指令 |
| 直接说"帮我画个..." | LLM 自然语言触发绘图 |



### 选项 3：指令式大而全（内建工作流 + 模型选择）

插件：`tjc6666666666666/astrbot_plugin_ComfyUI_promax`（v3.3）

**AstrBot WebUI → 插件 → astrbot_plugin_ComfyUI_promax → 设置**：

| 字段 | 值 | 说明 |
|------|-----|------|
| `comfyui_url` | `["http://127.0.0.1:8188,主服务器"]` | 列表格式，支持多服务器轮询 |
| `ckpt_name` | `Anima/miaomiaoHarem_anima14.safetensors` | 支持子目录路径（ComfyUI 自动解析） |
| `model_config` | `["Anima/miaomiaoHarem_anima14.safetensors,二次元动漫"]` | `文件名,描述` 格式列表 |
| `lora_config` | 同上格式可选 | LoRA 配置 |

**关键配置项**：

- **模型文件在子目录**：`models/checkpoints/Anima/xxx.safetensors` → `ckpt_name` 填 `Anima/xxx.safetensors`（ComfyUI 加载 checkpoint 时自动拼接 models/checkpoints/ 前缀）
- **model_config**：`["文件名,描述", ...]` 列表，LLM / `model:描述` 命令通过描述选模型
- **批量/分辨率**：`txt2img_batch_size`、`default_width/height`、`max_width/height` 等限制在 `_conf_schema.json` 里
- **插件自带文生图/图生图 workflow**：`aimg <prompt>` / `img2img` 命令，不需要额外上传 workflow JSON（但如果要自定义，可以在 `workflow/` 下放自己的）
- **控制项**：`admin_ids`、`whitelist_group_ids`、`cooldown_seconds`、`lockdown` 等对个人 Bot 可留空/默认

**验证**：`aimg cat` 应该出图。第一次用确保 `ckpt_name` 指向的模型在 ComfyUI 服务器上存在。

## CivitAI API 使用

CivitAI 提供 REST API，**不要用浏览器爬**，直接用 curl：

```bash
# 基础参数
API_KEY="你的key"

# 本月最热 Checkpoint
curl -s "https://civitai.com/api/v1/models?limit=20&sort=Most%20Downloaded&period=Month&types=Checkpoint" \
  -H "Authorization: Bearer $API_KEY"

# 搜索模型（query 参数受限制，可能返回空）
curl -s "https://civitai.com/api/v1/models?query=anime&limit=5" \
  -H "Authorization: Bearer $API_KEY"

# 单个模型详情
curl -s "https://civitai.com/api/v1/models/620406" \
  -H "Authorization: Bearer $API_KEY"
```

**参数**：
- `types`：`Checkpoint`, `LORA`, `Controlnet`, `VAE`, `Upscaler` 等
- `sort`：`Most Downloaded`, `Highest Rated`, `Newest`
- `period`：`Day`, `Week`, `Month`, `Year`, `AllTime`
- `limit`：最多 200

**常见 base model 标识**（CivitAI 不全是 SD1.5/SDXL，有独立架构的新模型）：

| 标识 | 架构 | 说明 |
|------|------|------|
| `SD 1.5` | SD1.5 | 传统，~2GB pruned |
| `SDXL 1.0` | SDXL | ~6.5GB |
| `Pony` | SDXL 微调 | 动漫 v-pred |
| `Illustrious` | SDXL 微调 | 动漫 eps |
| `NoobAI` | SDXL 微调 | 动漫 eps |
| **`Anima`** | **2B，Flow Matching** | CircleStone Labs × Comfy Org 新架构，16ch VAE，0.6B LLM text encoder |
| **`ZImageTurbo`** | **独立架构** | BF16 3-11GB |
| `Krea 2` | 独立 | ~13GB |
| `Flux` | 3.5B/9B，Flow Matching | `diffusion_models/` 目录，非标准 checkpoint |

## 验证连通性

配置完重启 AstrBot 后，验证 ComfyUI 可通：

```bash
curl -s http://127.0.0.1:8188/system_stats
```

有 JSON 返回说明隧道和插件都就绪。
