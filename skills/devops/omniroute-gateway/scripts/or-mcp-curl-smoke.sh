#!/bin/bash
# OmniRoute MCP enable + 99-tool discovery smoke test
#
# Verifies, in order:
#   1. Dashboard login works with the given password
#   2. Settings PATCH flips mcpEnabled + mcpTransport
#   3. API key creation returns a usable sk- key
#   4. /api/mcp/stream initialize handshake succeeds
#   5. tools/list returns >50 tools (current OR ships 99)
#   6. Any tool call round-trip works (using omniroute_get_health — read-only)
#
# Usage:
#   OR_URL=http://localhost:20128 OR_ADMIN_USER=admin OR_ADMIN_PASS=*** ./or-mcp-curl-smoke.sh
#
# Outputs:
#   - exit 0 if all 6 stages passed
#   - exit 1 with the failing stage number printed
#   - verbose stdout shows every request/response

set -uo pipefail

OR_URL="${OR_URL:-http://localhost:20128}"
OR_ADMIN_USER="${OR_ADMIN_USER:-admin}"
OR_ADMIN_PASS="${OR_ADMIN_PASS:-}"
OR_KEY_NAME="${OR_KEY_NAME:-smoke-test-$(date +%s)}"

if [[ -z "$OR_ADMIN_PASS" ]]; then
  echo "OR_ADMIN_PASS not set. Set it to the dashboard admin password." >&2
  exit 2
fi

step() { echo; echo "==== Stage $1: $2 ===="; }

# Stage 1: login
step 1 "Login to /api/auth/login"
COOKIE=$(curl -sS -m 10 -X POST "$OR_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$OR_ADMIN_USER\",\"password\":\"$OR_ADMIN_PASS\"}" \
  -c - 2>&1 | grep auth_token | awk '{print $7}')
if [[ -z "$COOKIE" ]]; then
  echo "  FAIL: login did not return auth_token cookie" >&2
  exit 1
fi
echo "  OK: cookie len=${#COOKIE}"

# Stage 2: enable MCP
step 2 "PATCH /api/settings mcpEnabled + mcpTransport"
RESP=$(curl -sS -m 8 -X PATCH "$OR_URL/api/settings" \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_token=$COOKIE" \
  -d '{"mcpEnabled":true,"mcpTransport":"streamable-http","a2aEnabled":true}' 2>&1)
if echo "$RESP" | grep -q '"mcpEnabled":true'; then
  echo "  OK: mcpEnabled=true confirmed"
else
  echo "  FAIL: PATCH did not enable MCP" >&2
  echo "  Response: $RESP" >&2
  exit 2
fi

# Stage 3: create API key
step 3 "POST /api/keys (admin scope)"
KEY_RESP=$(curl -sS -m 10 -X POST "$OR_URL/api/keys" \
  -H "Content-Type: application/json" \
  -H "Cookie: auth_token=$COOKIE" \
  -d "{\"name\":\"$OR_KEY_NAME\",\"scopes\":[\"admin\"]}" 2>&1)
KEY=$(echo "$KEY_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('key',''))" 2>/dev/null)
if [[ -z "$KEY" ]]; then
  echo "  FAIL: key creation did not return 'key' field" >&2
  echo "  Response: $KEY_RESP" >&2
  exit 3
fi
echo "  OK: key=${KEY:0:8}...${KEY: -4} (len=${#KEY})"

# Stage 4: MCP initialize handshake
step 4 "POST /api/mcp/stream initialize (capture Mcp-Session-Id)"
INIT_RESP=$(curl -sS -m 8 -X POST "$OR_URL/api/mcp/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $KEY" \
  -D /tmp/or-init-headers.txt \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"or-smoke","version":"1.0"}}}' 2>&1)
SESSION=$(grep -i 'mcp-session-id' /tmp/or-init-headers.txt | sed 's/.*: //;s/\r//')
if [[ -z "$SESSION" ]]; then
  echo "  FAIL: initialize did not return Mcp-Session-Id header" >&2
  echo "  Body: $INIT_RESP" >&2
  exit 4
fi
echo "  OK: session=$SESSION"

# Stage 5: tools/list
step 5 "POST /api/mcp/stream tools/list (with session)"
TOOLS_RESP=$(curl -sS -m 8 -X POST "$OR_URL/api/mcp/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $KEY" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' 2>&1)
TOOL_COUNT=$(echo "$TOOLS_RESP" | python3 -c "
import sys, json, re
text = sys.stdin.read()
# tools/list response comes as SSE: 'data: {...}\n\n'
m = re.search(r'data: ({.*})', text, re.DOTALL)
if not m: print(0); exit()
try:
    d = json.loads(m.group(1))
    print(len(d.get('result', {}).get('tools', [])))
except Exception:
    print(0)
" 2>/dev/null)
if [[ "$TOOL_COUNT" -lt 50 ]]; then
  echo "  FAIL: tools/list returned $TOOL_COUNT tools (expected >= 50)" >&2
  echo "  Body: $TOOLS_RESP" >&2
  exit 5
fi
echo "  OK: $TOOL_COUNT tools discovered"

# Stage 6: tool call round-trip
step 6 "POST /api/mcp/stream tools/call omniroute_get_health"
CALL_RESP=$(curl -sS -m 10 -X POST "$OR_URL/api/mcp/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $KEY" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"omniroute_get_health","arguments":{}}}' 2>&1)
if echo "$CALL_RESP" | grep -q '"result"'; then
  echo "  OK: tool call returned result"
else
  echo "  FAIL: tool call did not return result" >&2
  echo "  Body: $CALL_RESP" >&2
  exit 6
fi

echo
echo "==== ALL 6 STAGES PASSED ===="
echo "Smoke key (delete after test): $KEY"
exit 0