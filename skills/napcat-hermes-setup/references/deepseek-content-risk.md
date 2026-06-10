# DeepSeek "Content Exists Risk" 在 NapCat/QQ 场景的排查记录

**日期**：2026-06-09  
**Session**：`20260609_165440_83d1176c`

## 错误特征

```
ERROR agent.conversation_loop: Non-retryable client error: Error code: 400
{'error': {'message': 'Content Exists Risk', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_request_error'}}
```

- Provider: deepseek
- Model: deepseek-v4-flash
- Base URL: https://api.deepseek.com/v1
- 触发频次：同一 session 内连续 3 次（16:54, 17:13, 17:15）

## 时间线

| 时间 | API 调用 | 结果 |
|------|---------|------|
| 16:54:45 | #1 (成功) | 264 tokens 输出，含 tool calls（web_search + terminal） |
| 16:54:50 | #2 (失败) | HTTP 400: Content Exists Risk |
| 17:13:38 | #1 (失败) | HTTP 400: Content Exists Risk |
| 17:15:04 | #1 (失败) | HTTP 400: Content Exists Risk |

第 2、3 次失败时，上下文已包含前一次失败产生的错误消息，形成污染循环。

## 跨 bot 连锁污染

群 `707942526` 中有两个 bot：
- Hermes (2628392161)
- 人出 bot

agent.log 17:15:03 记录：
```
history=6 msg='[Replying to: "[人出bot] ❌ Non-retryable error (HTTP 400): HTTP 400: Content Exist...'
```

人出 bot 先收到错误并发出 → Hermes 收到这条消息作为回复上下文 → 再次触发 Content Exists Risk。

## 为什么错误消息会发到群里

Gateway `run.py` line 8877：
```python
response = agent_result.get("final_response") or ""
```

Agent 在第 1 次 API 调用成功时 `final_response` 已设为模型输出的文本（147 chars）。agent 失败后 gateway 仍送达中间输出。

## 解决方案对比

| 方案 | 难度 | 效果 | 副作用 |
|------|------|------|--------|
| 换模型（NAPCAT_MODEL 改非 deepseek） | 低（改 .env + 重启） | 彻底消除 | 可能增加费用 |
| /reset 手动清 session | 低（群里发指令） | 临时恢复 | 丢失上下文 |
| 改 gateway 不送错误到群 | 中（改 run.py） | 消除 UX 问题 | 错误静默 |
| 加连续 2 次 Content Exists Risk 自动 reset | 中（改 run.py + conversation_loop） | 根治 | 需测试 |
