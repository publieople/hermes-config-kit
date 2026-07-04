---
name: notionnext-fork-maintenance
description: |
  Maintain a NotionNext fork (publieople/NotionNext and similar) including: upstream sync that diverged 1+ months behind, branch rebase onto a clean upstream HEAD, GitHub/Vercel deployment verification, and debugging Vercel build failures. Load when the user mentions "NotionNext 同步失败", "fork 跟 upstream 分叉", "Vercel 部署失败", "rebuild on upstream", or any workflow around forking/upgrading notionnext-org/NotionNext.
version: 1.0.0
author: Hermes Agent
tags: [notionnext, github, vercel, fork, deployment, build, sync]
related_skills:
  - notionnext-blog
---

# NotionNext Fork 维护与部署

NotionNext 站点 fork (`publieople/<name>`) 在长期分叉后,如何回 baseline、与 upstream 同步、debug Vercel 部署 — 不再每个 session 现抓。

## 何时加载

- "NotionNext 同步失败" / "fork 跟 upstream 分叉了" / "Upstream Sync workflow 失败"
- "fork 怎么升级到最新 upstream"
- "Vercel 部署 build fail" / "yarn run build exited with 1"
- "merge conflict 几百个" / "force-push main"
- "`.github/workflows/sync.yaml` 改 upstream 仓库"

## 触发时立即检查的若干面

一次性读完所有可读面,**别猜**。每条都是真实排错路径。

```bash
# 1. fork 状态
gh repo view publieople/NotionNext \
  --jq '{default_branch, pushed_at, html_url, is_fork}'

# 2. fork HEAD vs upstream HEAD
gh api repos/publieople/NotionNext/commits/main --jq '{sha, msg: .commit.message | split("\n")[0]}'
gh api repos/notionnext-org/NotionNext/commits/main --jq '{sha, msg: .commit.message | split("\n")[0]}'

# 3. upstream 真实最新 tag(branch HEAD 不一定是 release tag!)
gh api repos/notionnext-org/NotionNext/tags --jq '[.[] | {name, sha: .commit.sha[0:7]}] | .[0:8]'

# 4. fork 的 Upstream Sync workflow 最近 5 次运行
gh run list --repo publieople/NotionNext --workflow=sync.yaml --limit 5 \
  --json databaseId,conclusion,createdAt,event

# 5. 当前 fork branch 列表 + default branch
gh api repos/publieople/NotionNext --jq '{default_branch}'
gh api repos/publieople/NotionNext/git/refs/heads --jq '.[] | .ref'

# 6. Vercel production deployment 状态(token 在 ~/.vercel/auth.json)
TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.vercel/auth.json'))['token'])")
PROJ="prj_mNU1hAPHWEhTG1gcOqhnufP7QwJe"  # notion-next project
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.vercel.com/v6/deployments?projectId=$PROJ&limit=10&target=production" \
  | jq '.deployments[] | {sha: .meta.githubCommitSha[0:10], state, errorCode}'
```

把它们全 dump 出来再读 — "哪一个 production build 跟 fork HEAD 是否同步"是后面的关键诊断点。

## Fork Reset 流程(累积 1.5+ 个月分叉时的唯一解)

**不要试图 3-way merge 上百个 add/add 文件** — 必败。正确做法是 reset 到 upstream 单一 commit,保留 fork-only 11 个左右 overlay 文件单独 patch。

### 步骤

1. **抓 11 个真正的 fork-only 文件**(`git log origin/main --not $(merge-base) --name-only --pretty=format: --no-merges`):
   - `blog.config.js`(作者/BIO/链接/主题 默认值)
   - `conf/analytics.config.js`、`conf/animation.config.js`、`conf/code.config.js`、`conf/comment.config.js`、`conf/contact.config.js`、`conf/image.config.js`、`conf/right-click-menu.js`
   - `public/css/custom.css`(封面 blur/glassmorphism 等多次迭代 CSS)
   - `public/favicon.ico`(自定义 ico)
   - `.github/workflows/sync.yaml`(改 sync 行为)
   - `package.json` 的多次手动 bump(让 upstream 自己 auto-bump)

2. **拣 upstream 锚点**:用 `gh api repos/notionnext-org/NotionNext/tags`,**用 tag SHA 而非 `commits/main` SHA**。Branch HEAD 不一定是 release-ready 的代码,有时隔了好几个 hotfix tag。

3. **`git checkout --orphan <branch> <upstream-sha>`**:把 working tree 替换到 upstream HEAD,parent 自动变成 upstream commit。

4. **拷 11 个 overlay 回 working tree**(`cp -r ...`),commit + force-push。

### GitHub API 限流

`gh api ... -X DELETE` on default branch → **HTTP 422 "Cannot delete the default branch"**。绕过:

```bash
# 1. 切 default 到临时分支
gh api repos/publieople/NotionNext -X PATCH -f default_branch=reset-fork-orphan

# 2. 现在 default 切走了,可以删原 main
gh api repos/publieople/NotionNext/git/refs/heads/main -X DELETE

# 3. 重建 main 指向同一 SHA
SHA=$(gh api repos/publieople/NotionNext/git/refs/heads/reset-fork-orphan --jq .object.sha)
gh api repos/publieople/NotionNext/git/refs \
  -X POST -f ref=refs/heads/main -f sha=$SHA

# 4. 切 default 回 main
gh api repos/publieople/NotionNext -X PATCH -f default_branch=main

# 5. 删临时分支
gh api repos/publieople/NotionNext/git/refs/heads/reset-fork-orphan -X DELETE
```

注意步骤 5 之后第 4 步:**default 必须先切回 main 再尝试删 temp 分支**,否则又会有 "Cannot delete the default branch"。

## Vercel Deployment Debug

### 关键: `module_not_found` 不是缺 npm 模块

Vercel API 返回的 `errorCode` 对 build fail 是 blanket 简化,**真正的 root cause 在 events 里**。

```bash
TOKEN=$(python3 -c "import json; print(json.load(open('$HOME/.vercel/auth.json'))['token'])")
# 找到出错 deployment 的 uid
gh_deployment_uid=$(gh api ... | jq -r .uid)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.vercel.com/v1/deployments/$gh_deployment_uid/events" \
  | jq '.[] | select(.text | test("TypeError|module|undefined|cannot|Cannot read")) | .text[:300]'
```

### `Upstream Sync` workflow 触发方式

```bash
# 手动触发(不依赖 cron schedule)
gh workflow run "Upstream Sync" --repo publieople/NotionNext

# 看最近 1 次 run 日志
gh run list --repo publieople/NotionNext --workflow=sync.yaml --limit 1 --json databaseId \
  | jq '.[] | .databaseId' | xargs -I {} gh run view {} --repo publieople/NotionNext --log-failed
```

### Sync workflow `upstream_sync_repo` 字段

```yaml
upstream_sync_repo: notionnext-org/NotionNext  # 不是 tangly1024/NotionNext
```

upstream 已经迁组织。`tangly1024/NotionNext` 仍 redirect,但 aormsby action 不走 GitHub 网络 redirect 仍可能出现 `fatal: error processing shallow info`。

## Upstream NotionNext Build Errors — 已知问题家族

`processPostData` / `getPostBlocks` 在 4.10.0 引入了对 `block.value.content` 的严格假设。Notion 数据库某些 block type(`sync_block`, `column_list`, `child_database` toggle 等)的 `content` 是 `null` 或 string 而非 array 时,build 时 throw:

```
TypeError: t.block[l].value.content is not iterable
[resolvePostProps] processPostData failed
Error: Error serializing .prev returned from getStaticProps in "/[prefix]/[slug]"
Command "yarn run build" exited with 1
```

**Upstream 修复状态**:
- issue #3943 (历史):`Cannot destructure property 'actual'`,修在 PR #3946 → 合到 4.9.5.x
- 4.10.1 (`9c793e3`):修了 `sync_block` block type 但**没有覆盖**所有同 family 路径
- 4.10.3 (`896780c`):build fail 仍可复现,说明 issue 家族仍未根除

**当前安全选择**:production 用 `ca670b059e` (4.9.5.5) 或 4.9.5.x 系列 tag SHA。**不要**升 4.10.x 直到 upstream 出 4.10.4+ 进一步修。

诊断一句话:**build error "yarn run build exited with 1" + `errorCode="module_not_found"` ⇒ 大概率 processPostData Notion data schema 错容问题**,不是真的缺包。

## 偏好:用 gh cli 不用 curl | python

直接 `gh api` 比 `curl | python3 -c ...` 更耐网络、不会触发 smart approval。规则:
- `curl -s -H "Authorization: Bearer $TOKEN" "$URL"` + `jq` 是允许的(纯 pipeline,非 ssh injection 类)
- 用 gh 拿 raw file:`gh api -H "Accept: application/vnd.github.raw" repos/<o>/<r>/contents/<path>?ref=<sha>`(注意 `?ref=` 在 url query)
- 搜 issues/PRs:`gh search issues <keyword> --repo ...`、`gh pr list --repo ... --search <keyword>`

## 偏好:宣称完成前 cross-surface sweep

完成 "fork 修好了" 这类收尾时,**必须**检查过的面:
1. `gh api` 看 fork HEAD sha + parent
2. fork `<default_branch>` 实际指向哪
3. sync workflow 最近 run 的 conclusion
4. Vercel production deployment state(target=production 至少 1 条 READY)
5. production 站 HTML 200 + 内容对(AUTHOR/BIO 等个人化字段仍在)

5 条任意一条异常 ⇒ 没完。

## pitfall 速查

- **用 commit SHA 而非 "tag"-style ref spec** — `git fetch upstream 896780cb...:refs/heads/v4.10.3` 在某些 git 版本报 "致命错误:无法找到远程引用 896780cb"。直接用完整 40 字符 SHA。
- **`git fetch` 大 fork 必 timeout**(43MB+):换 shallow + 单 commit SHA。`git fetch --depth=1 upstream <full-sha>:<local-ref>`。
- **Vercel UI 看 preview 失败常常 SSO 挡住** — 没 vercel token 时 `curl -I https://...vercel.app` 看到 302 redirect 到 Vercel login,取不到真正的 build error。这条强制用 API 而非 UI。
- **Force push 必加 `--force-with-lease`** — 不然队友刚 push 的 commit 会被无声吞掉。`--force-with-lease` 拿 ref log 比照,发现 remote 已前移就拒绝。(_hermes 通常是 solo,所以无风险,但保习惯_)
- **upstream_sha fetch 详细 output 走 `tail -3` 而非 `head -3`** — `git fetch` 网络超时场景里 error 在最后。
- **Cron sync workflow 成功后 ≠ production 会重 deploy** — Vercel 只在 fork HEAD sha 变化触发 production build,WebHook 检测到的新 commit 不一定能 short-circuit 进 production。git ref "delete-and-recreate" 操作也会让 GitHub API 推 sha 给 Vercel 但 Vercel 不一定 rebuild。要主动 promotion 才能把 preview 升 production。

## 相关 skill

- `notionnext-blog` — 发布文章到 Publieople Blog,**不**动 fork 维护
- `comet` — 用 spec-driven 流程时,可作 fork rebase 的设计阶段工具
