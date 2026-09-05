---
name: model-provider-research
description: Compare LLM API platform pricing and select providers. Use when shopping for model API platforms, comparing prices, or finding cheaper alternatives to a current provider.
---

# Model Provider Research

## Trigger

User is comparing API platform pricing, looking for cheaper model providers, or evaluating alternatives to their current setup.

## Workflow

### 1. Check official pricing first
Go to the model's official pricing page (e.g., `api-docs.deepseek.com/quick_start/pricing`). This is ground truth — everything else derives from it.

### 2. Search for recent news
API pricing changes fast. Search for "model name + 涨价/降价/price + current month" before trusting any cached data. Price changes often hit news before docs update.

### 3. Check aggregators for provider discovery
- **models.dev** (`models.dev/api/v1/models/{provider}/{model-id}`) — comprehensive, open-source, lists all providers with prices. Best for discovering who even hosts this model.
- **OpenRouter** (`openrouter.ai/models?q=model`) — shows providers, routing, and real-time throughput/latency. Good for cross-referencing.

### 4. Visit platform websites
Aggregator data can be stale or missing region-specific pricing (peak/off-peak, CNY vs USD). For the shortlisted platforms, visit their pricing page directly. Browser is more reliable than web_search for pricing pages — many are JS-rendered.

### 5. Convert and compare
Account for:
- Peak/off-peak pricing (Chinese platforms increasingly use time-based pricing)
- Currency (CNY vs USD, use ~7.3 rate)
- Network accessibility (does the platform need a VPN from China?)
- Payment methods (Alipay/WeChat vs credit card/crypto)
- Caching discounts (DeepSeek official gives 90% cache discount, resellers often don't)

### 6. Check subscription/token plans (when user asks about "plan" or "订阅")
API pay-as-you-go is cheapest for cheap models (V4 Flash, Groq). Subscription plans beat API only when:
- User wants **better models** (Claude Opus, GPT-5.5) at high enough volume for breakeven
- User owns a plan already (yearly/annual) — check if they're paying for something unused
- User wants multi-model access under one key

Reference file: `references/coding-plans-and-subscriptions-2026-07.md`

### 7. For plan owners, ask "are you using your existing plan?"
Many users have purchased plans and forgotten. Always check what they already own before recommending new purchases. A plan they already paid for is always cheaper than buying anything new.

### 8. End by asking "use any of these?"

After presenting options, ask the user which one they want to try. They often own plans they haven't activated or forgot about. Pushing usage > pushing more research.

See `references/user-existing-plans-and-preferences.md` for this user's specific setup.

## Pitfalls

- **Search engines lag on pricing.** A model can go from "permanent 75% off" to "peak pricing 2x" in 24 hours. Always verify on platform websites.
- **Older model pricing ≠ current model pricing.** SiliconFlow V3.1 was ¥4/¥12, V4 is ¥1/¥2. Don't mix generations.
- **Aggregator prices are list prices.** They don't reflect peak/off-peak, regional discounts, or promo periods.
- **Free tiers matter.** SiliconFlow has free 9B models; OpenRouter has free models. Check before paying.
