# VR + EEG 硬件全景对比 (2026.06)

## 国际方案

### EEG 设备

| 产品 | 通道 | 价格 | 信号质量 | VR兼容 | 开源 | 中国购买 |
|---|---|---|---|---|---|---|
| NeuroSky MindWave 2 | 1 (TGAM) | ~$100 | 消费级 | 头带式，与VR物理冲突 | 部分 | 淘宝有售 |
| Emotiv EPOC X | 14 | ~$849 | 专业级 | 独立佩戴，有Unity插件 | ❌ | 官网直邮 |
| Emotiv Insight | 5 | ~$499 | 专业级 | 同上 | ❌ | 官网直邮 |
| Muse S / Muse 2 | 4-7 | ~$250 | 消费级 | 头带式，有VR实验项目 | ❌ | 淘宝有售 |
| OpenBCI Cyton 8ch | 8 | ~$999 | 研究级 | 开源，MIT Hack验证VR流 | ✅ | 淘宝代理 |
| OpenBCI Cyton 16ch | 16 | ~$1,999 | 研究级 | 同上 | ✅ | 淘宝代理 |
| OpenBCI Galea | EEG+EMG+EDA+PPG+眼动 | ~$22,500 | 研究级 | **原生集成Varjo Aero** | ✅ | 极困难 |
| DSI-VR300 | 7ch干电极 | ~$5,000-10,000 | 研究级 | **原生集成Quest/Vive** | ❌ | neurospec代理 |

### VR 头显

| 产品 | 价格 | 特点 |
|---|---|---|
| Meta Quest 3 | ~$500 | 生态最丰富 |
| Pico 4 | ¥2,499 | 国内首选 |
| Pico 4 Ultra | ¥3,999 | 最新款，MR |
| HTC Vive Pro | ~$800 | 兼容DSI-VR300 |
| Varjo Aero | ~$2,000 | 配Galea，高端 |

---

## 国产方案

### EEG 设备

| 产品 | 通道 | 价格 | 信号质量 | VR兼容 | SDK | 购买渠道 |
|---|---|---|---|---|---|---|
| **TGAM模块** | 1 | ¥150-400 | 消费级 | 需自研支架 | 蓝牙串口，你的代码已支持 | 淘宝 |
| **强脑科技 Focus** | 1-3 | ¥2,500-3,500 | 消费级 | 头环式，性能有限 | 有SDK | 京东 |
| **OpenBCI Cyton 8ch** | 8 | ¥5,000-7,000 | 研究级 | 开源灵活 | Python/Arduino | 淘宝代理(uoimy) |
| **博睿康 NeuSen W 8/16** | 8-64 | ¥20,000-50,000+ | **研究级** | **有专门VR方案** | 联系销售 | 官网询价 |
| **博睿康 DSI-24** | 24干电极 | ¥15,000-30,000 | 研究级 | 干电极帽，5分钟佩戴 | 联系销售 | 官网询价 |

### 国产VR头显

| 产品 | 价格 | 特点 |
|---|---|---|
| Pico 4 | ¥2,499 | 性价比之王，国内SDK完善 |
| Pico 4 Ultra | ¥3,999 | 最新MR一体机 |
| 大朋 P2 | ¥1,999 | 偏B端 |
| 小派 Crystal Light | ¥5,599 | 高端PCVR |

---

## 推荐组合

### 国赛场景（按预算排序）

| 排名 | 方案 | EEG | VR | 总价 | 优势 |
|---|---|---|---|---|---|
| 🥇 | 博睿康 Pro | NeuSen W 8ch | Pico 4 | ¥22,000-52,000 | 清华团队，WRC指定，VR原生方案 |
| 🥈 | 开源中端 | OpenBCI Cyton 8ch | Pico 4 | ¥8,000-10,000 | 完全开源，MIT验证，Python直连 |
| 🥉 | 极低成本 | TGAM模块 | Pico 4 | ¥2,700 | 代码已有TGAM协议，快速原型 |

---

## 演示资源

### 博睿康 B站官方号
- UID: 1915780602
- https://space.bilibili.com/1915780602/video
- 20+ 演示视频，包括：
  - 脑控无人机 | 脑电+VR（最直接相关）⭐
  - 脑控接电话 | 脑电+AR
  - 脑控机械臂 | SSVEP
  - 脑控打字 | P300 (WRC现场)
  - 运动脑控打字 | SSVEP
  - 多人脑同步、脑控机器人
  - 情绪控制情绪灯

### YouTube
- DSI-VR300 Demo: https://www.youtube.com/watch?v=axOosqretGI
- OpenBCI Galea: https://www.youtube.com/watch?v=uhLxggasiqE

### 学术案例
- **NeuroGaze** (Frontiers 2025): Meta Quest Pro + Emotiv EPOC X, EEG+眼动, 20人实验
- **MIT Reality Hack 2025**: OpenBCI Galea + Cyton, 3个获奖项目
- **CoFeel** (MIT Hack): OpenBCI Cyton → Quest 无线EEG流式传输
- **VR-BCI手功能康复** (PMC 2024): 博睿康设备, 多感官刺激康复

---

## 联系方式

| 厂商 | 电话 | 邮箱 | 官网 |
|---|---|---|---|
| 博睿康 | 400-080-0672 | info@neuracle.cn | neuracle.cn |
| 强脑科技 | — | — | brainco.cn |
| Pico 开发者 | — | — | developer-cn.picoxr.com |
| OpenBCI代理(uoimy) | — | — | uoimy.com |
