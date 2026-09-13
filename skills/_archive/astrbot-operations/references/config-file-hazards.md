# AstrBot 配置文件陷阱

## BOM 编码

`data/cmd_config.json` 带 **UTF-8 BOM** 头（`\xEF\xBB\xBF`），直接用 `json.load()` 会报 `Unexpected UTF-8 BOM`：

```python
# 正确：
with open('cmd_config.json', encoding='utf-8-sig') as f:
    cfg = json.load(f)
```

BOM 对 AstrBot 自身处理无影响（它用 Python 的 `utf-8-sig` 读取），但用 外部脚本/curl/编辑器 直接解析时要注意。

## Key 是占位符

混淆来源：`/v1/models` 不需要认证（可访问），但 `/v1/chat/completions` 需要。所以 OpenCode 的模型列表能列出来，但发消息就 401。

验证 API key 是否有效：
```bash
curl -s -X POST https://opencode.ai/zen/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $KEY" \
  -d '{"model":"deepseek-v4-flash-free","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```
- 401 = key 无效或占位符
- 200 = 可用
- 500/cors = 服务端问题，与 key 无关
