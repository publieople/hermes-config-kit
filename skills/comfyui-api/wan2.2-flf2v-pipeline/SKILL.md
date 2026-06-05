---
name: wan2.2-flf2v-pipeline
description: Wan2.2 FLF2V (First/Last Frame to Video) 管线 — 生成首尾帧之间的插值视频，支持电影级镜头过渡
---

# Wan2.2 FLF2V Pipeline

## 核心原理

`WanFirstLastFrameToVideo` 节点在扩散过程中强制 t=0 和 t=1 的边界条件，首尾帧作为 ground truth，
模型生成中间的连贯过渡帧。和 I2V/T2V 使用**同一组模型**（`wan2.2_i2v_high_noise` + `wan2.2_i2v_low_noise`），
区别只在用 FLF 节点替代 `WanImageToVideoLatent`。

## 模型总览（Wan2.2 家族）

我们的服务器上已有所有需要的模型，**零下载，直接跑**：

| 模型 | 用途 | 服务器状态 |
|------|------|-----------|
| Wan2.2 I2V 14B | 图生视频 | ✅ `wan2.2_i2v_high/low_noise_14B_fp8_scaled.safetensors` |
| Wan2.2 FLF2V (本skill) | 首尾帧插值 | ✅ 使用同一组 I2V 模型 |
| Wan2.2 Fun Control 14B | 受控生成(Canny/Depth/Pose/MLSD/轨迹) | ❌ 未下载，约20GB |
| Wan2.2 Smooth Mix (社区) | 改进版首尾帧 + RIFE插帧 + 自动提示词 | ❌ 需自定义节点 |

**Vidu 2.0**（生数科技）: SaaS在线服务，**不可本地部署/ComfyUI集成**，无需再研究。

### Wan2.2 Fun Control（值得后续探索）

> 阿里开源，Apache 2.0，支持：
> - Canny（线稿）、Depth（深度）、OpenPose（人体姿态）、MLSD（边缘）控制
> - **轨迹控制** — 让角色按指定路径运动
> - 对短剧分镜控制非常有用（固定角色姿势、指定运镜路径）

如需使用需下载：
- `wan2.2_fun_control_high_noise_14B_fp8_scaled.safetensors`
- `wan2.2_fun_control_low_noise_14B_fp8_scaled.safetensors`
- 模型来源：[Comfy-Org/Wan_2.2_ComfyUI_Repackaged](https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged)

### Wan2.2 Smooth Mix（社区参考）

> 社区改进版首尾帧工作流：
> - `RH_Captioner` 节点自动根据首尾帧生成提示词
> - RIFE VFI 插帧提升流畅度
> - `wanBlockSwap` 模型融合
> - 需要额外安装：[KJ](https://github.com/kijai/ComfyUI-WanVideoWrapper) 等自定义节点

## AI 短剧剧本写作（FLF2V 优化版）

### 为什么 FLF2V 需要不同的剧本设计

传统漫剧分镜 = 每个镜头一张静态图，靠镜头切换讲故事。

FLF2V 视频 = **每个镜头两帧（首+尾）+ 一段插值视频**。首尾帧的差异决定了视频动态的丰富度。

### 核心剧本结构

```
Act 1: 建立（~6镜）— 世界正常展示，最后出现微小的异常
Act 2: 裂痕（~8镜）— 异常变频繁，主角发现不对劲
Act 3: 崩溃（~10镜）— 世界规则瓦解，密度最高
Act 4: 终结（~8镜）— 转向抽象，收束，余震
```

### 镜头类型与 FLF2V 的对应

| 镜头类型 | FLF2V 用法 | 首尾帧设计原则 |
|----------|-----------|---------------|
| **静态运镜**（固定/慢推/横移） | 首帧=近景构图 / 尾帧=稍远或稍近构图 | 首尾帧仅构图变化，场景元素不变 |
| **内容变化**（表情变/物体glitch） | 首帧=正常态 / 尾帧=异常态 | 两帧区别集中在变化区域，其余保持一致 |
| **场景过渡**（切新场景） | 首帧=旧场景尾帧 / 尾帧=新场景首帧 | 用 prompt 描述过渡效果（溶解/遮挡/像素化） |
| **动作镜头**（奔跑/溶解/消散） | 建议用 I2V 而非 FLF2V | 全动态由 I2V 模型生成，FLF2V 做边界衔接 |

### 三件套 Prompt 模式

每个镜头需要三组 prompt，分层编写：

```python
# 1. 首帧 prompt — Flux 生成 start_image
start_prompt = f"{STYLE_ANCHOR}, [场景描述_视角A]"

# 2. 尾帧 prompt — Flux 生成 end_image（必须不同！）
end_prompt = f"{STYLE_ANCHOR}, [场景描述_视角B/场景变化后]"

# 3. 视频 prompt — FLF2V 插值的运镜描述
video_prompt = "[运镜方式] + [首→尾的变化过程] + [禁止发生的负面描述]"
```

**关键规则**：
- 首帧和尾帧的 noise_seed 相差 1 即可保证风格一致性（相同 seed 出相同图）
- 首尾帧 prompt 只在视角/位置/状态上不同，角色/光照/风格描述保持完全相同
- FLF2V 的 prompt 只需要描述"从首到尾发生了什么"，不要重复描述画面本身

### 首帧→尾帧差异设计指南

| 想要的画面效果 | 首帧 | 尾帧 | FLF2V prompt |
|---------------|------|------|-------------|
| 缓慢推镜 | 远景城市 | 中景同一城市 | "Slow cinematic push-in. Camera smoothly moves forward..." |
| 物体变化 | 正常咖啡表面 | glitch/冻结咖啡表面 | "Liquid ripples normally, then abruptly freezes. Tiny pixel glitch..." |
| 场景溶解 | 完整建筑 | 破碎消散的建筑 | "Building dissolves like sand, fragments float upward without gravity..." |
| 主角察觉 | 看手机 | 手机乱码，表情变化 | "Map flickers, street names transform to code '0101...', hand tightens..." |
| 空间过渡 | 街道 | 同一个位置的虚空 | "Everything dissolves into data fragments, leaving black void..." |

### 用 FLF2V 做镜头间无缝过渡

这是 FLF2V 相比传统 AI 视频管线最大的优势：

```python
# 镜头N → 镜头N+1 的过渡
# 复用上一镜尾帧作为下一镜首帧
shot_N_end_image = "rr04_end.png"
shot_N+1_start_image = shot_N_end_image  # 复用！

# 过渡 FLF2V 的 prompt 只描述过渡效果
"Scene dissolves through a momentary flash of pixelation, transitioning smoothly to the new scene"
```

**好处**：角色/场景一致性自动保持 — 因为首帧就是上一个镜头的画面。

### 节奏控制公式

```
总时长估算 = Σ(每镜帧数) ÷ 16fps

每镜帧数选择：
- 长镜头（6秒+）= length=97~129
- 标准镜头（4~5秒）= length=65~81  
- 短镜头（3秒）= length=49
- 过渡镜头（1秒）= length=17
```

### 风格锚定

每次生图追加完全相同的风格字符串。写实电影风格示例：

```
# 风格锚定（英文，用于所有 Flux + FLF2V prompt）
cinematic photorealistic style, hyper-detailed skin texture, 
natural pores and skin details, accurate human anatomy, 
movie-grade lighting, soft natural light with realistic shadow transitions, 
shallow depth of field, professional film composition, 
8K ultra HD, cinema lens distortion, 
realistic material reflections, subtle film grain, 
neutral color palette, atmospheric haze

# 负面提示词（通用）
oversaturated, cartoon, anime, illustration, painting, 
3D render, CGI look, plastic skin, smooth skin, stylized, 
deformed hands, distorted face, low quality, blurry, 
jpeg artifacts, text, watermark, signature
```

### 完整例子：Scene → Prompts 映射

从实际项目腐烂现实 Act 1 提取：

| 镜头 | 首帧 | 尾帧 | 视频效果 | 
|------|------|------|---------|
| 城市晨光 | 高空广角城市+晨雾 | 中近景城市+轻轨 | 缓慢推镜，晨光穿透雾气 |
| 街道生机 | 早餐摊+蒸汽（广角） | 早餐摊+大爷看手机（中景） | 横移揭示日常，过于完美 |
| 主角登场 | 窗边侧脸，晨光轮廓 | 喝咖啡，若有所思 | 静态微动，呼吸感 |
| 咖啡 glitch | 液面正常波纹 | 液面冻结+像素 glitch | 正常→静止→像素闪烁 |
| 导航乱码 | 看手机，正常地图 | 手机乱码，握紧 | 地图 flicker→乱码→恢复 |

## Chain FLF2V 生产模式（N 图 → N-1 段无缝视频）

### 适用场景

当你有 N 张按叙事顺序排列的 Flux 图（如 00003→00004→00005→00006→00007→00008），想生成首尾衔接的无缝视频序列时，使用**链式配对**：

```
图1 ──FLF2V──→ 图2 ──FLF2V──→ 图3 ──FLF2V──→ 图4 ...
     Segment 1      Segment 2      Segment 3
```

每张中间图同时是上一段的尾帧 + 下一段的首帧，天然实现连续过渡。

### Chain 总览

| 张数 | 段数 | 示例 |
|------|------|------|
| 6 张 | 5 段 | 00003→04, 04→05, 05→06, 06→07, 07→08 |

### 执行流程

```
Step 1: Flux T2I 按顺序生成 6 张图（每张 prompt 的叙事递进：广角→中景→近景→特写）
Step 2: 在 ComfyUI 中加载 FLF2V 工作流
Step 3: 设置第一对的 首帧/尾帧 LoadImage → 修改视频 prompt → Queue Prompt
Step 4: 等跑完 → 首帧换成上一对的尾帧图 + 尾帧换成下一张图 → 改 prompt → Queue
Step 5: 重复 Step 4 直到全部 N-1 段跑完
Step 6: ffmpeg concat 拼接所有段
```

### 每段 prompt 设计原则

| 段类型 | 首→尾变化类型 | prompt 重点 |
|--------|-------------|------------|
| 推镜/拉镜 | 相同场景，不同距离 | "Slow push-in from wide to medium shot" |
| 场景过渡 | 场景 A→场景 B（不同内容） | "Dissolve/fade through..." 描述过渡特效 |
| 物体变化 | 静止→发光/变形 | "The [object] begins to glow/transform..." |
| 角色动作 | 姿态 A→姿态 B | "Character slowly turns/looks up/emerges..." |
| 情绪变化 | 表情/氛围转变 | "Atmosphere shifts from serene to mysterious..." |

### 与"复用同一图"的区别

| 模式 | 图数量 | 连接方式 | 效果 |
|------|--------|---------|------|
| 链式（本skill） | N 张不同图 | 每张图既是尾帧又是下一段首帧 | 完美无缝，场景递进 |
| 复用同一图 | 1 张图当两段用 | 上一段尾帧 = 下一段首帧（同一张图） | 静止卡顿，适合停顿 |

### 生成后拼接（ffmpeg concat）

在服务器上拼接所有 MP4 段（注意远端 fish shell 的陷阱）：

```bash
# 1. 本地生成 concat 列表（pipe 到 ssh 避免 fish 引号问题）
printf "file '/path/to/video/ComfyUI_00013_.mp4'\nfile '/path/to/video/ComfyUI_00014_.mp4'\n..." | ssh server 'bash -c "cat > /tmp/concat.txt"'

# 2. SSH 执行 ffmpeg
ssh server 'bash -c "ffmpeg -y -f concat -safe 0 -i /tmp/concat.txt -c copy /tmp/output.mp4"'

# 3. 下载（base64 管道绕过 fish greeting）
ssh server 'base64 -w0 /tmp/output.mp4' 2>/dev/null | base64 -d > local_output.mp4
```

## 关键经验

### 1. 首尾帧必须不同
FLF2V 的插值空间来自首帧和尾帧的差异。如果两帧相同，输出接近静态图。
- **正确做法**：用 Flux T2I 生成首尾帧时，故意设计构图差异
  - 首帧 prompt：`"高空广角全景，俯视城市天际线"`
  - 尾帧 prompt：`"低空近景，特定建筑群，仰角"`
- 仅改 noise_seed 不够——prompt 本身要有视角/距离/角度变化

### 2. 参数配置

| 参数 | 非剧烈运镜（4-step Lightning） | 剧烈运镜（20-step Default） |
|------|---------------------|-------------------|
| LoRA | lightx2v_4steps (strength=1) | 无 |
| shift | 5.0 | 8.0 |
| steps | 4 | 20 |
| cfg | 1.0 | 4.0 |
| high_noise step | 0→2 | 0→10 |
| low_noise step | 2→10000 | 10→10000 |
| high leftover_noise | enable | enable |
| low leftover_noise | disable | disable |
| **~每镜耗时 (81帧@640×640)** | **~80-180s** | **~20min (单 A10)** |
| **显存占用** | **~18.5GB (单卡)** | **~18.7GB (单卡)** |

### 3. 时长控制
- 主体镜头：`length=81`（81帧@16fps = 5秒）
- 过渡效果：`length=16`（16帧@16fps = 1秒）

### 4. Prompt 结构

FLF2V 的 prompt 需要同时约束两部分：

```
[场景一致性] 描述两个帧中都有的不变元素
[镜头变化] 描述运镜方式：前推/横移/环绕/下降
[场景变化] 描述两帧之间的场景演变（如果有）
[否定约束] 禁止跳切、相机抖动、画面中出现新元素
```

### 5. 短剧分镜间转场技巧

这是 FLF2V 在短剧中最有价值的用法 — **用首尾帧实现镜头平滑过渡**，天然保持角色和场景一致性。

**核心技巧**：复用上一镜的尾帧作为下一镜的首帧，再加 prompt 引导。

```
Step 1: 镜头A 首帧 → 尾帧（正常 FLF2V）
Step 2: 镜头B 的首帧 = 镜头A 的尾帧（复用同一张图）
        用 prompt 引导场景/视角变化：
        "快速略过变化场景，瞬间变换场景为[新场景描述]"
```

**原理**：模型以同一张图作为"固定锚点"，过渡过程被 prompt 控制为场景切换，而不是内容突变。这样角色外貌、光照风格等自动保持一致。

### 电影过渡效果

FLF2V 能理解以下 cinematic transition 关键词：
- **遮挡过渡**：`"路人从镜头前走过遮挡画面，离开时露出新场景"`
- **裂缝扩散**：`"玻璃反射面裂开，裂缝扩散覆盖全屏，溶解到新场景"`
- **溶解**：`"画面像冰一样融化，露出下方的场景"`
- **推入瞳孔**：`"快速推入瞳孔，转场到下一个画面"`
- **碎片飞过**：`"碎片飞出遮挡镜头，落下时已切入新场景"`

### 6. 完整管线流程 + 性能基准（A10实测）

```
Step 1: Flux T2I 生成首帧（20步，1024×1024）~60s
Step 2: Flux T2I 生成尾帧（不同 prompt + seed）~60s  
Step 3: FLF2V 主体（4-step Lightning ≈ 80s~3min，20-step Default ≈ 20min 在单 A10）
    ↓ 如需过渡到下一镜
Step 4: FLF2V 过渡（4-step, length=16, 1s）~1min
```

**实测数据**（A10 24GB, Wan2.2 14B I2V fp8_scaled）：
| 操作 | 耗时 | 显存 |
|------|------|------|
| Flux T2I 1024×1024, 20步 | ~58-60s | ~16GB |
| FLF2V 640×640, 81帧, 20步 Default | ~20min | ~18.7GB |
| FLF2V 640×640, 81帧, 4步 Lightning | ~80-180s | ~18.5GB |

**注意**：Wan2.2 14B 模型只使用单 GPU（不支持自动多卡并行），单 A10 下 20 步非常慢。

### 7. 模型路径
```
diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors
diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors
loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors
loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors
vae/wan_2.1_vae.safetensors
text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors
```

### 8. ComfyUI API 格式参考 — 已验证通过的工作流

#### ⚠️ 已知坑点

| 坑 | 表现 | 解决 |
|---|------|------|
| **CreateVideo 缺 fps** | 400: `required_input_missing: fps` | GUI 工作流导出的 JSON 可能不带 `fps` 字段，API 提交时必须显式加 `"fps": 16` |
| **img2vid 的 SaveVideo 缺 format/codec** | 400 或输出为空 | 旧 I2V 工作流中 `format` 和 `codec` 值必须用 `"auto"` (COMBO) 而非 `"h264"/"mp4"` 等 |
| **LoadImage 的 image 路径** | 404 找不到文件 | 先用 `POST /upload/image` 上传图片，再引用上传后的文件名 |
| **WanFirstLastFrameToVideo 的 image inputs 在 optional** | 不传时模型退化为纯 conditioning 生成 | `start_image` 和 `end_image` 属于 optional 输入，作为 IMAGE 类型的 link 传入 |
| **FLF2V 输出是 3 个值** | KSampler 连错输入 | 三个 output 分别是 CONDITIONING(positive), CONDITIONING(negative), LATENT，分给两个 KSamplerAdvanced: positive/negative/latent_image |

#### 已验证通过的 Default (20-step) API 工作流结构

```python
wf = {
    # === 模型加载 ===
    "38": {"class_type": "CLIPLoader",
           "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
    "72": {"class_type": "CLIPLoader",  # 第二个 CLIP（FLF 的正负 prompt 需要独立的 CLIP）
           "inputs": {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
    "79": {"class_type": "VAELoader",
           "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
    "76": {"class_type": "UNETLoader",
           "inputs": {"unet_name": "wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"}},
    "77": {"class_type": "UNETLoader",
           "inputs": {"unet_name": "wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors", "weight_dtype": "default"}},
    "73": {"class_type": "ModelSamplingSD3",
           "inputs": {"model": ["76", 0], "shift": 8.0}},
    "74": {"class_type": "ModelSamplingSD3",
           "inputs": {"model": ["77", 0], "shift": 8.0}},

    # === 图片加载（先上传再用文件名）===
    "80": {"class_type": "LoadImage",
           "inputs": {"image": "start_frame.png", "upload": "image"}},
    "89": {"class_type": "LoadImage",
           "inputs": {"image": "end_frame.png", "upload": "image"}},

    # === Prompt 编码 ===
    "90": {"class_type": "CLIPTextEncode",  # Positive prompt
           "inputs": {"text": "[Video prompt here]", "clip": ["72", 0]}},
    "78": {"class_type": "CLIPTextEncode",  # Negative prompt
           "inputs": {"text": "static, still image, no motion, frozen, cartoon, illustration, low quality, blurry",
                      "clip": ["72", 0]}},

    # === 核心 FLF 节点 ===
    "81": {"class_type": "WanFirstLastFrameToVideo", "inputs": {
        "positive": ["90", 0], "negative": ["78", 0], "vae": ["79", 0],
        "start_image": ["80", 0], "end_image": ["89", 0],
        "width": 640, "height": 640, "length": 81, "batch_size": 1
    }},

    # === 高噪采样器 ===
    "84": {"class_type": "KSamplerAdvanced", "inputs": {
        "model": ["73", 0], "add_noise": "enable", "noise_seed": 5001, "steps": 20, "cfg": 4.0,
        "sampler_name": "euler", "scheduler": "simple",
        "positive": ["81", 0], "negative": ["81", 1], "latent_image": ["81", 2],
        "start_at_step": 0, "end_at_step": 10, "return_with_leftover_noise": "enable"
    }},

    # === 低噪采样器 ===
    "87": {"class_type": "KSamplerAdvanced", "inputs": {
        "model": ["74", 0], "add_noise": "disable", "noise_seed": 0, "steps": 20, "cfg": 4.0,
        "sampler_name": "euler", "scheduler": "simple",
        "positive": ["81", 0], "negative": ["81", 1], "latent_image": ["84", 0],
        "start_at_step": 10, "end_at_step": 10000, "return_with_leftover_noise": "disable"
    }},

    # === 解码输出 ===
    "85": {"class_type": "VAEDecode",
           "inputs": {"samples": ["87", 0], "vae": ["79", 0]}},
    "86": {"class_type": "CreateVideo",
           "inputs": {"images": ["85", 0], "fps": 16}},  # ⚠️ fps 是 required！
    "83": {"class_type": "SaveVideo",
           "inputs": {"video": ["86", 0], "filename_prefix": "output",
                      "format": "auto", "codec": "auto"}}
}
```

#### 提交 + 轮询模式

```python
# 1. 提交
resp = requests.post(f"{API}/prompt", json={"prompt": wf}, timeout=15)
pid = resp.json()["prompt_id"]

# 2. 轮询（最多等 900s/15min）
while time.time() - start < 900:
    resp = requests.get(f"{API}/history/{pid}", timeout=15)
    if resp.status_code == 200 and pid in resp.json():
        outputs = resp.json()[pid]["outputs"]
        for node_out in outputs.values():
            for key in ("videos", "files", "gifs"):
                for item in node_out.get(key, []):
                    fname = item["filename"]
                    # 下载: GET /view?filename={fname}&type=output
                    dl = requests.get(f"{API}/view", params={"filename": fname, "type": "output"}, timeout=30) 
    time.sleep(10)

# 3. 上传图片
with open(local_path, 'rb') as f:
    resp = requests.post(f"{API}/upload/image",
        files={'image': (filename, f, 'image/png')}, timeout=30)
uploaded_name = resp.json()["name"]  # 用这个值作为 LoadImage 的 "image" 参数
```

#### Lightning (4-step) 模式差异

只需在 Default 结构基础上做以下改动：
- 模型前加 `LoraLoaderModelOnly` 节点加载 LoRA
- shift 改为 5.0, steps=4, start=0→2/2→10000, cfg=1.0
