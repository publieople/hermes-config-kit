---
name: flux2-klein-character-consistency
description: Flux 2 Klein 原生参考图角色一致性生成 — 使用 ReferenceLatent 节点零样本保持角色身份，替代旧有的 prompt engineering 风格锚定方案。适用于 AI 短剧管线中的角色资产生成。
---

# Flux 2 Klein 角色一致性（ReferenceLatent）

## 背景

**不要用 Flux Redux（那是 Flux.1 时代的 adapter）。** 我们的服务器跑的是 **Flux 2 Klein 9B**，架构原生支持多参考图融合，零额外 adapter 下载。

服务器已有：
- ✅ `flux-2-klein-base-9b-fp8.safetensors`（diffusion model）
- ✅ `qwen_3_8b_fp8mixed.safetensors`（text encoder）
- ✅ `flux2-vae.safetensors`（VAE）
- ✅ ComfyUI v0.13.0（原生支持 ReferenceLatent 节点）
- ✅ 内置工作流 `image_flux2_klein_image_edit_9b_distilled.json`

## ⚠️ 关键选型陷阱：CLIPLoader 与 TextEncoder

**这是最容易翻车的地方。** Flux 2 Klein 用 Qwen 3 8B 作为文本编码器（不是标准 Flux 的 CLIP-L + T5），选错加载器/类型会直接炸 `mat1 and mat2 shapes cannot be multiplied`。

### CLIPLoader：必须用非 GGUF 版

| 组件 | 节点 | 选型 | 说明 |
|------|------|------|------|
| CLIP | **`CLIPLoader`**（非 GGUF） | `type="flux2"`, clip_name=`qwen_3_8b_fp8mixed.safetensors` | ✅ 正确 |
| CLIP | `CLIPLoaderGGUF` | `type="flux2"` | ❌ 会炸 `256x4096 vs 2048x1024`（GGUF ops 与 Qwen 不兼容） |
| CLIP | `DualCLIPLoaderGGUF` | `type="flux"` | ❌ 会炸 `256x4096 vs 10240x4096`（找不到 t5xxl key） |

**规律：** `qwen_3_8b_fp8mixed.safetensors` 是 `.safetensors` 格式，必须走非 GGUF 的 `CLIPLoader`。`UnetLoaderGGUF` 只加载 UNet 部分，不影响 CLIP。

### TextEncoder：必须用标准 CLIPTextEncode，不是 CLIPTextEncodeFlux

| 节点 | 输入格式 | Flux 2 Klein 兼容性 | 原因 |
|------|---------|-------------------|------|
| ✅ `CLIPTextEncode` | 单 `text` 字段 | ✅ 正常 | Qwen 是单编码器，不需要 split |
| ❌ `CLIPTextEncodeFlux` | `clip_l` + `t5xxl` | ❌ KeyError: 't5xxl' | 专为 CLIP-L + T5 设计，Qwen tokenize 没有 t5xxl key |

### 为什么 CLIPLoaderGGUF 不行

`ComfyUI-GGUF` 插件的 GGUF ops 会拦截 Linear 层的前向计算，用 `dequantize + matmul` 代替标准计算。但 Qwen 模型的某些层需要 FP16/BF16 前向，GGUF 的 `forward_comfy_cast_weights` 会做输入与权重的矩阵乘法，而 Qwen 的权重格式与 GGUF dequant 后的格式不匹配，导致 shapes 对不上。

**结论：** 只有 UNet 用 `UnetLoaderGGUF`，CLIP 始终用标准 `CLIPLoader`（type="flux2"）。

## 核心概念：ReferenceLatent

`ReferenceLatent` 是 ComfyUI 针对 Flux 2 Klein 的原生参考图像注入节点。

**原理：** 把参考图通过 VAE 编码为 latent，然后将这个 latent 作为 conditioning 的一部分注入 Flux 的生成过程。模型在 cross-attention 层中同时考虑 text prompt 和 reference latent，输出同一身份在新场景中的图像。

**关键节点：**

| 节点 | 用途 | 位置 |
|------|------|------|
| `ReferenceLatent` | 接受 VAE-encoded reference latent，作为 conditioning 注入 | `comfy-core` 内置 |
| `LoadImage` | 加载参考图 | `comfy-core` |
| `VAEEncode` | 把参考图编码为 latent（喂给 ReferenceLatent） | `comfy-core` |
| `ImageScaleToTotalPixels` | 统一分表率（参考图和输出需同一分表率） | `comfy-core` |
| `EmptyFlux2LatentImage` | 创建空 latent（Flux 2 专用） | `comfy-core` |
| `Flux2Scheduler` | Flux 2 专属 scheduler | `comfy-core` |
| `ConditioningZeroOut` | 可选，调节 conditioning 强度 | `comfy-core` |

## 工作流架构

### 关键连接模式

ReferenceLatent 的正确连接法（最容易出错的地方）：

```
CLIPLoader(type="flux2") → CLIPTextEncode → Conditioning ──┐
LoadImage(ref) → VAEEncode(vae) → Latent ──────────────────┼──→ ReferenceLatent
                                                               → 输出的 CONDITIONING 已包含参考图特征
                                                                  → KSampler.positive
```

注意：`VAEEncode` 的 `vae` 输入要连到 `VAELoader` 的输出，ReferenceLatent 并不是自动获取 vae 的。

### 完整管线一览

```
┌─ Model Loaders ──────────────────────────────┐
│ UnetLoaderGGUF("flux-2-klein-9b-Q4_K_S.gguf")│ → MODEL ───┐
│ CLIPLoader("qwen_3_8b_fp8mixed.safetensors",  │ → CLIP ──┐ │
│   type="flux2") -- 非GGUF!                    │          │ │
│ VAELoader("flux2-vae.safetensors")            │ → VAE ─┐ │ │
└───────────────────────────────────────────────┘        │ │ │
                                                         │ │ │
┌─ Reference Image Chain ───────────────────────┐        │ │ │
│ LoadImage(ref) → VAEEncode(vae) → Latent      │        │ │ │
│                                             │        │ │ │
│ CLIPTextEncode(clip, text="...") → Conditioning │ ←────┘ │ │
│                                             │        │   │ │
│ ReferenceLatent(cond=↑, latent=↑)            │        │   │ │
│   → 融合后的 Conditioning                    │        │   │ │
│                                             │        │   │ │
│ FluxKontextMultiReferenceLatentMethod(       │        │   │ │
│   cond=↑, method="uxo/uno")                  │        │   │ │
└───────────────────────────────────────────────┘        │   │
                                                         │   │
┌─ Sampling ──────────────────────────────────┐         │   │
│ EmptyFlux2LatentImage(1024,1024)             │         │   │
│ Flux2Scheduler(steps=4)                      │         │   │
│ KSampler(model, positive, negative,           │ ←───────┘   │
│          latent, scheduler)                  │             │
│ VAEDecode(samples, vae)                      │ ←───────────┘
│ SaveImage                                    │
└───────────────────────────────────────────────┘
```

### 两种 KSampler 方案对比

| 方案 | 节点 | 复杂度 | 推荐度 |
|------|------|--------|--------|
| ✅ 推荐 | `KSampler`（标准） | 低 | 首选 |
| ⚠️ 也可 | `SamplerCustomAdvanced` + `CFGGuider` + `RandomNoise` | 高 | 仅当需要自定义 noise 时 |

**已验证的标准 KSampler 方案（推荐）：**
```
KSampler(model, seed, steps, cfg, sampler_name, scheduler, positive, negative, latent_image, denoise)
- model ← UnetLoaderGGUF
- positive ← FluxKontextMultiReferenceLatentMethod output (含参考latent的conditioning)
- negative ← CLIPTextEncode(text="")
- latent_image ← EmptyFlux2LatentImage
```

### 多参考图（3 张输入，已预置在工作流中）

Node 92 是 ComfyUI 内置的多参考子图包装器，包含 3 个 ReferenceLatent 实例：

```
LoadImage(ref1) → VAEEncode → ReferenceLatent ─┐
LoadImage(ref2) → VAEEncode → ReferenceLatent ├→ 融合 conditioning
LoadImage(ref3) → VAEEncode → ReferenceLatent ─┘
                                                ↓
                                 ...同一生成管线... → SaveImage
```

服务器工作流 `image_flux2_klein_image_edit_9b_distilled.json` 中：
- **Node 75** (UUID: `7b34ab90-...`): 单参考管线
- **Node 92** (UUID: `65c22b29-...`): 多参考管线（接受 `image`, `image_1`, `image_2` 三个输入）
- **Node 9**: 单参考输出 SaveImage
- **Node 94**: 多参考输出 SaveImage

## ⚠️ 模型选择：Base vs Distilled (GGUF)

### 现状

| 模型 | 文件 | 服务器状态 | 下载方式 |
|------|------|-----------|---------|
| **Base 9B FP8** | `flux-2-klein-base-9b-fp8.safetensors` | ✅ 已有 | — |
| **Distilled 9B FP8** | `flux-2-klein-9b-fp8.safetensors` | ❌ Gated，不下载 | |
| **Distilled 9B GGUF Q4_K_S** | `flux-2-klein-9b-Q4_K_S.gguf` | ✅ **已有（5.56GB）** | modelscope unsloth 仓库 |

### 实测对比（2026-05-07 更新）

| 模型 | 步数 | CFG | 分辨率 | 耗时（T2I） | 写实度 | 身份保持 |
|------|------|-----|--------|------------|--------|---------|
| **Base 9B FP8** | 20 | 3.5-4.0 | 1024×1024 | ~90-155s | ⚠️ 中等，AI glossy | ~80% |
| **Distilled 9B GGUF Q4_K_S** | **4** | **1.0** | 1024×1024 | **~17s** | ✅ **显著更好** | ✅ 更佳 |

**用户验证：** base 模型输出偏"美式风格化漫画/AI glossy"，蒸馏模型的写实度明显更好，皮肤质感更接近真实照片。

### 获取蒸馏模型（已验证可用的下载方式）

从 modelscope 的 unsloth 仓库下载 GGUF 版本（非 gated，可直连）：

```bash
# Q4_K_S 版本（5.56GB，推荐）
curl -L -o /data/comfy/ComfyUI/models/diffusion_models/flux-2-klein-9b-Q4_K_S.gguf \
  "https://modelscope.cn/api/v1/models/unsloth/FLUX.2-klein-9B-GGUF/repo?Revision=master&FilePath=flux-2-klein-9b-Q4_K_S.gguf"

# 实测速度 ~21 MB/s，约 4分20秒下完
```

**原理：** modelscope API 返回 302 跳转到阿里云 CDN（`cdn-lfs-cn-1.modelscope.cn`），`curl -L` 自动跟随跳转拿到带有效 auth_key 的下载链接。

### 前置条件：安装 ComfyUI-GGUF 自定义节点

GGUF 模型需要额外节点加载（KJNodes 的 `GGUFLoaderKJ` 依赖 `ComfyUI-GGUF`）：

```bash
cd /data/comfy/ComfyUI/custom_nodes
git clone https://github.com/city96/ComfyUI-GGUF.git
# 重启 ComfyUI
```

重启后节点可用：
- `GGUFLoaderKJ`（来自 KJNodes）— 输出 MODEL，直接替换 UNETLoader
- `UnetLoaderGGUF`（来自 ComfyUI-GGUF）— 替代方案

### GGUF 蒸馏模型 API 工作流

用 `GGUFLoaderKJ` 替换 `UNETLoader`，其余节点保持不变：

```python
wf = {
    "1": {"class_type": "GGUFLoaderKJ", "inputs": {
        "model_name": "flux-2-klein-9b-Q4_K_S.gguf",
        "extra_model_name": "none",
        "dequant_dtype": "default",
        "patch_dtype": "default",
        "patch_on_device": False,
        "attention_override": "none"
    }},
    # ... 其余节点与 base 模型相同 ...
    # 但参数改为：steps=4, cfg=1.0（蒸馏模型专用）
}
```

**关键参数差异：**

| 参数 | Distilled (GGUF) | Base (FP8) |
|------|------------------|------------|
| 步数 | 4 | 20-24 |
| CFG | 1.0-1.5 | 3.5-5.0 |
| scheduler | simple | simple |
| sampler | euler | euler |

### 强化推荐：优先使用蒸馏 GGUF

**Distilled GGUF 应作为首选模型，base 仅作为无 GGUF 插件时的降级方案。**
### 获取蒸馏模型的可能途径

1. 在 HF 上登录账号 → 接受 FLUX Non-Commercial License → 获取 personal access token
2. 用 `HF_TOKEN` 环境变量通过 huggingface_hub 的 `hf_hub_download` 下载
3. 或从其他已下载的机器 scp 过来

### 短期对策

在获得蒸馏模型之前，base 模型是目前唯一可用方案。但必须搭配正确的 prompt 策略（见下文"Prompt 策略"章节），否则输出风格严重漂移。

## API 工作流格式（已验证通过 ✅）

两个工作流脚本均已在服务器上测试通过（A10 23GB, Flux 2 Klein base 9B fp8）。

### 单参考图 API 调用（已验证 ✅ 17s 出图，蒸馏 GGUF KSampler 方案）

**这是推荐方案——标准 KSampler，节点最少，最稳定。**

```python
import requests, time

API = "http://localhost:8188"

def submit_wait(wf, max_wait=300):
    resp = requests.post(f"{API}/prompt", json={"prompt": wf}, timeout=30)
    if resp.status_code != 200:
        print(f"ERROR: {resp.status_code} - {resp.text}")
        return None
    pid = resp.json()["prompt_id"]
    print(f"Prompt ID: {pid}")
    start = time.time()
    while time.time() - start < max_wait:
        resp = requests.get(f"{API}/history/{pid}", timeout=15)
        if resp.status_code == 200 and pid in resp.json():
            outputs = resp.json()[pid].get("outputs", {})
            if outputs:
                print(f"Completed in {time.time() - start:.1f}s")
                return outputs
        time.sleep(2)
    return None

# 参考图已在 ComfyUI/input/ 目录中
REF_IMAGE = "ref_p1.jpg"

wf = {
    # Model Loaders
    "3": {"class_type": "UnetLoaderGGUF",
          "inputs": {"unet_name": "flux-2-klein-9b-Q4_K_S.gguf"}},
    "4": {"class_type": "CLIPLoader",                     # ← 非GGUF！
          "inputs": {"clip_name": "qwen_3_8b_fp8mixed.safetensors",
                     "type": "flux2"}},                    # ← type必须为flux2
    "6": {"class_type": "VAELoader",
          "inputs": {"vae_name": "flux2-vae.safetensors"}},

    # Reference image
    "1": {"class_type": "LoadImage",
          "inputs": {"image": REF_IMAGE}},
    "2": {"class_type": "VAEEncode",
          "inputs": {"pixels": ["1", 0], "vae": ["6", 0]}},

    # Text encoding
    "5": {"class_type": "CLIPTextEncode",                # ← 标准，不是CLIPTextEncodeFlux
          "inputs": {"clip": ["4", 0],
                     "text": "写实摄影风格，与参考图完全相同的人物面部特征。"}},
    "13": {"class_type": "CLIPTextEncode",
           "inputs": {"clip": ["4", 0], "text": ""}},

    # Reference injection
    "7": {"class_type": "ReferenceLatent",
          "inputs": {"conditioning": ["5", 0], "latent": ["2", 0]}},

    # Reference method (控制融合策略)
    "8": {"class_type": "FluxKontextMultiReferenceLatentMethod",
          "inputs": {"conditioning": ["7", 0],
                     "reference_latents_method": "uxo/uno"}},

    # Sampling
    "9": {"class_type": "EmptyFlux2LatentImage",
          "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
    "10": {"class_type": "Flux2Scheduler",
           "inputs": {"steps": 4, "width": 1024, "height": 1024}},
    "11": {"class_type": "KSampler",
           "inputs": {"model": ["3", 0], "seed": 42, "steps": 4, "cfg": 1.0,
                      "sampler_name": "euler", "scheduler": "simple",
                      "positive": ["8", 0], "negative": ["13", 0],
                      "latent_image": ["9", 0], "denoise": 1.0}},
    "12": {"class_type": "VAEDecode",
           "inputs": {"samples": ["11", 0], "vae": ["6", 0]}},
    "14": {"class_type": "SaveImage",
           "inputs": {"images": ["12", 0], "filename_prefix": "flux2_ref_test"}},
}

outputs = submit_wait(wf)
```

**节点连接说明（关键）：**
```
CLIPLoader(type=flux2) ──→ CLIPTextEncode ──→ Conditioning ──┐
LoadImage(ref) ──→ VAEEncode(vae) ──→ Latent ────────────────┤
                                                              ├→ ReferenceLatent
                                                              │   (cond+latent)
                                                              ↓
FluxKontextMultiReferenceLatentMethod(method="uxo/uno")
                                                              ↓
                                                          KSampler.positive
```

### 多参考图 API 调用（链式 ReferenceLatent）

```python
REF1 = "reference_person1.jpg"
REF2 = "reference_person2.jpg"

wf = {
    # Model Loaders
    "3": {"class_type": "UnetLoaderGGUF",
          "inputs": {"unet_name": "flux-2-klein-9b-Q4_K_S.gguf"}},
    "4": {"class_type": "CLIPLoader",
          "inputs": {"clip_name": "qwen_3_8b_fp8mixed.safetensors", "type": "flux2"}},
    "6": {"class_type": "VAELoader",
          "inputs": {"vae_name": "flux2-vae.safetensors"}},
    # Reference images
    "1": {"class_type": "LoadImage", "inputs": {"image": REF1}},
    "2": {"class_type": "LoadImage", "inputs": {"image": REF2}},
    # Text encoding
    "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 0], "text": "[场景描述]"}},
    "13": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 0], "text": ""}},
    # VAE encode references
    "7": {"class_type": "VAEEncode", "inputs": {"pixels": ["1", 0], "vae": ["6", 0]}},
    "8": {"class_type": "VAEEncode", "inputs": {"pixels": ["2", 0], "vae": ["6", 0]}},
    # Chain ReferenceLatent: ref1 → ref2
    "9": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["5", 0], "latent": ["7", 0]}},
    "10": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["9", 0], "latent": ["8", 0]}},
    # Reference method
    "15": {"class_type": "FluxKontextMultiReferenceLatentMethod",
           "inputs": {"conditioning": ["10", 0], "reference_latents_method": "uxo/uno"}},
    # Sampling
    "11": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
    "12": {"class_type": "Flux2Scheduler", "inputs": {"steps": 4, "width": 1024, "height": 1024}},
    "14": {"class_type": "KSampler", "inputs": {"model": ["3", 0], "seed": 42, "steps": 4, "cfg": 1.0,
        "sampler_name": "euler", "scheduler": "simple", "positive": ["15", 0], "negative": ["13", 0],
        "latent_image": ["11", 0], "denoise": 1.0}},
    "16": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["6", 0]}},
    "17": {"class_type": "SaveImage", "inputs": {"images": ["16", 0], "filename_prefix": "flux2_multiref"}},
}
```

**多参考链式注入原理：**
```
Ref 1 → VAEEncode → ReferenceLatent(cond=text_prompt, latent=ref1_latent)
                                                         ↓ (输出融合后的 conditioning)
Ref 2 → VAEEncode → ReferenceLatent(cond=↑, latent=ref2_latent)
                                                         ↓ (进一步融合)
                                                  → CFGGuider.positive
```
链越长，身份特征融合越充分。实测 2 张参考图身份保持 ~90%+（vs 单张 ~80%）。

### 参数速查

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| 模型 | `flux-2-klein-base-9b-fp8.safetensors` | 9B base，质量更优 |
| CLIP | `qwen_3_8b_fp8mixed.safetensors`, type=`flux2` | |
| VAE | `flux2-vae.safetensors` | |
| 分表率 | 1024×1024 | A10 23GB 上稳妥 |
| Steps | 20（base 模型） / 4（distilled 模型） | |
| CFG | 3.5-5.0（base） / 1.0-1.5（distilled） | |
| Sampler | euler | |
| Scheduler | simple | |

## 性能基准（A10 23GB 实测）

### 蒸馏 GGUF 模型（推荐）

| 模式 | 步数 | 分辨率 | 耗时 | 身份保持 | 写实度 |
|------|------|--------|------|---------|--------|
| 单参考 T2I（蒸馏 GGUF, 无ref） | 4步 | 1024×1024 | **~17s** | — | ✅ 好 |
| 单参考（蒸馏 GGUF, 1张图） | 4步 | 1024×1024 | **~17s** | ~85%+ | ✅ 好 |
| 双参考（蒸馏 GGUF, 2张图，链式） | 4步 | 1024×1024 | **~17-20s** | ~90%+ | ✅ 好 |

### Base FP8 模型（降级方案）

| 模式 | 步数 | 分辨率 | 耗时 | 身份保持 | 写实度 |
|------|------|--------|------|---------|--------|
| 单参考 | 20步 | 1024×1024 | **~90-155s** | ~80% | ⚠️ 中等（AI glossy） |
| 双参考 | 20步 | 1024×1024 | **~90-155s** | ~90%+ | ⚠️ 中等（AI glossy） |
| T2I（无ref） | 20步 | 1024×1024 | **~90s** | — | ⚠️ 中等 |

**蒸馏 GGUF（Q4_K_S）vs Base FP8 差距显著：**
- 速度：27s vs 155s（快 5.7 倍）
- 写实度：蒸馏明显优于 base（用户验证过）
- 身份保持：蒸馏默认就比 base 好

**身份保持规律：**
- 1张参考：面部结构基本一致，但发型、配饰颜色等细节可能漂移
- 2张参考：面部特征更稳定（鼻型、眼距、发际线），发型保持更好
- 3+张参考：理论上更强，但 3 张以上的边际收益递减
- **优先使用蒸馏 GGUF 模型，base 仅在无 GGUF 插件时降级使用**

## 参考图选择策略

| 参考图类型 | 效果 | 说明 |
|-----------|------|------|
| 单张正面 | ~80% | 够用，但发型/细节可能漂移 |
| 正面+侧面/全身 | ~90%+ | **推荐**，模型学到生物特征 vs 可变特征的区分 |
| 同一场景多角度 | ~85% | 角度信息丰富，但场景绑定强 |
| 不同场景同一人 | **~90%+** | 最佳，模型自然会学到"脸不变，环境可变" |

## ⚠️ 实测教训：Prompt 必须显式约束写实风格（否则画风漂移）

2026-05-07 实测教训：参考图是真实照片（人像+室内自拍），输出变成了美式风格化 AI 图。

**根因：** base 模型本身写实度不如蒸馏版 + prompt 未明确约束风格。
**对策：** prompt 中必须显式声明"写实摄影""真实照片质感""没有任何绘画或漫画风格"。

### 正确的 prompt 策略

```python
# ✅ 正确（中文写实叙述句）
text = "写实摄影风格，与参考图完全相同的人物面部特征、皮肤质感。该年轻男性穿着白色短袖POLO衫，站在现代大学校园广场上，自然日光，真实皮肤纹理和毛孔细节，专业人像摄影，浅景深，真实照片质感，没有任何绘画或漫画风格"

# ❌ 错误（英文标签堆砌，无风格约束 → 画风漂移成美式漫画）
text = "A confident young man in white polo, university campus, professional photography, high quality, 8K"
```

### 原则

1. **场景细节靠 prompt，长相特征靠参考图**——不要在 prompt 里重复描述长相
2. **但必须显式约束视觉风格**——写实照片就写"写实摄影风格，真实照片质感，没有任何绘画或漫画风格"
3. **用自然语言而非标签**——Flux 2 Klein 用 Qwen 3 8B 编码器，擅长叙述性文本
4. **中文比英文效果好**——Qwen 编码器对中文理解更好

## Prompt 策略

```python
# ✅ 正确：用叙述性语言描述场景
text = "A medium shot of the same man from the reference image, now sitting in a dimly lit cyberpunk bar, wearing a worn leather jacket, neon lights reflecting off his face, cinematic moody lighting, photorealistic, 8K"

# ❌ 错误：用标签堆砌（适合 SD 但不适合 Flux 2）
text = "man, sitting, bar, cyberpunk, leather jacket, neon light, cinematic, photorealistic"
```

**关键原则：**
- 保留角色身份的 prompt 语言不要过于详细——身份已经在参考图里了
- prompt 专注描述 **新场景** 而非角色长相
- 如果要改变服装，在 prompt 里明确说
- 如果要保持服装不变，写 "wearing the same outfit as in the reference image"

## 与旧方案的对比

| 对比 | 旧方法（prompt 锚定） | ReferenceLatent（新方法） |
|------|---------------------|--------------------------|
| 身份保持方式 | 每次写 "oval face, black hair, blue eyes..." | 参考图 latent 注入 |
| 一致性 | 50-70%（描述永远不够精确） | 80-95%（潜空间直接对齐） |
| 工作量 | 每张图都要写完整特征 | 一张参考图+场景描述 |
| 需要额外模型? | 否 | 否（Flux 2 Klein 原生） |
| 支撑多角度? | 很难（文字描述转角度不准） | 好（参考图提供多视角锚定） |
| 服装换装? | 改文字 | 改文字 + 参考图融合 |

## 与 Wan2.2 管线集成

**角色一致性→视频短片：**

```
角色设计(1张参考图) → Flux2多参考融合 → 多角度/多场景角色图集
                                              ↓
                                    每张图作为 Wan2.2 I2V 的输入
                                              ↓
                                    或作为 FLF2V 的首帧/尾帧
```

**最佳实践：**
1. 为每个角色准备 1-3 张高质量参考图（正面/半侧/全身）
2. 用 ReferenceLatent 在不同场景 prompt 下生成同一角色
3. 把生出的图喂给 Wan2.2 I2V（单图动画）或 FLF2V（首尾帧过渡）
4. 全部生成完后，角色身份自然一致——不需要额外的视频特征对齐

## ⚠️ 已知限制：1024×1024 系统性生成失败

**2026-05-11 验证：** 该模型在 1024×1024 分辨率下存在系统性缺陷——所有变体（base FP8、蒸馏 GGUF、官方 SamplerCustomAdvanced 工作流、简化 KSampler）均只有顶部 5-15% 渲染成功，其余为纯灰色区域。即使在 640×640 下底部仍有 45-50% 灰色。

**对策：** 
1. 对于需要完整 1024×1024 高质量动漫风格图片的场景，使用 MiaoMiao Harem SDXL 模型（`CheckpointLoaderSimple` 加载，30步, cfg=4, euler, normal）
2. Flux 2 Klein 仅适用于可接受底部裁剪的场景
3. 参考 `comfyui-api` skill 中的详细分析

## 已知限制

| 限制 | 说明 |
|------|------|
| 参考图质量敏感 | 参考图质量差 → 生成结果差。首先生一张高质量的 Flux 2 Klein T2I 作为参考 |
| 多参考融合权重不可调 | 目前 ComfyUI 原生 ReferenceLatent 没有显式权重参数，链式融合是平均的 |
| 不支持分参考层控制 | 不能指定"图1保持脸，图2保持衣服"——这是更高级的 Identity Feature Transfer 能力 |
| 分表率限制 | 生成和参考图分表率需一致（直接设置 EmptyFlux2LatentImage 的 width/height） |
| 4卡不利用 | Flux 2 Klein 单卡跑，A10 23GB 上 1024×1024 无压力 |
| **GGUF 模型需要额外插件** | GGUFLoaderKJ 需要同时安装 `ComfyUI-GGUF`（city96）和 `ComfyUI-KJNodes`。已在服务器上完成安装 |
| 多参考比单参考略慢 | 链式 ReferenceLatent 增加 conditioning 融合开销，但蒸馏模型下差异不大（27s→30s） |
| **画风漂移风险** | Prompt 不够具体时，输出可能偏离参考图的写实风格。必须在 prompt 中明确要求"写实摄影""真实照片质感""没有任何绘画或漫画风格" |
| **单参考发型/细节易漂移** | 一张参考图时，发型（竖碎发→偏分）、配饰颜色（粉色挂绳→红色）可能变化。双参考大幅缓解此问题 |
| **Base 模型不推荐** | 与蒸馏 GGUF 相比，base 模型质量差距明显。非必要不使用 |

## 进阶方向

- **ByteDanceImageReferenceNode**（服务器上已有）— 可能对应 InfiniteYou 的身份保持
- **ComfyUI-Flux2Klein-Enhancer**（未安装）— 社区增强，提供 Identity Feature Transfer，可精确控制身份保持 vs prompt edit 的平衡
- **多角色同框**：需要分别生成每个角色的 reference latent，然后 merging——目前原生不支持，需要社区节点

## 触发器

当用户提到以下内容时加载此 skill：
- Flux 2 Klein 参考图/角色一致性/多参考
- ReferenceLatent 节点
- 要生成同一个角色在不同场景中的图
- "保持角色一致"、"不 LoRA 保持角色"、"参考图生角色"
- 与 Wan2.2 管线配合的角色生成
- "替代 style anchoring"、"角色资产生成"、"character sheet"
