#!/usr/bin/env bash
# Per-symbol oracle check harness.
# Usage: oracle_check.sh <repo-root>
# Reads `<repo-root>/spec-baseline/inventory/test-oracle.md`, parses each
# `### <symbol>` block, and runs the verification. Avoids bash-quoting
# landmines by using python heredocs instead of nested `python -c`.

set -u
REPO_ROOT="${1:-.}"
VENV_BIN="${REPO_ROOT}/.venv/bin"

if [ -d "$VENV_BIN" ]; then
  export PATH="$VENV_BIN:$PATH"
fi

PASS=0; FAIL=0

check_eq() {
  local desc="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    echo "  PASS  $desc"
    PASS=$((PASS+1))
  else
    echo "  FAIL  $desc  expected='$expected'  actual='$actual'"
    FAIL=$((FAIL+1))
  fi
}

# === Equality-style oracles ===
# Add one line per public surface. Format:
#   <symbol-expression-as-python> | <expected-output>
declare -a CASES=(
  "from greeter import format_default; print(format_default('Ada'))|Hello, Ada!"
  "from greeter import format_with_lang; print(format_with_lang('Ada','es'))|Hola, Ada!"
  "from greeter import format_with_lang; print(format_with_lang('Ada','xx'))|Hello, Ada!"
  "from greeter import greet; print(greet('  Ada  '))|Hello, Ada!"
  "from greeter import shout_greet; print(shout_greet('Ada'))|HELLO, ADA!"
  "from greeter import shout_greet; print(shout_greet('Ada','es'))|HOLA, ADA!"
)

for entry in "${CASES[@]}"; do
  py="${entry%|*}"
  expected="${entry#*|}"
  actual=$(python -c "$py")
  check_eq "$py" "$expected" "$actual"
done

# === Raise-style oracles ===
# Add one entry per `with pytest.raises(...)` in the original suite.
for inp in '""' '"   "'; do
  actual=$(python -c "
from greeter import greet
try:
    greet($inp)
    print('NO_RAISE')
except ValueError as e:
    print('RAISED')
")
  if [ "$actual" = "RAISED" ]; then
    echo "  PASS  greet($inp) raises ValueError"
    PASS=$((PASS+1))
  else
    echo "  FAIL  greet($inp) did not raise (got '$actual')"
    FAIL=$((FAIL+1))
  fi
done

echo ""
echo "oracle summary: PASS=$PASS FAIL=$FAIL"
exit $FAIL