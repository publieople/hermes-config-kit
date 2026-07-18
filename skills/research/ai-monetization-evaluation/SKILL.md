---
name: ai-monetization-evaluation
description: Use when a user asks whether an AI project, agent, or workflow can autonomously make real money for them — including "AI 赚钱", "AI 被动收入", "AI 自动交易", "let AI make money for me", "AI side hustle", "passive income with AI", "AI 数字人赚钱", "AI 量化 自动下单". Evaluates claims through a 3-axis filter (real revenue path × regulatory friction × disclosure honesty) and produces a routed verdict (real-and-runnable / jurisdiction-blocked / research-grade / scam). Does NOT itself attempt to make money; identity-bound actions (registration, KYC, payments, real brokerage/exchange accounts) require explicit per-call user authorization.
triggers: [AI 赚钱, AI 自动搞钱, AI 被动收入, AI side hustle, AI passive income, AI 自动交易, let AI make money for me, AI 量化, 数字人 直播 赚钱, AI 副业, AI 一键 收入]
category: research
---

# AI Monetization Claim Evaluation

The "AI makes money automatically" category is saturated with three things mixed together: real revenue paths, marketing fiction, and scams. This skill separates them **before** the user spends time, identity, or money.

## When to use

- "Can this AI thing actually make me money?"
- "I want you to take over and earn for me"
- "Compare open-source projects that print revenue for the user"
- "Is this trading bot / agent / SaaS legit?"
- "Will the platform monetize my AI content?"

## When NOT to use

- Real financial advice for a specific portfolio decision → refer to a licensed adviser
- Tax filing for specific income → refer to a CPA
- "Help me get rich quick" framing → refuse, route to scam-pattern literature

## The 3-axis filter

Every candidate project must pass **all three** axes together:

```text
Axis 1 ─ Real revenue path
   □ Where does the money actually come from? (buyer, sponsor, exchange, ad share, commission)
   □ Does the project move money on the user's behalf, or only produce content/research?
   □ Is the revenue source reachable from the user's jurisdiction (KYC, age, country)?

Axis 2 ─ Regulatory friction
   □ CFTC: trading automation, derivative signals, retail forex — which class are you in?
   □ SEC: investment advice vs investment tool; stay in research-tool territory unless licensed
   □ FTC: material-connection disclosure for affiliate content (#ad, #sponsored)
   □ Platform AI-content policies (YouTube inauthentic, TikTok Creator Rewards, Meta)
   □ Local tax reporting obligations (1099-K / 1099-MISC thresholds, VAT, GST, 境外所得)

Axis 3 ─ Disclosure honesty
   □ README + LICENSE contain disclaimer hedges? "does not actually make trades",
     "educational purposes only", "research only", "proof of concept",
     "not investment advice", "no liability", "at your own risk"
   □ Hedge present → research grade; not a real money-maker regardless of star count
   □ Hedge absent → independently verify the execution path before trusting
```

A project passes only when all three check out. A single-axis failure is enough to disqualify.

## Numbered evaluation procedure

```bash
# 1. Get repo metadata (gh-authenticated) or fetch the README
gh repo view OWNER/REPO --json description,licenseInfo,stargazerCount,pushedAt,defaultBranchRef

# 2. Find the execution path: where does the project handle real-world money?
rg -in 'order|trade|withdraw|publish|email|payout|register|deploy|charge|settle' README.md | head -40

# 3. Find the disclaimer hedge
rg -in 'educational|research|not advice|proof of concept|not financial|no liability|at your own risk' README.md LICENSE

# 4. Find the broker / exchange / payment integration list
rg -in 'binance|coinbase|alpaca|ibkr|stripe|paypal|adsense|affiliate|partnerstack' README.md | head -20

# 5. Check staleness — >12 months without push is a soft fail
gh repo view OWNER/REPO --json pushedAt --jq '.pushedAt'
```

If step 2 produces only verbs like "analyzes / summarizes / generates", the project is research grade regardless of star count. Stars are a funding signal, not a money signal.

## Decision routing (exactly one bucket)

Place the verdict in ONE of these buckets and tell the user which:

1. **Real revenue path, low friction** → describe the path, then ask for explicit per-action authorization before any identity-bound step
2. **Real revenue path, jurisdiction-blocked** → explain what unlocks it (KYC age, entity, US/EU residency) and what changes if the user qualifies
3. **Research tool only** → useful as study/scaffolding; never call it a money-maker
4. **Marketing fiction / scam** → name the red flags ("guaranteed returns", "passive income", "100x", zero-risk framing) and explain which regulator already calls it out

## Refusal rules (absolute)

Apply before proposing any action:

- Never register an account, complete KYC, or submit identification documents in the user's name
- Never spend real money (gas, exchange funding, paid model API keys) without explicit per-call authorization
- Never connect to a brokerage / exchange / payment account the user has not personally authorized for that specific project
- Never promise income. "Guaranteed returns", "passive income", "set and forget", "AI prints money" are the literal CFTC red flags
- When the user says "you take over, make money" — clarify this skill produces a verdict, not a money-maker. Income still depends on the user's decisions, identity, and assets

## Pitfalls

- Stars are a funding signal, not a money signal. A 90k-star "AI Hedge Fund" can still be marked "the system does not actually make any trades"
- "AI" prefix + money keyword ≠ income. Distinguish: AI analyzes → research, AI executes → candidate
- The same project may pass Axis 2 for one country and fail for another. Always ask jurisdiction before recommending
- "Staking yield" / "yield farming" / "liquidity mining" carry impermanent loss, slashing, counterparty risk — default to "no"
- Affiliate links require platform disclosure on most regimes (FTC, ASA, CMA). Disclosure absence is an independent disqualifier even when revenue is real
- The reason a project is open-source is often **because it's research** — research-grade work is published, production trading systems are not. Star count plus openness is often a tell

## References

- `references/regulator-quickref.md` — CFTC, SEC, FTC + platform AI-content policies, with the one rule each actually enforces and the source link
- `references/project-disclaimer-patterns.md` — common README/LICENSE hedge phrasings and what each signals (POC, research, educational, no liability)
- `references/revenue-paths.md` — concrete paths by category (trading, content, commerce, agent-as-service, data/API) with the typical KYC/age/jurisdiction snag each one hits
