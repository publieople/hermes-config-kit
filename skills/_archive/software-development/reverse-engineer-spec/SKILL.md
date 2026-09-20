---
name: reverse-engineer-spec
description: Reverse-engineer an unfamiliar repository into a machine-readable spec/ tree that an AI coding agent can read to rebuild the project from scratch. Triggers on "reverse engineer this repo", "把仓库转成 spec", "repo → spec/", "spec out this codebase", or any task asking for a structured, buildable spec from source. Drives the agent to deeply explore the codebase before writing, capture contracts (not implementation), enumerate protocols/ABCs, and verify the spec with a blind rebuild.
tags: [reverse-engineering, spec, codebase-analysis, regent, codebase-review, agent-rebuild, test-oracle]
metadata:
  hermes:
    related_skills: [codebase-review, plan, writing-plans, spike, requesting-code-review, software-development]
---

# Reverse-Engineer → Spec

Produce a `spec/` tree that an AI coding agent can read end-to-end and rebuild
the target project from scratch. The output is a **contract**, not a paraphrase
of the source. Output verification: a fresh agent must be able to read the spec
and implement passable code without ever seeing the original.

## When to Use

- User hands over a repo URL or local path and asks for a structured spec.
- User wants to migrate, fork, or rebuild a project with no time to read all
  source.
- Downstream pipeline needs a stable spec schema as input for build/refactor.
- Sanity-checking another AI's understanding of a codebase.

**Don't use for:** chatty "what does this repo do" answers, single-file
walkthroughs, or anything where a structured tree is overkill. For
human-readable code-quality feedback, use `codebase-review` instead.

## The Lazy-Decision Heuristic (read first, before scanning)

Before scanning, pick the scope. **Default is Option B** unless the repo is
small enough for full reverse.

```
Total source LOC estimate?
├─ <5k    → Option A: full-repo reverse at depth=normal
├─ 5k-30k → Option A: depth=quick, per-file deep read of non-trivial only,
│          produce layout/per-file-skip.md for trivial modules
├─ >30k   → Option B: pick ONE non-trivial module, deep-read it, produce
│          specs/ for that module only, list sibling modules in
│          specs/_missing.md with one-line reasons
└─ unsure → clone first, `find . -name '*.py' | xargs wc -l`, decide
```

Justify the choice in 1-2 lines at the top of the final report. A rebuild
grading 50+ checklist items against 5k LOC is easy; grading 50+ items against
a 100k-LOC monorepo from a single module's spec is not.

## Workflow

Each step ends with a checkable condition.

### 1. Acquire

- URL: `git clone --depth 1 <url>` into `/tmp/<name>`.
- Local: use in place. **Never mutate the source.**
- Verify entry files exist (README, package manifest, license).

### 2. Recon (mandatory full-tree scan)

Inspect every entry including hidden (`.github/`, `.vscode/`, CI, Dockerfile).
For each: path, kind (code/config/doc/test/asset/build/ci), rough LOC,
language.

Output a file-count tally: **total files, code, test, config, doc, asset**.
Every category must be non-zero unless the project genuinely lacks one.

### 3. Module / dependency mapping

**Lazy imports count.** Grep `import x` / `from x import y` *inside function
bodies*, not just top-of-file. Libraries that avoid import-time cycles by
lazy-loading are still dependencies. (See `references/regent-reverse-diff.md`
pitfall #7.)

Module map must include:
- Top-level layout (src/lib/cmd/internal).
- Public entry points (CLI entry, `__init__.py`, exported package).
- Module boundaries — which directories are cohesive units?
- Per-module lazy imports called out.

If >30 top-level files, do this with a quick scan, not full read.

### 4. Per-file deep read

For every source file **in your chosen scope** and every test file
corresponding to it, record:
- One-line purpose (what, not how).
- Public API: function/class names + signatures + 1-line behavior.
- Notable invariants: preconditions, error paths, side effects, locks.
- Test coverage hint: which test file(s) exercise this code.

**Protocols and ABCs are the contract.** For every `@runtime_checkable
Protocol` or `ABC` declared in any file in scope, list every abstract /
duck-typed method *and* every call site that dispatches on it (e.g.
`hasattr(x, '__rich_console__')`). A spec missing a protocol method is
incomplete because the rebuild agent has no other way to learn it.

For docs and config, summarize intent only.

**Skip** (with one-line annotation):
- Generated (dist/, build/, node_modules/, lock files).
- Vendored deps.
- Large binary blobs.
- `if __name__ == '__main__':` blocks — *record with `role: self-demo, not API`*
  in `layout/src.map.md`; they are NEVER part of the contract.

### 5. Inferred conventions

Every rule needs `file:line` evidence. Mine for:
- Style: indentation, quotes, line length (`.editorconfig`, formatter configs).
- Type system usage.
- Error handling patterns — **especially for files owning I/O**.
- Test framework + patterns (fixture style, mocking, parametrization).
- Build/lint commands (`package.json scripts`, `tox.ini`, `Makefile`,
  `.github/workflows/`).

**I/O-owning files require an architecture-rules.md section** covering:
- Error-to-exception mapping (which exceptions raised, byte-exact messages).
- Exit semantics (`SystemExit(1)`? swallows broken-pipe?).
- Std-stream side effects (`os.dup2`, `SIGPIPE` handler, global fd mutation).

### 6. Functional inventory

Enumerate user-observable behaviors with verification commands. Each becomes a
`- [ ]` in `inventory/functional-checklist.md`. Aim for 10-50 entries.

Format: `- [ ] WHEN <trigger>, THEN <expected observable> (<file:line>).`
The rebuild grader greps these literally.

Include byte-exact literals:
- Greetings, error prefixes, log formats.
- CLI exit codes (if any).
- Non-CLI byte-exact exception messages (substitute when no CLI exists).

### 6b. Distill a test-oracle (white-box grading key)

The functional checklist is **black-box** ("does the CLI exit 0?").
That alone is not enough. The rebuild will pass the checklist by
coincidence while getting per-symbol invariants wrong — order of
operations, full-width punctuation, error-before-format, dispatch
precedence.

For each public symbol, distill a per-function oracle into
`inventory/test-oracle.md`:

```
### `<symbol>`
- input: <literal, byte-exact>
- expects: <literal output> OR <raises ExactException(message)>
- pins: <one-line statement of WHICH invariant this pins>
```

Cap at 1-2 entries per public surface. **Target total: 15-25 entries**
for a single-module spec; **30-60** for a full-repo spec at depth=normal.
Above those, you kept scaffolding variants instead of cutting them — fold
related cases into one entry (e.g. one entry for `Min/Max/Exact/Range`
error envelopes with a small table of expected strings) and let the pin
cite the helper. This is a **load-bearing subset** of the original test
suite, NOT a copy. See `rebuild-validation/references/oracle-distillation.md`
for the full method, including worked examples (greeter) and anti-patterns
(test-file transcription, vague `pins:`).

**How to find discriminative tests efficiently** when the target test
file is large (this is normal — a 4000-line test file is not unusual):

1. `rg '^func Test\w+' <test_file>` — list all test names. Tests with
   parametric suffixes (`TestX_WithY`, `TestX_WithoutZ`) are usually
   scaffolding variants of `TestX`; keep `TestX` and skip the variants
   unless one variant exercises a genuinely distinct contract.
2. Read tests whose name contains the public symbol you want to pin
   (`TestNoArgs`, `TestValidArgsFunc*`, `TestDisableFlagParsing`).
3. **Prefer tests with literal expected-output blocks** (`if output !=
   expected { t.Errorf(...) }`) over property-only tests
   (`expectSuccess(output, err, t)`); the literal pins the bytes.
4. Read helper functions (`expectSuccess`, `noArgsWithArgs`,
   `minimumNArgsWithLessArgs`) once and cite them from many entries —
   the pin is to the helper, not the test wrapper. Reading one helper
   pin can replace 5–10 test-level reads.
5. **Skip `t.Run("subcase", ...)` blocks inside parametrised loops**
   unless one subcase is uniquely contract-bearing; usually the loop's
   setup is enough to describe the family.

**Budget hint for test-file reading.** A 4000-line test file can usually
be reduced to ~500 lines of targeted reads via the above. Do not "read
the whole file" — that path burns budget on scaffolding and parametrised
variants with no contract value. If a test file has >2k lines, the right
read budget is *test names list + 6–10 targeted windows + cited helpers*,
not the whole file.

When the original project has no test suite, emit a single-paragraph
`test-oracle.md` stating "no source tests existed; checklist-only
grading applies" — do not invent oracles.

### 7. Emit spec tree

```
spec/
├── AGENTS.md                # Index + rebuilding instructions (mandatory, read first)
├── README.md                # Human overview of the original project
├── architecture.md          # arc42-lite: goals / quality goals / building blocks / dataflow
├── layout/
│   ├── tree.txt             # Annotated original tree
│   └── src.map.md           # File → purpose + public API + protocol dispatch sites
├── specs/
│   ├── <module>.spec.md     # OpenSpec-lite: Purpose / Requirements (R-1..R-N) / Scenarios (S-1..S-N)
│   ├── _missing.md          # If Option B or >25 modules skipped, list with one-line reasons
│   └── README.md            # Index of specs/ for navigation
├── conventions/
│   ├── code-style.md
│   ├── dev-env.md           # Build / test / lint commands
│   └── architecture-rules.md  # Threading, error policy, I/O side effects
└── inventory/
    ├── functional-checklist.md   # Black-box behaviour; rebuild grading key
    └── test-oracle.md            # White-box per-symbol invariants
```

File rules:

- `AGENTS.md` is **mandatory** and tells the agent to use the spec to rebuild
  from scratch, NOT to copy code.
- Each `specs/<module>.spec.md` uses OpenSpec-lite: `## Purpose` /
  `## Requirements` (with SHOULD/MUST, numbered R-1..R-N) / `## Scenarios`
  (WHEN...THEN... form, numbered S-1..S-N).
- Each spec MUST include a literal table of human-facing strings
  (greetings, error prefixes, log formats) byte-for-byte.
- Each spec MUST enumerate every `Protocol` / `ABC` method declared in the
  module.
- Each spec MUST enumerate every exception type raised with byte-exact
  messages. **If the module has no CLI**, substitute the "exit-code prefix"
  rule with: "list every exception type with its byte-exact message."
- `conventions/*.md` cites `file:line` for every rule.
- `inventory/functional-checklist.md` is plain markdown checklist, machine-
  greppable. Each entry has `- [ ]` form and a verification command.

**Presentation is not contract.** The spec does not pin
`pyproject.toml` metadata fields (`description`, `author`, URLs),
`LICENSE` body text, or `README.md` prose — these are presentation,
not API contract. The rebuild agent invents them. Pinning them in the
spec produces permanent false-positive spec debt on every roundtrip
without strengthening the API. (See `references/regent-reverse-diff.md`
session log: a 20/20 PASS roundtrip with 4 inventions of metadata
content was a true pass — the inventions did not weaken the spec.)

### 8. Self-review

- All categories from step 2 accounted for in some output file.
- Every module has a spec OR a documented reason to skip.
- Every inferred convention cites a source.
- The functional checklist has ≥1 entry per public CLI / API surface.
- Every `Protocol` / `ABC` declared in scanned files appears as an R- rule
  in at least one spec.
- **`inventory/test-oracle.md` has ≥1 entry per public surface that
  had a discriminating test in the original suite** (or a documented
  "no source tests existed" note). Checklist-only grading is a
  fallback, not a default.
- Run a tree check: the layout matches step 7.

### 9. Blind rebuild verification (high-value optional)

Build a small surface area (one function, one class, one CM) from the spec
*without* opening the source. Write a self-check that exercises:
- One byte-exact literal (error message, output prefix).
- One Protocol dispatch site.
- One thread/lock/invariant if the module has one.
- One exception type raised.

Run it. **Pass = spec is sufficient for that surface.** A failure pinpoints
the gap. This is the only objective check that the spec is rebuild-ready.

## Common Pitfalls

1. **Skimming the tree.** If you read fewer than 80% of source files in
   scope, redo.
2. **Hallucinating APIs.** If a name cannot be confirmed in the source,
   omit it; never invent.
3. **Generic conventions without evidence.** "Use camelCase" with no
   `file:line` is noise.
4. **Conflating code with spec.** If `src.map.md` starts copying source,
   rewrite it. The spec describes *what and why*, not *how line-by-line*.
5. **Skipping tests.** Tests reveal the true contract.
6. **Missing functional checklist.** The grader has no key without it.
7. **Missing lazy imports.** A naive top-of-file `import` scan misses
   `from .jupyter import display` inside `_write_buffer()`. Grep inside
   function bodies too.
8. **Missing Protocol dispatch sites.** If a module declares
   `class ConsoleRenderable(Protocol)` with `__rich_console__`, the spec
   must also document where `hasattr(x, '__rich_console__')` is checked.
9. **Treating `__main__` blocks as API.** Self-demos are not contract.
10. **Treating lazy imports as dependencies only.** They are also evidence
    of architectural decisions (cycle avoidance, optional platforms).
11. **Transcribing the test suite into the oracle.** A `test-oracle.md`
    that reads like `tests/test_x.py` with the word "test" replaced
    by `###` is a renamed copy, not a distilled oracle. The rebuild
    then copies verbatim and the roundtrip is no longer a roundtrip.
    See `rebuild-validation/references/oracle-distillation.md` for
    the cap-at-1-or-2-per-surface rule and the worked example.

## Verification Checklist

- [ ] Repo acquired without mutating the source.
- [ ] Full tree scanned; tally recorded.
- [ ] Module + dependency graph sketched (incl. lazy imports).
- [ ] Every source file and every test file in scope has at least one entry
      in `layout/src.map.md`.
- [ ] Every Protocol/ABC in scope has its methods enumerated in an R- rule.
- [ ] Every lazy import in scope is in the dependency graph.
- [ ] Each module has `specs/<module>.spec.md` with Purpose, Requirements,
      Scenarios.
- [ ] `conventions/*.md` cite file:line for every rule.
- [ ] `inventory/functional-checklist.md` has 10+ entries (fewer if repo
      genuinely small, state why).
- [ ] `AGENTS.md` is written and links the rest.
- [ ] Tree matches step 7.
- [ ] Blind-rebuild self-check passes (if performed).

## References

- `references/regent-reverse-diff.md` — Concrete diffs to make
  `regent-reverse` scale beyond toy fixtures, derived from a real
  stress-test against `Textualize/rich`.