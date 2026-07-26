#!/usr/bin/env bash
# Diagnose WSLg readiness for Electron / GTK / Qt GUI apps.
# Use when: $DISPLAY is empty, or App crashes with "Missing X server or $DISPLAY"
#           + SIGSEGV, but /tmp/.X11-unix/X0 exists.

set +e

echo "=== 1. WSLg daemon sockets / mounts ==="
ls -la /tmp/.X11-unix/ 2>/dev/null || echo "  no /tmp/.X11-unix"
ls /mnt/wslg/ 2>/dev/null | head -10 || echo "  no /mnt/wslg"
mount | grep -i wslg

echo
echo "=== 2. WSLg version ==="
cat /mnt/wslg/versions.txt 2>/dev/null | head -3 || echo "  cannot read versions.txt"

echo
echo "=== 3. session env (current shell) ==="
env | grep -E "^(DISPLAY|WAYLAND_DISPLAY|XDG_RUNTIME_DIR|PULSE_SERVER)=" || echo "  none set"

echo
echo "=== 4. systemd --user status ==="
if systemctl --user is-active >/dev/null 2>&1; then
  echo "  user bus: ACTIVE"
else
  echo "  user bus: BROKEN (this is why env not injected)"
  systemctl --user is-active 2>&1 | head -2
fi

echo
echo "=== 5. WSLg runtime-dir contents ==="
USER_UID=$(id -u)
ls -la "/mnt/wslg/run/user/$USER_UID/" 2>/dev/null | head -15

echo
echo "=== Verdict ==="
if [ -S /tmp/.X11-unix/X0 ] && [ -z "$DISPLAY" ]; then
  echo "  ⚠️  WSLg daemon UP, but session env not injected."
  echo "  → Fix: add to ~/.config/fish/config.fish (fish) or ~/.bashrc (bash):"
  echo "       export XDG_RUNTIME_DIR=/run/user/\$(id -u)"
  echo "       export DISPLAY=:0"
  echo "       export WAYLAND_DISPLAY=wayland-0"
  echo "       export PULSE_SERVER=unix:/mnt/wslg/PulseServer"
elif [ ! -S /tmp/.X11-unix/X0 ]; then
  echo "  ❌  WSLg daemon NOT running. Install via 'wsl --update' on Windows side + restart WSL."
else
  echo "  ✅  WSLg daemon UP and session env present. GUI should work."
fi