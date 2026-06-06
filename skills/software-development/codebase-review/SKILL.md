---
name: codebase-review
description: "Analyze unfamiliar codebases from archives or repos — architecture understanding, code quality assessment, structured feedback — plus open-source tool survey for build-by-integration projects."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [code-review, project-analysis, architecture-review, code-quality, student-project, oss-survey, tool-selection, integration-planning]
    related_skills: [github-code-review, requesting-code-review, plan, writing-plans, spike]
---

# Codebase Review — Project Analysis from Scratch

Analyze an unfamiliar project holistically: extract from archive, understand architecture, evaluate code quality, and deliver structured feedback.

## When to Use

- User shares a project archive (zip/tar/rar) and wants a review
- User asks "看看我这个项目怎么样" / "帮我审查代码"
- User shares a GitHub repo link wanting an architecture overview
- Student project evaluation / peer review
- Any "what is this project about and is it good" question

**Not for:** git diff / PR reviews (use `github-code-review`), pre-commit verification (use `requesting-code-review`), LOC counting (see `references/codebase-inspection-pygount.md`).

## Workflow

### Step 1 — Locate and Examine Archive

Determine where the project lives:

```bash
# Windows path → WSL mount
ls -la "/mnt/e/path/to/project.zip"

# Check file size and type
mcp_windows_mcp_FileSystem(mode='info', path='E:\\path\\to\\project.zip')
```

Always check: file size, modification date, whether it includes node_modules (red flag).

### Step 2 — List and Extract Contents

List archive structure first — don't blindly extract:

```bash
unzip -l project.zip | head -100
# Or for tar:
tar tf project.tar.gz | head -50
```

**Critical: skip node_modules on extraction.** They bloat the extract (often 500MB+) and aren't source code.

```bash
# Extract only source files — exclude node_modules and dist
unzip -o project.zip 'src/*' '*.md' '*.json' '*.ts' '*.tsx' '*.js' '*.css' '*.html' 'vite.config.*' 'tsconfig*' '*.config.*' 2>/dev/null

# Or for repos: git clone, skip dotfiles
```

Alternative: use `grep -v` on `unzip -l` to filter out node_modules/dist before deciding what to extract.

### Step 3 — Read Structural Files First (in this order)

These files tell you what the project IS before you look at the code:

1. **package.json** — dependencies, scripts, project name
2. **README.md** — what the project claims to do
3. **Any 使用说明书 / README_CN / manual** — user-facing docs (often reveal more than README)
4. **vite.config.ts / next.config / webpack.config** — build setup
5. **tsconfig.json / tsconfig.app.json** — TypeScript strictness
6. **.gitignore** — what they think should be ignored (often missing)

### Step 4 — Read Core Source in Dependency Order

Follow the data flow / dependency graph:

1. **Types/Interfaces** (`types/`, `types.ts`) — the data protocol, reveals the mental model
2. **State Management** (`store/`, `context/`, `redux/`) — how data flows
3. **Parsers/Utils** (`parser/`, `utils/`, `lib/`) — where logic lives
4. **Entry point** (`main.tsx`, `index.ts`) — how it boots
5. **Root component** (`App.tsx`, `App.js`) — composition
6. **Page/Container components** — layout and orchestration
7. **Leaf components** — implementation details, 3D scenes, chart configs, etc.

### Step 5 — Assess Code Quality (the checklist)

**Architecture (30%)**
- [ ] Clear separation of concerns? (types / store / components / utils)
- [ ] Single responsibility per file?
- [ ] Data flow is unidirectional and traceable?
- [ ] Error boundaries / error handling exists?
- [ ] Has config/constants extracted, not hardcoded?

**TypeScript hygiene (20%)**
- [ ] Proper types, not `any` everywhere?
- [ ] Shared interfaces, not duplicated?
- [ ] Enums / union types for constrained values?
- [ ] Generic helper functions where appropriate?

**UX / Polish (20%)**
- [ ] Loading states, empty states, error states?
- [ ] Performance considerations (memoization, debounce)?
- [ ] Responsive layout?
- [ ] Transition animations / feedback?

**Code style (15%)**
- [ ] Consistent naming conventions?
- [ ] Comments explain WHY, not WHAT?
- [ ] No dead code / console.log / commented blocks?
- [ ] Imports organized?

**Project hygiene (15%)**
- [ ] `.gitignore` exists and is populated?
- [ ] `node_modules` not committed?
- [ ] Package.json has meaningful name and version?
- [ ] index.html has proper `<title>`?
- [ ] Has a real README (not framework boilerplate)?

### Step 6 — Deliver Structured Feedback

Format:

```
## 项目分析：「项目名」

**作者：** 开发者
**时间：** 日期

### 项目定位（一句话）

### 技术栈
| 层 | 技术 |
|---|---|

### 代码质量评估
坦白的评价 + 具体证据（引用源码行号）

### 亮点（指出做得好的地方）

### 问题/改进点（按优先级）

### 可以怎么帮他（可选，给出下一步建议）
```

Rules:
- Be specific — reference actual file paths and line numbers
- Praise genuinely — don't manufacture approval
- Prioritize — distinguish "ship-blocker" vs "nice-to-have"
- Offer help — "你要我直接帮改吗？" at the end

## Open-Source Tool Survey (Build by Integration)

Use this section when the user wants to **build by integration** — instead of implementing functionality from scratch, research and select the best open-source libraries to combine. Also use when the user says "research what's out there", "compare X vs Y", "find good open-source alternatives".

### Core Philosophy

**Don't implement what you can integrate.** Before writing a single line of feature code, assume there's already a good OSS solution.

### When to Use This Section

- **File format handling** (PDF viewers, image editors, document parsers)
- **Rich UI components** (diagram editors, spreadsheet grids, code editors)
- **Media processing** (video players, audio visualizers, 3D viewers)
- **Any "swiss army knife" app** combining multiple capabilities
- **Tech stack decisions** where 2+ competing libraries exist
- You catch yourself thinking "I could build this from scratch" — stop and research first

### Methodology

#### Step 1: Categorize the Problem

Break the project into independent functional categories. Each becomes one research thread.

#### Step 2: Parallel Research via delegate_task

For 3+ categories, fan out research:

```javascript
delegate_task({
  tasks: [
    {
      goal: "Research best open-source web-based code editor for React",
      context: "Requirements: pure frontend, MIT license, syntax highlighting for Python/JS/TS/Go, mobile-friendly, good bundle size. Evaluate: CodeMirror 6, Monaco Editor, Ace Editor, CodeJar.",
      toolsets: ["web"]
    },
    {
      goal: "Research best PDF viewer for browser integration",
      context: "Requirements: pure frontend, MIT/Apache 2.0 license. Evaluate: PDF.js (Mozilla), react-pdf.",
      toolsets: ["web"]
    }
  ]
})
```

**Each subagent prompt should include:** clear requirements, named candidates, success criteria.

#### Step 3: Consolidate Findings

Collect all results and build a master comparison table:

| Category | Winner | Runner-up | License | Bundle Size | Reason |
|----------|--------|-----------|---------|-------------|--------|
| Text editor | CodeMirror 6 | Monaco Editor | MIT | ~300KB | Modular, mobile-friendly |
| PDF viewer | PDF.js | — | Apache 2.0 | ~300KB | Only game in town |

#### Step 4: Estimate Total Bundle Impact

Add up winners' bundle sizes:
- < 500KB: Excellent
- 500KB-2MB: Good — use code splitting
- > 2MB: Heavy — lazy-load aggressively

#### Step 5: Write Recommendations

Present in the plan document with:
- Winner summary table
- Integration notes with minimal code snippet per winner
- Edge format coverage (formats with no drop-in solution)
- Architecture diagram showing how pieces fit together

#### Step 6: Flag Licensing Risks

| License | Action |
|---------|--------|
| MIT | ✅ Go ahead |
| Apache 2.0 | ✅ Go ahead |
| AGPL | ❌ Find alternative |
| LGPL | ⚠️ Acceptable for library use |

**Check for known license traps**: Handsontable (MIT→non-commercial), SSPL, "source available".

### Session-Specific Research

Save session-specific research (detailed comparison tables, winner choices, integration snippets) as a reference file under the `open-source-tool-survey` section of this skill:

```
software-development/codebase-review/
├── SKILL.md
└── references/
    └── tool-survey-<YYYY-MM-DD>-<project-slug>.md
```

Use `skill_manage(action="write_file")` with `file_path="references/tool-survey-<slug>.md"`.

## Pitfalls

1. **Don't extract node_modules** — zip can be 124MB because of it but source is tiny (under 500KB for typical student project). Use targeted glob patterns.
2. **Read the docs file FIRST** — many Chinese students write a detailed 使用说明书.md that reveals the project's intent better than the README.
3. **Check for dist/ output** — if dist exists, check if it works standalone (static deploy-ready). This is often the easiest way to validate.
4. **Don't review the Vite/React scaffold code** — default README, default config, default ESLint setup are boilerplate, not the student's work. Focus on `src/`.
5. **Balance praise with critique** — student projects need confidence building. Always lead with what's genuinely good.
6. **Zip from WeChat** — the file path pattern `xwechat_files/.../temp/RWTemp/...` means it came from WeChat file transfer. The file may have been renamed by WeChat.
