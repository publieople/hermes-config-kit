# User's Existing Plans & Preferences
Last updated: 2026-07-04

## Owned Plans

### MiniMax Token Plan Plus (年度)
- **Status:** Paid but effectively unused
- **Cost:** Already paid (~¥200/year), expires at unknown date
- **Models available:** M3 (flagship), M2.7, M2 (all under same quota)
- **Quota:** ~1.7B tokens/month, user uses ~150M on DeepSeek — plenty of room
- **API:** OpenAI-compatible at `https://api.minimaxi.com/v1` (China), key from `mmx auth`

### Active Setup
- **Default model:** DeepSeek V4 Flash ($0.14/$0.28 per 1M tokens)
- **Monthly spend:** ~¥260 ($36)
- **Hermes provider:** `deepseek` (direct)

## Preferences

1. **"Plan 比按量划算"** — even when math says pay-as-you-go is cheaper, default to recommending subscription/plan options. The user prefers fixed-cost predictability.
2. **先提醒已有的 plan** — before recommending new purchases, always check if they already own a plan they're not using. A paid plan is always cheaper than buying something new.

## This Session's Outcome

Switched Hermes default model to MiniMax-M3 via custom provider `minimax-cn`, using the existing Token Plan key. M3 is SWE-bench Pro ~59% (vs V4 Flash ~? not listed), but user gets it at no additional cost since the plan is already paid for.

## Cheat Sheet: Model Tiers (July 2026)

| Tier | Models | Output $/1M | SWE-bench Pro |
|------|--------|-------------|---------------|
| Budget | DeepSeek V4 Flash | $0.28 | — |
| Value | MiniMax M3, Qwen3.7 Max, Kimi K2.6 | $1.20-$4.00 | ~59%-62% |
| Premium | Claude Opus 4.8, GPT-5.5 | $25-$30 | 69% |
| Latest | Claude Fable 5 (suspended/resumed) | $50 | 95% (reported) |

Key insight: 用户年度 Plus 已付费，M3 比 V4 Flash 强一档且不额外花钱。值不值得用 M3 取决于用户对 agent 输出稳定性的容忍度。
