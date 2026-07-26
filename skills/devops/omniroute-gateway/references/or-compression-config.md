# OmniRoute Compression Configuration — Operational Notes

The compression system has **three persistence surfaces** and **two stack levels**. Most users land here from a session where they discovered that the dashboard showed a `zh` option but `omniroute_compression_configure` (MCP) ignored it. That contradiction is real: the MCP tool writes the *top-level trigger config*, not the *schema-validated persisted config*.

Last verified against `release/v3.8.49` (2026-07).

## Endpoints / surfaces (which one writes what)

| Endpoint / tool | Persists | Schema-validated? | Returns full state? |
|---|---|---|---|
| `GET  /api/settings` | global / general | n/a (read-only) | yes — but **excludes compression sub-fields** |
| `PATCH /api/settings` | global / general | global | no — silently drops `languageConfig`-family keys |
| `PUT   /api/settings/compression` | **compression** | **yes — Zod `compressionSettingsUpdateSchema`** | **yes** — this is the real one |
| `GET   /api/settings/compression` | n/a (read) | n/a | yes — full config incl. `languageConfig` |
| `POST  /api/compression/language-packs` | n/a (read) | n/a | yes — installed language pack list |
| `omniroute_compression_status` (MCP) | n/a (read) | n/a | partial — **does not return `languageConfig`** |
| `omniroute_compression_configure` (MCP) | top-level trigger only | partial | n/a — does NOT write languageConfig |
| `omniroute_set_compression_engine` (MCP) | engine pipeline only | n/a | n/a — does NOT write trigger config |

**Gotcha:** reading via MCP `compression_status` makes you think `languageConfig` is *missing from the schema* — it is not; it's just not returned by that tool. The real state lives at `PUT /api/settings/compression`.

## Verified "zh pack" recipe

```bash
# 1. Verify available language packs server-side
curl -sS http://localhost:20128/api/compression/language-packs \
  -H "Authorization: Bearer $KEY"
# returns ["en","zh","pt-BR","es","de","fr","ja","id"] in v3.8.49
# zh pack metadata: { language: "zh", categories: ["dedup","filler","ultra"], ruleCount: 16 }

# 2. Enable zh (top-level shape only — schema rejects nested shapes)
curl -sS -X PUT http://localhost:20128/api/settings/compression \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"languageConfig":{"enabled":true,"enabledPacks":["en","zh"],"defaultLanguage":"zh","autoDetect":true}}'
```

The wiki docs at `https://github.com/.../wiki/Compression-Language-Packs` list only 6 packs (en, es, pt-BR, de, fr, ja) and are out of date. **`zh` and `id` exist** in v3.8.49 but only in source code (`open-sse/services/compression/rules/{zh,id}/`).

## Recommended "standard" config (conservative default)

Trigger layer (`/api/settings/compression`):
```json
{
  "enabled": true,
  "defaultMode": "standard",
  "autoTriggerMode": "standard",
  "autoTriggerTokens": 4096,
  "cacheMinutes": 5,
  "preserveSystemPrompt": true,
  "preserveSystemPromptMode": "always",
  "mcpDescriptionCompressionEnabled": true
}
```

Pipeline layer (set via MCP `omniroute_set_compression_engine` or `PUT /api/settings/compression`):
```json
{ "defaultMode": "stacked", "stackedPipeline": [
    { "engine": "rtk", "intensity": "standard" },
    { "engine": "caveman", "intensity": "full" }
] }
```

Run order when triggered (prompt >= 4096 tokens):
1. `rtk` standard: tool results capped at 120 lines / 12 KB / dedup ≥3 identical lines collapsed
2. `caveman` full: user messages ≥ 50 chars get fluff removal; system / assistant / tool results skipped
3. Stop once prompt hits `targetRatio` (0.7 = cap at 70% of input)

## Two stack-level API gotchas

### `set_compression_engine` vs `compression_configure` write different layers
The two MCP tools persist under different settings rows:
- `set_compression_engine` → `engines` + `stackedPipeline` + `rtkConfig` + `cavemanConfig`
- `compression_configure` → `defaultMode`, `autoTriggerMode`, `autoTriggerTokens`, `strategy`, `targetRatio`, `preserveSystemPrompt`, `mcpDescriptionCompressionEnabled`

Calling only one gives you a misconfigured compression pipeline. To bootstrap from zero, **call both** — engine first (decides WHAT pipeline runs), then trigger (decides WHEN + HOW MUCH).

### `engines.<name>.enabled=false` doesn't mean the engine is off
When `stackedPipeline` lists `rtk` explicitly, that engine is invoked **regardless of the `engines.rtk.enabled` flag**. The toggle is overridden by the stacked-pipeline entry. Same for `caveman`. So you can read `caveman.enabled: false` in the status and still be using it.

## API key auth gotcha for `PUT /api/settings/compression`

The `manage` scope is enough — you don't need `admin`. Verified with a `manage, self:usage` key:
```bash
curl -sS -o /dev/null -w "%{http_code}\n" -X PUT \
  http://localhost:20128/api/settings/compression \
  -H "Authorization: Bearer sk-...manage-only-key..." \
  -H "Content-Type: application/json" -d '{...}'
# → 200
```

But `/api/keys` admin operations and `/api/auth/login` revocation need `admin` scope.

## Auth lockout reset

If you grind login attempts and OR returns `{"error":"Too many failed attempts. Try again later."}`, this restriction is in-memory and **clears on service restart** — no waiting:
```bash
systemctl --user restart omniroute.service
sleep 5
# /api/auth/login now accepts a new attempt
```

## Pitfall (one I hit twice): API key creation returns masked value

```bash
curl -X POST /api/keys -d '{"name":"hermes","scopes":["admin"]}'
# Response: {"key":"sk-XX...YY","id":"..."}    ← MASKED
```

The `reveal` endpoint is **disabled by default in v3.8.49** (`{"error":"API key reveal is disabled"}`). The full key is shown once, only when an admin clicks the "copy" button in Dashboard. CLI/API users cannot recover it. Plan: ask the user to create the key in Dashboard and paste it; do **not** rely on the API to be the source of full keys.

## Validation schema entry point (for advanced users)

`src/shared/validation/compressionConfigSchemas.ts` is the Zod schema for the body of `PUT /api/settings/compression`. Fields like `languageConfig.enabledPacks` are validated against the regex `[a-z]{2}(-[A-Z]{2})?` — to add a pack you must drop `.json` files into `open-sse/services/compression/rules/<lang>/` AND ship the rules. Adding the file alone is not enough; the pack auto-discovery in `getAvailableLanguagePacks` reads the directory at runtime.
