# Worked Example: Evaluating ClawHub Skills for TOON Format

Session: 2026-07-12. User asked "看看这个 https://github.com/toon-format/toon" → explored TOON → asked "如何给你使用" → asked "你先找找有没有 toon 的 skill 或者 Hermes 插件" → "你先看看这几个哪个最合适".

This file captures the discovery + evaluation matrix so future sessions can reuse the pattern (search → matrix → decision) without re-discovering the same pitfalls.

## Step 1: Confirm ClawHub exists locally

```bash
clawhub --version   # ClawHub CLI v0.18.0
```

## Step 2: Search (the only command that works)

```bash
clawhub search toon
# - Searching
# toon  @bonk-moltbot  Toon  (3.690)
# toon-adoption-skill  @nelohenriq  TOON  (2.515)
# toon-json  @zmkkevin  Shrink JSON in Prompts (TOON Encoder/Decoder)  (2.513)
# toonany  @casperkwok  Toonany  (1.490)
```

**Pitfall hit during this session**: `clawhub info <slug>` was tried twice — both failed with usage error. `clawhub` only has `search` for inspection; everything else is install/manage.

## Step 3: Pull hub pages

Hub URL pattern: `https://hub.openclaw.ai/<author>/<slug>` (NOT `clawhub.dev`, NOT `clawhub.ai` — those return 404 / different pages).

```bash
web_extract urls=[
  "https://hub.openclaw.ai/bonk-moltbot/toon",
  "https://hub.openclaw.ai/zmkkevin/toon-json",
  "https://hub.openclaw.ai/nelohenriq/toon-adoption-skill"
]
```

## Step 4: Build the comparison matrix

| | `toon` (@bonk-moltbot) | `toon-json` (@zmkkevin) | `toon-adoption-skill` (@nelohenriq) |
|---|---|---|---|
| **Positioning** | shell pipe `cat data.json \| toon` | Python CLI encode/decode + schema | 纯 spec 文档，**无脚本** |
| **Spec version** | 最新（用 `@toon-format/cli`，spec v3.3） | **TOON v1** ⚠️ 与官方 SDK v3.3 不兼容 | 文档教语法，没绑定 SDK |
| **Implementation** | `npx @toon-format/cli` + 包装脚本 | `scripts/toon_json.py` 独立实现 | 只有 SKILL.md，靠 agent 自己写 |
| **Dependency** | 依赖 `npx` (Node.js) | Python 3 | 零依赖 |
| **Reliability** | 用官方 CLI，权威性最高 | 自己实现的 v1，spec 漂移风险 | 文档，agent 可能写错 |
| **Hermes fit** | 需 PATH 里有 `toon`（要手动 cp 脚本） | 需 Python + 跑脚本 | 零依赖但每次让 agent 现写 → 不可靠 |
| **Score** | 3.69 | 2.51 | 2.52 |

## Step 5: Decide

`toon-adoption-skill` — 排除：只教语法不附工具。

`toon-json` — 排除：明确写"TOON v1"，官方现在是 v3.3，语法差很多（v1 不一定支持 `[N]{fields}` 表头、引用规则可能不同），装上后用官方 SDK round-trip 验证会失败。

**`toon` (@bonk-moltbot) — 推荐**：
- 用 `@toon-format/cli` = 官方 spec v3.3，最权威
- pipe 模型对 LLM 友好：`curl / cat data.json \| toon` 直接出结果
- 评分最高（3.69）
- 唯一缺点：脚本要手动放到 `~/.local/bin/toon`

## Step 6: Recommend install

```bash
clawhub install @bonk-moltbot/toon
cp ~/.hermes/skills/<dir>/toon/scripts/toon ~/.local/bin/
chmod +x ~/.local/bin/toon
command -v toon   # verify
```

Or, since `@toon-format/toon` npm package is already in `~/.npm-global/lib/node_modules/`, write a 30-line wrapper script that uses it directly — cleaner than installing the skill + copying its wrapper.

## Reusable Patterns

1. **Don't trust score alone.** `toon` (3.69) beat `toon-json` (2.51) on every axis except name match. Score is vector relevance, not fitness.

2. **Always check spec version vs reference SDK.** A skill claiming "v1" when the canonical SDK is v3 is a trap — round-trip will fail silently.

3. **Hub URL is `hub.openclaw.ai`, not `clawhub.dev`.** Don't waste web_extract calls on the wrong domain.

4. **`clawhub install` ≠ PATH installation.** Skills that ship scripts need an extra `cp + chmod + verify on PATH` step. Document this for any skill whose value is the binary, not the docs.

5. **Pure-teaching skills (`-adoption`, `-guide`) need a companion tool** to be useful. If the agent has no encoder/decoder already, those skills are dead weight.

## Verification That Recommendation Was Sound — FAILED

Verified locally that `@toon-format/toon` SDK v2.3.0 (latest stable) is already installed at `~/.npm-global/lib/node_modules/@toon-format/toon/`. Quick smoke test:

```js
import { encode, decode } from '/home/po/.npm-global/lib/node_modules/@toon-format/toon/dist/index.mjs';
// → produces:
task: find bugs
friends[3]: ana,luis,sam
hikes[3]{id,name,distanceKm,elevationGain,companion,wasSunny}:
  1,Blue Lake Trail,7.5,320,ana,true
  ...
```

SDK works → installing `@bonk-moltbot/toon` skill + its `scripts/toon` wrapper (which just `npx @toon-format/cli` under the hood) is sound. Round-trip is lossless.

## Correction: Original Recommendation Was Wrong (2026-07-12 second pass)

**The `@bonk-moltbot/toon` skill is an empty shell.** After `clawhub install @bonk-moltbot/toon`, the package contained only:

```
/.clawhub/origin.json
/_meta.json
/SKILL.md
/skill-card.md
```

**No `scripts/toon` file.** The README told users to `cp scripts/toon ~/.local/bin/`, but `scripts/` didn't exist. The 3.690 score was for `SKILL.md` content quality, not delivery completeness. The original Step 6 recommendation cannot be executed — the file isn't there.

`@zmkkevin/toon-json` has a working `scripts/toon_json.py` BUT it implements a fork called "TOON v1" with format prefix `v1|J|...` — round-trip fails against any data encoded by the official `@toon-format/toon` SDK (spec v3.3). Same incompatibility on both candidates, opposite directions: `toon` ships nothing, `toon-json` ships incompatible bytes.

**What actually worked**: a 14-line Node ESM wrapper written from scratch at `~/.local/bin/toon` that imports the locally-installed `@toon-format/toon` SDK directly. Uses ESM `import` (NOT CJS `require` — the SDK is ESM-only, mixing them throws `ReferenceError: require is not defined in ES module scope`). Verified with 50-row uniform-primitive dataset: 5282 bytes JSON → 1782 bytes TOON (-66.3%), lossless round-trip.

```javascript
#!/usr/bin/env node
import { encode, decode } from '/home/po/.npm-global/lib/node_modules/@toon-format/toon/dist/index.mjs';
import { readFileSync } from 'fs';
const src = readFileSync(0, 'utf8');
if (process.argv[2] === '--decode') {
  process.stdout.write(JSON.stringify(decode(src.trim()), null, 2) + '\n');
} else {
  try { process.stdout.write(encode(JSON.parse(src)) + '\n'); }
  catch { process.stdout.write(src); }  // passthrough for non-JSON
}
```

## Revised Reusable Patterns (supersedes earlier list)

1. **Don't trust score alone.** `toon` (3.69) beat `toon-json` (2.51) on every axis except name match AND delivery completeness. Score is vector relevance, not fitness, not shipping.

2. **Always check spec version vs reference SDK.** A skill claiming "v1" when the canonical SDK is v3 is a trap — round-trip will fail silently.

3. **Hub URL is `hub.openclaw.ai`, not `clawhub.dev`.** Don't waste web_extract calls on the wrong domain.

4. **`clawhub install` ≠ PATH installation. Always `ls scripts/` after install** to confirm the promised wrapper actually shipped. Empty-shell skills (SKILL.md describes a script that doesn't exist) are common — write your own wrapper using the locally-installed SDK instead.

5. **Pure-teaching skills (`-adoption`, `-guide`) need a companion tool** to be useful. If the agent has no encoder/decoder already, those skills are dead weight.

6. **When both the empty-shell AND the spec-drift candidates fail, write your own minimal wrapper using the locally-installed upstream SDK.** 14 lines is faster than debugging someone else's incompatible reimplementation.

7. **TOON tabular eligibility is empirical**: data with nested arrays of strings (e.g., `topics: ["react","ssr"]`) falls back to list-style and **grows** JSON by ~6% instead of shrinking. Only uniform-primitive arrays hit the 60%+ compression claim. Verify with a test encode before committing.