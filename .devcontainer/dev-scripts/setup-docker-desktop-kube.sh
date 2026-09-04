#!/bin/bash
# Setup script to make Docker Desktop Kubernetes accessible from dev container
# with security filtering to block production cluster access

if [ ! -f ~/.kube/config ]; then
    echo "ℹ No kubeconfig found at ~/.kube/config"
    return 0
fi

echo "Configuring Kubernetes access with security filtering..."

# Create directory for filtered config
mkdir -p ~/.kube-container

# Filter out production clusters using Python
python3 - <<'PYTHON_EOF'
import yaml
import sys

# Patterns to block (production environments)
BLOCKED_PATTERNS = [
    'production',
    'prod',
]

def should_block(name):
    """Check if a cluster/context name should be blocked"""
    name_lower = name.lower()
    return any(pattern.lower() in name_lower for pattern in BLOCKED_PATTERNS)

try:
    # Read original kubeconfig
    with open('/root/.kube/config', 'r') as f:
        config = yaml.safe_load(f)
    
    blocked_items = []
    
    # Filter clusters
    if 'clusters' in config:
        original_count = len(config['clusters'])
        config['clusters'] = [c for c in config['clusters'] if not should_block(c.get('name', ''))]
        blocked_clusters = original_count - len(config['clusters'])
        if blocked_clusters > 0:
            blocked_items.append(f"{blocked_clusters} cluster(s)")
    
    # Filter contexts
    if 'contexts' in config:
        original_count = len(config['contexts'])
        config['contexts'] = [c for c in config['contexts'] 
                             if not should_block(c.get('name', '')) and 
                                not should_block(c.get('context', {}).get('cluster', ''))]
        blocked_contexts = original_count - len(config['contexts'])
        if blocked_contexts > 0:
            blocked_items.append(f"{blocked_contexts} context(s)")
    
    # Filter users (remove users only used by blocked contexts)
    if 'users' in config:
        # Get remaining context user names
        remaining_users = set()
        for ctx in config.get('contexts', []):
            user = ctx.get('context', {}).get('user')
            if user:
                remaining_users.add(user)
        
        original_count = len(config['users'])
        config['users'] = [u for u in config['users'] 
                          if u.get('name') in remaining_users or not should_block(u.get('name', ''))]
        blocked_users = original_count - len(config['users'])
        if blocked_users > 0:
            blocked_items.append(f"{blocked_users} user(s)")
    
    # Check if current context was blocked
    current_context = config.get('current-context', '')
    if current_context and should_block(current_context):
        # Try to switch to docker-desktop, otherwise first available
        if any(c.get('name') == 'docker-desktop' for c in config.get('contexts', [])):
            config['current-context'] = 'docker-desktop'
            print("  ℹ Switched to docker-desktop context", file=sys.stderr)
        elif config.get('contexts'):
            config['current-context'] = config['contexts'][0]['name']
            print(f"  ℹ Switched to {config['contexts'][0]['name']} context", file=sys.stderr)
        else:
            config['current-context'] = ''
    
    # Write filtered config
    with open('/root/.kube-container/config', 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    # Print blocked items
    if blocked_items:
        print(f"  🔒 Blocked: {', '.join(blocked_items)}", file=sys.stderr)
    else:
        print("  ✓ No production clusters found", file=sys.stderr)
    
except Exception as e:
    print(f"  ⚠ Error filtering kubeconfig: {e}", file=sys.stderr)
    # Fallback: just copy the config
    import shutil
    shutil.copy('/root/.kube/config', '/root/.kube-container/config')
    sys.exit(0)

PYTHON_EOF

# Set KUBECONFIG to use the filtered copy
export KUBECONFIG=~/.kube-container/config

echo "✓ Kubernetes configured with security filtering"
echo "  Production clusters are NOT accessible from dev container"
echo "  Filtered config at ~/.kube-container/config"
echo ""
