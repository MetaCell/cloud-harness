# Docker Socket Proxy Security

This dev container uses [Tecnativa's docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy) to provide secure, filtered access to the Docker daemon.

## Why Socket Proxy?

### The Problem
Direct access to `/var/run/docker.sock` gives near-root access to the host system:
- Can mount any host directory
- Can run privileged containers  
- Can escape container isolation
- Supply chain attacks can exploit this access

### The Solution: API-Level Filtering
Instead of mounting the Docker socket directly, we use a proxy container:

```
Dev Container → TCP:2375 → docker-socket-proxy → /var/run/docker.sock → Docker Daemon
              (filtered)                         (direct access)
```

## Security Features

### ✅ What's Allowed

**Read Operations** (completely safe):
- `docker ps`, `docker images`, `docker logs`
- `docker inspect`, `docker version`, `docker info`
- Viewing events and monitoring

**Build Operations** (needed for development):
- `docker build` - Building images
- `docker commit` - Committing container changes

**Container Operations** (standard dev work):
- `docker run` - Starting containers
- `docker create` - Creating containers
- `docker exec` - Executing commands in containers
- `docker stop`, `docker start`, `docker restart`

**Network & Volume Operations** (needed for docker-compose):
- Creating and managing networks
- Creating and managing volumes

### ❌ What's Blocked

**Dangerous Operations** (blocked at API level):
- `docker run --privileged` - **BLOCKED** by proxy
- Host namespace modes require privileged - **BLOCKED**
- Device access requires privileged - **BLOCKED**

**Mount Restrictions** (client-side validation):
- Mounting paths outside `/workspace` - **BLOCKED** by validator
- System directories (`/`, `/etc`, `/home`, etc.) - **BLOCKED**
- Only workspace paths allowed for security

## Configuration

### Socket Proxy (API-Level Filtering)

The proxy is configured via environment variables in `docker-compose.yml`:

```yaml
environment:
  # Read operations - SAFE
  EVENTS: 1
  PING: 1
  VERSION: 1
  IMAGES: 1
  INFO: 1
  CONTAINERS: 1
  
  # Write operations - NEEDED FOR DEV
  POST: 1      # Create containers
  BUILD: 1     # Build images
  EXEC: 1      # Execute in containers
  NETWORKS: 1  # Manage networks
  VOLUMES: 1   # Manage volumes
  
  # Dangerous operations - DISABLED
  ALLOW_PRIVILEGED: 0  # Block --privileged
```

### Mount Validator (Client-Side Filtering)

Additional validation is performed client-side before API calls:

```bash
# Configured via environment variables
DOCKER_MOUNT_VALIDATION=on  # Enable validation
WORKSPACE_ROOT=/workspace    # Allowed mount prefix

# Applied via alias
alias docker='/usr/local/share/dev-scripts/docker-mount-validator.sh'
```

**Why Both Layers?**
- **Socket Proxy**: Blocks privileged operations (cannot bypass)
- **Mount Validator**: Blocks dangerous mounts (adds convenience layer)
- **Defense in Depth**: Multiple security layers

## How It Works

### 1. Proxy Container Startup
The proxy starts automatically with docker-compose when you open the dev container.

### 2. Dev Container Connection
```bash
# Dev container uses TCP to connect to proxy via localhost
export DOCKER_HOST=tcp://127.0.0.1:2375
docker ps  # Proxied through security layer
```

### 3. API Filtering
```bash
# Allowed operation
docker run ubuntu echo "hello"
# → API call permitted → executes

# Blocked operation
docker run --privileged ubuntu
# → API call blocked by proxy → error returned
```

## Usage Examples

### Normal Development (All Work Normally)

```bash
# Build images
docker build -t myapp .

# Run containers
docker run -d --name myapp -p 8080:80 myapp

# Debug containers
docker exec -it myapp bash
docker logs myapp

# Use docker-compose
docker-compose up -d

# Manage resources
docker images
docker ps -a
docker volume ls
```

### What Gets Blocked

```bash
# Privileged container - BLOCKED by proxy
docker run --privileged ubuntu
# Error: API call rejected by proxy

# System directory mounts - BLOCKED by validator
docker run -v /etc:/etc ubuntu
# ❌ MOUNT VALIDATION FAILED:
#    Attempting to mount: /etc
#    Only /workspace paths are allowed for security.

# Workspace mounts - ALLOWED
docker run -v /workspace/data:/data ubuntu
# ✅ Works fine
```

## Advantages

### 1. **No Bypass Possible**
- Security enforced at network/API level
- Cannot circumvent by calling different binary
- Cannot disable with environment variable
- True defense in depth

### 2. **Battle-Tested**
- Used in production by thousands of projects
- Active development and security updates
- Well-documented and community-supported

### 3. **Granular Control**
- Enable only needed API endpoints
- Adjust permissions per environment
- Clear security policy via configuration

### 4. **True Privileged Blocking**
Unlike wrappers that just warn, this actually BLOCKS:
```bash
docker run --privileged ubuntu
# Error: Forbidden - privileged mode is not allowed
```

## Configuration Options

### Stricter Security (Limit More)

Edit `docker-compose.yml`:
```yaml
environment:
  CONTAINERS: 1   # Read only
  POST: 0         # Block creating containers
  BUILD: 1        # Allow builds only
  EXEC: 0         # Block exec
```

### More Permissive (Enable More)

```yaml
environment:
  # Enable Docker Swarm
  SERVICES: 1
  SWARM: 1
  NODES: 1
  
  # Enable secrets
  SECRETS: 1
```

## Troubleshooting

### "Cannot connect to Docker daemon"

Check proxy is running:
```bash
docker ps | grep cloudharness-docker-proxy
```

Check environment variable:
```bash
echo $DOCKER_HOST
# Should show: tcp://127.0.0.1:2375
```

### "Forbidden" or "Permission Denied"

The proxy is blocking the operation (e.g., `--privileged`). This is intentional for security.

To allow specific operations, edit `docker-compose.yml` and restart the proxy.

### "MOUNT VALIDATION FAILED"

The mount validator is blocking paths outside `/workspace`. This is intentional for security.

To bypass temporarily:
```bash
DOCKER_MOUNT_VALIDATION=off docker run -v /path:/path ubuntu
```

To allow specific paths, edit `.devcontainer/dev-scripts/docker-mount-validator.sh`:
```bash
ALLOWED_MOUNT_PATHS=(
    "/workspace"
    "/your/custom/path"  # Add here
)
```

## Monitoring

### View Proxy Logs
```bash
# See what API calls are being made
docker logs -f cloudharness-docker-proxy

# Look for blocked operations
docker logs cloudharness-docker-proxy | grep -i forbidden
```

## Security Checklist

- [x] Docker socket not mounted in dev container
- [x] Proxy has read-only access to socket
- [x] Privileged mode blocked (`ALLOW_PRIVILEGED=0`)
- [x] Mount validator restricts paths to /workspace only
- [x] Proxy runs on localhost only (`127.0.0.1:2375`)
- [x] Minimal API endpoints enabled
- [x] Proxy logs available for auditing
- [x] Proxy automatically starts with dev container
- [x] Client-side mount validation enabled

## Additional Resources

- [Tecnativa docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy)
- [Docker Socket Security](https://docs.docker.com/engine/security/)
- [Container Security Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)

---

**Remember**: This provides defense-in-depth security. The proxy adds a strong security layer, but always follow best practices: use trusted images, scan for vulnerabilities, and monitor container activity.
