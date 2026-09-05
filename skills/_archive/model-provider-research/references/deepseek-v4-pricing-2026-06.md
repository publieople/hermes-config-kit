# DeepSeek V4 Flash — Provider Pricing (2026-06-30)

## Context
DeepSeek announced peak/off-peak pricing on 2026-06-29, effective mid-July with V4正式版.
- Peak: 9:00-12:00, 14:00-18:00 Beijing time = 2x off-peak
- Off-peak: all other hours

## Official DeepSeek

| Model | 缓存命中 | 缓存未命中 | 输出 | 高峰×2 |
|-------|---------|-----------|------|--------|
| V4 Flash | ¥0.02/M | ¥1/M | ¥2/M | ¥4/M |
| V4 Pro | ¥0.025/M | ¥3/M | ¥6/M | ¥12/M |

## Chinese Platforms (CNY, 国内直连)

| Platform | V4 Flash 输出 | Peak? | Notes |
|----------|-------------|-------|-------|
| **SiliconFlow** | ¥2 | No | Best option. API: api.siliconflow.cn/v1 |
| Tencent Cloud | ¥2 | Unknown | 6/3 price cut to match official |
| Alibaba Bailian | ¥2 | Unknown | Savings plans for extra discount |
| Baidu Qianfan | ¥2 (est.) | Unknown | Day-0 V4 support |
| Volcengine | AFP credits | N/A | Package-based, not pay-per-token |

## International (USD, via models.dev)

All prices from models.dev API (2026-06-30). 29 total providers.

Cheapest for V4 Flash:
- Deep Infra: $0.10/$0.20 (¥0.73/¥1.46) — VPN required
- GMI Cloud: $0.11/$0.22 (¥0.80/¥1.61)
- CrofAI: $0.12/$0.21 (¥0.88/¥1.53)
- SiliconFlow: $0.14/$0.28 (¥1.02/¥2.04) — same as domestic pricing

Most providers charge $0.14/$0.28 (official list price).

## Key Resources

- models.dev API: `GET https://models.dev/api/v1/models/deepseek/deepseek-v4-flash`
- DeepSeek official pricing: https://api-docs.deepseek.com/zh-cn/quick_start/pricing
- SiliconFlow pricing: https://siliconflow.cn/zh-cn/models (browser-rendered)
