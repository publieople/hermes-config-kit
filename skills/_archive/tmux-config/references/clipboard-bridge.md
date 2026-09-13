# tmux Clipboard Bridge — picking the right one per host

The only block in `~/.tmux.conf` that has to change per host is the
copy/paste bridge. Everything else can be identical.

## Decision table

| Host                 | Bridge                                          | Why                                    |
| -------------------- | ----------------------------------------------- | -------------------------------------- |
| WSL2 (Windows host)  | `/mnt/c/Windows/System32/clip.exe`              | Native Windows clipboard, no X server  |
| WSL2 + WSLg         | `clip.exe` still wins, but `wl-copy` also works  | Pick one; clip.exe is fewer surprises  |
| Linux + X11 + xsel   | `xsel --clipboard --input` / `--output`         | Writes to both PRIMARY and CLIPBOARD   |
| Linux + X11 + xclip  | `xclip -selection clipboard` / `-o`             | Equivalent to xsel                     |
| Linux + Wayland      | `wl-copy` / `wl-paste`                          | Wayland-native; xsel won't work        |
| macOS                | `pbcopy` / `pbpaste`                            | Only if SSH'd in with TTY allocation   |
| Headless (no display) | OSC 52 escape sequences only                   | Use a terminal that speaks OSC 52      |

## Detection snippet (drop into tmux.conf)

```sh
# Pick the best clipboard tool on the host
clip_set=' '
clip_get=' '
if [ -x /mnt/c/Windows/System32/clip.exe ]; then
  clip_set='tmux save-buffer - | /mnt/c/Windows/System32/clip.exe'
  clip_get='/mnt/c/Windows/System32/powershell.exe -NoProfile -Command Get-Clipboard'
elif command -v pbcopy >/dev/null; then
  clip_set='tmux save-buffer - | pbcopy'
  clip_get='pbpaste'
elif command -v wl-copy >/dev/null; then
  clip_set='tmux save-buffer - | wl-copy'
  clip_get='wl-paste'
elif command -v xsel >/dev/null; then
  clip_set='tmux save-buffer - | xsel --clipboard --input'
  clip_get='xsel --clipboard --output'
elif command -v xclip >/dev/null; then
  clip_set='tmux save-buffer - | xclip -selection clipboard'
  clip_get='xclip -selection clipboard -o'
fi
```

Then bind conditionally, or just bind to a wrapper script that no-ops when
no tool exists.

## Pitfalls

- **`xsel` writes to PRIMARY by default** — most GUI apps read CLIPBOARD.
  Always pass `--clipboard`. xclip's default is also wrong; pass `-selection clipboard`.
- **`pbcopy` needs a TTY** — over `ssh host 'tmux ... | pbcopy'` it can hang
  silently. Use `</dev/null` or `-S` or just bind inside tmux where the TTY exists.
- **WSL2 `clip.exe` writes CR-LF**, Unix tools downstream may choke. Strip with
  `tr -d '\r'` if you see weird line endings after paste.
- **`/mnt/c/...` paths are slow** — each invocation forks into the 9P filesystem.
  For hot paths (copy-mode-vi y) it's fine; don't put it in a status-interval script.
- **OSC 52 fallback** — works over SSH without any clipboard tool, but only if
  the terminal emulator supports it. iTerm2, WezTerm, recent Alacritty, kitty: yes.
  Windows Terminal: yes. Older PuTTY: no.
