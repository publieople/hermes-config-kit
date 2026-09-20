---
name: delegate-repo-analysis
description: Use when orchestrating reverse-engineering, refactor, or build workflows on a codebase — the parent agent dispatches leaf subagents to read and analyze the codebase while the parent only orchestrates and accepts reports. Covers regent-reverse, regent-refactor, regent-build and any "look at this repo, produce structured output" task. Triggers on phrases like "派子agent去测试", "reverse this repo", "refactor to spec", or any task that targets a worktree (clone, spec dir, refactor output) where the parent is tempted to run read_file directly.
version: 0.1.0
author: REgent contributors
license: GPL-3.0-or-later
metadata:
  hermes:
    tags: [delegation, subagent, reverse, refactor, build, workflow]
    related_skills: [subagent-driven-development, regent-reverse, regent-refactor, regent-build]
---

# delegate-repo-analysis

Parent-orchestrator pattern for codebase workflows: reverse, refactor, build,
and any "look at this repo and produce structured output" task. The parent
reads ONLY subagent reports and final artifacts. All worktree reads go to
leaf subagents.

## When to Use

- An active skill (regent-reverse, regent-refactor, regent-build, or similar)
  targets a worktree (clone, spec dir, refactor output, vendor source).
- The work involves >2 files of source reading, per-file deep analysis, or
  multi-file mutation.
- The user said any of: "派子agent去测试", "let the subagent do it",
  "用 subagent-driven-development", or similar delegation cues.

**Don't use for:**
- Tasks that don't touch a worktree (pure Q&A, planning, single-file edits).
- Tasks where the parent IS the implementer (one-shot scripts, small fixes).

## The boundary

```
┌─────────────────────────────────────────────────────────────┐
│  Parent (you)                                               │
│  - Acquire worktree (clone, mkdir, ls)         — OK direct  │
│  - Dispatch leaf subagents per step            — ALWAYS     │
│  - Read subagent summaries, spec output, diff  — OK direct  │
│  - Run pytest / go test / make / final smoke   — OK direct  │
│                                                             │
│  Leaf subagent (delegated)                                  │
│  - read_file / search_files on source files    — NEVER      │
│    done by parent                                           │
│  - Per-file deep read                         — ALWAYS     │
│  - Per-file write (spec sections, code edits) — ALWAYS     │
└─────────────────────────────────────────────────────────────┘
```

If the parent runs `read_file` on more than two source files in the
worktree, the boundary has been crossed. User has explicitly corrected
this pattern:

> "你怎么自己开始干了, 不是应该先把他的仓库clone下来, 然后你派子agent去测试吗"

## The three non-negotiable subagent prompt elements

Every leaf subagent prompt MUST include:

1. **Exact file/path list.** "Read /tmp/foo/X, /tmp/foo/Y. NOT others."
   Subagents without a path list drift into the whole repo.
2. **HARD BUDGET** in lines or files. "Total reads < 800 lines."
   Without a budget, "read every test file" prompts time out at 600s on
   real repos (17 test files × 500 LOC = 9.8K lines is a known timeout
   case).
3. **Concrete deliverable path.** "Write /path/to/output.md. Format
   follows SKILL.md §X. Cite file:line for every rule."
   Subagents without a deliverable path drift into exploration and never
   converge.

## Pattern: split a large task

When the cumulative source surface of a task exceeds ~5000 lines:

1. **List stage** — `ls *_test.go`, get counts. Pick the 3-5 files that
   cover the public API the spec cares about.
2. **Search stage** — for each candidate fixture in the spec, search
   the picked files for the discriminative test (pattern: function name
   + invocation). Read 30-line windows.
3. **Cite stage** — every oracle entry pins `test_file:start-end`.

Dispatch 2-3 parallel subagents, each with its own budget. See
`references/reverse-and-refactor-delegation.md` §2 for a worked example
(cobra reverse, three parallel subagents, each ≤800/200/400 lines).

## The clarification-only refactor pattern

For regent-refactor with `strategy: side-by-side`, when the spec edit is
a **pure clarification** (no inputs/outputs/error-paths change), the
correct rewriter output is **zero source diff**.

```bash
diff -r --brief <source_dir> <out_dir>  # ignore .git, .venv, __pycache__
```

If every tracked file is identical AND all three grading keys
(pytest + functional-checklist + test-oracle) are green, the refactor
**PASSED**. State this explicitly in the report:

> Clarification-only refactor: zero source changes, spec edit is
> documented intent only.

Don't treat zero-diff as "rewriter failed to act" — verify first.

## Spec-debt watch list

Common conflation when writing `inventory/functional-checklist.md`:

- **Library fallback** vs **CLI fallback**. Library functions fall back;
  CLIs reject unknown `--<flag>` values via argparse `choices=`. Pin
  library behaviour in `test-oracle.md`, CLI behaviour in
  `functional-checklist.md`. Putting library fallback into the CLI
  checklist produces a failing entry that has to be walked back.

- **Self-test vs contract.** `if __name__ == "__main__"` blocks, Rust
  `#[cfg(test)] mod tests`, Go `func TestXxx(*testing.T)` are NOT
  contract — they are test scaffolding. The real `func main()` of a
  binary IS contract. Don't conflate.

- **Deprecation markers as signal.** `FIXME Gt is unused by cobra...`
  marks back-compat helpers. The spec should record them as "kept for
  back-compat, planned for v2 removal" — not as live API.

## Pitfalls

1. **Parent reads >2 source files directly** — cross the boundary, the
   user will correct it. Dispatch instead.
2. **Unbounded read in subagent prompt** — "read every test file" with
   no budget causes 600s timeout. Always pin a HARD BUDGET.
3. **No deliverable path in subagent prompt** — subagent explores
   forever, never writes. Always pin a concrete output file path.
4. **Treating zero-diff as failure** — for clarification-only refactors,
   zero source diff is the correct outcome. Verify by diffing the two
   trees, not by counting edits.
5. **Conflating library and CLI behaviour in checklists** — produces
   false failures. Library behaviour goes in oracle, CLI behaviour in
   checklist.

## One-shot recipe

```bash
# 1. Acquire the worktree (parent does this directly, one command).
git clone --depth 1 https://github.com/<owner>/<repo>.git /tmp/<repo>

# 2. Dispatch 2-3 parallel subagents for the heavy lifting.
# Each prompt MUST include: file list, HARD BUDGET, deliverable path.
delegate_task(goal="...", context="Read these files: A, B, C.
HARD BUDGET: <800 lines total. Write output to /path/to/X.md.")

# 3. Accept subagent reports, dispatch the next phase (often a build
# agent that consumes the spec to blind-rebuild the project).

# 4. Run final verification on the rebuild output (parent does this):
go test ./...
diff -r --brief <source> <rebuild>
```