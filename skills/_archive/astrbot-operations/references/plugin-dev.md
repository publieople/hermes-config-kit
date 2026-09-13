# AstrBot 插件开发实战

> SKILL.md 已写核心规则速查；本文档记录本次 fork-and-customize astrbot_plugin_Pic 项目的完整配方、踩过的坑、验证脚本模板。

## 1. Fork 模式 vs 从零写

**决策标准**：AstrBot 插件市场 + GitHub 搜一遍，能找到功能相近的直接 fork；找不到再从零写。

```bash
# gh fork 自动加 upstream remote
gh repo fork <upstream-owner>/<repo> --clone=false
# 然后在本地 data/plugins/ 下 clone（gh repo clone 也行）
cd ~/astrbot/data/plugins
gh repo clone publieople/<repo>
```

**fork 后必改的 3 处**（让插件显示成自己的 fork 而非冒名上游）：

1. `metadata.yaml` 的 `version` 升一个小号（fork 改过任何东西）
2. `metadata.yaml` 的 `author` 改成 `原作者 / publieople`
3. `main.py` 的 `@register(...)` 第二个参数同步成 `原作者 / publieople`

**commit message 规范**：英文（看上游），用 `type: summary` 格式：

```
v1.8.0: configurable category filter
v1.8.1: /来点 [分类] command for per-category explicit send
fix: ycy display name and 二次元 alias
fix(schema): ycy label 银次缘 -> 二次元自适应 in WebUI defaults
```

## 2. 文档路径速查（大量 404！）

AstrBot 文档站 `https://docs.astrbot.app` 经常返回 404。**真实路径前缀**：

| 搜索关键词 | 真实 URL |
|---|---|
| 插件开发入门 | `/dev/star/plugin-new.html` |
| 插件配置 schema | `/dev/star/guides/plugin-config.html` |
| Plugin Pages | `/dev/star/guides/plugin-pages.html` |
| LLM tool | `/dev/star/guides/llm-tool.html`（推测） |

**404 的路径**（别去）：
- `/dev/star/llm-tool.html` ❌
- `/dev/star/publish.html` ❌
- `/dev/star/basic.html` ❌

**找不到文档时的备用查法**：直接在 AstrBot 源码里 grep：

```bash
SRC=/home/po/.local/share/uv/tools/astrbot/lib/python3.12/site-packages/astrbot

# 装饰器签名
grep -nE 'def register_llm_tool' $SRC/core/star/register/star_handler.py

# provider type enum
grep -nE '^class .*Type' $SRC/core/provider/entities.py

# 现有 provider 实现（看怎么配）
ls $SRC/core/provider/sources/  # 找对应类型
```

## 3. 装饰器签名陷阱

AstrBot 的装饰器签名**不一致**，AST 检查时必须小心：

| 装饰器 | 装饰器用法 | AST 检查关键 |
|---|---|---|
| `@register("name", "author", "desc", "v1.0.0", "url")` | 5 个 positional | `d.args[i]` |
| `@command("name")` | 1 个 positional | `d.args[0].value` |
| `@llm_tool(name="x")` | **keyword only** | `d.keywords[0].value` |

**AST 提取通用模板**：

```python
import ast
tree = ast.parse(src)
for n in ast.walk(tree):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for d in n.decorator_list:
            if not isinstance(d, ast.Call): continue
            name = d.func.id if isinstance(d.func, ast.Name) else d.func.attr
            arg = None
            if d.args and isinstance(d.args[0], ast.Constant):
                arg = d.args[0].value
            for kw in d.keywords:
                if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                    arg = kw.value.value
            print(f"{n.name} @{name} arg={arg!r}")
```

## 4. schema `_conf_schema.json` 字段类型实战

**复选列表**（最常用，用户能勾选开关）：

```json
{
  "enabled_categories": {
    "type": "list",
    "description": "启用的图源分类",
    "hint": "勾选要启用的栗次元分类。空 = 全启用。",
    "options": ["ycy", "moez", "ai", ...],
    "labels": ["二次元自适应", "萌版自适应", "AI 自适应", ...],
    "items": {"type": "string"},
    "default": []
  }
}
```

**坑**：
- `options` 和 `labels` 数组长度必须严格一致且一一对应
- 改 `labels` 中文名时记得同步改 `main.py` 里 `CATEGORIES[key][0]` —— **两个地方必须同时改**（本次 ycy/二次元踩的就是这个）
- `list` 类型的 `items` 支持 `options`/`labels`（推断自 string 用法，WebUI 实际可渲染）

**用户改 schema 后**：AstrBot 配置 migration 是**递归检查**——新增字段加默认值，不存在字段移除，已存值不动。所以改 `labels` 不会破坏已存 `enabled_categories` 值。

## 5. WebUI 标签同步规则

`labels` 数组（WebUI 显示）必须和 `CATEGORIES` 中文名（代码里用）保持同步。规则：

- 改 `CATEGORIES[k][0]` → 同步改 `labels[i]`
- 改 `labels[i]` → 同步改 `CATEGORIES[k][0]`
- `_ALIAS[k]` 的中文别名可以跟 `CATEGORIES[k][0]` 不一样（`_ALIAS` 是用户口语别名，`CATEGORIES` 是权威中文名）

**修改后验证**：

```python
# ast + 业务逻辑模拟
import ast
tree = ast.parse(open("main.py").read())
# 抽 CATEGORIES + _ALIAS + labels 三方一致性
# ...
```

## 6. 验证模式（ad-hoc 脚本模板）

每个改动写一个 `/tmp/hermes-verify-<scope>.py` 跑完删。**典型结构**：

```python
"""ad-hoc: <一句话说验证什么>"""
import ast, json, sys
from pathlib import Path

ok = True
def chk(label, cond, detail=""):
    global ok
    print(f"  [{'OK  ' if cond else 'FAIL'}] {label}" + (f" -- {detail}" if detail else ""))
    ok &= cond

# 1. 文件可读
src = Path("/path/to/file").read_text()
chk("syntax", True)  # ast.parse 在 try/except 里

# 2. 数据结构正确
tree = ast.parse(src)
# 抽装饰器 / dict / class 属性

# 3. 业务逻辑模拟
def resolve(q): ...

# 4. schema 改后保留其他字段
chk("other config fields unchanged", ...)

print(f"\nresult: {'ALL OK' if ok else 'FAILED'}")
sys.exit(0 if ok else 1)
```

**常见检查项**：
- 装饰器是否存在 + 参数 keyword/positional 正确
- `@register` 的 version 与 metadata.yaml 的 version 一致
- 字典 keys 数量、values 类型
- 数据一致性（CATEGORIES ⊃ _ALIAS keys）
- 边界 case（empty / None / unknown / 大小写）

**journal 验证**（每次 restart 后必看）：

```bash
sudo systemctl restart astrbot
sleep 4
sudo journalctl -u astrbot --since "30 seconds ago" --no-pager | \
  grep -E "plugin_Pic|error|exception|traceback"
```

期望看到：
- `Loading plugin astrbot_plugin_xxx` （启动加载）
- `Added llm tool: <tool_name>` （LLM 工具注册）
- 没有任何 `error/exception/traceback` 跟你的插件相关

## 7. 外部 API 集成的具体配方

### 栗次元 (t.alcy.cc)

17 个分类，URL pattern：`https://t.alcy.cc/{key}` → 302 → 图片

| key | 中文（用户视角） |
|---|---|
| ycy | 二次元自适应 |
| moez | 萌版自适应 |
| ai | AI 自适应 |
| ysz | 原神自适应 |
| pc / moe / fj / bd / ys | PC/萌版/风景/白底/原神 横图 |
| acg | 动图（**返 mp4，会被图片白名单过滤掉**） |
| mp / moemp / ysmp / aimp | 移动/萌版/原神/AI 竖图 |
| tx | 头像方图 |
| lai | 七濑胡桃 |
| xhl | 小狐狸 |

**集成注意**：
- acg 分类返 `video/mp4` 不会被 ImageManager（基于 ALLOWED_IMAGE_MIMES 过滤）接受，会触发"获取失败"
- 用户输 `acg`/动图 时**预期会失败**，不要在 _ALIAS 里加动图除非你改 ImageManager

### NVIDIA Rerank Provider（之前 session 配过）

```json
{
  "id": "nvidia_rerank",
  "type": "nvidia_rerank",
  "api_key": "nvapi-xxx",
  "model": "nv-rerank-qa-mistral-4b:1",
  "provider_type": "rerank"
}
```

URL 拼接规则（AstrBot 内置 `nvidia_rerank_source.py` 的 `_get_endpoint` 实现）：
- 模型名无 `/` → `https://ai.api.nvidia.com/v1/retrieval/nvidia/reranking`
- 模型名含 `/` → `{base_url}/{model_path}/{endpoint}`

## 8. 提交与发版节奏

**每个 PR 一件事**。fork 仓的优势是版本号自己控制，节奏：

| 改动类型 | 版本号 | commit prefix |
|---|---|---|
| 加新功能 | 升小版本 v1.7.0→v1.8.0 | `feat: <一句话>` |
| 修 label / 改字符串 | 不升版本 | `fix: <一句话>` |
| 修 bug | 升 patch v1.8.0→v1.8.1 | `fix: <bug 简述>` |
| 文档/README | 不升版本 | `docs: <一句话>` |

**标签 vs 中文名修改**：永远要同时改两处（schema labels + CATEGORIES label），单独改一个会出现"代码用新名，WebUI 显示旧名"的诡异情况。
