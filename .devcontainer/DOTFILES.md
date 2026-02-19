# Custom Dotfiles Support

The dev container supports custom dotfiles for personal configuration preferences.

## Using Your Own Dotfiles

### Option 1: Using VS Code's Dotfiles Support

VS Code can automatically clone and apply your dotfiles repository:

1. Open VS Code Settings (Cmd/Ctrl + ,)
2. Search for "dotfiles"
3. Set "Dotfiles: Repository" to your dotfiles repo (e.g., `username/dotfiles`)
4. Optionally set "Dotfiles: Install Command" (default: `install.sh`)
5. Optionally set "Dotfiles: Target Path" (default: `~/dotfiles`)

VS Code will automatically clone and install your dotfiles when creating the dev container.

### Option 2: Manual Setup

Place your dotfiles in `.devcontainer/home/`:

```bash
# Example structure
.devcontainer/home/
  .bashrc          # Your custom bash config (will be merged)
  .gitconfig       # Your git configuration
  .tmux.conf       # Your tmux configuration
  .config/
    nvim/
      init.vim     # Your neovim configuration
    starship.toml  # Your starship prompt config
```

These files are mounted into the container at `/root/` and persist across rebuilds.

## Common Customizations

### Bash

The container sources `/usr/local/share/dev-scripts/common-bashrc.sh` for shared aliases.
Add your personal aliases to `~/.bashrc` or `.devcontainer/home/.bashrc`:

```bash
# Personal aliases
alias myproject='cd /workspace/applications/myapp'
alias restart-server='docker-compose restart backend'
```

### Git

Create `.devcontainer/home/.gitconfig`:

```ini
[user]
    name = Your Name
    email = your.email@example.com
[core]
    editor = nvim
[alias]
    st = status
    co = checkout
    br = branch
```

### Neovim

The default config is at `/root/.config/nvim/init.vim`.
You can override it by placing your config in `.devcontainer/home/.config/nvim/init.vim`.

For plugin managers, consider:
- [lazy.nvim](https://github.com/folke/lazy.nvim)
- [packer.nvim](https://github.com/wbthomason/packer.nvim)

### Starship Prompt

Customize the prompt by editing `.devcontainer/home/.config/starship.toml`:

```toml
# Example: Change prompt format
format = """
$username\
$hostname\
$directory\
$git_branch\
$character"""

[character]
success_symbol = "[➜](bold green)"
error_symbol = "[✗](bold red)"
```

See [Starship Configuration](https://starship.rs/config/) for all options.

### Tmux

Create `.devcontainer/home/.tmux.conf` for your tmux preferences:

```bash
# Example customizations
set -g prefix C-b  # Use Ctrl-b instead of Ctrl-a
set -g mouse off   # Disable mouse mode
```

### asdf Version Manager

Install language plugins as needed:

```bash
# Install Node.js plugin
asdf plugin add nodejs

# Install specific version
asdf install nodejs 20.10.0
asdf global nodejs 20.10.0

# Install Python plugin (if you need different versions)
asdf plugin add python
asdf install python 3.11.6
```

Popular plugins:
- `nodejs` - Node.js versions
- `python` - Python versions
- `golang` - Go versions
- `ruby` - Ruby versions
- `terraform` - Terraform versions

See [asdf plugins](https://github.com/asdf-vm/asdf-plugins) for full list.

## Sharing Team Configurations

To share configurations across the team:

1. Add them to `/usr/local/share/dev-scripts/common-bashrc.sh` for aliases
2. Create default configs in `.devcontainer/home/.config/`
3. Document them in this file
4. Commit to the repository

Team members can override these with their personal dotfiles.

## Tools Already Configured

The container includes sensible defaults for:

- **Bash**: Common aliases for git, docker, kubernetes
- **Starship**: Minimal prompt showing context, git status, k8s context
- **Neovim**: Basic IDE-like features without plugins
- **Tmux**: Ergonomic key bindings and status bar
- **Atuin**: Enhanced shell history with sync support

## Tips

### Atuin Shell History

Atuin provides enhanced shell history with:
- Full-text search: `Ctrl+R`
- Statistics: `atuin stats`
- Sync across machines: `atuin sync`

To enable sync:
```bash
atuin register -u <username> -e <email>
atuin login -u <username>
atuin sync
```

### k9s Kubernetes UI

Launch the interactive Kubernetes dashboard:
```bash
k9s
```

Key shortcuts:
- `:pod` - View pods
- `:svc` - View services
- `:deploy` - View deployments
- `?` - Help
- `/` - Filter
- `l` - Logs
- `d` - Describe
- `e` - Edit

### Neovim LSP (Optional)

To add LSP support, create a plugin config. Example with lazy.nvim:

```vim
" In ~/.config/nvim/init.vim, add:
lua << EOF
-- Bootstrap lazy.nvim
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git", "clone", "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable", lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

-- Install plugins
require("lazy").setup({
  "neovim/nvim-lspconfig",
  "hrsh7th/nvim-cmp",
  "hrsh7th/cmp-nvim-lsp",
})
EOF
```

## Troubleshooting

### Dotfiles not loading

- Check file permissions: `ls -la ~/.config/`
- Verify mount in devcontainer.json
- Reload window: Cmd/Ctrl + Shift + P → "Reload Window"

### Conflicts with default configs

Files in `.devcontainer/home/` override defaults. If you want to extend instead:

```bash
# In your .bashrc
source /usr/local/share/dev-scripts/common-bashrc.sh
# Your customizations here
```

### asdf not working

Ensure it's sourced in your shell:
```bash
echo '. $HOME/.asdf/asdf.sh' >> ~/.bashrc
source ~/.bashrc
```
