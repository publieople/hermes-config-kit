# NVIDIA Rerank Provider 配置 (AstrBot)

AstrBot 内置 `nvidia_rerank` provider，调用 NVIDIA NIM 的 rerank 端点。
**端点 URL 拼接规则跟 NVIDIA 官方文档不一致**，按文档直接拼会 404。

## 配置文件位置

`/home/po/astrbot/data/cmd_config.json` → `provider[]` 列表里加一项：

```json
{
  "id": "nvidia_rerank",
  "type": "nvidia_rerank",
  "provider": "nvidia",
  "provider_type": "rerank",
  "enable": true,
  "timeout": 20,
  "nvidia_rerank_api_key": "nvapi-...",
  "nvidia_rerank_api_base": "https://ai.api.nvidia.com/v1/retrieval",
  "nvidia_rerank_model": "nv-rerank-qa-mistral-4b:1",
  "nvidia_rerank_model_endpoint": "/reranking",
  "nvidia_rerank_truncate": ""
}
```

API key 申请：https://build.nvidia.com （免费额度）。

## ⚠️ 端点 URL 拼接规则（关键坑）

AstrBot 源码 `nvidia_rerank_source.py` 的 `_get_endpoint()` 行为：

- 模型名 **不带 `/`**（如 `nv-rerank-qa-mistral-4b:1`） → URL = `https://ai.api.nvidia.com/v1/retrieval/nvidia/reranking`
- 模型名 **带 `/`**（如 `nvidia/llama-nemotron-rerank-1b-v2`） → URL = `https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-nemotron-rerank-1b-v2/reranking`

**直接按 NVIDIA 官方文档拼 `nv-rerank-qa-mistral-4b:1/reranking` 会 404**。

## Payload 格式

```json
{
  "model": "nv-rerank-qa-mistral-4b:1",
  "query": {"text": "..."},
  "passages": [{"text": "..."}, ...]
}
```

注意是**嵌套对象** `query.text`，不是裸字符串 `query`；候选文档在 `passages[].text` 而不是 `documents[].text`。

## 响应格式

```json
{
  "rankings": [
    {"index": 1, "logit": 8.9140625},
    ...
  ]
}
```

按 `logit` (或部分模型用 `relevance_score`) 降序排。

## 冒烟验证脚本

```bash
# 跑一次确认 API key + 端点 + payload 都对
python3 -c "
import json, urllib.request, urllib.error
key = 'nvapi-你的key'
url = 'https://ai.api.nvidia.com/v1/retrieval/nvidia/reranking'
payload = {
    'model': 'nv-rerank-qa-mistral-4b:1',
    'query': {'text': '测试查询'},
    'passages': [{'text': '相关文档'}, {'text': '不相关文档'}]
}
req = urllib.request.Request(url, data=json.dumps(payload).encode(),
    headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json', 'Accept': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        print(r.read().decode()[:400])
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.read().decode()[:300]}')
"
```

成功 → JSON 含 `rankings` 数组。

## 绑定到 AngelMemory

`/home/po/astrbot/data/config/astrbot_plugin_angel_memory_config.json`：

```json
{
  "retrieval": {
    "rerank_provider_id": "nvidia_rerank",
    ...
  }
}
```

重启后 AngelMemory 召回会自动走 rerank，无日志输出也属正常（debug 级别）。

## 源码路径

```
/home/po/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/astrbot/core/provider/sources/nvidia_rerank_source.py
```

排查 `model_endpoint` / payload 行为直接看 `_get_endpoint()` 和 `_build_payload()`。