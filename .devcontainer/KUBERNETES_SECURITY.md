# Kubernetes Security in Dev Container

This dev container includes Kubernetes tooling (kubectl, helm, skaffold) with security measures to protect against supply chain attacks and accidental cluster modifications.

## Security Measures

### 1. Tool Installation Security

All Kubernetes tools are installed with:
- **Pinned versions**: Specific versions are used (not "latest") to ensure reproducibility
- **Checksum verification**: SHA256 checksums are verified during installation to detect tampering
- **Official sources only**: Tools are downloaded directly from official repositories

Current versions:
- kubectl: v1.31.2
- Helm: v3.16.2
- Skaffold: v2.13.2

### 2. Read-Only Kubeconfig Mount

The host's `~/.kube` directory is mounted as **read-only** inside the container:
- Container cannot modify kubeconfig files
- Cannot add malicious clusters or contexts
- Cannot steal or exfiltrate credentials by modifying config

### 3. Production Cluster Filtering

Production clusters are automatically filtered out from the kubeconfig inside the container:
- **Blocked patterns**: `production`, `prod`, `mnp-cluster-production`
- Clusters, contexts, and users matching these patterns are removed
- Container cannot accidentally connect to production environments
- Filtering happens on container startup via `setup-docker-desktop-kube.sh`

### 4. Kubectl Safety Wrapper

A kubectl wrapper script provides safety checks for destructive operations:

#### Protected Operations
The following operations require confirmation:
- `delete`, `apply`, `create`, `replace`, `patch`, `edit`
- `drain`, `cordon`, `taint`, `label`, `annotate`
- `scale`, `rollout`, `set`

#### Critical Namespace Protection
Extra warnings are shown for operations on:
- `kube-system`, `kube-public`, `kube-node-lease`, `default`

#### Usage

The wrapper is enabled by default. To bypass (use with caution):
```bash
# Disable safety wrapper for a single command
KUBECTL_SAFE_MODE=off kubectl delete pod my-pod

# Use the real kubectl binary directly (not recommended)
/usr/local/bin/kubectl delete pod my-pod
```

To enable the wrapper in your shell, add to your `.bashrc`:
```bash
alias kubectl='/usr/local/share/dev-scripts/kubectl-wrapper.sh'
```

## Best Practices

### For Development
1. **Use separate contexts**: Create dev-specific kubeconfig contexts
2. **Limit permissions**: Use RBAC to limit what the dev context can do
3. **Read-only by default**: Use `kubectl get`, `describe`, `logs` for most tasks
4. **Test in safe namespaces**: Create dedicated development namespaces

### For CI/CD
1. **Use service accounts**: Don't share personal credentials with containers
2. **Principle of least privilege**: Grant only necessary permissions
3. **Audit logging**: Enable and monitor cluster audit logs
4. **Network policies**: Restrict container network access if possible

### Protecting Against Supply Chain Attacks

1. **Verify checksums**: When updating tool versions in Dockerfile, always:
   ```bash
   # Download and calculate checksum
   curl -LO https://dl.k8s.io/release/v1.31.2/bin/linux/amd64/kubectl
   sha256sum kubectl
   ```

2. **Review changes**: Always review Dockerfile changes that update tools

3. **Pin dependencies**: Never use `latest` tags or unpinned versions

4. **Scan images**: Run security scans on built images:
   ```bash
   docker scan cloudharness-dev:latest
   ```

## Emergency Response

If you suspect a compromised container:

1. **Stop the container immediately**
   ```bash
   docker stop cloudharness-dev
   ```

2. **Check cluster audit logs** for suspicious activity

3. **Rotate credentials**:
   ```bash
   # Regenerate kubeconfig
   kubectl config view --raw > ~/.kube/config.backup
   # Request new certificates from cluster admin
   ```

4. **Review cluster resources** for unauthorized changes:
   ```bash
   kubectl get all --all-namespaces
   kubectl get secrets --all-namespaces
   ```

## Configuration

### Environment Variables

- `KUBECONFIG`: Points to `/root/.kube/config` (read-only mount)
- `KUBECTL_SAFE_MODE`: Set to `off` to disable safety wrapper (not recommended)

### Disabling Kubernetes Access

To run the dev container without Kubernetes access:

1. Comment out the kubeconfig mount in `.devcontainer/devcontainer.json`:
   ```jsonc
   // "source=${localEnv:HOME}${localEnv:USERPROFILE}/.kube,target=/root/.kube,type=bind,readonly",
   ```

2. Remove KUBECONFIG environment variable

3. Rebuild the container

## Updating Tool Versions

To update kubectl, helm, or skaffold versions:

1. Find the latest stable version from official sources
2. Download and calculate SHA256 checksum
3. Update version and checksum in `Dockerfile`
4. Test the build before committing
5. Document the update in your commit message

Example:
```bash
# For kubectl
KUBECTL_VERSION="v1.32.0"
curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl"
sha256sum kubectl

# Update Dockerfile with new version and checksum
```

## Additional Resources

- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)
- [Supply Chain Security](https://slsa.dev/)
- [Docker Security](https://docs.docker.com/engine/security/)
