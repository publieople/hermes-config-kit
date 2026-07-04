---
name: notionnext-blog
description: 发布文章到 Publieople's Blog（NotionNext 驱动的博客）——搜索数据库、理解 schema、创建文章、验证上线。
category: productivity
---

# NotionNext 博客发布

## 触发条件
- 用户要求"写博客""发到博客""发布文章""post to my blog"
- 用户提到 blog.for-people.cn 或 NotionNext
- 需要查询/管理已有的博客文章
- **新增**:补全/修改已发布 Notion 页面里的章节内容(中间插入 block)
- **新增**:用户的 fork 跟上游 NotionNext 不同步 — Upstream Sync workflow 失败、conflict 报错、上游组织迁了、sync 几个月没动过
- **新增**:"vercel 部署失败 / build exit 1 / module_not_found / production 没刷新 / deployment 没触发"

## 相关文件
- `references/notion-blocks.md` — 完整 block 构造模板(高级 block、表格、媒体、错误码、限流)
- `references/fork-sync-and-vercel.md` — fork ↔ upstream 同步失败 + Vercel build/deploy 失败排查模式(含你 fork 这次恢复的实战参考)

## 前置条件

Notion API key 在 `~/.config/notion/api_key`，格式 `ntn_...`。

## 博客数据库

- **名称**: Publieople's Blog
- **数据库 ID**: `02e0b2a07b164c37abb9cfc3db88c605`
- **NotionNext 配置中的 NOTION_PAGE_ID**: `097e5f674880459d8e1b4407758dc4fb`（blog.config.js）
- **博客地址**: https://blog.for-people.cn

## 数据库 Schema

| 属性 | 类型 | 可选值 |
|------|------|--------|
| `title` | title | — |
| `status` | select | Published, Invisible, Draft |
| `type` | select | Post, Page, Notice, Menu, SubMenu, Config |
| `category` | select | 技术分享, 心情随笔, 差生文具多, 知识分享, 资源整理, 项目经历, 折腾记录, 活动体验 |
| `slug` | rich_text | URL 路径（如 `tiez-webdav-debugging`） |
| `tags` | multi_select | 自由标签 |
| `summary` | rich_text | 文章摘要（用于 meta description） |
| `date` | date | 发布日期 |
| `password` | rich_text | 文章密码（可选） |
| `icon` | rich_text | 自定义图标 URL（可选） |

## 发布流程

### 1. 获取 key

```python
import subprocess
key = subprocess.run(["cat", "/home/po/.config/notion/api_key"], capture_output=True, text=True).stdout.strip()
```

### 2. 创建文章（Python + Notion API）

**不要用 shell curl**——API key 在终端中会被掩码为 `***` 导致 auth 失败。

```python
import json, urllib.request

DB = "02e0b2a07b164c37abb9cfc3db88c605"

markdown = """# 文章标题

文章内容（Notion-flavored Markdown）。
"""

payload = {
    "parent": {"database_id": DB},
    "properties": {
        "title": {"title": [{"text": {"content": "文章标题"}}]},
        "type": {"select": {"name": "Post"}},
        "status": {"select": {"name": "Published"}},
        "category": {"select": {"name": "折腾记录"}},
        "date": {"date": {"start": "2026-06-08"}},
        "slug": {"rich_text": [{"text": {"content": "url-slug"}}]},
        "tags": {"multi_select": [{"name": "Tag1"}, {"name": "Tag2"}]},
        "summary": {"rich_text": [{"text": {"content": "文章摘要"}}]}
    },
    "markdown": markdown
}

req = urllib.request.Request(
    "https://api.notion.com/v1/pages",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    },
    method="POST"
)

with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read())
    page_id = result["id"]
    print(f"Published: https://notion.so/{page_id.replace('-','')}")
```

### 3. 验证上线

NotionNext 默认 revalidate 60 秒。验证：

```bash
curl -sI "https://blog.for-people.cn/article/{slug}" | grep HTTP
# HTTP/2 200  → 上线成功
```

## 文章写作风格

来自用户资料：
- **先结论后展开**：用 `<callout>` 把结论放在开头
- **精确、直接**：不讲故事，说事实
- **技术叙事**：按时间线展开调试过程，带代码片段
- **Notion 块**：善用 `<callout>`、`<details>`、代码块等 Notion-flavored Markdown

## 编辑已有文章:在中间位置插入 block

NotionNext 渲染按 DB 顺序,所以"补充某章节内容"必须插在指定 block 后面,不能 append 到页尾。

API 支持 `position` 参数,放到 body 顶层(不是 children 里):

```python
# 找到目标 H2 的 block id,作为 anchor
H2_ID = "5a066ad7-c9c4-8304-aaff-81441e0e7744"  # 例:「版本控制」H2

payload = {
    "children": [/* 任意数量的 block,单次上限 100 */],
    "position": {"type": "after_block", "after_block": {"id": H2_ID}}
}
req = urllib.request.Request(
    f"https://api.notion.com/v1/blocks/{PAGE_ID}/children",
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"},
    method="PATCH",  # 注意是 PATCH 不是 POST
)
```

### 探针-验证-批量 模式(必须)

插入位置失败会报 400,但错误信息不告诉你具体哪个 block 错了。**先用一个标记 callout 验证位置语义**,再批量:

1. 插入一个 `📌 [probe]` 探针 → fetch 页面 block 列表,确认探针确实出现在目标 H2 之后
2. 删除探针(DELETE `/v1/blocks/{probe_id}`)
3. 批量插入正文

跳过这一步直接批量 = 大概率插错位置,删起来很烦。

### 块数量与单次上限

- 单次请求最多 **100 个 block**
- 100 不是看 children 数组长度,而是**展开后**的所有 leaf block 数(每个 `numbered_list_item` / `bulleted_list_item` 算 1 个 leaf,但有的端点会算成多个 children)
- 一次插 60+ 个 numbered_list_item + bullet 经常触发 100 上限被截断,**插入后必须 fetch 验证尾部内容是否完整**

### 构造 block 的辅助函数

Ponytail: 5 个 helper 覆盖 90% 场景,不要造更复杂的。

```python
def p(text): return {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":text}}]}}
def h2(text): return {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":text}}]}}
def h3(text): return {"object":"block","type":"heading_3","heading_3":{"rich_text":[{"type":"text","text":{"content":text}}]}}
def bullet(text): return {"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":text}}]}}
def num(text): return {"object":"block","type":"numbered_list_item","numbered_list_item":{"rich_text":[{"type":"text","text":{"content":text}}]}}
def code(lang, text): return {"object":"block","type":"code","code":{"rich_text":[{"type":"text","text":{"content":text}}],"language":lang}}
def callout(text, emoji="💡"): return {"object":"block","type":"callout","callout":{"icon":{"type":"emoji","emoji":emoji},"rich_text":[{"type":"text","text":{"content":text}}]}}
def divider(): return {"object":"block","type":"divider","divider":{}}
```

完整 list / 表格 / toggle / image / bookmark 等高级 block 见 `references/notion-blocks.md`。

### Code block language 白名单

**`language` 字段是枚举,传错立刻 400 Bad Request 且错误信息不指出字段名。** 常用值:

`plain text` / `bash` / `shell` / `powershell` / `python` / `javascript` / `typescript` / `json` / `yaml` / `html` / `css` / `markdown` / `sql` / `go` / `rust` / `java` / `c` / `c++` / `c#` / `ruby` / `php` / `mermaid` ...

**没有 `"text"` 这个值** —— 纯文本框图用 `"plain text"`。

### 删除 block

```python
req = urllib.request.Request(
    f"https://api.notion.com/v1/blocks/{block_id}",
    headers={"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28"},
    method="DELETE",
)
```

返回 200 即成功。Notion API **不支持"移动 block",只能 delete + re-append**。

## 常见错误

### `comment is not a property that exists`
数据库中属性名是 `comment `（尾部有空格），但 API 要求精确匹配。忽略此属性即可，不影响发布。

### API key 失效（`unauthorized`）
终端 curl 命令中 `$NOTION_KEY` 被系统掩码为 `***`，导致 auth header 变成字面量 `Bearer ***`。**必须用 Python 脚本**读文件取 key。

### 数据库找不到（`Could not find database`）
两种可能：
1. 数据库未授权给 Hermes integration → 在 Notion 里 `...` → Connections → 添加 Hermes
2. ID 使用了 NOTION_PAGE_ID（page token）而非 database_id → 用 search API 搜索 "blog" 找到真正的 database_id

## 博客运维:fork sync 与 Vercel 部署

发布文章之外的"博客不工作"问题主要走这两条路径。详细步骤见 `references/fork-sync-and-vercel.md`。

### 路径 A — sync 失败 / Upstream Sync workflow 报错

1. `gh run list --workflow="Upstream Sync"` 看最近 10 次结论。`conclusion: failure` 是信号。
2. `gh run view <id> --log-failed | grep -E "CONFLICT|fatal|error processing shallow"` 读根因。
3. **三种常见根因**:
   - 上游 repo owner 迁移(`tangly1024 → notionnext-org` 或类似)→ 修 `.github/workflows/sync.yaml` 的 `upstream_sync_repo`
   - long-term fork 跟 upstream 分叉 → 走 fork 重置流程(见 references)
   - `fatal: error processing shallow: 4` → `aormsby` sync action 的 `shallow_since` 找不到合并基线,等同分叉前兆
4. 修 sync.yaml 后手动 `gh workflow run "Upstream Sync"` 验证一次,**只看结论**:success → 修好了;failure → log 看新的 reason。

### 路径 B — Vercel build/deploy 失败

1. **站点是否还在跑**:`curl -sI https://blog.for-people.cn | head -3`。200 + Vercel header → production 没事;只关心最近一次失败的 build。
2. `vercel login`(device code)→ `curl -H "Authorization: Bearer $TOKEN" "https://api.vercel.com/v6/deployments?projectId=$PRJ"` 拉最近 15 次 list。
3. **Vercel 上 `errorCode: module_not_found` 经常是 misnamed**。真因要看 events:
   ```bash
   curl -s -H "Authorization: Bearer $TOKEN" \
     "https://api.vercel.com/v1/deployments/$DID/events" \
     | python3 -c "import sys, json; print('\n'.join(e.get('text','') for e in json.load(sys.stdin) if e.get('type')=='stderr'))"
   ```
4. **最常见的 upstream 4.10.0+ build fail 真因** = `processPostData` schema 严格化:`TypeError: t.block[l].value.content is not iterable` → 某篇 Notion 文章数据不全。会在 yaml 看到多个 `[article/<slug>] [resolvePostProps] processPostData failed`。
5. **Production 不动时也别傻等**。clean 路径: 看 production 是否仍 READY(可能在跑旧 commit),如果 READY 且用户没受影响,短期 hold,不要 force 推到新 commit 上 → 那个 commit 会再次撞同样的 build fail。
6. Preview URL 经常被 Vercel SSO 拦,看不到 build page ≠ 真坏。查 `gh api .../deployments/$DID/statuses` 拿到结论状态。

## 触发 sync 前跟用户的 keep-it-clear 习惯

用户有时会**盲复制**我前一条消息里的 gh 命令 — 在多阶段任务里这经常导致在不合理时机触发 workflow(例:关闭一个 fork main 的 PR 前就先 gh workflow run)。规则:在多阶段任务里,**每个 gh 命令前都必须先句子明示"前提是 X 已完成,否则 Y"**,**且要强调当前阶段没用上**。例:别顺手说"你也可以试试 gh workflow run verify", — 如果用户真去跑了,就要在下一回合补救而不是解释。

## 一次 fork 跟 upstream 完全分叉后的恢复模板(参考)

如果 fork 跟 upstream 累积几百个 conflict / 几百个 add/add,直接 `git merge upstream/main` 会爆炸。**最小侵入恢复**:

1. **在干净 fresh clone 上 `git checkout --orphan reset-fork upstream/main`** — 工作树 = 上游 HEAD,父历史脱离 fork 完全分叉状态。
2. 从 `origin/main`(`git show origin/main:<path>`)拷回 fork-only 个性化文件(典型: blog.config.js、conf/*、public/css/custom.css、public/favicon.ico、.github/workflows/sync.yaml 里的 fork 特定改)。
3. `git commit -m "chore(rebase): reapply fork-specific overlays on <upstream version>"`。
4. 推到新分支,**不要 force push main**。
5. **GitHub server 不允许 API 直接删 default branch**。绕道:
   - `PATCH /repos/{owner}/{repo}` 把 `default_branch` 改成目标 branch(例如 `reset-fork`)
   - `DELETE /repos/{owner}/{repo}/git/refs/heads/<old-main>`
   - `POST /repos/{owner}/{repo}/git/refs` 重建 `<new-main>` 指到新 commit
   - `PATCH /repos/{owner}/{repo}` 把 `default_branch` 改回 main
6. 跑 `gh workflow run "Upstream Sync"` 验证 sync 健康。如果结论 "No new commits to sync. Finishing sync action gracefully." — 修复成功。
7. **不要**当场跑 `yarn build` 试图验证 Vercel — 让 Vercel 自己 webhook 触发;如果 fork main 出现"删了重建",Vercel 可能错过新 ref,**手动 trigger 一次**(选项见 references)或等下一个 push。

### 数据库找不到（`Could not find database`）
两种可能：
1. 数据库未授权给 Hermes integration → 在 Notion 里 `...` → Connections → 添加 Hermes
2. ID 使用了 NOTION_PAGE_ID（page token）而非 database_id → 用 search API 搜索 "blog" 找到真正的 database_id

## 博客运维:fork sync 与 Vercel 部署