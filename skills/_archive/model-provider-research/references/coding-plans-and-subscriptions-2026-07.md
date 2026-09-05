# AI Coding Plans & Subscriptions (2026-07)

## Quick Reference

### Users with $30-40/mo DeepSeek API spend
API pay-as-you-go is the **default cheapest option** for moderate usage on cheap models like V4 Flash. Subscription/Token Plans only beat API billing when:
1. You want access to a **better model** (Claude Opus, GPT-5.5) and use it enough to hit breakeven
2. You want **multi-model access** through a single platform
3. The subscription outlasts price volatility (yearly plans lock in rates)

## Plan Tiers by Budget

### ~$10/mo (~¥73)
- **GitHub Copilot Pro** — Claude Code + Codex support, AI credits model. Best entry-level.
- **Z.ai GLM Coding Lite** — ~$10/quarter(!), GLM-5.x family, OpenAI-compatible. Cheapest model backend.

### ~$20/mo (~¥145)
- **MiniMax Token Plan Plus** — ~1.7B tokens/mo on M3/M2.7 family. 80.5% SWE-bench M3. **Best value plan for coding agents.**
- **Claude Pro** — All Claude models + Claude Code CLI, but tight per-window quotas. Realistic: ~$36-178/mo API for heavy users.
- **ChatGPT Plus** — GPT-5.5 + Codex. Good for general + light coding.
- **Cursor Pro** — 500 fast requests/mo + unlimited slow. IDE-native.

### ~$50/mo (~¥365)
- **MiniMax Token Plan Max** — ~5.1B tokens/mo, 4-5 concurrent agents.
- **Alibaba Qwen Coding Pro** — Multi-model (Qwen + Kimi + GLM + MiniMax) under one key.

### ~$100/mo (~¥730)
- **Claude Max 5x** — Breakeven at ~26 features/mo on Opus. Makes sense when daily agent usage is heavy.
- **Codex Pro** — 5x GPT-5.5 rate limits.

## Model Quality Tiers (coding)

| Tier | Models | SWE-bench Pro | Output/Mtok |
|------|--------|--------------|-------------|
| **Frontier** | Claude Opus 4.8, GPT-5.5 | 69%, ~60% | $25-$30 |
| **Strong** | Gemini 3.1 Pro, MiniMax M3, Kimi K2.6 | 59-80% | $2.40-$12 |
| **Cheap-capable** | DeepSeek V4 Pro, V4 Flash | ~80% (V4 Pro Max) | $0.28-$0.87 |
| **Ultra-cheap** | GLM-4.7-Flash | Free | Free |

Note: SWE-bench Pro numbers are from Scale's standardized harness. Vendor self-reported SWE-bench Verified is often ~15-20 points higher.

## MiniMax Token Plan Details

| Plan | Price | Est. monthly tokens | Agent concurrency | Best for |
|------|-------|-------------------|-------------------|----------|
| Plus | $20/mo (~$17/mo yearly) | ~1.7B | 3-4 | Personal coding, prototyping |
| Max | $50/mo | ~5.1B | 4-5 | Daily coding, heavy agent use |
| Ultra | $120/mo | ~10-12.5B | 6-7 | Heavy agent workflows |

**M3 model reality check:**
- Benchmarks: 59.0% SWE-bench Pro (independent), 80.5% SWE-bench Verified (vendor self-reported)
- Real-world: Unreliable for complex agentic tasks. BridgeBench failed 8/12 UI tests. Slow output. Buggy on refactoring.
- Good for: Cheapest 80%+ model, 1M context window works well, multimodal input
- Bad for: Production coding agents, complex multi-step tasks
- **Recommendation for MiniMax plan holders**: M2.7 is more stable for known workloads. Test M3 per-task rather than defaulting to it.

## User Preference (Publieople)

Current setup:
- Model: DeepSeek V4 Flash via direct API
- Monthly spend: ~¥260 ($36) on V4 Flash alone
- Has: MiniMax Token Plan Plus **annual** (already paid, barely used) — should at minimum route some traffic through it to get value
- Wants: A plan that either (a) saves money vs ¥260, or (b) gives better models at the same price

Key insight: For Publieople's usage, the MiniMax plan is already owned and already covers 10x their monthly token consumption. The question is whether M3 is good enough to replace V4 Flash — answer: not reliably for agent work, but M2.7 is worth testing.

## Key Resources

- MiniMax Token Plan: https://platform.minimax.io/subscribe/token-plan
- MiniMax M3 docs: https://platform.minimax.io/docs/guides/models-intro
- OpenRouter free models: https://openrouter.ai/models?q=free
- Price per token (model catalog): https://pricepertoken.com
- Morph LLM API comparison: https://www.morphllm.com/llm-api
- AI Coding Costs calculator: https://www.morphllm.com/ai-coding-costs
