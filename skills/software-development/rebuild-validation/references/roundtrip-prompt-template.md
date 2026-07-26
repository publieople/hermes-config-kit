# Roundtrip prompt template (rebuild-validation)

A copy-pasteable subagent goal template, derived from a real roundtrip
that produced a clean **20/20 PASS + spec-debt list** on a greeter
fixture. Drop in your values for `<angle-bracketed>` placeholders.

## Why this template

The pattern that worked for blind-rebuild validation is:

- Whitelist the spec directory **explicitly**. Do not just say "only
  read the spec"; say what is forbidden and where the original lives.
- Ask for both checklist grading **and** a separate spec-debt list.
- Demand concrete evidence per item (output, exit code, command) so a
  reader can re-tick by hand.
- Ban `sudo` and pre-set the working directory. Lock the language
  preference so the report is in the right language.

If you change one thing, keep the **whitelist + spec-debt pair**.
That pair is what distinguishes a graded rebuild from a vibe-coded
one.

## Template

```
You are running a blind-rebuild verification for a structured spec.

Critical constraint: **You may ONLY read files under the spec
directory below.** The original source exists at <ORIGINAL_PATH>
but is **off-limits** for reading. Do not ls / cat / grep / git log /
search the web / open your training memory for the original repo.
The spec is the only authoritative source.

Spec dir: <SPEC_DIR>
Out dir:  <OUT_DIR>  (already cleaned: rm -rf before this prompt)

Steps:
1. Read <SPEC_DIR>/<ENTRY_POINT> first. Follow its rebuild order literally.
2. Read the rest of the spec to understand what <TARGET> is supposed
   to do.
3. Implement the package at <OUT_DIR> from spec ONLY. Do not clone,
   fetch, web search, or open anything outside <SPEC_DIR>.
4. Run the verification commands from <SPEC_DIR>/<DEV_ENV_FILE>.
5. Cross-check every line of <SPEC_DIR>/<CHECKLIST_FILE> against
   your rebuild. Each `- [ ]` becomes ✓ or ✗ with one-line evidence
   (the output / exit code / command you ran).
6. Final report (<4 KB):
   - Spec sections that were clear (cite path:line).
   - Spec sections that were vague / missing / forced invention
     (cite path:line).
   - Bullet-list of every checklist item with PASS/FAIL + one-line
     reason.
   - A separate bullet-list of **inventions** the rebuild made that
     were NOT in the spec (e.g. "chose dict vs if-branch in <FILE>
     because spec didn't mandate either", "invented LICENSE body
     text", "chose print() to stdout vs sys.stdout.write — stdlib
     convention").
   - Final overall verdict: PASS (spec sufficient) / FAIL (spec has
     gap), and if FAIL list the EXACT gap (which R-/S- requirement
     was missing).

NEVER use sudo. Use the build tool described in <SPEC_DIR>/<DEV_ENV_FILE>.
The dir <OUT_DIR> starts empty.
```

## Worked example — 20/20 PASS on greeter fixture

Provenance: published roundtrip test of `regent-reverse` v0.1.0 +
`regent-build` v0.1.0 on `publieople/reverse-fixture-tiny` (143-LOC
Python `greeter` package). 20/20 checklist PASS, 4 spec-debt items
(all in metadata: LICENSE body, README prose, pyproject description,
stdout method — all carved out as non-contract). Subagent runtime:
108s, single subagent, single-shot.

The verbatim goal that produced this result:

```
You are running a blind-rebuild verification for the REgent regent-build
skill test.

Critical constraint: **You may ONLY read files under the spec directory
below.** The original repo exists at
`/home/po/projects/reverse-fixture-tiny/` but is **off-limits** for
reading. Do not `ls`, `cat`, `grep`, `git log`, or otherwise read
anything from it. This is the whole point of the test — the spec must
be self-sufficient.

Spec dir: `/home/po/projects/REgent/spec-out/reverse-fixture-tiny/spec/`
Out dir: `/tmp/rebuild-greeter-b/` (already cleaned)

Steps:
1. Read `<spec_dir>/AGENTS.md`. Follow its rebuild order literally.
2. Read the rest of the spec to understand what `greeter` is
   supposed to do.
3. Implement the package at `<out_dir>` from spec ONLY.
4. Run the verification commands from
   `<spec_dir>/conventions/dev-env.md`.
5. Cross-check every line of
   `<spec_dir>/inventory/functional-checklist.md` against your
   rebuild. Each `- [ ]` becomes ✓ or ✗ with evidence (output,
   exit code, command run).
6. Final report (under 4 KB):
   - Spec sections that were clear (cite `path:line`).
   - Spec sections that were vague / missing / forced invention
     (cite `path:line`).
   - Bullet-list of checklist items with PASS/FAIL and one-line
     reason each.
   - A separate bullet-list of **inventions** the rebuild made
     that were NOT in the spec (e.g. "chose dict vs if-branch in
     `formats.py` because spec didn't mandate either").
   - Final overall verdict: PASS (spec sufficient) / FAIL (spec
     has gap), and if FAIL list the EXACT gap (which `R-` or
     S-num was missing).

NEVER use sudo. Use `uv venv` + `uv pip install` if a venv is
needed. The dir `/tmp/rebuild-greeter-b/` starts empty.
```

## Adjustments per language / scale

| Situation | Adjust |
|---|---|
| Rust target | Add `cargo build` to step 4; list `&dyn Trait` / `impl<T: Trait> Trait for &T` blanket impls in inventions if the rebuild was forced to invent trait-object dispatch. |
| >30 file target | Add "justify your choice of `whole` vs `single-module` in 2 lines at the top of the report". The validator should pick `single-module` defensibly, not be told. |
| Spec without `AGENTS.md` | Skip step 1; tell the validator the spec layout in the prompt. (Or refuse and patch the spec first — pre-flight rule.) |
| Spec has `[features]` / build tags | Add "every feature flag must be captured in your report — feature flags are silent rebuild failure modes". |
