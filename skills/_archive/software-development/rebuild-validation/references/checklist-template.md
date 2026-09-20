# Functional-checklist starter template

A machine-tickable checklist for the rebuild-validation pattern. Copy,
rename, fill in concrete items per your artifact.

```markdown
# Functional checklist — <repo-name>

The rebuild is verified against this list. Each entry is a concrete,
command- or call-shaped check that the rebuilt artifact must satisfy.
PASS / FAIL should be decidable without reading source code.

## <Category 1>

- [ ] <call/command shape 1>
- [ ] <call/command shape 2>

## <Category 2>

- [ ] ...

## Pass criterion

The rebuild is accepted when **every box above is checked**.
```

## Rules

1. **Every item is concrete.** A reader must be able to do the check
   without inventing intermediate steps.
2. **Include the expected outcome in the item.** "Returns 'Hello, Ada!'"
   not just "greets Ada".
3. **Include at least one negative case** per major behaviour:
   empty input, unknown language, missing file.
4. **Byte-exact for any user-visible string**: error prefixes, log
   formats, status messages. The author of the original probably
   wasn't checking exact bytes — the rebuild author needs to.
5. **Test runner must be one item, not five.** "pytest exits 0" beats
   "every test method passes" because the latter requires the validator
   to enumerate tests.

## Anti-patterns to avoid

- "Works correctly" — unfalsifiable.
- "Looks like the original" — subjective.
- "All 8 scenarios from specs/foo.md pass" — redundant with the spec;
  copy/paste the actual checks here.
- "Documentation is accurate" — what does that mean? Reframe.
