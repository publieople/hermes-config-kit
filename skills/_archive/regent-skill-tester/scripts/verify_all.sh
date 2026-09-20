#!/usr/bin/env bash
# Full three-key verification: pytest + functional-checklist.md + test-oracle.md
# Usage: verify_all.sh <repo-root>

set -u
REPO_ROOT="${1:-.}"
VENV_BIN="${REPO_ROOT}/.venv/bin"

if [ -d "$VENV_BIN" ]; then
  export PATH="$VENV_BIN:$PATH"
fi

PASS=0; FAIL=0
ok()   { echo "  PASS  $1"; PASS=$((PASS+1)); }
fail() { echo "  FAIL  $1"; FAIL=$((FAIL+1)); }

# ---- pytest ----
if python -m pytest -q >/tmp/pytest.out 2>&1; then
  ok "pytest"
else
  fail "pytest"; cat /tmp/pytest.out
fi

# ---- functional-checklist.md ----
# Each `- [ ] <description> | <expected> | <actual>` line. The simplest
# form just runs the CLI and compares stdout.
declare -a CHECKS=(
  "greeter Ada|Hello, Ada!"
  "greeter Ada --lang es|Hola, Ada!"
  "greeter Ada --lang fr|Bonjour, Ada!"
  "greeter Ada --lang zh|你好，Ada！"
  "greeter Ada --shout|HELLO, ADA!"
  "greeter Ada --shout --lang es|HOLA, ADA!"
)

for entry in "${CHECKS[@]}"; do
  cmd="${entry%|*}"; expected="${entry#*|}"
  actual=$($cmd)
  if [ "$expected" = "$actual" ]; then
    ok "$cmd"
  else
    fail "$cmd  expected='$expected' actual='$actual'"
  fi
done

# Error-path: stderr + exit code (do NOT conflate stdout)
for name in '""' '"   "'; do
  err=$(greeter "$name" 2>&1 1>/dev/null); ec=$?
  if [ "$err" = "error: name must not be empty" ] && [ "$ec" -eq 2 ]; then
    ok "greeter $name stderr + exit 2"
  else
    fail "greeter $name  stderr='$err' exit=$ec"
  fi
done

# ---- test-oracle.md (delegate to oracle_check.sh) ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if bash "$SCRIPT_DIR/oracle_check.sh" "$REPO_ROOT" >/tmp/oracle.out 2>&1; then
  ok "test-oracle.md"
else
  fail "test-oracle.md"; cat /tmp/oracle.out
fi

echo ""
echo "verify-all summary: PASS=$PASS FAIL=$FAIL"
exit $FAIL