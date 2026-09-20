# Distilling a `test-oracle.md` from a real test suite

This is the producer side of the white-box grading key. The companion
skill `reverse-engineer-spec` runs this; the `rebuild-validation`
skill consumes the result. Read this if you are writing the spec, not
validating it.

## Goal

A `test-oracle.md` is a per-symbol **load-bearing subset** of the
original test suite. It is NOT a copy of the test file. It is NOT a
restatement of `R-` / `S-` requirements. It is the smallest set of
fixtures that, if rebuilt verbatim into the test suite, would catch
the invariants that the behavioural checklist **cannot** catch.

## When to skip

- The original test suite has <5 tests per public surface on average
  — there is no meaningful "subset" to distill; just list the
  tests as oracle entries one-for-one.
- The original has no tests (no `tests/` or `__tests__/` directory) —
  emit `test-oracle.md` with a single paragraph stating "no source
  tests existed; the oracle is empty; checklist-only grading applies".
  Do not invent oracles.

## Method (per public symbol)

For each public function / method / class in scope:

1. Find the test(s) in the original `tests/` (or `__tests__/`,
   `*_test.go`, `tests/.../*.rs`) that exercise this symbol with the
   **most discriminating input** and the **strictest expectation**.
2. Reduce each test to a triple:

   ```
   ### `<symbol>`
   - input: <literal, byte-exact>
   - expects: <literal output> OR <raises ExactException(message)>
   - pins: <one-line statement of WHICH invariant this pins>
   ```

3. Cap at **one or two entries per public surface**. More than two
   means the test is heavy on scaffolding (fixture setup, parametrize
   tables, mocking) that does not pin any new invariant — reduce.

## What "pinning" means

The `pins:` line is the discipline. It must state a non-trivial
property that the rebuild would get wrong **by coincidence** if it
were not pinned:

- Order of operations: "strip AFTER emptiness check, not before"
  (gates `greet("   ")` correctness).
- Byte-exact punctuation: "full-width `，` and `！` for `lang='zh'`"
  (gates `greet("Ada", "zh") == "你好，Ada！"`).
- Dispatch precedence: "smart-case activates iff input is
  lowercase-only" (gates regex matching behaviour).
- Error-before-format ordering: "validation runs before
  localization; never localize a validation error" (gates that
  `greet("")` does not produce `"你好,"` instead of raising).
- Cross-feature interaction: "the `lock = None` branch in process
  spawn MUST skip the `os.dup2` global-fd mutation" (gates that no
  test of either feature in isolation pins, but the interaction is
  the contract).

If a test reduces to a behaviour already covered by `functional-
checklist.md` (e.g. "CLI exit 0 on success"), drop it. The oracle
exists to pin things the checklist cannot.

## Anti-patterns

- **Transcribing test files.** If `test-oracle.md` reads like
  `tests/test_x.py` with the word "test" swapped for "###", you
  copied the test suite and renamed it. The rebuild will then
  rebuild verbatim, and the roundtrip is no longer a roundtrip — it
  is a copy with extra steps.
- **One entry per parametrized case.** If the original test uses
  `@pytest.mark.parametrize` with 8 cases, you do NOT need 8 oracle
  entries. Pick the one that pins the most discriminating invariant
  (the ordering test, the full-width punctuation test, etc.).
- **Mock-heavy entries.** If the only way to pin an invariant is
  with mocks and patching, the spec probably can't pin it either —
  reconsider whether it's actually contract or implementation detail.
- **Scaffolding in `pins:`.** "Test that the function returns the
  correct value" is not pinning. State what *specific* property
  would be wrong if the rebuild made a different choice.

## Worked example: greeter

Given `tests/test_greeter.py` with 8 tests:

| Original test                                         | Oracle entry? | Why / why not |
|-------------------------------------------------------|---------------|---------------|
| `test_default_format`                                 | yes           | Pins the English default literal |
| `test_format_with_lang_spanish`                       | yes           | Pins the Spanish punctuation (half-width `,`) |
| `test_format_with_lang_unknown_falls_back`            | NO            | Visible from CLI smoke-test alone (in checklist) |
| `test_greet_strips_whitespace`                        | yes           | Pins that strip happens AFTER validation |
| `test_greet_rejects_empty`                            | yes           | Pins byte-exact `ValueError` message |
| `test_greet_rejects_whitespace_only`                  | yes           | Pins that `"   "` is rejected (not silently stripped) |
| `test_shout_greet`                                    | NO            | Already covered by `shout_greet(name, lang='en')` uppercase check |
| `test_shout_greet_spanish`                            | yes           | Pins that `.upper()` happens AFTER localization, not before — the same test as `shout_greet` English but the property is "order of operations across localization" |

Result: 6 oracle entries from 8 tests. Two dropped because they are
already pinned by the checklist or by a stronger oracle entry.

## Worked example: what NOT to do

A copy-paste oracle:

```
### `test_default_format`
- input: `"Ada"`
- expects: returns `"Hello, Ada!"`
- pins: returns the correct value
```

This is bad: `pins: returns the correct value` is not an invariant
the rebuild could violate specifically. It would pass against both
correct and subtly-wrong implementations (e.g. one with swapped
locale, one that strips before validating, one that swallows
exceptions). The whole point of `pins:` is to make that distinction.

## When to amend mid-roundtrip

If the validator surfaces a checklist-green + oracle-red PASS, the
oracle is doing its job. The reaction is:

1. Add the missing invariant to the relevant `pins:` line, or
2. Add a new oracle entry capturing the invariant the rebuild got
   wrong, or
3. If the spec genuinely cannot pin it without copying code, mark
   the oracle entry as `pins: best-effort` and accept the debt.

Path 3 is the failure mode of last resort; paths 1-2 are normal
post-roundtrip work and exactly what test-oracle is for.
