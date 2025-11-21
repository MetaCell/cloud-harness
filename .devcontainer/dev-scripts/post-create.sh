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
source /workspace/dev-scripts/common-bashrc.sh

# Source the virtual environment (must use source, not bash)
if [ -f /workspace/dev-scripts/use-venv ]; then
    source /workspace/dev-scripts/use-venv
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

# Fix for VS Code shell integration overriding PROMPT_COMMAND
# Ensure bash-preexec hooks are called so atuin and starship work
if declare -F __bp_precmd_invoke_cmd &>/dev/null; then
    # Prepend bash-preexec to PROMPT_COMMAND if not already there
    if [[ "$PROMPT_COMMAND" != *"__bp_precmd_invoke_cmd"* ]]; then
        PROMPT_COMMAND="__bp_precmd_invoke_cmd; $PROMPT_COMMAND"
    fi
fi

# asdf version manager
if [ -f "$HOME/.asdf/asdf.sh" ]; then
    . "$HOME/.asdf/asdf.sh"
    . "$HOME/.asdf/completions/asdf.bash"
fi
EOF
fi

# Initialize Atuin (shell history database)
if command -v atuin &> /dev/null; then
    echo "Initializing Atuin shell history..."
    
    # Create atuin data directory if it doesn't exist
    mkdir -p ~/.local/share/atuin ~/.config/atuin
    
    # Generate default config with explicit paths
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
    
    # Import existing bash history
    if [ -f ~/.bash_history ]; then
        echo "Importing bash history into Atuin..."
        atuin import auto 2>/dev/null || true
    fi
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
