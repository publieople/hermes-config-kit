# Worked example: `greeter` blind-rebuild (20/20 PASS)

Target: `publieople/reverse-fixture-tiny` — Python 3.10+ CLI that produces greeting strings in 4 locales.

## Spec coverage

| Section | Path | Notes |
|---|---|---|
| Layout | `layout/src.map.md` | 4 src modules + 1 test file enumerated |
| API contracts | `specs/greeter.spec.md` R1-R4 | All 4 R- requirements + 9 S- scenarios |
| Style | `conventions/code-style.md` | Python ≥3.10, f-strings, absolute imports, `__all__` |
| Layering | `conventions/architecture-rules.md` | core→formats, cli→core, no reverse edges |
| Build/env | `conventions/dev-env.md` | `pip install -e .` + `pytest`, no conftest |
| Grading | `inventory/functional-checklist.md` | 20 items, 4 categories |

## Implementation choices honored from spec evidence

- `_TEMPLATES: dict[str, str]` in `formats.py` — spec (`architecture-rules.md:19-21`) literally says "function defs and a `dict` literal". Dict was the only honest reading.
- `if lang == "en": format_default(...) else: format_with_lang(...)` in `core.greet` — matches `architecture.md:32-33` dataflow diagram.
- `print(f"error: {exc}", file=sys.stderr); return 2` — matches `specs/greeter.spec.md:35-36` literal `"error: "` prefix requirement.

## Inventions explicitly logged

1. LICENSE body text — spec called it only `[doc] MIT license stub`.
2. README quick-start body — spec said "two CLI examples + pytest", no copy provided.
3. pyproject.toml `description` and `[project]` metadata fields — only `requires-python`, build backend, console script were mandated.

## Verification commands run

```bash
cd /tmp/rebuild-greeter-b
uv venv && source .venv/bin/activate
uv pip install -e .        # extra `[test]` warning harmless, no extra defined
uv pip install pytest
pytest -v                   # 8 passed in 0.02s
greeter Ada                 # Hello, Ada!\n  exit=0
greeter Ada --lang es       # Hola, Ada!\n  exit=0
greeter Ada --shout         # HELLO, ADA!\n  exit=0
greeter ""                  # stderr: error: name must not be empty  exit=2
greeter --help              # exit=0
python -c 'import greeter; greeter.__version__'  # 0.1.0
```

## Report shape that earned PASS

The 20-row checklist table, an explicit "Inventions" bullet-list, and `path:line` cites on every clear/vague spec reference. The "explicit inventions" section is what makes a PASS-grade report trustworthy — it shows the agent didn't paper over gaps.

## What would have been FAIL

If `specs/greeter.spec.md:48` had not specified the exact zh full-width punctuation `，` and `！`, the rebuild would have silently produced `你好, Ada!` (half-width comma) and the zh checklist row would fail. Conversely, if `inventory/functional-checklist.md:11` had been omitted, the zh row would not be testable — that's a spec gap, not a PASS.
