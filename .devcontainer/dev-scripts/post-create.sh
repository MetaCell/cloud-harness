#!/bin/bash
# Post-create setup script for CloudHarness dev container

set -e

echo "Setting up CloudHarness development environment..."

# Make scripts executable
chmod +x /usr/local/share/dev-scripts/*.sh

# Run vscode setup
/usr/local/share/dev-scripts/vscode-setup.sh

# Setup Kubernetes access
/usr/local/share/dev-scripts/setup-docker-desktop-kube.sh

# Setup Docker config (remove incompatible credential helpers)
echo "Configuring Docker credentials..."
mkdir -p /root/.docker-container
if [ -f /root/.docker/config.json ]; then
    # Copy and sanitize the Docker config using jq to properly handle JSON
    if command -v jq &> /dev/null; then
        jq 'del(.credsStore)' /root/.docker/config.json > /root/.docker-container/config.json
    else
        # Fallback: use Python to remove credsStore
        python3 -c "import json, sys; config=json.load(open('/root/.docker/config.json')); config.pop('credsStore', None); json.dump(config, sys.stdout, indent=2)" > /root/.docker-container/config.json
    fi
else
    # Create minimal config if none exists
    echo '{}' > /root/.docker-container/config.json
fi

# Download bash-preexec if it doesn't exist (required for atuin/starship)
if [ ! -f ~/.bash-preexec.sh ]; then
    echo "Downloading bash-preexec..."
    curl -sL https://raw.githubusercontent.com/rcaloras/bash-preexec/master/bash-preexec.sh -o ~/.bash-preexec.sh
fi

# Initialize bashrc if needed
if [ ! -f ~/.bashrc ] || [ ! -s ~/.bashrc ] || ! grep -q 'common-bashrc' ~/.bashrc; then
    echo "Initializing ~/.bashrc..."

    cat > ~/.bashrc << 'EOF'
# CloudHarness Dev Container Bash Configuration

# Enable colors for ls and grep
export LS_COLORS='di=1;34:ln=1;36:so=1;35:pi=1;33:ex=1;32:bd=1;33:cd=1;33:su=1;31:sg=1;31:tw=1;34:ow=1;34'
alias ls='ls --color=auto'
alias grep='grep --color=auto'

# Setup Docker Desktop Kubernetes access (sources KUBECONFIG)
source /usr/local/share/dev-scripts/setup-docker-desktop-kube.sh

# Kubectl safety wrapper
alias kubectl='/usr/local/share/dev-scripts/kubectl-wrapper.sh'
export KUBECTL_SAFE_MODE=on

# Docker security is handled by docker-socket-proxy
# Additional client-side mount validation for extra protection
if [ -n "$DOCKER_SOCKET_PROXY" ]; then
    echo "Docker access secured via socket proxy at $DOCKER_HOST"
    alias docker='/usr/local/share/dev-scripts/docker-mount-validator.sh'
    export DOCKER_MOUNT_VALIDATION=on
    export WORKSPACE_ROOT=/workspace
fi

# Source common bash configuration (aliases and functions)
if [ -f /usr/local/share/dev-scripts/common-bashrc.sh ]; then
    source /usr/local/share/dev-scripts/common-bashrc.sh
fi

# Source the virtual environment (must use source, not bash)
if [ -f /usr/local/share/dev-scripts/use-venv ]; then
    source /usr/local/share/dev-scripts/use-venv
fi

# Load bash-preexec (required for atuin and starship to work with VS Code)
if [ -f ~/.bash-preexec.sh ]; then
    source ~/.bash-preexec.sh
fi

# Initialize Atuin BEFORE Starship (order matters!)
# Atuin needs bash-preexec and to hook into PROMPT_COMMAND before Starship
if command -v atuin &> /dev/null; then
    eval "$(atuin init bash)"
fi

# Initialize Starship prompt (must be after Atuin)
# Starship will preserve existing PROMPT_COMMAND entries
if command -v starship &> /dev/null; then
    export STARSHIP_CONFIG=~/.config/starship.toml
    eval "$(starship init bash)"
fi

# Fix for VS Code shell integration overriding bash-preexec's DEBUG trap
# VS Code loads its shell integration after bashrc, so we restore the trap on each prompt
__restore_bash_preexec_trap() {
    if declare -F __bp_preexec_invoke_exec &>/dev/null; then
        local current_trap=\$(trap -p DEBUG)
        if [[ "\$current_trap" != *"__bp_preexec_invoke_exec"* ]]; then
            trap '__bp_preexec_invoke_exec "\$_"' DEBUG
        fi
    fi
}

# Add the trap restoration to PROMPT_COMMAND
if [[ "\$PROMPT_COMMAND" != *"__restore_bash_preexec_trap"* ]]; then
    PROMPT_COMMAND="__restore_bash_preexec_trap\${PROMPT_COMMAND:+; \$PROMPT_COMMAND}"
fi

# asdf version manager
if [ -f "\$HOME/.asdf/asdf.sh" ]; then
    . "\$HOME/.asdf/asdf.sh"
    . "\$HOME/.asdf/completions/asdf.bash"
fi
EOF
fi

# Initialize Atuin (shell history database)
if command -v atuin &> /dev/null; then
    echo "Initializing Atuin shell history..."
    
    # Create atuin data directory if it doesn't exist
    mkdir -p ~/.local/share/atuin ~/.config/atuin
    
    # Generate default config with explicit paths (only if it doesn't exist)
    if [ ! -f ~/.config/atuin/config.toml ]; then
        cat > ~/.config/atuin/config.toml << 'ATUINCONF'
## Atuin configuration for CloudHarness dev container

## Explicitly set paths to avoid VS Code XDG_DATA_HOME issues
db_path = "~/.local/share/atuin/history.db"
key_path = "~/.local/share/atuin/key"
session_path = "~/.local/share/atuin/session"

dialect = "uk"
auto_sync = false
update_check = false
search_mode = "fuzzy"
filter_mode = "global"
style = "auto"
inline_height = 20
show_preview = true
exit_mode = "return-original"
max_preview_height = 4
show_help = true
secrets_filter = true
enter_accept = true
history_filter = ["^secret", "^password", "AWS_SECRET", "KUBECONFIG"]
ATUINCONF
    fi
    
    # Import existing bash history
    if [ -f ~/.bash_history ]; then
        echo "Importing bash history into Atuin..."
        atuin import auto 2>/dev/null || true
    fi
fi

# Create Starship config if it doesn't exist
if [ ! -f ~/.config/starship.toml ]; then
    echo "Creating Starship prompt configuration..."
    mkdir -p ~/.config
    cat > ~/.config/starship.toml << 'STARSHIPCONF'
# Starship prompt configuration for CloudHarness dev container
# Documentation: https://starship.rs/config/

# Timeout for starship to run (in milliseconds)
command_timeout = 1000

# Add a new line before the prompt
add_newline = true

# Format of the prompt
format = """
[╭─](bold green)$username\
$hostname\
$directory\
$git_branch\
$git_status\
$python\
$nodejs\
$docker_context\
$kubernetes
[╰─](bold green)$character"""

[character]
success_symbol = "[➜](bold green)"
error_symbol = "[✗](bold red)"

[username]
style_user = "bold yellow"
style_root = "bold red"
format = "[$user]($style) "
disabled = false
show_always = true

[hostname]
ssh_only = false
format = "[@$hostname](bold blue) "
disabled = false

[directory]
truncation_length = 3
truncate_to_repo = true
format = "[$path]($style)[$read_only]($read_only_style) "
style = "bold cyan"
read_only = " 🔒"

[git_branch]
symbol = " "
format = "on [$symbol$branch]($style) "
style = "bold purple"

[git_status]
format = '([\[$all_status$ahead_behind\]]($style) )'
style = "bold red"
conflicted = "🏳"
ahead = "⇡${count}"
behind = "⇣${count}"
diverged = "⇕⇡${ahead_count}⇣${behind_count}"
untracked = "?${count}"
stashed = "$${count}"
modified = "!${count}"
staged = "+${count}"
renamed = "»${count}"
deleted = "✘${count}"

[python]
symbol = " "
format = 'via [${symbol}${pyenv_prefix}(${version} )(\($virtualenv\) )]($style)'
style = "yellow"
pyenv_version_name = false
detect_extensions = ["py"]
detect_files = [".python-version", "Pipfile", "__pycache__", "pyproject.toml", "requirements.txt", "setup.py", "tox.ini"]
detect_folders = []

[nodejs]
symbol = " "
format = "via [$symbol($version )]($style)"
style = "bold green"

[docker_context]
symbol = " "
format = "via [$symbol$context]($style) "
style = "blue bold"
only_with_files = true
detect_files = ["docker-compose.yml", "docker-compose.yaml", "Dockerfile"]
detect_folders = []

[kubernetes]
symbol = "☸ "
format = 'on [$symbol$context( \($namespace\))]($style) '
style = "cyan bold"
disabled = false
detect_files = ["k8s"]
detect_folders = ["k8s"]

[kubernetes.context_aliases]
"docker-desktop" = "🐳 desktop"
"kind-.*" = "kind"
"minikube" = "mini"

[cmd_duration]
min_time = 500
format = "took [$duration](bold yellow) "

[time]
disabled = false
format = '🕙[\[ $time \]]($style) '
time_format = "%T"
style = "bold white"

[memory_usage]
disabled = true
threshold = -1
symbol = " "
format = "via $symbol[${ram_pct}]($style) "
style = "bold dimmed white"

[package]
disabled = true
STARSHIPCONF
fi

# Create tmux config if it doesn't exist
if [ ! -f ~/.tmux.conf ]; then
    cat > ~/.tmux.conf << 'EOF'
# CloudHarness tmux configuration

# Remap prefix to Ctrl-a
unbind C-b
set-option -g prefix C-a
bind-key C-a send-prefix

# Split panes using | and -
bind | split-window -h
bind - split-window -v
unbind '"'
unbind %

# Reload config file
bind r source-file ~/.tmux.conf \; display "Config reloaded!"

# Switch panes using Alt-arrow without prefix
bind -n M-Left select-pane -L
bind -n M-Right select-pane -R
bind -n M-Up select-pane -U
bind -n M-Down select-pane -D

# Enable mouse mode
set -g mouse on

# Don't rename windows automatically
set-option -g allow-rename off

# Start windows and panes at 1, not 0
set -g base-index 1
setw -g pane-base-index 1

# Status bar
set -g status-position bottom
set -g status-style 'bg=colour234 fg=colour137'
set -g status-left ''
set -g status-right '#[fg=colour233,bg=colour241] %d/%m #[fg=colour233,bg=colour245] %H:%M:%S '
set -g status-right-length 50
set -g status-left-length 20

# Active window
setw -g window-status-current-style 'fg=colour81 bg=colour238 bold'
setw -g window-status-current-format ' #I#[fg=colour250]:#[fg=colour255]#W#[fg=colour50]#F '

# Inactive windows
setw -g window-status-style 'fg=colour138 bg=colour235'
setw -g window-status-format ' #I#[fg=colour237]:#[fg=colour250]#W#[fg=colour244]#F '
EOF
fi

echo ""
echo "✓ CloudHarness development environment ready!"
echo ""
echo "Available tools:"
echo "  - kubectl, helm, skaffold, k9s (Kubernetes)"
echo "  - nvim (Neovim with sensible defaults)"
echo "  - tmux (terminal multiplexer)"
echo "  - starship (beautiful prompt)"
echo "  - atuin (shell history)"
echo "  - htop, tig, gmap, rhttp"
echo ""
echo "Type 'alias' to see common shortcuts or check /usr/local/share/dev-scripts/common-bashrc.sh"
echo ""
