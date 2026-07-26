# Session note — greeter fixture, regent-refactor v0.1.0 e2e test

Date: 2026-07-19
Fixture: `/home/po/projects/reverse-fixture-tiny/` (8 files, pure stdlib)
Spec dir: `/tmp/refactor-test/spec-baseline/`
Output: `/tmp/refactor-test/refactored/`

## What was tested

End-to-end run of `regent-refactor` v0.1.0 against the user-edited
spec (R-3a clarification: `--shout` + empty name → stderr + exit 2).
The clarification pins an existing layering invariant (shout_greet
routes through greet, which raises first). No code change required.

## Result

**PASS** — all three grading keys green, byte-level diff = 0 across
all 8 source files. Discipline check passed (no upstream leakage, no
training-data smuggling).

## Gaps found in regent-refactor/SKILL.md

These are improvements I would propose for the next version. They
are NOT addressed in v0.1.0:

1. **§1 "Diff the spec"** — does not acknowledge that a clarification-
   only edit may produce zero code changes. A first-time reader could
   misread §7's "Rewriter's diff matches the symbol list" as "must
   produce a diff." Add a sentence: "If the symbol-level change list
   is empty, the verification step still MUST run — zero changes is
   a passing outcome, not a skipped one."

2. **§5 "Run verification"** — does not cover the
   **clarification-derived oracle check**. When the spec adds a new
   requirement that pins existing layering (R-3a case), the rewriter
   should derive a new oracle entry from the clarification itself
   (`greeter "" --shout → exit 2 + stderr 'error: ...'`) and call
   it out so the user can see the clarification is exercised.

3. **§3 "Snapshot before mutating"** — for `strategy: side-by-side`,
   the snapshot step is implicit. State it explicitly: "With
   side-by-side, the original `source_dir` is the rollback; no
   separate snapshot needed."

4. **§6 "Decide"** — the green-path branch assumes a non-empty diff.
   Add an explicit branch: "If `git diff --stat source_dir out_dir`
   is empty AND all three grading keys are green, report
   'Clarification-only refactor: zero source changes, spec edit is
   documented intent only.' This is a successful outcome, not a
   failure to edit."

## Spec-debt observed in this session

- Initial checklist entry claimed `greeter Ada --lang xx` falls back.
  **Wrong**: argparse `choices=` rejects before code runs. The
  library `format_with_lang` does fall back (pinned by oracle), but
  the CLI does not. Layers must be spelled out in architecture-
  rules.md.

## Reusable artifacts produced

- `/tmp/oracle_check.sh` — per-symbol oracle harness (no nested
  quoting). Saved as `scripts/oracle_check.sh` in
  `regent-skill-tester`.
- Spec tree at `/tmp/refactor-test/spec-baseline/` — 11 files, 290
  LOC. Can serve as a worked example for future REgent reverse runs.