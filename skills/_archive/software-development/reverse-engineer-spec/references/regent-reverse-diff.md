# Stress-test of `regent-reverse` against Textualize/rich

Source session: stress-test of `skills/regent-reverse/SKILL.md` (v0.1.0) by
applying it to `github.com/Textualize/rich`, specifically `rich/console.py`
(2 698 LOC). Repo cloned to `/tmp/rich-real`; spec output to
`/home/po/projects/REgent/spec-out/rich/spec/` (939 LOC across 10 files);
blind rebuild at `/tmp/rebuild-rich/console_rebuild.py` passed 7/7 contract
checks.

This file collects the diff-style suggestions that the regent-reverse skill
itself should adopt to scale beyond toy fixtures. Grouped by section heading
in the original SKILL.md.

---

## New: Lazy-Decision Heuristic

The current SKILL.md has **no guidance for repos larger than the toy
`greeter` fixture**. Suggested addition under `## Workflow` (before step 1):

```markdown
### 0. Scope (lazy-decision heuristic)

Before scanning, pick the scope:

- `<5k` LOC total → Option A: full-repo reverse at depth=normal.
- `5k-30k` LOC → Option A at depth=quick; per-file deep read of non-trivial
  modules only; produce `layout/per-file-skip.md` listing skipped modules.
- `>30k` LOC → Option B: pick ONE non-trivial module (suggest `*.console.py`
  or the public API entry), reverse it in full, produce spec for that module
  only. Document skipped modules in `specs/_missing.md`.

Justify the choice in 1-2 lines at the top of the report.
```

Justification (why this matters): the current "read every source and every
test" rule does not specify what to do when "every" is 100 files × 2 700 LOC
each. Without an Option B path, agents either burn 50k tokens or skim and
violate pitfall #1.

---

## Step 3 — Module / dependency mapping

Add to step 3 body:

> **Lazy imports count.** Grep `import x` / `from x import y` *inside function
> bodies*, not just top-of-file. Libraries that avoid import-time cycles
> (e.g. `from .jupyter import display` called inside `_write_buffer`) are
> still dependencies and must appear in the module graph.

Add to `Common Pitfalls`:

> 7. **Missing lazy imports.** A naive top-of-file `import` scan misses
>    `from .jupyter import display` inside `_write_buffer()`. Grep inside
>    function bodies too.

---

## Step 4 — Per-file deep read

Add bullet:

> For every `@runtime_checkable Protocol` or `ABC` declared in any file in
> scope, list every abstract/duck-typed method AND every call site that
> dispatches on it (e.g. `hasattr(x, '__rich_console__')`). A spec missing a
> protocol method is incomplete because the rebuild agent has no other way
> to learn it.

Add bullet:

> `if __name__ == '__main__':` blocks are NEVER part of the contract.
> Record them in `layout/src.map.md` with `role: self-demo, not API`.

Add pitfall #8:

> 8. **Missing Protocol dispatch sites.** If a module declares
>    `class ConsoleRenderable(Protocol)` with `__rich_console__`, the spec
>    must also document where `hasattr(x, '__rich_console__')` is checked.

---

## Step 5 — Inferred conventions

Add bullet:

> Files owning I/O MUST produce an entry in `conventions/architecture-rules.md`
> covering: error→exception mapping (byte-exact messages), exit semantics
> (`SystemExit(1)`? swallows broken-pipe?), std-stream side effects
> (`os.dup2`, `SIGPIPE` handler, global fd mutation).

---

## Step 7 — Emit spec tree (file-rules block)

Add rule:

> Each `specs/<module>.spec.md` MUST enumerate every `Protocol` declared in
> the module and every method on it. (See step 4 amendment above.)

Add rule:

> Each `specs/<module>.spec.md` MUST enumerate every exception type raised
> with byte-exact messages. **If the module contains no CLI entry point**,
> substitute the "exit-code prefix" rule with: "list every exception type
> with its byte-exact message."

Add rule:

> A `if __name__ == '__main__':` block is **NEVER part of the contract** —
> record it in `layout/src.map.md` with `role: self-demo, not API`.

Add optional section to the tree template:

```markdown
specs/
├── <module>.spec.md
├── _missing.md          # Option B or >25 modules skipped: one-line reasons
└── README.md            # Navigation index for specs/ (especially Option B)
```

Add pitfall #9:

> 9. **Treating lazy imports as dependencies only.** They are also evidence
>    of architectural decisions (cycle avoidance, optional platforms).
>    Note them in `conventions/architecture-rules.md`, not just the dep graph.

---

## Verification Checklist

Add checklist line:

> - [ ] Every `Protocol` / `ABC` declared anywhere in the scanned files
>       appears as an R- requirement in at least one spec.

Add checklist line:

> - [ ] Every lazy import in scope is in the dependency graph.

---

## Self-review (step 8)

Add explicit acknowledgement of the Option B branch:

> - If Option B was chosen, `specs/_missing.md` exists and names every
>   sibling module with a one-line reason.

---

## Functional Checklist size guidance

Current rule says "10-50 entries". Add:

> Aim for ≥1 entry per public API surface AND ≥1 entry per Protocol dispatch
> site AND ≥1 entry per raised exception type. The latter two are
> non-negotiable; the "10-50" range applies to the total.

---

## Tested: blind-rebuild verification (NEW step 9)

The current SKILL has no objective check that the spec is rebuild-ready.
Suggested addition:

> ### 9. Blind rebuild verification (optional but high-value)
>
> Pick a small surface area — one function, one class, one CM. Implement it
> from the spec **without** opening the source. Write a self-check (`if
> __name__ == '__main__'`) that exercises:
>
> 1. One byte-exact literal (error message, output prefix).
> 2. One Protocol dispatch site (`isinstance(x, Protocol)` or
>    `hasattr(x, '__dunder__')`).
> 3. One thread/lock/invariant if the module has one.
> 4. One exception type raised.
>
> Pass = the spec was sufficient for that surface. Failure pinpoints the
> gap. This is the only objective check that the spec is rebuild-ready.

Proven result from the rich stress-test: 7/7 contract checks passed at
`/tmp/rebuild-rich/console_rebuild.py` against a 275-LOC spec.

---

## Recommended new pitfall #10 (consolidation)

> 10. **Re-implementing dependencies instead of treating them as
>     black-box.** `console.py` references `Segment`, `Text`, `Style`,
>     `Theme`, `Pager`, etc. — the spec MUST list these as external
>     dependencies, NOT re-spec them. Each spec scope is the file in
>     question; everything else is "use as-is with public interface X".

This prevents the spec tree from ballooning into a full-repo re-spec when
Option B is chosen.

---

## Summary of concrete edits

| Where | Add |
|---|---|
| `## Workflow` (new step 0) | Lazy-decision heuristic |
| Step 3 body | Lazy-import grep rule |
| Step 4 body | Protocol/ABC enumeration, `__main__` rule |
| Step 5 body | I/O-file policy |
| Step 7 file-rules | Protocol/exception rules + substitute for non-CLI |
| Step 7 tree template | `specs/_missing.md`, `specs/README.md` |
| Step 8 self-review | Option B acknowledgement |
| Step 9 (new) | Blind-rebuild verification |
| `Common Pitfalls` | #7 lazy imports, #8 protocol dispatch, #9 lazy-as-evidence, #10 dependency scope |
| `Verification Checklist` | Protocol rule + lazy-import rule |