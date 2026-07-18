# Disclaimer patterns in AI-trading / auto-income repos

Hedges in README/LICENSE are *evidence*, not noise. A hedge that matches a known pattern usually tells you the bucket the project belongs in: research tool, POC, or genuinely production-grade. Grep before recommending.

## High-signal hedges (usually = research / educational)

| Phrase | What it actually signals | Typical repo profile |
|---|---|---|
| `does not actually make trades` | Pure research framework. No order routing wired to a live exchange. | TradingAgents, AI Hedge Fund |
| `educational and research purposes only` | Construction kit, not a service. User assembles their own strategy. | FinRL, ai-hedge-fund |
| `proof of concept` | Authors built it to explore an idea, not to run money. | ai-hedge-fund |
| `not financial, investment, or trading advice` | Liability-only; doesn't change what the code does | nearly all reputable quant libs |
| `use at your own risk` / `no liability assumed` | Disclaimed exposure; in some jurisdictions imposes real obligations on users (own capital = own risk) | Freqtrade (very explicit block at the top) |
| `for [N18+] users` | Distancing from minors-age risk — pairing with KYC is a *good* sign, not a bad one | Jersey-based prediction-market bots |
| `dry-run by default` / `requires manual --execute-*` | Engine supports live trading but ships with a non-destructive default | Kalshi-bot, TradingAgent crawlers |
| `paper trade` / `simulated exchange` | Backtesting + sandbox only | TradingAgents |

## Red flags that look like hedges but actually hide revenue claims

| Phrase | Why it is a yellow flag, not a hedge |
|---|---|
| `set and forget` on a money-maker | Marketing copy, usually a YouTube/CoinMarketCap promo |
| `guaranteed returns` / `passive income` / `100x` / `zero risk` | CFTC fraud red flags even if the site adds "not advice" elsewhere |
| `users have made $X total` with no methodology | Inflated claim. Insist on per-user distribution, time window, and source |
| `win rate 92%` / `Sharpe 4.5` without a reproducible backtest notebook | Backtest overfitting — fail any 3-year OOS test |
| `covered by insurance` with no insurer named | Insurance fraud indicator |
| Closing disclaimer that contradicts copy above the fold | Not a hedge; copy-laundering |

## What "low-disclaimer" looks like and why it matters

A suspiciously clean README with no hedge AND no permissioning notes AND claims of money generation → look for:

- No `LICENSE` file, or a custom permissive license without a patent clause
- Repo archived without explanation (often = abandonment after a withdrawal-fraud investigation)
- Heavy pay-affiliate links to "signal groups" + Telegram QR code
- Demo video showing real-dollar P/L with no audit summary

If you see all of the above, route to **bucket 4 (scam/marketing fiction)** and name the specific red flags.

## Mapping README → verdict (cheat sheet)

```text
README hedges present + no execution verb (analyzes/generates/visualizes)
  → bucket 3 (research tool). User cannot monetize.

README hedges present + execution verb wired (places orders / sends emails / charges)
  → bucket 1 or 2. Real project, real liability — needs jurisdiction + KYC + per-action auth.

No hedges + execution verb + claim of income
  → bucket 4. Look for the red flags table above.

Stale (no commit > 12 mo) + execution verb + income claims
  → bucket 4 even if live. Abandoned money-handling code = exposure.
```

## How to verify without running the code

1. `gh repo view OWNER/REPO --json pushedAt --jq '.pushedAt'` — staleness
2. `gh repo view OWNER/REPO --json licenseInfo`
3. `rg -in 'binance|coinbase|alpaca|ibkr|kraken|bybit|stripe|paypal' README.md docs/`
4. `rg -in 'order|trade|withdraw|email|payout|charge|settle|payment' README.md app/`
5. If you see broker/exchange names *and* execution verbs *and* low/no hedge, that's bucket 4.
