#!/usr/bin/env bash
# Discipline check: prove the rewriter touched nothing outside the
# symbol list from the spec diff.
#
# Usage: spec_diff_check.sh <original-repo> <refactored-repo>
# Exits 0 only if byte-diff is empty across all non-.git/.venv files.

set -u
ORIG="${1:?original repo path required}"
REFA="${2:?refactored repo path required}"

# Compare every file under both trees, ignoring build artifacts.
CHANGED=0
while IFS= read -r -d '' f; do
  rel="${f#$ORIG/}"
  other="$REFA/$rel"
  if [ ! -f "$other" ]; then
    echo "  MISSING in refactored: $rel"
    CHANGED=$((CHANGED+1))
    continue
  fi
  if ! diff -q "$f" "$other" >/dev/null 2>&1; then
    echo "  DIFFERENT: $rel"
    diff "$f" "$other" | head -20
    CHANGED=$((CHANGED+1))
  fi
done < <(find "$ORIG" -type f \
            -not -path '*/.git/*' \
            -not -path '*/.venv/*' \
            -not -path '*/__pycache__/*' \
            -not -path '*/.pytest_cache/*' \
            -not -path '*/.egg-info/*' \
            -print0)

# Also flag files that exist only in refactored (rewriter invention).
while IFS= read -r -d '' f; do
  rel="${f#$REFA/}"
  case "$rel" in
    .venv/*|__pycache__/*|.pytest_cache/*|.egg-info/*) continue ;;
  esac
  if [ ! -f "$ORIG/$rel" ]; then
    echo "  ADDED in refactored (not in original): $rel"
    CHANGED=$((CHANGED+1))
  fi
done < <(find "$REFA" -type f \
            -not -path '*/.git/*' \
            -not -path '*/.venv/*' \
            -not -path '*/__pycache__/*' \
            -not -path '*/.pytest_cache/*' \
            -not -path '*/.egg-info/*' \
            -print0)

echo ""
if [ "$CHANGED" -eq 0 ]; then
  echo "spec_diff_check: ZERO diff (clarification-only or no-op refactor)"
  exit 0
else
  echo "spec_diff_check: $CHANGED file(s) changed outside expected scope"
  exit 1
fi