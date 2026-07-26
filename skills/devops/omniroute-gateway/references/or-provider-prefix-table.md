# OmniRoute Provider Alias / Model-ID Prefix Table

Verified against `GET /v1/models` on OmniRoute v3.8.48 / v3.8.49. Alias values come from `src/shared/constants/providers.ts` and `open-sse/config/providers/registry/<provider>/index.ts` `alias:` field.

## How to get this list

```bash
KEY="sk-..."   # OR gateway key
curl -sS http://localhost:20128/v1/models \
  -H "Authorization: Bearer $KEY" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
by = {}
for m in d['data']:
    by.setdefault(m['owned_by'], []).append(m['id'])
for o in sorted(by):
    print(f'## {o}  ({len(by[o])})')
    for i in by[o]: print(f'  {i}')
"
```

## Provider alias → prefix map (OR 3.8.x)

| Provider ID | Alias | Prefix used in model IDs | Auth type | Notes |
|---|---|---|---|---|
| `minimax-cn` | `minimax-cn` | `minimax-cn/` | apikey | China endpoint, Token Plan supported |
| `minimax` | `minimax` | `minimax/` | apikey | Global endpoint |
| `github` | `gh`, `github` | `gh/` or `github/` | oauth | GitHub Copilot (both prefixes work) |
| `auggie` | `aug` | `aug/` | oauth | Augment Code |
| `opencode` | `oc` | `oc/` | oauth | OpenCode Zen free tier |
| `duckduckgo-web` | `ddgw` | `ddgw/` | web-cookie | DDG AI Chat |
| `theoldllm` | `tllm` | `tllm/` | web-cookie | theoldllm.com |
| `veoaifree-web` | `veo-free` | `veo-free/`, `veoaifree-web/` | web-cookie | veo3 + seedance |
| `mimocode` | `mcode` | `mcode/` | apikey | Xiaomi MiMo |
| `chipotle` | `pepper` | `pepper/` | — | pepper-1 |
| `auto` (system) | `auto` | `auto/`, `auto/coding`, `auto/fast`, `auto/cheap`, `auto/coding:fast`, `auto/reasoning:pro`, `auto/smart`, `auto/offline`, `auto/vision`, `auto/multimodal`, `auto/minimax`, `auto/minimax-m3-free`, `auto/claude-opus`, `auto/claude-sonnet`, `auto/best-coding`, `auto/best-free` | system | Virtual combos — virtual factory, no DB row |
| `combo` (system) | — | (user-defined combos) | system | Persisted combos (none by default) |

## How to discover a NEW provider's alias

```bash
# After connecting a provider in Dashboard:
curl -sS http://localhost:20128/api/providers -H "Cookie: auth_token=$COOKIE" \
  | python3 -c "import sys,json; [print(c['provider']) for c in json.load(sys.stdin)['connections']]"
# Then look up its alias in the registry file:
grep -l "id: \"<provider>\"" ~/.npm-global/lib/node_modules/omniroute/open-sse/config/providers/registry/
grep -A 3 "id: \"<provider>\"" ~/.npm-global/lib/node_modules/omniroute/open-sse/config/providers/registry/<provider>/index.ts
# The `alias:` field is what precedes the slash in model IDs.
```

## Common mistakes

- **`mm/` and `mm-cn/` and `mmcn/` are NOT aliases.** Only `minimax-cn/` works (verified by testing `mmcn`, `mmcn-cn`, `mm-cn` all → `No active credentials for provider: <that-alias>`).
- **`minimax-cn/` is the *only* working alias for the China MiniMax provider.** Despite the underlying provider ID being `minimax-cn`, some agents try `mm-cn/` or `mm/` thinking "MiniMax CN = mm-cn". Only the literal registry alias works.
- **`github/` and `gh/` both work** for GitHub Copilot — they map to the same provider connection. Use whichever is shorter.
- **`auto/minimax-m3-free` exists as a virtual alias** for the OpenCode free M3 model — distinct from `minimax-cn/MiniMax-M3` (paid Token Plan). Both work, different billing.

## Combo strategy reference

OmniRoute routes models with these strategies (declared in `src/shared/constants/routingStrategies.ts → ROUTING_STRATEGY_VALUES`, 18 total):

`priority` · `round-robin` · `weighted` · `p2c` · `least-used` · `cost-optimized` · `auto/cheap` · `context-relay` · `context-optimized` · `random` · `strict-random` · `fusion` (multi-model + arbiter) · `reset-window` · `headroom` · `auto` (9-dim scoring) · `lkgp` (last-known-good-provider stickiness) · `reset-aware` · `quota-share` (internal) · `auto-pro` / `auto-free` filters

For Zero-Config, just set `model: "auto"` or `model: "auto/coding"` — virtual factory handles it.

## URL conventions for model IDs not in OR's catalog

If you have a model ID that's not in `/v1/models`, the request will fail with `model_not_found`. Verify before use:
```bash
curl -sS http://localhost:20128/v1/models -H "Authorization: Bearer $KEY" \
  | python3 -c "import sys,json; ids=set(m['id'] for m in json.load(sys.stdin)['data']); import sys; sys.exit(0 if '<your-model-id>' in ids else 1)"
```