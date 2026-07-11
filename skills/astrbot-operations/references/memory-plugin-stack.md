# AstrBot 记忆/认知插件栈选型与配置

AstrBot 生态里有几套记忆/认知插件，并存会互相污染上下文。本文记录作者在 `astrbot_plugin_angel_heart` + `astrbot_plugin_angel_memory` 配套使用上的实测结论，以及 AstrBot 内置 rerank provider 的选型。

## Angel Heart + Angel Memory（kawayiYokami 出品）

两个插件配套使用，是当前功能最完整的组合：

- **Angel Heart**（v0.9.3，"天使之心"）— 行为引擎：4 状态机 + 轻重双 AI 核（秘书模型廉价快、主模型贵但精），解决"群聊 AI 太频繁 / 不懂分寸"的问题
- **Angel Memory**（v1.4.20，"天使之魂"）— 记忆引擎：三层认知架构（潜意识层检索 → 主意识层生成 → 反馈与进化）+ 4 个 LLM 工具（`angel_remember`/`angel_recall`/`angel_note_read`/`angel_note_create`）

README 原文："AngelHeart + AngelMemory = 完整的 AI 认知架构"。

### 必填 3 个 provider id

**这是最容易踩的坑：插件目录放进去 ≠ 启用。3 个关键 provider id 全空，跑起来 AI 不会主动思考/记忆。**

| 插件 | 字段 | 推荐填什么 | 不填的后果 |
|------|------|-----------|-----------|
| Angel Heart | `analyzer_model` | 廉价快速模型（如 `opencode/deepseek-v4-flash-free`） | 每次对话都白跑一次空决策 |
| Angel Heart | `image_caption_provider_id` | 没图片理解需求就留空 | — |
| Angel Memory | `provider_id` | 带思考能力的模型（如 `deepseek/deepseek-v4-pro`） | 记忆整理质量极差或直接不工作 |

`is_reasoning_model` 默认 `true` 不要关（DeepSeek/Qwen 等带思维链的模型需要）。

### ⚠️ 与其他记忆插件冲突

**AstrBot 生态里有多套记忆/认知插件，并存会互相打架：**

- `astrbot_plugin_livingmemory`
- `astrbot_plugin_self_learning`（人格选择逻辑还会覆盖 WebUI 切换，详见 SKILL.md 人格系统节）
- Angel Memory

同一句消息会被记 3 次，AngelMemory 召回时上下文被污染。**启用 Angel Memory 前必须先把前两个禁用。**

判断标准：留 1 套即可，功能最完整的是 Angel Heart + Angel Memory 组合。

### personality 字段是真正的"灵魂"

只填 provider 不改 `personality.ai_self_identity` 和 `personality.reply_strategy_guide`，AI 跑起来还是默认人格。这两个字段直接注入 LLM system prompt，决定 AI 是谁、什么时候说话什么时候闭嘴。

`reply_strategy_guide` 推荐写法示例：
```
编程、数学相关的话题，有人迷惑时可以提出自己的建议。
火药味大的时候立刻闭嘴。
怀疑你是不是人类的时候选择闭嘴。
```

### Rerank 配置：现在跳掉

AstrBot 内置 4 个 rerank provider（`/home/po/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/astrbot/core/provider/sources/`）：

| Provider | 后端 | 配置门槛 |
|----------|------|---------|
| `bailian_rerank` | 阿里云百炼 `qwen3-rerank` | 阿里云 API Key |
| `nvidia_rerank` | NVIDIA NIM `nv-rerank-qa-mistral-4b:1` | NVIDIA API Key（有免费额度） |
| `vllm_rerank` | vLLM 自部署 | 需先部署 bge-reranker（端口默认 8001） |
| `xinference_rerank` | Xinference 自部署 | 需先部署 |

**全部需要在 cmd_config.json 注册才能用。** 默认没有任何 rerank provider。

**Angel Memory 自己的 README 怎么说：**
> "向量带来的额外提升通常较小，重排效果提升明显。推荐优先配置 rerank_provider。"

但作者实测建议：**先跳掉**，理由：
1. 重排空数据库没意义（需要积累几百条记忆）
2. BM25 直出已经覆盖 80% 场景
3. 留空会自动降级为非重排策略，跑起来没毛病
4. 记忆系统还没跑起来就花时间配 rerank 是 YAGNI

**重新评估时机**：记忆库 > 500 条 或 召回结果肉眼可见不相关时再上。

### 验证启用是否生效

不用重启 AstrBot（热加载已生效），直接发消息测试：
- WebUI → `http://localhost:6185` → 侧边栏 → **🧾 记忆浏览**
- 跟 AI 聊几句后回来刷新，看到新记录就说明通了
- 失败查日志：`~/astrbot/logs/` 搜 `angel`

## 其他认知/行为插件速查（并存互斥）

- `astrbot_plugin_portrayal` — 角色扮演/画像（与人格系统相关但更偏静态设定）
- `astrbot_plugin_self_learning` — 自学习（与人格选择逻辑绑定，建议关掉改用 Angel Memory）
- `astrbot_plugin_livingmemory` — 老牌记忆（功能被 Angel Memory 覆盖，建议关掉）

## 相关阅读

- Angel Memory README: https://github.com/kawayiYokami/astrbot_plugin_angel_memory
- Angel Heart README: https://github.com/kawayiYokami/astrbot_plugin_angel_heart
- AstrBot 插件目录：`/home/po/astrbot/data/plugins/`
- AstrBot 插件配置：`/home/po/astrbot/data/config/astrbot_plugin_*_config.json`