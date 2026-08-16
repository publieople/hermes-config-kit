# Provider Setup Investigation

When a user says "switch to provider X" or "it was configured before", systematically check these locations in order:

## 1. Primary Config (`config.yaml` `model` section)
```bash
grep -A5 '^model:' ~/.hermes/config.yaml
# Check: model.default, model.provider, model.base_url, model.api_key
```

## 2. Custom Providers (`config.yaml` `custom_providers`)
```bash
grep -A3 '^custom_providers:' ~/.hermes/config.yaml
# Also check: are there multiple providers defined? Which one is active?
```

## 3. API Keys (`.env`)
```bash
grep -i <PROVIDER> ~/.hermes/.env
```
Known env var patterns:
| Provider | Env Var |
|----------|---------|
| DeepSeek | `DEEPSEEK_API_KEY` |
| MiniMax (global) | `MINIMAX_API_KEY` |
| MiniMax (China) | `MINIMAX_CN_API_KEY` |
| Bailian/DashScope | `BAILIAN_API_KEY` or `DASHSCOPE_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |

## 4. Credential Pools (`auth.json`)
```bash
cat ~/.hermes/auth.json | python3 -m json.tool
```
Covers `credential_pool` entries per provider. Some providers may have stale/expired credentials here even if `.env` exists.

## 5. Past Sessions
```python
session_search(query="provider_name OR model_name OR 配置")
```

## 6. Memory
```python
# Check both targets:
# user — profile preferences
# memory — personal notes about config state
```

## Critical: Auxiliary Provider Mismatch Trap

The main model and auxiliary services (vision, compression, session_search, etc.) use **separate** provider configurations:

```yaml
# config.yaml
model:
  default: <main model>
  provider: <main provider>

auxiliary:
  vision:         # ← SEPARATE provider config
    provider: <vision provider>
    model: <vision model>
    api_key: ...
```

When switching the main model provider:
1. **Always check `auxiliary.vision`** — it may use a different provider whose credentials are expired
2. If the vision API key is invalid (401), you must update `auxiliary.vision` to use a working provider
3. Common victims: old trial keys, expired Coding Plan API keys, provider-specific endpoints that deprecated

## MiniMax-Specific Notes

- MiniMax offers full-modal (text+image+audio) models like `minimax-m2.5`
- Config pattern:
  ```yaml
  model:
    default: minimax-m2.5
    provider: minimax  # or minimax-cn for China endpoint
  ```
- `.env`: `MINIMAX_API_KEY` (global) or `MINIMAX_CN_API_KEY` (China)
- Also update `auxiliary.vision` to use MiniMax or another working provider since the old one may be expired
