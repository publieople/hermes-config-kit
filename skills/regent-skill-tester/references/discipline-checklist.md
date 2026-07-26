# Discipline checklist — what the rewriter must NOT do

A refactor that produces green grading keys can still fail if the
agent smuggled in intent from outside its inputs. These are the
forbidden moves; tick each one off before declaring PASS.

## Hard constraints

- [ ] Did NOT `git clone` any repo other than the fixture under test
- [ ] Did NOT inspect `git log` / remote history of the fixture
- [ ] Did NOT pull in patterns from training data (Python idioms
      beyond the spec, e.g. adding `dataclasses`, `pydantic`,
      type-var generics, custom Protocols)
- [ ] Did NOT add dependencies not in `pyproject.toml`
- [ ] Did NOT change the public API surface (no new exports, no
      removed exports)
- [ ] Did NOT add tests not pinned in `inventory/test-oracle.md`
- [ ] Did NOT add `if __name__ == "__main__"` blocks (those are
      self-demo, not contract)

## Soft signals (warning if seen)

- The rewriter invents helper functions not in the spec.
- The rewriter renames anything (variables, functions, files).
- The rewriter restructures `__init__.py` re-exports.
- The rewriter changes the error message text (the literal prefix
  `error: ` is contract per R-5 in most greeter-style specs).

## How to verify

```bash
# 1. Diff against the symbol list (which functions SHOULD change?)
diff <(grep -E '^### |^def ' spec-baseline/inventory/test-oracle.md) \
     <(grep -E '^### |^def ' refactored/src/*/)

# 2. Confirm no deps added
diff <(grep -A20 '\[project\]' original/pyproject.toml) \
     <(grep -A20 '\[project\]' refactored/pyproject.toml)

# 3. Confirm no new exports
diff <(grep '__all__' -A20 original/src/*/__init__.py) \
     <(grep '__all__' -A20 refactored/src/*/__init__.py)
```

If any of those diffs is non-empty, the rewriter overstepped.