# Revenue paths and their typical snag

Map each candidate to one or more of these paths, then identify which *factor* can stop it cold.

## Trading — automated order routing (高风险，监管重)

| Path | Typical executor | Snag |
|---|---|---|
| Spot crypto | Freqtrade + Binance/OKX | KYC for withdrawal to fiat; off-ramp country restriction (CN, RU, sanctioned). Binance "no mainland China" since 2021 is permanent. Strategy needs to be profitable net of fees — most aren't |
| Crypto perpetual futures | Freqtrade futures, Jesse | Capital in hot wallet; liquidation risk; same off-ramp snag + funding fees |
| Stock / ETF | Alpaca / IBKR via Lumibot, QuantConnect Lean | US SEC-pattern rules; PDT rule if under 25k USD; KYC registration. IBKR Pro has minimum equity and currency conversion |
| Equities via MCP | QuantAgent, TradingAgents-adjacent | Generally no execution = research only. Wraps limit orders via Alpaca; same PDT snag |
| Prediction markets | Kalshi-bot, Polymarket (no open source bot yet) | KYC required; US jurisdictions only for Kalshi; capped loss limits |

**Routine verdict bucket:** any of these is bucket 1 or 2 if the user can clear KYC in their jurisdiction. Without KYC, the project can still run, but withdrawal-to-fiat stops at the exchange gate.

## Content & audience monetization

| Path | Typical executor | Snag |
|---|---|---|
| YouTube ad share | MoneyPrinterTurbo → Upload-Post → YT | YT "inauthentic content" policy (Jul 15 2025 update). Mass-produced faceless videos no longer monetize even if AI is technically allowed for original content. Originality + disclosure + commercial-use rights required |
| TikTok Creator Rewards | Same pipeline | Original + filmed/designed/produced by you + 1k qualified FY views + AI labels when realistic |
| Affiliate referrals | Affiliate-skills + n8n + landing page | FTC (US) / ASA (UK) / CMA require disclosure. Affiliate income counts as self-employment income in most jurisdictions — tax filing required. Networks (Partnerstack, Impact, CJ) require site-of-record, not just a Telegram channel |
| Sponsorships | Cold outreach via OpenOutreach or MarketClaw | Sales cycle measured in weeks; FTC disclosure still required; some platforms forbid AI-only ads |

**Routine verdict bucket:** whichever platform, expect 3–6 months to first revenue. Treat any "30-day cash" claim as fraud.

## E-commerce / POD

| Path | Typical executor | Snag |
|---|---|---|
| Printify / Printful via MCP | TSavo/printify-mcp, Purple-Horizons/printful-mcp | Account registration requires real identity for payouts. Copyright/trademark review still manual. Etsy fees + ad spend + returns |
| Dropshipping | 1688/East-side sourcing via agent | Customs declarations, platform ToS around auto-listing; AliExpress affiliate bans aggressive scraping |
| Digital products (course, template, e-book) | Sell on Gumroad/LemonSqueezy via Open SaaS clone | Discoverability is the constraint, not generation. AI-written course on cold traffic averages < 1% conversion |

## Agent-as-service

| Path | Typical executor | Snag |
|---|---|---|
| Per-job marketplaces (Agent Market, Devtask, Fiverr) | `mastrophot/first-earning-agent-tutorial` style | Market is early — visible payouts measured in low single-digit NEAR or USD. Reputation takes 3–5 jobs minimum before higher-value bids possible. Account and withdrawal both KYC'd |
| B2B outreach / cold email | OpenOutreach | No product → no revenue. Deliverable is the AI service you already know how to sell |
| SaaS template white-label | Anil-matcha awesome-generative-ai-apps / Open SaaS | Distribution + customer support + refund handling still on the user. Margin is high but volume is the constraint |

## Data & API arbitrage

| Path | Typical executor | Snag |
|---|---|---|
| Model API + markup (subscription SaaS) | Open SaaS / white-label | Customer support burden; model cost volatility; competitive churn |
| Affiliate search engine | No mainstream self-hosted option | Search engines don't pay affiliates; only affiliate networks do |

## Validator shortcut

Before recommending a path, ask in one short message:

```text
1. Jurisdiction (country of residence)
2. Age
3. Already holds accounts at any of: exchange / brokerage / Stripe / PayPal / Telegram / YouTube
4. Acceptable loss tolerance (zero / small / moderate)
5. Time-to-result expectation (days / months / year+)
```

If they can't or won't answer, the safe default is *research-grade scaffolding*, not a deployment recommendation.

## Real-talk revenue ranges (2026 baseline, individual operator)

- Crypto bot on retail: median outcome ≈ fees paid; top decile active strategy may grind 5–30%/yr in sideways markets, gets rekt in trends
- YouTube/TikTok AI channel: median 0 revenue at 6 months if mass-produced; only originality-distinct content compounds
- NEAR Agent Market: 0–20 NEAR (~0–10 USD) per accepted job; ~5 USD per accepted tutorial early on
- B2B cold-email + standard service: first 30-day revenue typically $0-$500; close rate 2–5%
- White-label AI SaaS: 3–9 months to first paying customer; median MRR $50–$500 in first year

Treat any single-source claiming >$10k/month for an unattended open-source stack as a paid-promo funnel.
