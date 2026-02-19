# Security Quick Reference

## 🔒 Security Features Enabled

| Feature | Status | Purpose |
|---------|--------|---------||
| Docker Socket Proxy | ✅ Enabled | API-level filtering, blocks privileged operations |
| Privileged Container Block | ✅ Enabled | Cannot run privileged containers |
| No Direct Socket Mount | ✅ Enabled | Dev container connects via TCP proxy only |
| Kubeconfig Read-Only Mount | ✅ Enabled | Prevents credential theft/modification |
| Production Cluster Filtering | ✅ Enabled | Blocks access to production environments |
| Tool Checksum Verification | ✅ Enabled | Prevents supply chain attacks |
| Kubectl Safety Wrapper | ✅ Enabled | Prevents accidental destructive operations |
| Pinned Tool Versions | ✅ Enabled | Prevents automatic updates to compromised versions |

## 📝 Quick Commands

### Docker Operations

#### Standard Operations (Work Normally)
```bash
docker ps
docker images
docker build -t myapp .
docker run -d myapp
docker exec -it myapp bash
docker logs myapp
docker-compose up
```

#### Blocked Operations (Cannot Bypass)
```bash
docker run --privileged ubuntu              # ❌ Blocked by API proxy
# Error: Forbidden - privileged mode not allowed

docker run --cap-add=ALL ubuntu             # ❌ Blocked by API proxy
docker run --pid=host ubuntu                # ❌ Blocked by API proxy

# Mount validation (client-side)
docker run -v /etc:/etc ubuntu              # ❌ Blocked by validator
# Error: MOUNT VALIDATION FAILED - Only /workspace paths allowed

docker run -v /workspace/data:/data ubuntu  # ✅ Allowed
```

#### Checking Proxy Status
```bash
# Check if proxy is running
docker ps | grep docker-proxy

# View proxy logs
docker logs cloudharness-docker-proxy

# Check docker connection
echo $DOCKER_HOST  # Should show: tcp://127.0.0.1:2375
```

### Kubernetes Operations

#### Safe Operations (No Prompt)
```bash
kubectl get pods
kubectl get nodes
kubectl describe service myapp
kubectl logs -f deployment/myapp
kubectl port-forward service/myapp 8080:80
```

### Destructive Operations (Requires Confirmation)
```bash
kubectl delete pod myapp-xyz          # ⚠️ Prompts for confirmation
kubectl apply -f deployment.yaml      # ⚠️ Prompts for confirmation
kubectl scale deployment myapp --replicas=3  # ⚠️ Prompts for confirmation
```

### Bypass Safety (Use Carefully)
```bash
# For a single command
KUBECTL_SAFE_MODE=off kubectl delete pod myapp-xyz

# For current shell session
export KUBECTL_SAFE_MODE=off
kubectl delete pod myapp-xyz

# Re-enable
export KUBECTL_SAFE_MODE=on
```

## 🚨 Critical Namespaces (Extra Protection)

These namespaces trigger additional warnings:
- `kube-system` - Core Kubernetes components
- `kube-public` - Public cluster information
- `kube-node-lease` - Node heartbeat data
- `default` - Default namespace

## ✅ Security Checklist

### Docker Security
- [ ] Docker socket proxy is running (`docker ps | grep docker-proxy`)
- [ ] DOCKER_HOST points to proxy (`echo $DOCKER_HOST`)
- [ ] Mount validation is enabled (`echo $DOCKER_MOUNT_VALIDATION`)
- [ ] Privileged operations are blocked (try `docker run --privileged ubuntu`)
- [ ] System directory mounts are blocked (try `docker run -v /etc:/etc ubuntu`)
- [ ] Images pulled from trusted registries
- [ ] Review proxy logs for suspicious activity
- [ ] Read DOCKER_SECURITY.md for detailed information

### Kubernetes Security
- [ ] Kubeconfig is mounted read-only (cannot write to `~/.kube/config`)
- [ ] Production clusters are filtered out (verify with `kubectl config get-clusters`)
- [ ] Safety wrapper is active (test with `kubectl delete` command)
- [ ] Tools are pinned versions (check with `kubectl version --client`)
- [ ] Read KUBERNETES_SECURITY.md for detailed information
- [ ] Use separate kubeconfig contexts for dev work
- [ ] Never disable safety mode in production contexts

### Verify Production Filtering
```bash
# Should NOT show any production clusters
kubectl config get-clusters | grep -i production
# Exit code 1 means no production clusters found (good!)
```

## 🔧 Troubleshooting

### "Forbidden" error from Docker
✅ This is expected! The socket proxy blocks dangerous operations like --privileged.
This is a security feature and cannot be bypassed from the dev container.

### "MOUNT VALIDATION FAILED" error
✅ This is expected! Only /workspace paths can be mounted for security.
To bypass temporarily: `DOCKER_MOUNT_VALIDATION=off docker run -v /path:/path ubuntu`

### "Cannot connect to Docker daemon"
Check if socket proxy is running:
```bash
docker ps | grep docker-proxy
echo $DOCKER_HOST   # Should output "tcp://127.0.0.1:2375"

# Restart proxy if needed
docker-compose restart docker-socket-proxy
```

### "Read-only file system" when accessing kubeconfig
✅ This is expected! The kubeconfig is intentionally read-only for security.

### Safety wrapper not asking for confirmation
Check if KUBECTL_SAFE_MODE is enabled:
```bash
echo $KUBECTL_SAFE_MODE  # Should output "on"
alias kubectl            # Should point to wrapper script
```

### Need to bypass safety for automation
```bash
# Docker - use environment variable
DOCKER_SAFE_MODE=off docker run -v /path:/path myimage

# Or use real docker
/usr/bin/docker run -v /path:/path myimage

# Kubernetes - use environment variable
KUBECTL_SAFE_MODE=off kubectl apply -f manifests/

# Or use real kubectl
/usr/local/bin/kubectl apply -f manifests/
```

## 📚 Documentation

- Docker socket proxy guide: `.devcontainer/DOCKER_SECURITY.md`
- Kubernetes security guide: `.devcontainer/KUBERNETES_SECURITY.md`
- Dev container guide: `.devcontainer/README.md`
- Docker-compose configuration: `.devcontainer/docker-compose.yml`

## 🆘 Emergency Actions

### Suspected Compromise
```bash
# 1. Stop container immediately
docker stop cloudharness-dev

# 2. Check cluster for suspicious changes
kubectl get all --all-namespaces
kubectl get secrets --all-namespaces

# 3. Rotate credentials
# Contact cluster admin to regenerate certificates
```

### Accidental Destructive Operation
```bash
# If you have kubectl operations in shell history:
history | grep kubectl

# Check cluster audit logs (if enabled)
# Contact cluster admin for assistance
```

## 🔄 Current Tool Versions

| Tool | Version | Installed |
|------|---------|-----------|
| kubectl | v1.31.2 | ✅ |
| Helm | v3.16.2 | ✅ |
| Skaffold | v2.13.2 | ✅ |

**Note**: These versions are verified with SHA256 checksums during installation.

---

**Remember**: Security is a shared responsibility. Use these tools wisely and follow best practices.
