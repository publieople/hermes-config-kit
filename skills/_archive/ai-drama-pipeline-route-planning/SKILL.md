---
name: ai-drama-pipeline-route-planning
description: AI漫剧/短剧管线选型评估 — 当用户想切换风格（写实→动漫/2D/3D）、评估生产路线、或不确定该走哪条管线时，通过系统性的资产盘点→选项调研→权衡对比→推荐，辅助决策。
---

# AI 漫剧/短剧管线选型评估

## 什么时候用

- 用户说"换个风格试试"、"动漫风/2D风/3D风能搞吗"
- 用户对当前管线质量不满，想评估替代方案
- 用户问"Flux和SDXL怎么选"、"走哪条路"
- 新项目启动，需要决定管线架构
- 用户说"给我一个方案/计划"（指整体方案而非执行细节）
- 服务器引入了新模型，需要评估是否纳入管线

## 核心方法：三段式评估

```
Step 1: 资产盘点 (Survey)  →  手里有什么，缺什么
Step 2: 路线调研 (Research) →  各方案信息搜集
Step 3: 权衡推荐 (Recommend) →  结构化的多路径对比
```

---

## Step 1: 资产盘点 — 摸清家底

### 1.1 模型清单

```bash
# 基础查一遍
ssh -p 35043 po@3722d01e5a6f.ofalias.com "
echo '===DIFFUSION_MODELS===WAIT' && ls /data/comfy/ComfyUI/models/diffusion_models/
echo '===CHECKPOINTS===WAIT' && ls /data/comfy/ComfyUI/models/checkpoints/
echo '===LORAS===WAIT' && ls /data/comfy/ComfyUI/models/loras/
echo '===CLIP===WAIT' && ls /data/comfy/ComfyUI/models/clip/
echo '===CLIP_VISION===WAIT' && ls /data/comfy/ComfyUI/models/clip_vision/
echo '===VAE===WAIT' && ls /data/comfy/ComfyUI/models/vae/
echo '===CONTROLNET===WAIT' && ls /data/comfy/ComfyUI/models/controlnet/ 2>/dev/null
echo '===STYLE_MODELS===WAIT' && ls /data/comfy/ComfyUI/models/style_models/ 2>/dev/null
echo '===UPSCALE===WAIT' && ls /data/comfy/ComfyUI/models/upscale_models/ 2>/dev/null
"
```

### 1.2 GPU/资源状态

```bash
ssh -p 35043 po@3722d01e5a6f.ofalias.com "
nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv,noheader,nounits
df -h /data/comfy/
"
```

### 1.3 已知工作流

```bash
ssh -p 35043 po@3722d01e5a6f.ofalias.com "ls /data/comfy/ComfyUI/user/default/workflows/"
```

### 1.4 识别模型类型

| 模型文件位置 | 对应的加载方式 | 说明 |
|---|---|---|
| `diffusion_models/` | `UNETLoader` | Flux/Flux distill/SD3 等 |
| `checkpoints/` | `CheckpointLoaderSimple` | SDXL/Pony/Illustrious/NoobAI 等 |
| `checkpoints/WAN/` | `CheckpointLoaderSimple` | Wan All-in-One 合并模型 |

**快速判断模型架构：**
- 文件名含 `flux` + 在 `diffusion_models` → Flux 系
- 文件名含 `xl` / `pony` / `animagine` / `illustrious` / `noobai` + 在 `checkpoints` → SDXL 系
- 文件名含 `wan` + 在 `diffusion_models` → Wan 系（video）
- 文件名含 `ltx` → LTX Video 系
- 文件名含 `qwen` → Qwen 图像编辑
- 文件名含 `hunyuan` / `3d` → Hunyuan 3D
- 文件名含 `z_image_turbo` → Z Image Turbo (SD3 架构, 快速)

**检查未知模型：**
```bash
# 看文件元数据中的 CLIP 结构判断架构
ssh -p 35043 po@3722d01e5a6f.ofalias.com "head -c 4096 /data/comfy/ComfyUI/models/checkpoints/some-model.safetensors | strings | grep -i 'text_model\|clip_g\|open_clip' | head -5"
```
- CLIP L (`text_model.encoder`) → SDXL
- CLIP G (`clip_g`) → SDXL 有双编码器
- Qwen 格式 → Flux 系

---

## Step 2: 路线调研 — 搜集选项信息

### 2.1 核心决策维度

每条路线从以下维度评估：

| 维度 | 问什么 |
|------|--------|
| **风格准确度** | 能否达到用户期望的画风？ |
| **角色一致性** | 用什么方案？Zero-shot(ReferenceLatent/IP-Adapter) or LoRA? |
| **视频兼容性** | Wan FLF2V/I2V 能直接用吗？需要改动吗？ |
| **上手成本** | 需要下载多少新模型？新 workflow？ |
| **生成速度** | 每镜耗时 vs 用户耐心 |
| **生态扩展性** | LoRA 资源丰富吗？社区支持如何？ |
| **可用性** | 模型已经在服务器上吗？缺什么依赖？ |

### 2.2 常见路线速查

#### 路线 A: Flux 纯 Prompt 风格
- 适合：快速原型 / 试风格方向
- 模型：`flux-2-klein-base-9b-fp8.safetensors`（已有）
- 角色一致性：ReferenceLatent ✅（已验证零样本保持）
- 视频：Wan FLF2V 直接可用
- 新增下载：0
- 优点：即刻启动，管线零改动
- 局限：Flux 骨子里偏写实，"动漫味"靠 prompt 硬拉，上限有限

#### 路线 B: Flux + 风格 LoRA
- 适合：高质量生产，性价比最优
- 模型：Flux 2 Klein + 风格 LoRA（~100MB）
- 角色一致性：ReferenceLatent ✅
- 视频：Wan FLF2V 直接可用
- 新增下载：1 个 LoRA
- 优点：Flux 质量打底 + 风格精准控制
- LoRA 来源：Civitai、HuggingFace（搜索 "flux anime lora" / "flux cel shade"）

#### 路线 C: SDXL 纯正二次元（Pony/Illustrious/NoobAI/MiaoMiao Harem）
- 适合：追求手绘/动画质感
- 模型：SDXL 系 checkpoint（`miaomiao-harem.safetensors` 已在服务器！6.5GB）
- 角色一致性：IP-Adapter / Reference Only（需设置）
- 视频：Wan FLF2V 同样可用（风格不敏感）
- 新增下载：SDXL CLIP ~4.5GB（`clip_l.safetensors` + `clip_g.safetensors` 或 SDXL 双编码器合并文件）
- 优点：真正"画出来"的动漫质感，Civitai 上巨量 LoRA 生态
- 局限：无 ReferenceLatent（Flux 独占），需搭新 workflow，生图比 Flux 慢

#### 路线 D: Wan Rapid AIO T2V 直接出视频
- 适合：快速出镜头，不追求精细控制
- 模型：`WAN/wan2.2-rapid-mega-aio-v1.safetensors`（已有！24.3GB）
- 角色一致性：无（纯文本→视频，需配参考图控制）
- 新增下载：0
- 优点：5min/镜快出，单模型省心
- 局限：512×512/640×640，质量不如 Flux+FLF2V

### 2.3 调研新模型的流程

当评估一个用户提到但不确定的模型时：

```python
# 信息搜集优先级
1. web_search("模型名 site:civitai.com")  # 社区评价 + 示例图
2. web_search("模型名 ComfyUI workflow")  # 工作流参考
3. web_search("模型名 架构 参数")          # 技术细节
4. 查看 ComfyUI object_info 确认节点兼容性
```

---

## Step 3: 结构化对比与推荐

### 3.1 对比表模板

| | 路线 A (纯Prompt) | 路线 B (Flux+LoRA) | 路线 C (SDXL动漫) | 路线 D (Wan T2V) |
|---|---|---|---|---|
| 风格准确度 | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 角色一致性 | ✅ 最强 | ✅ 最强 | ⚠️ IP-Adapter | ❌ 无 |
| 视频管线改动 | 0 | 0 | 0 (Wan不受风格影响) | 全换 |
| 新增下载 | 0 | ~100MB | ~4.5GB (CLIP) | 0 |
| 生图速度 | 快 | 快 | 中 | 最快 |
| 生态扩展 | — | 中等 | Civitai海量 | 有限 |
| 启动时间 | 0 | 5min | 30-60min | 0 |

### 3.2 推荐逻辑（按优先级）

```
适用场景 → 推荐路线
─────────────────────
快速试方向、调故事节奏  → 路线 A
追求质量+效率最优解     → 路线 B  🏆（通常最佳）
要真正的"手绘动漫质感"  → 路线 C
不苛求角色、要快速出片  → 路线 D
```

### 3.3 给用户的呈现结构

```
1. 资产盘点结果（手上有啥）
2. N 条可选路线（每条写清：模型、一致性方案、视频兼容性、新增下载量）
3. 对比表（视觉化权衡）
4. 我的推荐 + 理由
5. 下一步执行步骤
```

---

## Step 4: 执行计划模板

无论选哪条路，下一步通常遵循：

```
前置: 先训角色LoRA（如果需要）→ 批量生成所有分镜 → FLF2V动态化 → TTS → 合成
```

具体步骤根据路线调整：
- **路线 B 示例**: 下载LoRA → 用Flux+ReferenceLatent+LoRA批量出8-10张测试图 → 审核 → 批量全镜 → FLF2V → 后期
- **路线 C 示例**: 下载SDXL CLIP → 搭建SDXL T2I workflow → 装IP-Adapter → 测试角色一致性 → 批量全镜 → FLF2V → 后期

---

## 已知的服务器模型目录（2026-05 状态）

参见 `comfyui-api` skill 的"可用模型"和"Diffusion Models"章节获取完整清单。

**关键资产备忘：**
- Flux 2 Klein (9B fp8) ✅ — 主力文生图
- MiaoMiao Harem (6.5GB, SDXL Illustrious) ✅ — 动漫模型已下载
- Wan2.2 I2V/FLF2V 双模型 ✅ — 视频管线
- Wan2.2 Rapid All-in-One ✅ — 快速视频（checkpoints/WAN/）
- SkyReels-V3 R2V ✅ — 参考图生视频
- SDXL CLIP 模型 ❌ — 缺失，使用 MiaoMiao Harem 前需下载
