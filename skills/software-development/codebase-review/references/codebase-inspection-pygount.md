# Codebase LOC Inspection with pygount

Analyze repositories for lines of code, language breakdown, file counts, and code-vs-comment ratios.

## Prerequisites

```bash
pip install --break-system-packages pygount 2>/dev/null || pip install pygount
```

## Basic Summary

Get a full language breakdown with file counts, code lines, and comment lines:

```bash
cd /path/to/repo
pygount --format=summary \
  --folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,.eggs,*.egg-info" \
  .
```

**IMPORTANT:** Always use `--folders-to-skip` to exclude dependency/build directories, otherwise pygount will crawl everything and may hang on large dependency trees.

## Common Folder Exclusions

```bash
# Python projects
--folders-to-skip=".git,venv,.venv,__pycache__,.cache,dist,build,.tox,.eggs,.mypy_cache"

# JavaScript/TypeScript projects
--folders-to-skip=".git,node_modules,dist,build,.next,.cache,.turbo,coverage"

# General catch-all
--folders-to-skip=".git,node_modules,venv,.venv,__pycache__,.cache,dist,build,.next,.tox,vendor,third_party"
```

## Filter by Language

```bash
# Only Python files
pygount --suffix=py --format=summary .

# Python and YAML
pygount --suffix=py,yaml,yml --format=summary .
```

## Detailed File-by-File Output

```bash
# Default format shows per-file breakdown
pygount --folders-to-skip=".git,node_modules,venv" .

# Sort by code lines
pygount --folders-to-skip=".git,node_modules,venv" . | sort -t$'\t' -k1 -nr | head -20
```

## Output Formats

```bash
# Summary table (recommended)
pygount --format=summary .

# JSON for programmatic use
pygount --format=json .
```

## Interpreting Results

Summary table columns: **Language**, **Files**, **Code** (lines of actual code), **Comment** (lines that are comments), **%** (percentage of total).

Special pseudo-languages:
- `__empty__` — empty files
- `__binary__` — binary files (images, compiled, etc.)
- `__generated__` — auto-generated files
- `__duplicate__` — files with identical content
- `__unknown__` — unrecognized file types

## Pitfalls

1. **Always exclude .git, node_modules, venv** — without `--folders-to-skip`, pygount will crawl everything and may take minutes or hang.
2. **Markdown shows 0 code lines** — pygount classifies all Markdown content as comments, not code.
3. **JSON files show low code counts** — pygount may count JSON lines conservatively.
4. **Large monorepos** — consider using `--suffix` to target specific languages.
