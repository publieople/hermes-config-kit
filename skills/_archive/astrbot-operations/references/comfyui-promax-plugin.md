# astrbot_plugin_ComfyUI_promax 配置与坑

tjc6666666666666 的大而全版 ComfyUI 插件（AstrBot 市场名 ComfyUI_pro 或 promax）。

## 核心配置

```json
{
  "comfyui_url": ["http://127.0.0.1:8188,服务器1"],
  "ckpt_name": "Anima/miaomiaoHarem_anima14.safetensors",
  "model_config": ["Anima/miaomiaoHarem_anima14.safetensors,二次元动漫"],
  "open_time_ranges": "0:00-24:00"
}
```

- `comfyui_url` 是 **list**，每个元素 `"URL,名称"`（逗号分隔 URL 和显示名）
- `ckpt_name` 支持子目录路径（如 `Anima/xxx.safetensors`），ComfyUI 会自动从 `models/checkpoints/` 下解析
- `model_config` 每个元素 `"文件名,描述"`，描述供 LLM 选模型时参考
- `open_time_ranges`：`0:00-24:00` 全天开放；默认 `7:00-8:00,11:00-14:00,17:00-24:00`

## 插件两条完全独立的请求路径

插件有两个独立的路径最终提交给 ComfyUI：

### 路径 A：标准 txt2img（aimg 命令）

触发方式：
- `aimg 提示词`（`ImgGenerateFilter`）

走 `_process_comfyui_task()` → `_build_comfyui_prompt()` → **硬编码用 CheckpointLoaderSimple (节点 30)**

```python
"30": {"inputs": {"ckpt_name": selected_model or self.ckpt_name},
       "class_type": "CheckpointLoaderSimple"}
```

此路径依赖 checkpoint **内嵌 CLIP + VAE**。Anima 模型没有，所以走 `aimg` 一定失败。

### 路径 A'：LLM tool `comfyui_txt2img`（2026-07-08 已修复）

**历史问题**：原实现跟 `aimg` 一样走 `_build_comfyui_prompt`，LLM 调 tool 时直接 `clip input is invalid` 闪退 0.21s。ComfyUI journal 报：
```
!!! Exception during processing !!! ERROR: clip input is invalid: None
If the clip is from a checkpoint loader node your checkpoint does not contain a valid clip or text encoder model.
```

**修复**（main.py `comfyui_txt2img` 函数体内）：先查 `eng.workflow_prefixes.get("anima")`，存在则把 LLM tool 路由到路径 B（`build_workflow` + `is_workflow=True` + 走 `anima` workflow），anima workflow 缺失时 fallback 到原 `_build_comfyui_prompt` 路径（兼容 SDXL/Illustrious 等内嵌 CLIP 的 checkpoint）。

**配合修复**：把 LLM tool 的 docstring 改写为「Anima 配 Qwen3 0.6B 必须英文 Danbooru 标签」+ 中英对照示例 + 标签排序规则 + quality prefix。LLM 看到 docstring 才会自己把中文翻成 Danbooru 标签（之前 docstring 写"if Chinese, translate to English"，LLM 不翻译直接传中文 → Qwen3 切乱码 → 错乱图）。

**ad-hoc 验证脚本模板**（隔离在 `/tmp/hermes-verify-promax-behavior.py`）：
1. 用 `ast.unparse` 抽 `comfyui_txt2img` 函数体
2. stub `aiohttp.web` + 几个 lazy-import 的 `astrbot.core.platform.*` 模块
3. 在 astrbot venv 下 import main.py
4. 构造 FakeSelf/FakeEngine（带 `workflow_prefixes={"anima":"anima_t2i"}` + anima workflow dict）/FakeEvent
5. 调函数，捕获 `submit_task` 的 dict
6. 断言：is_workflow=True, workflow_name=anima_t2i, 有 CLIPLoader node 45, node 11 text 含用户 prompt, 无标准 txt2img 节点 6/30/33
7. `rm /tmp/hermes-verify-promax-behavior.py`

**坑**：anima workflow 必须配 `node_configs["11"]["text"]` 含 `aliases: ["提示词", "prompt"]`，否则 LLM 传的 prompt 进不到 CLIPTextEncode 输入（见下面"自定义 Workflow"章节的 `config.json` schema）。

### 路径 B：自定义 Workflow（前缀触发，如 anima）

触发方式：
- `anima 提示词`（WorkflowFilter 匹配 prefix）

走 `handle_workflow()` → `_process_workflow_task()` → `build_workflow()`

用完整的 workflow JSON（含 CLIPLoader、VAELoader、diffusion 模型三节点独立加载），**注入 prompt 通过 `node_configs` 覆盖 CLIPTextEncode 的 `text` 字段**。

此路径正确加载 Anima 的独立 CLIP/VAE，可以成功生成。

### 关键区别

| 特性 | 路径 A（标准 txt2img / `aimg`） | 路径 A'（LLM `comfyui_txt2img`） | 路径 B（workflow 前缀 `anima`） |
|------|----------------------|----------------------|----------------------|
| 触发 | `aimg xxx` | LLM 自决调 tool | `anima xxx` |
| CLIP 来源 | CheckpointLoaderSimple 内嵌 | workflow 内 CLIPLoader（修后） | workflow 内 CLIPLoader |
| VAE 来源 | CheckpointLoaderSimple 内嵌 | workflow 内 VAELoader（修后） | workflow 内 VAELoader |
| Anima 兼容 | ❌ `clip input is invalid: None` | ✅（修后走 anima workflow） | ✅ |
| 日志特征 | `model_type FLOW`，无 CLIP/VAE 加载 | `VAE load device` + `CLIP/text encoder model load device` | `VAE load device` + `CLIP/text encoder model load device` |

## 诊断：如何在 ComfyUI 日志中区分两条路径

ComfyUI 日志文件在远程服务器（`/data/comfy/ComfyUI/user/comfyui_{port}.log`）：

**路径 A 失败特征**（CheckpointLoaderSimple 路径）：
```
got prompt
model weight dtype torch.bfloat16, manual cast: None
model_type FLOW
WARNING: No VAE weights detected, VAE not initalized.
no CLIP/text encoder weights in checkpoint, the text encoder model will not be loaded.
!!! Exception during processing !!! ERROR: clip input is invalid: None
```

**路径 B 成功特征**（workflow 路径）：
```
got prompt
Using pytorch attention in VAE
VAE load device: cuda:0, offload device: cpu, dtype: torch.bfloat16
CLIP/text encoder model load device: cuda:0, offload device: cpu, current: cpu, dtype: torch.float16
Requested to load AnimaTEModel_
Model AnimaTEModel_ prepared for dynamic VRAM loading. 1136MB Staged.
Requested to load Anima
Model Anima prepared for dynamic VRAM loading. 3988MB Staged.
100%|██████████| 32/32 [00:31<00:00,  1.01it/s]
Requested to load WanVAE
Prompt executed in 32.38 seconds
```

**注意**：AstrBot 日志（`data/astrbot.log`）通常不显示 ComfyUI 返回的错误，因为错误在插件回调中被截断或只在轮询阶段发现"队列为空"。必须看 ComfyUI 服务端日志才能知道执行失败的实际原因。

## 常见坑

### 1. `/aimg` 命令 filter 不匹配

插件内置 ImgGenerateFilter 只检查 `aimg` 前缀，**不匹配 `/aimg`**（带斜杠的 AstrBot 命令格式）。

```python
# 原代码（main.py:83）—— 只匹配 aimg，不匹配 /aimg
return (text.startswith("aimg") or text.startswith("aimg ")) and text != "aimg"

# 修复：加 /aimg 前缀
return (text.startswith("aimg") or text.startswith("/aimg ") or text.startswith("aimg ")) and text != "aimg"
```

症状：发 `/aimg xxx` 不走插件，走 LLM → LLM 根据 tool description 里的开放时间描述回复"当前未开放"。

同样需要检查 `HelpFilter`、`Img2ImgFilter` 等是否也漏了 `/` 前缀。

### 2. 开放时间改了不生效

- 改完 `open_time_ranges` 后**必须重载插件**（WebUI 或 `/plugin reload`）
- **时间格式坑**：`24:00` 在 `_time_to_minutes()` 中经 `(hh % 24) * 60` 被算成 `0` 分钟而非 `1440`，导致 `0:00-24:00` 被解析为 `[(0, 0)]`（只允许午夜那一秒）。**必须手动修代码**：
  ```python
  # workflow_engine.py:371 — 原来是 (hh % 24) * 60 + mm
  return hh * 60 + mm  # 去掉 % 24
  ```
- 如果重载后仍不生效：检查 `data/config/astrbot_plugin_ComfyUI_promax_config.json` 是否确实写入新值（BOM 编码 utf-8-sig）

### 3. 端口占用导致旧实例残留

GUI 服务器默认端口 7777。热重载时旧实例的 Flask 可能未完全释放端口 → `Address already in use`。此时旧实例的 engine 可能仍在服务，新实例部分功能异常。

### AngelHeart 拦截导致命令走 LLM

即使 filter 匹配正确，**AngelHeart 的秘书/观测中状态可能在 filter 之前拦截消息**，路由到 LLM 而非插件命令处理函数。日志特征：

```
[14:16:01.734] [Plug] [INFO] [roles.secretary:78]: AngelHeart[default:GroupMessage:707942526]: 秘书处理消息 (状态: 观测中)
[14:16:01.734] [Plug] [INFO] [roles.secretary:258]: AngelHeart[default:GroupMessage:707942526]: 秘书开始调用LLM进行分析...
```

此时 LLM 看到 `comfyui_txt2img` LLM tool 的描述（含开放时间），可能拒绝调用（说"当前未开放"）或自行调用但返回带时间限制的错误信息。

**诊断**：grep journal 看有没有 `Secretary` / `秘书处理` 行。
**避免**：临时禁用 AngelHeart 的秘书模式，或等它恢复"不在场"状态。这条不影响 `/plugin reload`，重载后 AngelHeart 状态不会自动重置。

### 4. 模型放子目录

`models/checkpoints/Anima/miaomiaoHarem_anima14.safetensors` → `ckpt_name = "Anima/miaomiaoHarem_anima14.safetensors"`。ComfyUI 原生支持子目录路径。

### 5. 写入时的其他配置

- `enable_gui: false` — 不需要 GUI 管理界面时可关掉避免端口冲突
- `sampler_name: "euler"` — Anima 模型 flow matching 用 euler 就行
- `scheduler: "simple"` — 默认即可

### 6. Anima 模型不兼容 CheckpointLoaderSimple

Anima 是独立架构（2B 参数，flow matching，16 通道 VAE），不自带 CLIP 文本编码器。其文本编码器是单独的 text_encoders/qwen_3_4b.safetensors。

promax 插件的**标准 txt2img 路径**（路径 A）用 `_build_comfyui_prompt` 生成单一 `CheckpointLoaderSimple`，此节点要求 checkpoint 文件内嵌 CLIP。Anima 不含 CLIP 导致 ComfyUI 执行时报错：

```
clip input is invalid: None
```

表现为：插件提交任务 → ComfyUI 接受 → 执行失败 → 队列移除 → 插件查到空队列 + 无 history → "队列已为空" 错误。

**注意区分**：自定义 workflow 路径（`anima` 前缀，路径 B）不受此限制——它的 workflow JSON 包含独立 CLIPLoader 节点，能正常使用 Anima。只有 `aimg` 命令会走有问题的路径 A。**LLM tool `comfyui_txt2img` 2026-07-08 已修复**，默认走路径 B（参见上面路径 A' 章节）。

**解决方案**：
- 用 `anima <提示词>`（workflow 前缀）替代 `aimg <提示词>`
- 不在 `aimg` 命令中使用无内嵌 CLIP/VAE 的模型
- 保持 `model_config` 中只列兼容的 checkpoint（有内嵌 CLIP/VAE 的 SDXL/Illustrious 模型如 `miaomiao-harem.safetensors`）

### 7. enable_image_encrypt 需要 HilbertImageEncrypt 节点

默认 enable_image_encrypt: true，内置 workflow 会插入 HilbertImageEncrypt 节点。如果 ComfyUI 服务端没装 hilbert_image_encrypt 自定义节点，提交时报错 Node not found。关掉 enable_image_encrypt: false 即可。

### 8. 修改 workflow_engine.py 后热重载不生效

AstrBot 热重载只重建插件实例（main.py），不会重新导入 workflow_engine.py（Python 模块缓存）。修改 workflow_engine.py 后必须 sudo systemctl restart astrbot。

## 自定义 Workflow（GUI / 手动两种方式）

插件支持两种加自定义 workflow：

**GUI 方式**：WebUI 管理端 → 新建工作流 → 填表单。字段对应：

| 字段 | 说明 | 示例 |
|------|------|------|
| 工作流名称 | 唯一标识 | `anima_t2i` |
| 显示名称 | 展示名 | `Anima文生图` |
| 前缀 | 调用命令 | `anima` |
| 描述 | 说明文字 | 选填 |

创建后发 `<前缀> <提示词>` 调用。自定义 workflow 用本地导出的完整节点图（Load Checkpoint/Load CLIP/Load VAE），不受内置 workflow 限制。

**⚠️ GUI 坑**：选了「可配置节点」后还要在「节点参数配置」里加参数定义（键名、别名、类型）。只选节点不配参数 → `node_configs: {}` 空字典 → 插件不知道把提示词注入到哪个输入字段 → workflow 提交时带的是 JSON 默认值而非用户输入的提示词。

修正：直接编辑 `config.json` 的 `node_configs` 补上参数映射。CLIPTextEncode 节点的 `text` 输入需要 `aliases: ["提示词", "prompt"]`：

```json
{
  "11": {
    "text": {
      "type": "text",
      "default": "",
      "description": "提示词",
      "required": true,
      "aliases": ["提示词", "prompt"]
    }
  }
}
```

**手动方式**：`workflow/<name>/` 下放 `workflow.json`（API 格式）+ `config.json`（元配置）。参考 `workflow/zimage/` 目录示例。如需精细参数映射（尺寸/步数/seed），手写 `config.json` 的 `node_configs`。

### `config.json` 的关键字段

```json
{
  "name": "显示名",
  "prefix": "命令前缀",
  "input_nodes": [],         // 图片输入节点（空=无图输入）
  "output_nodes": ["46"],    // 输出节点 ID（用于提取结果）
  "configurable_nodes": ["11"],  // 可配置节点列表
  "node_configs": {
    "11": {                 // 节点 ID
      "text": {             // 输入字段名
        "type": "text",     // 参数类型
        "default": "",      // 默认值
        "description": "提示词",
        "required": true,
        "aliases": ["提示词", "prompt"]  // 别名（支持中英文）
      }
    }
  }
}
```

`node_configs` 通过 `build_workflow()` 迭代，将 `node_id:param_name` 匹配到的用户输入注入 workflow JSON。未匹配的参数会用 `default` 值。

### 9. Anima 模型的 Qwen 文本编码器不理解中文

**现象**：用 `anima 抽烟的白毛猫娘`（中文）生成的图片与 prompt 无关（变成随机动漫少女）。
**原因**：Anima 配套的 `qwen_3_06b_base.safetensors`（Qwen 3 0.6B）作为 CLIP 文本编码器，训练数据以英文 Danbooru 标签为主，中文 prompt 的 embedding 落在分布外。

**验证方法**：
1. 直接调 ComfyUI API 注入两个 prompt 对比：
   ```python
   wf = copy.deepcopy(built_workflow)
   wf["11"]["inputs"]["text"] = test_prompt
   # 提交一模一样的 workflow，只改 text 字段
   ```
2. 用 `vision_analyze` 检查输出图片是否匹配 prompt
3. 同一 workflow，英文 prompt 正常（`1girl, cat ears, white hair, smoking` → ✅ 白毛猫娘），中文 prompt 不正常（`抽烟的白毛猫娘` → ❌ 随机少女）→ 确诊是编码器问题

**解决方案**: 用英文 Danbooru 标签格式写 prompt：
```
anima 1girl, cat ears, white hair, smoking, cigarette, sitting by window
```

**诊断流程**（排查\"插件没传我的 prompt\"类问题时）：检查 ComfyUI 历史确认 prompt 确实被发送了（对比 cached vs executed nodes）；手动通过 API 提交同一 prompt 对比结果；用 vision 模型验证图片内容是否匹配。

### 10. CLIPLoader 的 `type` 字段必须跟文本编码器家族匹配

跟第 9 项(中文 prompt 编码失败)不同,这是**加载阶段**的 bug,不是语言问题。

**坑**:`workflow/anima_t2i.json` 里的 CLIPLoader:
```json
{
  "class_type": "CLIPLoader",
  "inputs": {
    "clip_name": "qwen_3_06b_base.safetensors",
    "type": "stable_diffusion",   ← Qwen 3 0.6B 不是 SD-CLIP
    "device": "default"
  }
}
```

`type` 字段控制 ComfyUI 用哪个 tokenizer / 权重格式加载这个 clip 文件:
- `stable_diffusion` → OpenAI CLIP ViT-L/14 tokenizer,匹配 SD1.5/SDXL/SD3 的内嵌 CLIP
- `flux` / `sd3` / `qwen_image` / `t5` 等 → 各家自己的,ComfyUI 节点定义里能看到全部可选值

**Anima 配套的 Qwen 3 0.6B 既不是 SD-CLIP,也不完全等同于上述任何一种**。ComfyUI 新版有专门的 `qwen_image` 之类的 type,Qwen3 0.6B 应该用匹配的 type,或者在 ComfyUI 节点浏览器里查 CLIPLoader 的 `type` 下拉框实际能选哪些。

**症状**:
- workflow 提交后 ComfyUI 加载时报 `unrecognized tokenizer` / `tensor size mismatch` / 类似错误
- 或加载成功但 embedding 是垃圾值,生成的图与 prompt 无关(跟中文 prompt 失效的症状相似但根因不同)
- 跟"未传 prompt"区分: ComfyUI 历史里 `cached` 和 `executed` 节点的 text 字段**相同**,说明 prompt 注入了,是 tokenizer 错

**诊断**:
1. 看 ComfyUI server.log,加载 CLIPLoader 时有没有 `tokenizer` / `Qwen` / `Error` 关键字
2. `curl http://127.0.0.1:8188/object_info | jq '.CLIPLoader.input.required.type'` 拿 `type` 字段实际可选值
3. 把 workflow JSON 的 `type` 字段手动试几个值(`qwen_image` / `flux` / 留空),看哪个能跑通

**修复**: 拿到服务端 ComfyUI 的真错信息再定 type 改成什么。在没看到 server.log 之前**不要盲改 type 字段**——瞎改换错 type 仍然是同样问题,反而多绕一圈。

**2026-07-08 实证**：`type=stable_diffusion` + `clip_name=qwen_3_06b_base.safetensors` 这套配在当前服务端跑了 8+ 次全部成功（每次 ~32 秒出图），ComfyUI journal 无任何 tokenize 错。**Anima 模型权重加载时内部覆盖了 CLIPLoader 的 `type` 行为**，workflow 里这行只是占位。**不要按"Qwen 必须用 qwen_image"的常识盲改**——改了反而可能坏。先看 ComfyUI journal 没报错就别动。

### 13. LLM provider 切换:`/provider <idx>` 是 session 级,改 `default_provider_id` 才是全局

**坑**:`/provider 2`(切到 MiniMax-M3)只对当前 AstrBot 进程内**该会话的 LLM 上下文**生效。其他群/新会话默认仍走 `cmd_config.json:233 default_provider_id`。如果 `default_provider_id` 是免费档(`opencode/deepseek-v4-flash-free`),新群消息来了仍走 free → 5 次 429 → fail。

**症状**:
- `/provider 2` 在群 A 切到 M3,立即在群 A 调 LLM 成功
- 同一时间在群 B 调 LLM,`journalctl -u astrbot` 看到 `[OpenAI] Request failed with retryable error; retrying (N/5): Error code: 429 - FreeUsageLimitError` 一连串 5 次 → LLM fail
- ComfyUI 端 `got prompt` 0 条 → bot 没机会调绘图 tool

**诊断**:
```bash
journalctl -u astrbot --since "5 min ago" --no-pager | grep -E "429|FreeUsageLimit|retrying"
journalctl -u astrbot --since "5 min ago" --no-pager | grep "GroupMessage"
```

**修复**(持久 — 改全局默认):
```bash
sed -i 's|"default_provider_id": "opencode/deepseek-v4-flash-free"|"default_provider_id": "minimax-token-plan/MiniMax-M3"|' /home/po/astrbot/data/cmd_config.json
sudo systemctl restart astrbot
```

**临时方案**:`/provider` 是 session 级,新会话要重新切。`/new` 切新会话会保留上次的 provider 选择(`get_using_provider()` 返回的是 context,不是会话级),实测有时仍需 `/provider 2` 重切。

### 14. AngelHeart 在 LLM 路径上不会自动调绘图 tool

**坑**:用户发"@bot 这是图 + 一句描述",AngelHeart 走"被呼唤"路径,LLM 分析后决策"参与"但**不会自动调 `comfyui_txt2img`**——除非 LLM 觉得用户要画图。LLM 看到纯展示意图("这是 X"),默认只是回文字。

**症状**:`journalctl -u astrbot` 看到:
```
[roles.front_desk:566]: 决策为'参与'。策略: 被呼唤回复
[core.angel_heart_context:492]: ... 话题: 尼古喵喵图片展示 ...
```
bot 回一句短回复,ComfyUI 端 0 个 `got prompt`。

**修复**:
- 用户必须**显式说"画"**:"@bot 画个 X"、"@bot 复刻这张"、"@bot t2i 一个 X"
- LLM tool docstring 引导(已改:让 LLM 知道 comfyui_txt2img 只在用户要图时才调)

**判断走没走 LLM tool**:ComfyUI journal 看 `got prompt` 数量,或 AstrBot journal 搜 `comfyui_txt2img` / `Adding llm tool` / `Adding tool result`。

### 15. AstrBot 部署是 system scope 不是 user scope

`/etc/systemd/system/astrbot.service` 是 root scope(systemd service),`sudo journalctl -u astrbot` 查 system journal。**不是** `~/.config/systemd/user/astrbot.service` + `journalctl --user -u astrbot`(后者在当前部署无 entries → `-- No entries --`)。

**关键 systemd unit 字段**(`/etc/systemd/system/astrbot.service`):
- `User=po` — 跑在 po 用户
- `WorkingDirectory=/home/po/astrbot`
- `ExecStart=/home/po/.local/bin/astrbot run`
- **没** `StandardOutput=append:` → stdout 默认进 system journal

**修改后**:`sudo systemctl daemon-reload && sudo systemctl restart astrbot`(不是 `systemctl --user`)。

### 16. LLM tool 路径的 prompt 空格变下划线副作用

`comfyui_txt2img` 体内有 `prompt = prompt.replace(" ", "_")`(原代码就有,2026-07-08 改 routing 时保留)。LLM 传 `"1girl, solo, white_hair, cat_ears"` 没问题(无空格),若传中文 `"抽烟的白毛猫娘"`(无空格)也不变,真正坑的是带空格的:`"a girl with long hair"` → `"a_girl_with_long_hair"`,Danbooru 解析器认不出。

**实际影响小**:LLM 看到 docstring 写明要 Danbooru 标签(无空格逗号分隔)就不会传带空格的;用户自己发中文也无空格。**真正使用场景下基本不触发**,但值得记一笔:若 LLM 传了带空格的 prompt,空格会变下划线。

### 11. ComfyUI 服务端日志在远程机器,本地够不着

AstrBot 这边能直接看的是 plugin 日志(走的 journal 或 `data/astrbot.log`)。ComfyUI 服务端(`3722d01e5a6f.ofalias.com:8188`)的 `comfyui_{port}.log` 或 `nohup.out` **必须 SSH 到那台机器才能看**。

排查"插件提交了任务但 ComfyUI 报错"类问题,先列能从本地诊断的:
- `/system_stats` (200 = 服务活) / `/queue` (队列长度) / `/object_info` (节点 + 模型清单) / `/history/<prompt_id>` (单任务执行历史)
- 提交完一个任务后立即 `curl http://127.0.0.1:8188/history/<prompt_id>`,看 status.messages 里 ComfyUI 自己的报错

如果本地 endpoint 都给不出错误细节(典型情况: queue 任务消失、history 查不到、但 service 活的),就只能登远程服务器看 server.log。

### 12. `enable_translation` 配置是 schema 死开关，不要被它误导

`config.json` schema 写 `enable_translation`「已弃用，v1.5 移除，保留仅为兼容」，但 **`_translate_cn_prompt()` 函数代码还在 `handle_workflow` 路径里直接调用**（main.py:1193）。schema 删了 ≠ 代码删了。

**实际行为**：
- schema 标 default `false` → 多数人不动
- 函数 `def _translate_cn_prompt(self, text)` **不读** `self.enable_translation`，直接调 LLM 翻
- LLM 翻译失败时 fallback 原文传 ComfyUI
- `aimg` / `anima` 路径都走这个流程

**结论**：不要靠 `enable_translation: true` 启用翻译——它从来就没真正控制过翻译。中文 prompt 走 `aimg`/`anima` 命令时,翻译逻辑是自动触发的（不管开关值），只是 LLM 翻译失败时 fallback 原文。**LLM tool `comfyui_txt2img` 路径不调这个函数**（2026-07-08 修复后走路径 B），由 LLM 自己负责把中文写成英文 Danbooru 标签。

**调试 prompt 是否被翻译**：
- 看 ComfyUI history 的 `node 11 text` 字段含中文字符 → 翻译失败 fallback 原文
- 看含英文 Danbooru 标签 → 翻译成功
- `aimg` 路径会有 `[MSG_ID:xxx]` 后缀（promax 加的）；`anima` 路径无后缀；LLM tool 路径完全无后缀且一定英文

**真正的修复方向**（不是改翻译开关）：改 promax 行为 / 改 workflow 默认 prompt starter / 让 LLM 看到清晰的 docstring。`enable_translation` 字段基本是个摆设。

### 17. @filter.command 是绕过 LLM tool calling 的最终手段

**问题**: M3 / deepseek-v4-flash 在 AstrBot 4.26.5 "被呼唤回复"路径下,3+ 次观测稳定**口头承诺"调 tool 给你跑"但不发 `tool_use` 块**(journal 行 `[WARN] ... skills_like tool re-query returned no tool calls; fallback to assistant response`)。M3 诚实自述:"我没法直接调用那个文件里的 curl 命令啊,我能用的是 comfyui_txt2img 这个 tool"。嘴说"会调"和手发 tool_use 是两个独立决策,docstring 改写 + 中英对照 + quality prefix 都没用,prose 指令对 M3 弱。

**修复** (2026-07-08): 在 promax 加 `@filter.custom_filter(DrawCommandFilter)` 装饰器 + `handle_draw` handler,**完全 bypass LLM 决策链**。

```python
class DrawCommandFilter(CustomFilter):
    def filter(self, event, cfg):
        text = event.message_obj.message_str.strip()
        if not text or text.startswith("aimg") or text.startswith("img2img"):
            return False
        if any(isinstance(m, Image) for m in event.get_messages()):
            return False
        head = text.split(maxsplit=1)[0]
        return head in ("画", "/画", "t2i", "/t2i", "复刻", "/复刻")

@filter.custom_filter(DrawCommandFilter)
async def handle_draw(self, event):
    text = event.message_obj.message_str.strip()
    parts = text.split(maxsplit=1)
    prompt = parts[1].strip() if len(parts) > 1 else ""
    # ... 白名单/时间/服务器检查
    wfn = eng.workflow_prefixes.get("anima")
    wf_info = eng.workflows[wfn]
    cfg, wf_data = wf_info["config"], wf_info["workflow"]
    params = eng.parse_workflow_params([f"提示词:{prompt}"], cfg)
    final_wf = eng.build_workflow(wf_data, cfg, params, [])
    await eng.submit_task({
        "prompt": final_wf, "workflow_name": wfn, "user_id": uid,
        "is_workflow": True, "image_paths": [],
        "workflow_config": cfg,
        "callback": self._make_result_callback(event, "workflow")
    })
```

**用户使用**: `画 1girl, solo, white_hair, cat_ears, smoking, cigarette, best quality, score_7, score_9` (不需要 @ bot,不需要 aimg 前缀)。bot 立即回 `Workflow「Anima文生图」已入队(排队:0个)`,30-40 秒后图。

**ad-hoc 验证模板** (隔离 venv 跑 main.py + fake engine, 不用重启 AstrBot):
```python
# /tmp/hermes-verify-promax-draw-v5.py
# 1. AST: 抽 DrawCommandFilter 的 `return head in (...)` 节点 → 确认 6 trigger words
# 2. AST: 抽 handle_draw 函数体 → 确认 9 个必需调用 token
# 3. 行为: 在 /home/po/.local/share/uv/tools/astrbot/bin/python3 下 import main.py
#    构造 FakeEngine(workflow_prefixes={"anima": "anima_t2i"}, workflows={...}) + FakeSelf + FakeEvent
#    await handle_draw(self_, FakeEvent("画 1girl, white_hair, ..."))
#    断言 eng.captured[0] 是 dict 包含 CLIPLoader + 注入 prompt
# 4. rm /tmp/hermes-verify-promax-draw-v5.py
```

**坑**: handle_draw 体内**别**做 `prompt.replace(" ", "_")` (LLM tool 路径有这副作用,绕过 LLM 后直接传原 prompt,空格留 OK 不会让 Danbooru 解析挂)。

### 18. SKILL.md 需要 `_meta.json` 才被 AstrBot 识别

**坑**: 放 `data/skills/<name>/SKILL.md` 后,`skills.json` 不会自动添加,`active: true` 也不出现 → LLM 看不到。**必须**同目录加 `_meta.json` 最小字段:

```json
{"ownerId": "local", "slug": "<name>", "version": "1.0.0", "publishedAt": <unix_ms>}
```

少了 `slug` 字段就注册失败。写完后 AstrBot 启动时扫描到,sandbox 里 metadata 完整 → skill 注入到 system prompt。

### 19. `tool_loop_agent_runner:843` 行是 LLM tool calling 失败标志

AstrBot 4.26.5 内部 `[WARN] ... skills_like tool re-query returned no tool calls; fallback to assistant response` (在 `core/runners/tool_loop_agent_runner.py:843`) — 出现这行说明 LLM 在 tool_use 步骤**没输出** tool_call 块,runner 退回让 LLM 自由回复。bot 报"我帮你调"但**实际**没调。看到这行 + 同一 session 内 ComfyUI 0 got prompt,直接判定 LLM tool call 失败,**不要再调 LLM docstring / 换 provider,直接上方案 17 (filter.command bypass)**。

## 完整 bot 不调 tool 排查路径

```
journalctl -u astrbot --since "5 min ago" --no-pager 2>&1 | grep -E "tool_loop|tool_use|func_tool_manager|执行完成|skill"
ssh server 'sudo journalctl -u comfyui --since "5 min ago" --no-pager' 2>&1 | grep "got prompt"
```

| AstrBot journal 看到 | ComfyUI 看到 | 诊断 |
|---|---|---|
| `Added llm tool: comfyui_txt2img` 启动行 + `tool_loop_agent_runner:843 ... skills_like tool re-query returned no tool calls` | 0 got prompt | LLM 选了不调 tool → 改方案 17 filter.command bypass |
| `Added llm tool: comfyui_txt2img` 启动行 + LLM 自由回复"我帮你跑" | 0 got prompt | LLM 口头承诺不真发 tool_use → 同上 |
| `Added llm tool: comfyui_txt2img` 启动行 + LLM 真发 tool_use | got prompt 出现 | LLM 调成功,看 ComfyUI 跑结果 |
| 0 tool 注册(无 `Added llm tool: comfyui_txt2img` 启动行) | 0 got prompt | promax 插件没加载,查 plugin 目录 |
| tool 调成功 + `Added tool result` 行 | got prompt + 0.21s 后 `clip input is invalid` | LLM 调了但走错路径(路径 A)→ 改路径 A' / 走 anima workflow |

`config.json` schema 写 `enable_translation`「已弃用，v1.5 移除，保留仅为兼容」，但 **`_translate_cn_prompt()` 函数代码还在 `handle_workflow` 路径里直接调用**（main.py:1193）。schema 删了 ≠ 代码删了。

**实际行为**：
- schema 标 default `false` → 多数人不动
- 函数 `def _translate_cn_prompt(self, text)` **不读** `self.enable_translation`，直接调 LLM 翻
- LLM 翻译失败时 fallback 原文传 ComfyUI
- `aimg` / `anima` 路径都走这个流程

**结论**：不要靠 `enable_translation: true` 启用翻译——它从来就没真正控制过翻译。中文 prompt 走 `aimg`/`anima` 命令时,翻译逻辑是自动触发的（不管开关值），只是 LLM 翻译失败时 fallback 原文。**LLM tool `comfyui_txt2img` 路径不调这个函数**（2026-07-08 修复后走路径 B），由 LLM 自己负责把中文写成英文 Danbooru 标签。

**调试 prompt 是否被翻译**：
- 看 ComfyUI history 的 `node 11 text` 字段含中文字符 → 翻译失败 fallback 原文
- 看含英文 Danbooru 标签 → 翻译成功
- `aimg` 路径会有 `[MSG_ID:xxx]` 后缀（promax 加的）；`anima` 路径无后缀；LLM tool 路径完全无后缀且一定英文

**真正的修复方向**（不是改翻译开关）：改 promax 行为 / 改 workflow 默认 prompt starter / 让 LLM 看到清晰的 docstring。`enable_translation` 字段基本是个摆设。

## LLM 工具 vs 命令处理函数

两者都注册了：
- **命令**（`ImgGenerateFilter` filter）：匹配 `aimg` 前缀 → 走路径 A（标准 txt2img，Anima 必失败）
- **LLM 工具**（`comfyui_txt2img`）：LLM 看到的 tool description（docstring）含开放时间 + Danbooru 格式要求 → 2026-07-08 修复后走路径 B（anima workflow）

**AngelHeart 拦截影响**：如果 AngelHeart 在 filter 之前拦截消息路由到 LLM，原本 `aimg` 命令也会被改走 LLM tool（路径 A'），用 `aimg` 和 LLM tool 效果不同：aimg 是用户手动命令、prompt 直接传（中文会出问题），LLM tool 是 LLM 自己写英文 Danbooru prompt 传。要排查"aimg 走的到底是哪条路径"，看 ComfyUI history 的 `node 11 text` 字段：
- 含中文原文 + `[MSG_ID:xxx]` 后缀 → 路径 A（aimg + 翻译 fallback）
- 含中文原文无后缀 → 路径 A（aimg + `_translate_cn_prompt` 翻译失败 fallback）
- 含英文 Danbooru 标签 → 路径 A' 或 B（LLM 写的或用户发的）

## 配置存储位置

插件配置在 AstrBot 独立 JSON 文件：
- `/home/po/astrbot/data/config/astrbot_plugin_ComfyUI_promax_config.json`

插件元信息在：
- `/home/po/astrbot/data/plugins.json`（搜索 `astrbot_plugin_ComfyUI_promax`）
