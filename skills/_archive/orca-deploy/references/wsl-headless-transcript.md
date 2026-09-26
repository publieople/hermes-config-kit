# WSL Headless Server Setup — Full Transcript

## Commands executed (2026-07-26)

```bash
# Install
paru -S stably-orca-bin

# First serve attempt — port 6768 occupied, fell back to 39514
orca-ide serve --json
# Output: {"type":"orca_server_ready","boundEndpoint":"ws://0.0.0.0:39514",...}

# Create systemd user unit
cat > ~/.config/systemd/user/orca-serve.service << 'EOF'
[Unit]
Description=Orca headless serve (WSL)
After=network-online.target
[Service]
Environment="PATH=/home/po/.local/bin:/home/po/.npm-global/bin:/home/po/.cargo/bin:/opt/miniforge/condabin:/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/sbin:/sbin:/bin"
ExecStart=/home/po/.local/bin/orca-ide serve --port 6768 --json
StandardOutput=append:/home/po/.orca/serve.log
StandardError=append:/home/po/.orca/serve.log
Restart=on-failure
RestartSec=5
ProtectSystem=false
ProtectHome=false
PrivateTmp=true
[Install]
WantedBy=default.target
EOF

# Enable and start
systemctl --user daemon-reload
systemctl --user enable --now orca-serve.service

# Extract pairing URL (display truncation workaround)
python3 -c "
import json
with open('/home/po/.orca/serve.log') as f:
    for line in f:
        if 'orca_server_ready' in line:
            d = json.loads(line[line.index('{'):line.rindex('}')+1])
            print(d['pairing']['url'])
            break
"

# Health check
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:39514/
orca-ide status --json
```

## What the pairing JSON contains

```json
{
  "v": 2,
  "endpoint": "ws://127.0.0.1:39514",
  "deviceToken": "59c98f6b0ee2fb8ea0445186fddc177b92efd47281afb609",
  "publicKeyB64": "r2iSpTwYloNwqlp+oE2829RfqTCusQgt2arr8s3CD0U=",
  "scope": "runtime"
}
```

## Orca agent hooks directory

```
~/.orca/agent-hooks/
  antigravity-hook.sh
  claude-hook.sh
  claude-statusline.sh (installed 2026-07-26)
  codex-hook.sh
  command-code-hook.sh
  copilot-hook.sh
  cursor-hook.sh
  devin-hook.sh
  droid-hook.sh
  gemini-hook.sh
  grok-hook.sh
  kimi-hook.sh
  openclaude-hook.sh
```

Hermes has no hook — not in Orca's built-in agent list. Use "Command" agent type with `hermes --tui`.
