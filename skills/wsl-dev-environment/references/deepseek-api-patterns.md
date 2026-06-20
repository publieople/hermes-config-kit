# DeepSeek API 模式与坑

## ReAct Agent 的 PAUSE 问题

DeepSeek 模型不会在 "PAUSE" 处停止，而是一次性生成完整的多轮对话（包含幻觉数据）。

**修复**：在 API 调用中添加 `stop=["PAUSE"]`：
```python
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    stop=["PAUSE"],  # ← 关键
)
```

## 中文冒号 vs 英文冒号

DeepSeek 有时输出中文冒号 `：`，有时英文 `:`。正则匹配需要兼容两者：
```python
re.search(r"Action[:：]\s*(\w+)", text)
re.search(r"Action Input[:：]\s*(\{.*?\})", text, re.DOTALL)
re.search(r"Final Answer[:：]\s*(.*)", text)
```

## Function Calling 工具格式

使用 OpenAI 兼容格式（非 ReAct 格式）：
```python
tools = [{
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "工具描述",
        "parameters": {"type": "object", "properties": {...}, "required": [...]}
    }
}]
```

## 环境变量

```python
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
```
