---
name: bci-device-selection
description: Compare and select EEG, VR, and combined BCI hardware — international and domestic (国产) options for projects, competitions, and research
category: mlops
---

# BCI Device Selection

## When to Load
- User is evaluating EEG, VR, or combined BCI hardware for a project
- User needs to compare devices (channels, price, VR compatibility, signal quality)
- User wants domestic (中国) alternatives for neurotech equipment
- User asks "what hardware should I use for..." in the context of brain-computer interfaces

## Process

### 1. Understand the Use Case
- Competition project? Research lab? Consumer prototype?
- What matters most: budget, signal quality, VR integration, developer SDK, domestic availability?
- Existing code/device constraints (e.g., already have TGAM protocol support)

### 2. Search Strategy
- Search **both** English and Chinese queries for full coverage
- Key Chinese terms: 脑电设备, 脑机接口, 干电极, 消费级EEG, VR脑电
- Key English terms: EEG headset VR compatible, BCI gaming, OpenBCI, NeuroSky
- Look for: academic papers (PMC), product pages, GitHub projects, Bilibili demos, YouTube demos

### 3. Evaluate by Axis
Always compare across these dimensions:
- **Channels**: 1 (consumer) → 8-16 (prosumer) → 32-64+ (research)
- **VR integration**: Native integrated (Galea, DSI-VR300) → Retrofit (cap under HMD) → Separate
- **Signal quality**: Consumer grade → Professional → Research grade
- **Price**: ¥100-500 (modules) → ¥2,000-5,000 (consumer) → ¥5,000-15,000 (prosumer) → ¥20,000+ (research)
- **China availability**: 淘宝/JD direct → Official website → Agent only → Import only
- **SDK/API**: Python SDK, Unity/Unreal plugin, raw data access, open source

### 4. Prioritize Domestic (国产) When Relevant
For users in China (especially student competitions):
- **VR**: Pico 4/Ultra (字节跳动) — native Chinese support, developer SDK
- **EEG entry**: TGAM modules on 淘宝 (¥150-400) — same chip as NeuroSky
- **EEG mid**: OpenBCI Cyton via 淘宝代理 (¥5,000-7,000)
- **EEG pro**: 博睿康 NeuSen W / DSI-24 — Tsinghua team, WRC official supplier
- **EEG consumer**: 强脑科技 BrainCo — JD available, consumer wearables

### 5. Find Demos
- Bilibili: Search for vendor official accounts (博睿康: UID 1915780602)
- YouTube: DSI-VR300 demo, OpenBCI Galea videos
- Product pages: Look for galleries, spec sheets, application scenarios
- Conference footage: 世界机器人大赛 (WRC) has BCI competition videos

### 6. Present Options
Always show a comparison table. For each option include:
- Total cost (EEG + VR + accessories)
- Channel count and signal quality
- VR integration level (native vs retrofit)
- Key advantage and key limitation
- Purchase channel and availability

## Pitfalls
- **Physical fit is the #1 hidden problem**: EEG cap/headband + VR HMD both need head space. Native integrated solutions (Galea, DSI-VR300) solve this; retrofit setups need 3D-printed brackets or careful testing.
- **博睿康 prices are not public**: Must contact sales (400-080-0672, info@neuracle.cn). Mention "教育/竞赛项目" for possible discounts.
- **Single-channel EEG (NeuroSky/BrainCo) is very limited**: Fine for attention/meditation metrics, inadequate for SSVEP, P300, or motor imagery BCI paradigms.
- **Domestic EEG ≠ always cheaper**: 博睿康 research-grade gear can cost ¥20,000-50,000+. Budget accordingly.

## References
- `references/vr-eeg-hardware-landscape.md` — Full vendor/product comparison tables from 2026 research
