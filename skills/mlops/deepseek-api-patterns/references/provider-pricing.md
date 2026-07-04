# DeepSeek V4 Provider Pricing (2026-06)

Last verified: 2026-06-30. Pricing changes fast — re-verify on provider sites before decisions.

## DeepSeek Official (api.deepseek.com)

From 2026-07 (mid-July): peak/off-peak pricing on V4正式版.

| Model | Period | Cache Hit | Cache Miss | Output |
|-------|--------|-----------|------------|--------|
| V4 Flash | Off-peak | ¥0.02 | ¥1 | ¥2 |
| V4 Flash | **Peak** | **¥0.04** | **¥2** | **¥4** |
| V4 Pro | Off-peak | ¥0.025 | ¥3 | ¥6 |
| V4 Pro | **Peak** | **¥0.05** | **¥6** | **¥12** |

Peak hours: 9:00-12:00, 14:00-18:00 Beijing time (Mon-Fri assumed).

## 硅基流动 (api.siliconflow.cn/v1)

Flat pricing, **NO peak/off-peak distinction** (verified on siliconflow.cn/pricing 2026-06-30).

| Model | Input | Output | Cache |
|-------|-------|--------|-------|
| V4 Flash | ¥1.00 | ¥2.00 | ¥0.02 |
| V4 Pro | ¥3.00 | ¥6.00 | ¥0.03 |

API: OpenAI-compatible, `https://api.siliconflow.cn/v1`. New users get free credits.

**Result: SiliconFlow = DeepSeek official off-peak price, 50% cheaper during peak hours.**

## 阿里云百炼 (bailian.console.aliyun.com)

Same price as DeepSeek official. Savings plans available for additional discount (up to 4.5折). Unclear whether they'll adopt peak pricing.

## 腾讯云

Price-matched to official as of 2026-06-02. Unclear whether peak pricing applies.

## Pitfall: Don't Trust Search Engines for Pricing

Web search returned stale V3.1 pricing for SiliconFlow (¥4/¥12), outdated model names, and missed the peak-pricing announcement. **Always use browser tools to check the actual provider pricing page** — not web_search or web_extract summaries.
