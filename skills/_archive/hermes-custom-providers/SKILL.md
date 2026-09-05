---
name: hermes-custom-providers
description: Add OpenAI-compatible custom model providers to Hermes — YAML format, OpenCode Zen / Ollama / vLLM integration, config pitfalls.
---

# Hermes Custom Providers

Add OpenAI-compatible model providers (OpenCode Zen, Ollama, vLLM, etc.) to Hermes.

## Trigger

User wants to add a new model provider, or mentions connecting an OpenAI-compatible API endpoint.

## Config format

In `~/.hermes/config.yaml`, add under `custom_providers`:

```yaml
custom_providers:
  - name: my-provider
    provider: openai
    base_url: https://api.example.com/v1
    api_key: "sk-..."
```

After config change, restart Hermes. Switch via `/model my-provider:model-name` or set `model.provider: my-provider`.

## Pitfalls

- **`hermes config set` serializes lists as JSON strings** — the CLI stores `custom_providers` as `'[{"name":...}]'` (a string, not a YAML list). Hermes won't parse it. Always edit `~/.hermes/config.yaml` directly with YAML syntax.
- **`patch` tool refuses to write config.yaml** — security restriction. Tell user to edit the file manually.
