# ~/.config/fish/config.fish template

if status is-interactive
    fastfetch -c examples/10
end

set -g fish_greeting ""

# Oh-My-Posh prompt
oh-my-posh init fish --config 'night-owl' | source

# npm global path
export PATH="$(npm prefix -g)/bin:$PATH"

# Hermes TUI mode
set -x HERMES_TUI 1

# Hermes completions
hermes completion fish | source
