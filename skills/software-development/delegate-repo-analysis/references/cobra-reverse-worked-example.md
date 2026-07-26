# Worked example: cobra reverse, second pass

A real session (2026-07-20) that produced the parent-orchestrator pattern
captured in `SKILL.md`. Concrete numbers, what failed, what worked.

## Context

Testing `regent-reverse` v0.4.0 + `regent-build` v0.2.0 against the
github.com/spf13/cobra Go library.

Repo size at the time:
- 66 files (36 .go source + 17 _test.go + 13 ancillary)
- 11,526 LOC of test code across 17 test files
- Single Go module, two packages (`cobra` + `doc/`)

## Failure: first-pass dispatch

Parent dispatched one leaf subagent with the prompt:

> "Write 4 spec files... You MUST read tests/test_greeter.py equivalents
> — i.e. /tmp/cobra-reverse/cobra/*_test.go AND
> /tmp/cobra-reverse/cobra/doc/*_test.go. Aim for 15-30 entries..."

The prompt had no file budget. The subagent dutifully tried to read all
17 test files (9,810 LOC). Result:

```
status=timeout, api_calls=17, 600.06s
(no summary — status=timeout)
```

Zero useful output. 10 minutes burned.

## Fix: three small subagents in parallel

Parent split the same task into 3 leaf subagents and added explicit
budgets:

| Subagent | Task | File budget | Time |
|---|---|---|---|
| `deleg_c0e76386` | `test-oracle.md` from 3 test files | <800 lines | (not returned in time) |
| `deleg_c2bb96d4` | `dev-env.md` from Makefile + golangci.yml + go.mod | <200 lines | 139s ✅ |
| `deleg_0af3c224` | `code-style.md` + `architecture-rules.md` from 5 source files | <400 lines | 57s ✅ |

Key elements added to each prompt:

```
HARD BUDGET:
- Read at most N lines TOTAL across the listed files. Use search_files
  to find discriminative tests, then read 30-line windows around them.
- DO NOT clone any repo. DO NOT git log upstream.
- DO NOT touch any path outside the output file.
```

Result: all three returned. The test-oracle subagent timed out later
but produced a useful intermediate (the parent verified the test-oracle
file existed and was substantial before declaring success).

## The third prompt element: concrete deliverable

The failing prompt had "research the code and tell me what you found."
The working prompts all had:

> "Output: write /path/to/file.md. Format: see SKILL.md §X.
> Must include items A, B, C with file:line citations.
> Report: file path, line count, list of items found."

Subagents without a concrete deliverable path drift into exploration and
never converge. The deliverable IS the contract.

## Pattern: explicit "do NOT" list

Each subagent prompt included an explicit out-of-scope section:

> "OUT OF SCOPE for you (other agents / parent will write):
> - AGENTS.md, README.md, architecture.md
> - specs/cobra.spec.md
> - inventory/functional-checklist.md
> - layout/tree.txt, layout/src.map.md
>
> CRITICAL RULES:
> - DO NOT clone any repo.
> - DO NOT git log upstream.
> - DO NOT pull in training-data knowledge."

Without this, the subagent tried to write files outside its scope and
sometimes rewrote others' work.

## The user correction (verbatim)

After the parent dispatched the first batch and the parent ALSO ran
`git clone`, `find`, `ls *.go`, `grep` on the cobra source directly:

> 用户: "你怎么自己开始干了, 不是应该先把他的仓库clone下来,
>       然后你派子agent去测试吗"

The correct split:
- Parent does: `git clone`, mkdir, ls once, `go test ./...` final.
- Subagents do: every `read_file` on source, every file analysis,
  every file write.

This rule is captured in `SKILL.md` §"The boundary".

## Reusable template

```yaml
goal: "<one-line task, e.g. 'Write X.md with Y format'>"
context: |
  Source: <absolute path to already-cloned worktree>
  Per-file map already produced: <optional, read first>
  
  Read these N files ONLY:
  1. /path/to/A (<lines> lines)
  2. /path/to/B (<lines> lines)
  
  Output: write /path/to/output.md
  Format: see SKILL.md §X.
  Must include: items A, B, C with file:line citations.
  
  HARD BUDGET:
  - Read at most N lines TOTAL across the listed files.
  - Use search_files(pattern=...) to find discriminative inputs,
    then read 30-line windows around them.
  - DO NOT clone any repo.
  - DO NOT git log upstream.
  - DO NOT touch any path outside the output file.
  
  Report: file path, line count, list of items, anything skipped.
role: leaf
```

This template is what `SKILL.md` §"The three non-negotiable subagent
prompt elements" formalizes.