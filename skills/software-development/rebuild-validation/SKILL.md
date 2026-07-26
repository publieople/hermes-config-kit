---
name: rebuild-validation
description: Use when validating that a structured artifact (spec, schema, contract, doc-set, runbook) is sufficient for an independent agent to reconstruct the underlying system from it alone. Triggers on "blind rebuild test", "validate this spec", "is this documentation enough", "spec-driven regression", "contract test", or when shipping any reverse-engineering / spec / schema work. Also covers refactor (the user edited R-/S- entries and asks the agent to splice the diff into an existing codebase - "按新 spec 改", "refactor to spec", "重写这个屎山"). Drives a subagent that has NEVER seen the source artifact to read only the spec and rebuild against a graded machine-tickable two-key grading (functional-checklist.md + test-oracle.md), then surfaces diff-able weaknesses.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [validation, spec, contract, subagent, regression]
    related_skills: [test-driven-development, dispatching-parallel-agents, receiving-code-review]
---

# Rebuild Validation

Empirical validation that a structured artifact — a spec, a schema, a
contract, a documentation set — is **sufficient** for an independent agent
to reconstruct the underlying thing from scratch.

The signal it produces is binary: PASS / FAIL per checklist item. The
output is a bulleted list of items, each marked PASS or FAIL with a
one-line reason, plus specific patching suggestions for the author.

## When to Use

- You just wrote a spec / contract / schema and need to know if it's enough.
- The artifact claims "this is the source of truth for X"; verify the claim.
- A reverse-engineering pipeline (`A → spec`) needs a feedback loop.
- Documentation accuracy: do these docs let a fresh agent complete the task?
- An API client rebuild task: are these stub docs enough to implement against?
- **Refactor scope:** the user edited `specs/*.spec.md` (added/removed
  R- or S- entry) and asks you to splice the new behaviour into the
  existing codebase without rebuilding it from scratch.

**Don't use for**: unit tests, "smoke tests" of running code, or anything
where the artifact isn't a static specification.

## Two grading keys, not one

A single `functional-checklist.md` answers "does the rebuilt code ship
the right observable behaviour?". That is not enough.

Every rebuild-grade spec SHOULD also include a `test-oracle.md` (or
equivalent) — a per-symbol **white-box** grading key:

```
### `<symbol>`
- input: <literal, byte-exact>
- expects: <literal output> OR <raises ExactException(message)>
- pins: <one-line statement of WHICH invariant this pins>
```

Why both:

- **functional-checklist** = black box. "Does the CLI exit 0 on
  success, 2 on `ValueError`?" — visible from outside the binary.
- **test-oracle** = white box. "Does `greet("   ")` raise
  `ValueError` before or after `.strip()`?" — pinned ordering the
  checklist cannot distinguish. The order is what makes the function
  correct; without oracle discipline, every rebuild gets it right *by
  coincidence* and you only find out at runtime.

What real roundtrips reveal: when both keys are run, the rebuild
typically passes 100% of checklist items (the easy grade) but fails
5-15% of oracle items (the order-of-operations, full-width
punctuation, error-before-format, dispatch-precedence class). The
oracle is what tells you the rebuild got the semantics right, not just
the behaviour. A green checklist with a red oracle is a **specific
failure** — list the exact oracle entry and the actual-vs-expected.

This skill consumes the oracle. The companion
`reverse-engineer-spec` skill is responsible for *distilling* it: one
or two fixtures per public surface from the original test suite (NOT
copying the whole test file). See `references/oracle-distillation.md`
for the distillation method, and treat that file as the source of
truth for "what goes into an oracle entry".

## Spec-edit → existing code (refactor)

This skill covers "build a thing from spec" (whole or scoped). The
companion edit-an-existing-thing-per-spec path has different
discipline and is captured here because the same grading keys apply:

1. **Diff the spec.** Identify which `R-` / `S-` / oracle entries the
   user added, removed, or edited. The user's edit is authoritative.
2. **Classify each change** into: behaviour change (rewrite affected
   symbol), conventions change (style / imports / error types),
   inventory-only (count or wording shifted but no behaviour),
   or **pure clarification** (codebase already satisfies it).
3. **Snapshot the source.** `git worktree add ../snapshot` if the tree
   is clean; otherwise refuse to run. With `side-by-side` strategy the
   original directory *is* the rollback; no separate snapshot needed.
4. **Spawn a leaf rewriter.** Constrain its scope to *only* the
   affected symbols from step 2. It is forbidden to refactor
   unrelated code, even ugly code. Patch, do not regenerate.
5. **Run all three grading keys** (pytest + functional-checklist +
   test-oracle). ALL THREE must be green.
6. **Verify the diff matches the symbol list.** `git diff --stat`
   between snapshot and rewriter output must touch only those files.
   Anything else is a regression of trust.

Two outcomes worth distinguishing explicitly:

- **All three green AND diff empty** → the edit was a *pure
  clarification*. Passing outcome, not failure to edit. The user's
  edit is now a documented intent, pinned by an oracle entry. Show
  the new oracle entry as proof the clarification is exercised.
- **All three green AND diff non-empty** → state the changed symbols
  and confirm the spec edit is now in the code.

The failure of trust mode: rewriter touches code outside its scope.
When `git diff` shows unrequested changes, **roll those back** and
tighten the rewriter's scope. Otherwise the audit breaks: the user can
no longer trust "diff == edit". Diff-vs-symbol-list is the audit
backbone of refactor; without it, refactor degrades into vibe-coding
that happens to also invoke pytest.

## The Five-Step Pattern

### 1. Write a graded checklist

`functional-checklist.md` (or equivalent) is plain markdown with bullets:

```
- [ ] <concrete check 1>
- [ ] <concrete check 2>
```

Each line MUST be machine-tickable: a concrete command, return value, or
observable outcome. "Works" / "looks right" is not enough. Good:

```
- [ ] greet("Ada", "es") returns "Hola, Ada!"
- [ ] `pytest` exits 0
- [ ] `greeter --help` writes usage to stdout, exit 0
```

**Pre-flight check before you even validate:** confirm the artifact
itself is ready. The minimum survivable spec has (a) an entry-point
document the validator will read first (`AGENTS.md` or equivalent) and
(b) a `functional-checklist.md` with ≥5 `- [ ]` items. If either is
missing, **stop and tell the author** — running a validator against a
stub spec produces a 0/0 PASS that nobody can act on.

See `references/checklist-template.md` for a starter.

### 2. Pick a blind validator

The validator MUST have **zero access to the source artifact** that
produced the spec. Two ways to enforce:

- Spawn a subagent in its own session; pass the spec path only.
- Restart the current session so prior context is gone; feed the spec.

The validator MUST NOT use `git log`, web search, or any debugging aid
that could leak the original. If it can leak, the test is invalid.

### 3. Let the validator pick its own scope

For large artifacts (>30 files or >5k LOC equivalent), the validator may
pick:

- **whole**: rebuild everything from spec.
- **single-module `<name>`**: rebuild one representative section. Pick
  the section most users / callers touch.
- **single-file `<path>`**: smallest scoped test.

The validator justifies its pick in one paragraph and proceeds. The
author records the choice in `AGENTS.md`.

Why this matters: forcing whole-artifact validation on a 100k-LOC spec
blows budget and produces false negatives. A well-chosen scoped PASS is
more useful than a global FAIL with token artifacts.

### 4. Run the rebuild

The validator works the spec top-down: `AGENTS.md` → `architecture.md` →
module specs → checklists. Conventions come last. After implementation,
the validator ticks every checklist item and reports PASS / FAIL with
reasons.

### 5. Surface diff-able weaknesses

Ask for **specific, actionable critique**, not narrative review. The
prompt format that worked:

> Critique the spec: which sections were clear, which were vague, where
> you had to invent something not in the spec. **Name the heading** in
> the spec. **Quote the missing text or rule** that would have made
> rebuilding unambiguous.

The author converts each weakness into a `patch` against the spec (or
against the producer skill). Re-run if cheap.

**Two distinct signals, not one.** Always separate failures from debt:

- **Failures** — checklist items the rebuild cannot tick. These mean
  the spec is missing or wrong on a contract.
- **Spec debt** — checklist items the rebuild ticked **but only by
  inventing something not in the spec** (LICENSE body, dict-vs-if
  branch, `print()` vs `sys.stdout.write`, etc.). These mean the spec
  is insufficiently prescriptive. A green build with 4 inventions is a
  weaker spec than a green build with 0 inventions, even though both
  report "20/20 PASS".

**Always produce the spec-debt list, even on a fully green run.**

## Strengths and Limits

**Strengths**:
- Quantifiable signal: `X / N PASS, M with reasons`.
- Catches contract drift, vocabulary mismatches, scope ambiguities, and
  missing error-message literals that no static review catches.
- Cheap: a 5-file codebase runs in ~30s of agent time.

**Limits**:
- Validator cost scales with spec size — scope must be chosen wisely.
- Cannot grade non-functional areas (perf, security, aesthetics) without
  explicit checklist items.
- A passing rebuild ≠ a correct rebuild. The checklist must be
  exhaustive; weak checklists pass weak specs.

## Common Pitfalls

1. **Leaky validator.** If the validator can see the original source
   (via `find /tmp/...` or browser history), the test is invalid.
   Verify isolation by passing only the spec path.
2. **Checklist that grades itself.** A checklist with "looks reasonable"
   or "is well-organized" is unfalsifiable. Every item must be a concrete
   check.
3. **Forcing whole scope.** Letting validators bail to a smaller scope
   when budget gets tight is correct, not failure. A scoped PASS with
   reason beats a global FAIL with token noise.
4. **Narrative review.** "The spec was good but could be clearer" is
   not actionable. Demand heading + missing-text-level critique.
5. **No re-run after fix.** Patch the spec, but skip re-validation when
   it's cheap. Same weakness can hide for months otherwise.
6. **Spec drift after the test.** If you patch the spec for unrelated
   reasons, re-run; the build phase will hit drift.
7. **Patching the rebuild until tests pass.** The validator's job is to
   grade the spec, NOT to debug or rewrite the rebuild. A tweaked file
   that now passes is a false green; the spec still has the gap. The
   validator must output a graded checklist and stop. If you (the human
   reading the report) are tempted to fix a failed item by editing the
   rebuild, that is the bug. Roundtrip tests don't produce fixes; they
   produce failure signals.
8. **Treating metadata as contract.** LICENSE body text, README prose,
   `pyproject.toml` `description` / `author` fields — none are contract.
   Let the rebuild invent them. A spec that tries to pin every
   presentation field produces false-positive spec debt on every run.
9. **Skipping the spec-debt list on a green run.** A green run with
   inventions is a weaker spec than a green run with zero inventions.
   Always list what the rebuild was forced to invent, even on PASS.
10. **Accepting a green checklist when the oracle is red.** The
    checklist is the easy grade; the oracle is the invariant check.
    Always run both. A green checklist + red oracle is a specific
    failure — list the oracle entry, not a vague PASS.
11. **Refactor diffing beyond its scope.** When the rewriter outputs a
    diff that touches more files than the symbol-list predicted, roll
    the extra changes back and tighten the brief. Otherwise the audit
    backbone (diff == edit) breaks and refactor degrades into
    vibe-coding that happens to also pass pytest.

## Verification Checklist

- [ ] Pre-flight passed: entry-point doc exists, functional checklist has
      ≥5 machine-tickable items.
- [ ] Validator has no access to the source artifact.
- [ ] Validator justified its scope choice if it picked <whole>.
- [ ] Report lists every checklist item with PASS / FAIL / reason.
- [ ] Spec-debt list is present (not optional), and non-empty when the
      validator invented anything **even on a fully green run**.
- [ ] Critique names spec headings and quotes missing text, not narrative.
- [ ] **No edits were made to the rebuild to mask failures.** Validator
      output is the only output; reading the report, you must not feel
      tempted to fix the rebuild.
- [ ] Weaknesses are patched; if cheap, the rebuild was re-run.

## One-Shot Recipes

### Toy-repo roundtrip (~30s)

```
# 1. Pick a 5–10 file repo with tests
# 2. Write functional-checklist.md with 10+ items
# 3. Spawn subagent with only spec path; ask it to rebuild at /tmp/rebuild-x
# 4. Subagent runs the checklist, reports PASS / FAIL
```

### Real-world module roundtrip (~5 min)

```
# 1. Pick a single high-coupling module (e.g. console.py for rich)
# 2. Write specs/<module>.spec.md with SHOULD / MUST + Scenarios
# 3. Subagent picks single-module scope; justifies
# 4. Subagent rebuilds only the chosen surface and grades checklist
```

## References

- `references/checklist-template.md` — starter functional-checklist template.
- `references/roundtrip-prompt-template.md` — copy-paste subagent goal
  template, with the whitelist + spec-debt pair that distinguishes a
  graded rebuild from a vibe-coded one. Pair this with `references/checklist-template.md`.
- `references/oracle-distillation.md` — how to distill a
  `test-oracle.md` from an original test suite (one or two fixtures
  per public surface, NOT a transcription). This is the producer side
  that `reverse-engineer-spec` runs; this skill consumes its output.
