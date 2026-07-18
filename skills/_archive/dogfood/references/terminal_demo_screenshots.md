# Terminal Demo Screenshots for Presentations

When you need to show a live API or service demo in a PPT slide, avoid raw terminal screenshots. Use one of these two approaches:

## Approach 1: Self-contained Bash Demo Script

Create a script that starts the service, runs demo requests, prints clean output, and shuts down:

```bash
#!/usr/bin/env bash
cd ~/your-project

# Start API in background, suppress Flask/worker logs
.venv/bin/python api_server.py > /dev/null 2>&1 &
SERVER_PID=$!
sleep 4  # Wait for service to start

echo "============================================================"
echo "  Service Name — Live Demo"
echo "============================================================"

# Health check
HEALTH=$(no_proxy='*' http_proxy='' curl -s http://127.0.0.1:5000/health)
echo "[Status] $HEALTH"

# Demo requests
echo ""
echo "  ── Prediction Results ──"
for case in "${cases[@]}"; do
  RESP=$(no_proxy='*' http_proxy='' curl -s -X POST \
    http://127.0.0.1:5000/api/v1/predict \
    -H "Content-Type: application/json" \
    -d "$case")
  # Parse and print results
done

echo ""
echo "============================================================"
echo "  Demo Complete ✓"
echo "============================================================"

# Cleanup
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null
```

**Key pitfalls:**
- `UID` is a bash read-only variable — use `USER_ID` instead
- Proxy intercepts localhost in WSL — always use `no_proxy='*' http_proxy=''` prefix for curl
- Flask access logs pollute output — redirect stdout/stderr to `/dev/null`
- Background Python may not flush output — use `python -u` or `PYTHONUNBUFFERED=1`
- `sleep 4` needed after starting service before first request

## Approach 2: HTML Terminal Mockup (Recommended for PPT)

When terminal emoji/font rendering is unreliable or you need polished formatting, create an HTML page styled as a terminal window. This avoids:
- Missing emoji/font glyphs in terminal (JetBrains Mono lacks many emoji)
- Background process output buffering
- Proxy interference with localhost
- Server log noise mixed with demo output

**Template structure:**
- Dark background (`#0d1117` — GitHub dark theme)
- macOS-style title bar with three dots (red/yellow/green)
- JetBrains Mono or Consolas font, 13-14px
- Color-coded output: green `#3fb950` for success, orange `#f0883e` for predictions, blue `#58a6ff` for headers
- Cursor prompt at bottom (`➜  ~`)
- Width ~900px, centered

Generate the HTML, open in browser via `browser_navigate`, screenshot via `browser_vision`. Produces consistent, publication-quality terminal screenshots regardless of actual terminal environment.
