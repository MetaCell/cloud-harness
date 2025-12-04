#!/bin/bash
# Common bash configuration for CloudHarness dev container
# Contributors can add useful aliases and functions here

# ============================================================================
# Common Aliases
# ============================================================================

# Enhanced ls
alias ll='ls -alFh'
alias la='ls -A'
alias l='ls -CF'

# Git shortcuts
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git log --oneline --graph --decorate'
alias gd='git diff'
alias gco='git checkout'
alias gb='git branch'

# Docker shortcuts
alias d='docker'
alias dc='docker-compose'
alias dps='docker ps'
alias dpsa='docker ps -a'
alias di='docker images'
alias dex='docker exec -it'
alias dlogs='docker logs -f'

# Kubernetes shortcuts
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get services'
alias kgd='kubectl get deployments'
alias kgn='kubectl get nodes'
alias kdp='kubectl describe pod'
alias kds='kubectl describe service'
alias kdd='kubectl describe deployment'
alias kexec='kubectl exec -it'

# Directory navigation
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias ~='cd ~'

# Safety
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'

# Editor
alias vim='nvim'
alias vi='nvim'

# Misc
alias h='history'
alias c='clear'
alias reload='source ~/.bashrc'
alias path='echo -e ${PATH//:/\\n}'
alias ports='netstat -tulanp'

# ============================================================================
# Useful Functions
# ============================================================================

# Create directory and cd into it
mkcd() {
    mkdir -p "$1" && cd "$1"
}

# Extract various archive formats
extract() {
    if [ -f "$1" ]; then
        case "$1" in
            *.tar.bz2)   tar xjf "$1"     ;;
            *.tar.gz)    tar xzf "$1"     ;;
            *.bz2)       bunzip2 "$1"     ;;
            *.rar)       unrar x "$1"     ;;
            *.gz)        gunzip "$1"      ;;
            *.tar)       tar xf "$1"      ;;
            *.tbz2)      tar xjf "$1"     ;;
            *.tgz)       tar xzf "$1"     ;;
            *.zip)       unzip "$1"       ;;
            *.Z)         uncompress "$1"  ;;
            *.7z)        7z x "$1"        ;;
            *)           echo "'$1' cannot be extracted via extract()" ;;
        esac
    else
        echo "'$1' is not a valid file"
    fi
}

# Quick find
qfind() {
    find . -name "*$1*"
}

# Git clone and cd
gclone() {
    git clone "$1" && cd "$(basename "$1" .git)"
}

# Docker quick cleanup
dclean() {
    docker system prune -af --volumes
}

# Kubernetes namespace quick switch
kns() {
    if [ -z "$1" ]; then
        kubectl config view --minify --output 'jsonpath={..namespace}'
        echo
    else
        kubectl config set-context --current --namespace="$1"
    fi
}

# Show kubectl current context
kctx() {
    if [ -z "$1" ]; then
        kubectl config current-context
    else
        kubectl config use-context "$1"
    fi
}

# Port forward shortcut
kpf() {
    local pod=$1
    local port=${2:-8080}
    kubectl port-forward "$pod" "$port:$port"
}

# Logs with namespace
klogs() {
    local pod=$1
    shift
    kubectl logs -f "$pod" "$@"
}

# Quick Python virtual environment activation
venv() {
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        echo "No virtual environment found (venv or .venv)"
    fi
}

# CloudHarness specific shortcuts
alias ch-deploy='harness-deployment'
alias ch-build='harness-deployment cloudharness . && skaffold build'
alias ch-dev='skaffold dev'

# ============================================================================
# Environment Configuration
# ============================================================================

# Better history
export HISTSIZE=10000
export HISTFILESIZE=20000
export HISTCONTROL=ignoreboth:erasedups
shopt -s histappend

# Better autocomplete
bind 'set completion-ignore-case on'
bind 'set show-all-if-ambiguous on'

# ============================================================================
# Tool Integrations
# ============================================================================

# fzf integration (if installed)
if command -v fzf &> /dev/null; then
    # CTRL-T: Paste the selected file path into the command line
    # CTRL-R: Search through command history
    # ALT-C: cd into the selected directory
    [ -f /usr/share/doc/fzf/examples/key-bindings.bash ] && source /usr/share/doc/fzf/examples/key-bindings.bash
    [ -f /usr/share/doc/fzf/examples/completion.bash ] && source /usr/share/doc/fzf/examples/completion.bash
fi

# NOTE: Starship and Atuin are initialized in ~/.bashrc
# in the correct order to ensure compatibility

# asdf version manager (if installed)
if [ -f "$HOME/.asdf/asdf.sh" ]; then
    . "$HOME/.asdf/asdf.sh"
    . "$HOME/.asdf/completions/asdf.bash"
fi

# ============================================================================
# Welcome Message
# ============================================================================

echo "CloudHarness Development Container"
echo "-----------------------------------"
echo "Common aliases loaded. Type 'alias' to see all available shortcuts."
echo ""
