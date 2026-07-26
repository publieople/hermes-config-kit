# REgent spec baseline — file layout

The minimum tree a `regent-reverse` run MUST produce. Anything missing
fails the verification checklist.

```
spec-baseline/
├── AGENTS.md            # Index + rebuild instructions (read first)
├── README.md            # Human overview of the original project
├── architecture.md      # Goals / quality goals / building blocks
├── layout/
│   ├── tree.txt         # Original tree (sortable)
│   └── src.map.md       # File → purpose + public API + evidence
├── specs/
│   └── <module>.spec.md # R-1..R-N + WHEN/THEN scenarios
├── conventions/
│   ├── code-style.md    # Cite file:line for every rule
│   ├── dev-env.md       # Build / test / lint commands
│   └── architecture-rules.md  # Layering invariants, I/O policy
└── inventory/
    ├── functional-checklist.md  # ≥10 `- [ ]` lines
    └── test-oracle.md            # One `### <symbol>` per public surface
```

## File rules (load-bearing)

- `AGENTS.md` is **mandatory** and first to read.
- Each `specs/*.spec.md` uses OpenSpec-lite: `## Purpose` /
  `## Requirements` (SHOULD/MUST) / `## Scenarios` (WHEN…THEN).
- Each spec MUST include a literal table of human-facing output
  strings (byte-exact) — never let the rebuild infer punctuation.
- `conventions/*.md` cites file:line for every rule.
- `functional-checklist.md` is plain markdown, machine-greppable.
- `test-oracle.md` is the *load-bearing subset* of tests, not a
  transcript. One entry per public surface with discriminating
  coverage.