# CloudHarness Dev Container

This directory contains the configuration for the CloudHarness development container.

## Overview

The dev container provides a complete development environment with:
- Python 3.12 with all CloudHarness libraries
- Node.js 20 and package managers (npm, yarn)
- Docker CLI (connects to host Docker daemon)
- Kubernetes tools (kubectl, helm, skaffold, k9s) with security features
- Modern shell tools (starship prompt, atuin history, tmux, fzf)
- Enhanced editors (neovim with sensible defaults)
- Development utilities (htop, tig, gmap, rhttp)
- Version management (asdf)
- VS Code extensions and configurations

## Security Features

### Docker Access
- Docker CLI installed in container
- **Secured via docker-socket-proxy** - API-level filtering
- **Privileged containers BLOCKED** - Cannot bypass
- **Mount restrictions** - Only /workspace paths allowed
- **No direct socket mount** - Connects through TCP proxy
- **Battle-tested solution** - Used in production environments
- See [DOCKER_SECURITY.md](DOCKER_SECURITY.md) for detailed security information

### Kubernetes Access
- kubectl, helm, and skaffold installed with checksum verification
- Host kubeconfig mounted **read-only** at `~/.kube`
- Safety wrapper on kubectl to prevent accidental destructive operations
- See [KUBERNETES_SECURITY.md](KUBERNETES_SECURITY.md) for detailed security information

## Files

- `devcontainer.json` - Main dev container configuration (uses docker-compose)
- `docker-compose.yml` - Docker compose with socket proxy setup
- `Dockerfile` - Container image definition
- `DOCKER_SECURITY.md` - Docker socket proxy security documentation
- `KUBERNETES_SECURITY.md` - Kubernetes security documentation and best practices
- `SECURITY_QUICKREF.md` - Quick reference for security features
- `DOTFILES.md` - Guide for customizing with personal dotfiles
- `dev-scripts/` - Utility scripts (kubectl wrapper, setup, etc.)
- `home/` - Files mounted into container home directory (your dotfiles go here)
- `vscode/` - VS Code workspace settings (launch.json, settings.json, etc.)

## Usage

### Opening the Dev Container

1. Install VS Code and the "Dev Containers" extension
2. Open the CloudHarness repository in VS Code
3. Click "Reopen in Container" when prompted (or use Command Palette → "Dev Containers: Reopen in Container")

### First Time Setup

The container will automatically:
1. Build the Docker image (may take several minutes)
2. Install Python packages and dependencies
3. Set up the virtual environment
4. Configure VS Code settings
5. Set up kubectl safety wrapper

### Working with Docker

```bash
# All standard operations work normally
docker ps
docker images
docker build -t myimage .
docker run -d --name myapp myimage
docker-compose up

# Privileged operations are blocked by proxy
docker run --privileged ubuntu  # ❌ Blocked at API level
# Error: Forbidden - privileged mode not allowed

# System directory mounts are blocked
docker run -v /etc:/etc ubuntu  # ❌ Blocked by validator
# Error: MOUNT VALIDATION FAILED

# Workspace mounts work fine
docker run -v /workspace/data:/data ubuntu  # ✅ Works
```

### Working with Kubernetes

```bash
# Read-only operations work without prompts
kubectl get pods
kubectl describe deployment myapp
kubectl logs pod/my-pod

# Destructive operations require confirmation
kubectl delete pod my-pod
# → Shows warning and asks for confirmation

# Bypass safety wrapper (use with caution)
KUBECTL_SAFE_MODE=off kubectl delete pod my-pod
```

### Using Helm and Skaffold

```bash
# Generate and deploy using CloudHarness tools
harness-deployment cloudharness .

# Use helm directly
helm list
helm upgrade myapp ./helm/myapp

# Use skaffold for local development
skaffold dev
```

## Mounted Directories

| Host Path | Container Path | Mode | Purpose |
|-----------|----------------|------|---------|
| Repository root | `/workspace` | RW | Source code |
| `~/.docker` | `/root/.docker` | RO | Docker config/credentials |
| `~/.kube` | `/root/.kube` | RO | Kubernetes config/credentials |
| `/var/run/docker.sock` | `/var/run/docker.sock` | RW | Docker daemon socket |
| `.devcontainer/home` | `/root` | RW | Container home directory |
| `.devcontainer/vscode` | `/workspace/.vscode` | RW | VS Code workspace settings |

## Environment Variables

- `PYTHONPATH` - Includes all CloudHarness library paths
- `DOCKER_HOST` - Points to docker-socket-proxy (`tcp://127.0.0.1:2375`)
- `DOCKER_SOCKET_PROXY` - Flag indicating proxy is enabled (`1`)
- `KUBECONFIG` - Points to read-only kubeconfig
- `KUBECTL_SAFE_MODE` - Enables kubectl safety wrapper (`on` by default)

## Customization

### Adding More Tools

Edit the `Dockerfile` and add installation commands. For security:
1. Pin specific versions
2. Verify checksums for downloaded binaries
3. Document the changes

### VS Code Extensions

Add extensions to `devcontainer.json`:
```jsonc
"extensions": [
    "publisher.extension-name"
]
```

### Shell Configuration

Files in `home/` directory are mounted to `/root`:
- `home/.bashrc` - Shell configuration
- `home/.gitconfig` - Git configuration
- etc.

## Troubleshooting

### Container won't start
- Check Docker daemon is running on host
- Ensure you have permission to access Docker socket
- Try rebuilding: Command Palette → "Dev Containers: Rebuild Container"

### Kubernetes commands fail
- Verify `~/.kube/config` exists on host
- Check cluster connectivity from host first
- Ensure kubeconfig is valid

### Python imports not working
- Virtual environment should auto-activate
- Check `PYTHONPATH` environment variable
- Try reloading window: Command Palette → "Developer: Reload Window"

## Rebuilding the Container

When you change:
- `Dockerfile`
- `devcontainer.json` (build section)
- Dependencies in requirements files

Rebuild the container:
1. Command Palette → "Dev Containers: Rebuild Container"
2. Or: "Dev Containers: Rebuild Without Cache" for clean rebuild

## Security Considerations

This dev container has access to:
- ✅ Host file system (workspace directory)
- ✅ Host Docker daemon (via **secure proxy** - API-level filtering)
- ✅ Host Kubernetes clusters (read-only config)

Security measures in place:
- **Docker socket proxy** filters all Docker API calls
- **Privileged containers BLOCKED** at API level (cannot bypass)
- **No direct socket mount** - only proxy access
- **Battle-tested security** - used in production environments
- **Kubeconfig is read-only** (cannot modify credentials)
- **kubectl wrapper** prevents accidental destructive operations
- **All tools installed with checksum verification**
- **Docker config is read-only**

**Important**: The container runs as root inside the container namespace. Files created will have host user permissions due to bind mounts.

See [DOCKER_SECURITY.md](DOCKER_SECURITY.md) and [KUBERNETES_SECURITY.md](KUBERNETES_SECURITY.md) for detailed security information.

## Additional Resources

- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [CloudHarness Documentation](../docs/README.md)
- [Docker Security](./DOCKER_SECURITY.md)
- [Kubernetes Security](./KUBERNETES_SECURITY.md)
