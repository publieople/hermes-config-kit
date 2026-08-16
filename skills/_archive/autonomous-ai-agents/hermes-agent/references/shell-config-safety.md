# Shell Configuration Safety

When modifying a user's shell init files (`.bashrc`, `config.fish`, `.zshrc`, etc.) to set Hermes environment variables or aliases, the wrong assumption can overwrite or misplace config. This reference documents the detection workflow and common pitfalls.

## Detection Workflow

```python
# DO this before any shell config modification:
1. current_shell = $SHELL                  # login shell (may be bash with exec fish)
2. check ~/.bashrc for "exec fish|exec zsh"  # user may switch after login
3. getent passwd $USER | cut -d: -f7       # actual login shell
4. which $CURRENT_SHELL                     # verify the shell is installed
5. ls the config file you plan to edit      # confirm it exists before overwriting
```

**Key rule**: Never assume the user's interactive shell matches `$SHELL`. Common patterns:
- Bash with `exec fish` in `.bashrc` → fish is the interactive shell
- `.bash_profile` → `.bashrc` → `exec` → the lines after `exec` never run
- `.bashrc` may have `[[ $- != *i* ]] && return` at the top → non-interactive bash skips rest

## Common Shell Config Files

| Shell | Config file | Notes |
|-------|------------|-------|
| bash | `~/.bashrc` | Interactive non-login. Login: `~/.bash_profile` or `~/.profile` |
| fish | `~/.config/fish/config.fish` + `~/.config/fish/conf.d/*.fish` | `conf.d/` loaded first, alphabetical order. `config.fish` may not exist — check before creating |
| zsh | `~/.zshrc` | |

## Hermes-Specific Settings

**Correct approach for TUI default:**
```bash
# bash/zsh
export HERMES_TUI=1

# fish
set -x HERMES_TUI 1
```

**Env var over alias.** `alias hermes='hermes --tui'` only covers bare `hermes`. `export HERMES_TUI=1` covers `hermes`, `hermes chat`, and any subprocess.

**Shell-agnostic alternative:** Set the env var in `/etc/environment`, `~/.pam_environment`, or the Windows `%USERPROFILE%\.wslconfig` (for WSL).

## Pitfalls

- **`exec fish` in .bashrc**: lines after `exec_fish` never run. Don't put env vars there.
- **`hermes config set display.mouse_tracking true`**: verified to place the key correctly under the `display:` section in config.yaml.
- **fish `config.fish` may not exist**: Don't create it without confirming with the user — they may have all their config in `conf.d/`. Creating an empty config.fish overrides nothing, but if you overwrite an existing one, you lose their startup commands (fastfetch, oh-my-posh, etc.).
- **WSL bash → exec fish**: the environment is still inherited from bash. `export HERMES_TUI=1` in `.bashrc` (before `exec fish`) works, but it's cleaner in `config.fish` so fish users find it where they expect it.
