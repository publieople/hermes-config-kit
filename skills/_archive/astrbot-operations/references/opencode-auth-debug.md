# OpenCode Zen 免费模型 Auth 调试记录

## 背景

AstrBot 配置 `opencode` provider source 用免费模型（`deepseek-v4-flash-free`），但一直 401/403。

## 根因

OpenCode Zen 的免费模型 API 行为反直觉：**不传 Authorization header 才 200，传了任何值都 401**。而 AstrBot 的 `openai_source.py` 用新版 OpenAI Python SDK，必须传一个 `api_key` 参数给 `AsyncOpenAI()`，否则 SDK 抛 `Missing credentials`。

## 测试过程

### 1. 不传 key 的 curl → ✅ 200
```
curl -X POST https://opencode.ai/zen/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash-free","messages":[{"role":"user","content":"hi"}],"max_tokens":5}'
```
返回 `cost":"0"`，JSON 格式，200。

### 2. 传假 key 的 curl → ❌ 401
```
curl -H "Authorization: Bearer sk-fakekey" ...
```
返回 `AuthError: Invalid API key.`

### 3. 不传 Auth header 的 Python SDK → ❌ 抛 Missing credentials
```python
AsyncOpenAI(api_key=None, ...)
# openai.OpenAIError: Missing credentials
```

### 4. 传假 key 的 Python SDK → ❌ 401
```python
AsyncOpenAI(api_key="sk-fakekey", ...)
# openai.AuthenticationError: 401
```

## AstrBot 源码关键行

`/home/po/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/astrbot/core/provider/sources/openai_source.py`

- **第 359-360 行**: `self.api_keys = super().get_keys()` → `self.chosen_api_key = ...`
- **第 384-385 行**: `AsyncOpenAI(api_key=self.chosen_api_key, ...)`

老版 OpenAI SDK 允许 `api_key=None`（不发 header），新版（AstrBot v4.26.2 依赖的版本）不再允许。

## 解决方案

### 方案 A：设环境变量绕 SDK（推荐）
```
# 在 ~/.config/astrbot/ 或 systemd service 里设
OPENAI_API_KEY=anything-will-do
```
`cmd_config.json` 里保持 `"key": []`。SDK 读到环境变量就不再抛 `Missing credentials`，且 `chosen_api_key` 仍为 `None` → 不传 Auth header。

### 方案 B：删掉 opencode provider
反正 fallback 链路有 minimax 和 deepseek 直连，不差这个。

## 确认有效的方式

```bash
# 设完环境变量后，AstrBot 进程需要重启才生效
sudo systemctl restart astrbot
# 检查日志有无 opencode 的 auth 错误
sudo journalctl -u astrbot --no-pager -n 20 | grep -iE "opencode|401|auth"
```
