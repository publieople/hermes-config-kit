# Deployment Pattern Examples

## Session: Audio-Analysis (2026-05-20)

**Repo**: https://github.com/publieople/Audio-Analysis — USB 3-mic recording on 泰山派 RK3566
**PR**: https://github.com/juzibububu/Audio-Analysis/pull/1

### Problem

Production deployment needed for an embedded Linux (Ubuntu on 泰山派) Python application that:
- Records audio from 3 USB microphones (`arecord`, ALSA)
- Uploads WAV files via custom TCP protocol to a Windows server
- Needs to run 24/7 unattended

Missing: auto-start on boot, crash recovery, health monitoring.

### Solution Stack

```
systemd service (auto-start + crash recovery)
  └─ watchdog cron (health checks every 5 min)
       └─ env file (config separate from code)
            └─ install script (one-command deploy)
```

### Key Design Decisions

1. **`After=network-online.target`** — critical for this app (requires network to upload). Without this, the app starts before networking is ready and logs "connection refused" errors until the watchdog restarts it.

2. **`StartLimitBurst=5` in 120s** — prevents infinite restart loops if the ALSA stack is broken or network is permanently down. The watchdog's cron-based restart provides a slower recovery path.

3. **Env file for server IP** — the server address changes per deployment site. Hardcoding it in the service unit means editing system files. The env file lives in `/opt/audio-analysis/` — non-engineers can edit it with `nano`.

4. **File staleness detection** — the watchdog checks if any `.wav` file was written in the last 300 seconds. This catches "app is running but not producing data" — a failure mode that process-alive checks miss. The 300s threshold accounts for the upload+delete cycle + potential UDP packet loss on the network.

5. **Bash-based watchdog, zero deps** — the 泰山派 may not have Python monitoring libraries or an internet connection. `pgrep`, `awk`, `systemctl`, and `logger` are guaranteed present on any Ubuntu/Debian system.

### Deviations from Standard Template

- The `ProtectSystem=full` line was added but commented out in the final service file because the app needs to write to `usb_recordings/`
- `PrivateTmp=yes` was also removed — the ALSA temp test files (`/tmp/usb_mic_test_*.wav`) break with private /tmp
- The watchdog's `STALL_SECONDS` (300) was tuned from the default to account for the 60-second recording duration + 1s interval + upload time

### Team Collaboration Flow

The developer (汲子) doesn't have remote SSH access to the 泰山派 yet. Approach:
1. Fork the repo → write deploy scripts in the open
2. Create a PR on the upstream repo
3. The developer pulls it locally and runs `sudo bash deploy/install.sh 192.168.1.100`
4. Done — no remote access needed, no mental handoff
