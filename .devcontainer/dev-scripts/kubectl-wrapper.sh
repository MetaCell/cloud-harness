#!/bin/bash
# Kubectl wrapper with safety features to prevent accidental cluster modifications
# This wrapper adds confirmation prompts for destructive operations

# Define destructive operations that require confirmation
DESTRUCTIVE_OPERATIONS=(
    "delete"
    "apply"
    "create"
    "replace"
    "patch"
    "edit"
    "drain"
    "cordon"
    "taint"
    "label"
    "annotate"
    "scale"
    "rollout"
    "set"
)

# Define critical namespaces that should have extra protection
CRITICAL_NAMESPACES=(
    "kube-system"
    "kube-public"
    "kube-node-lease"
    "default"
)

# Function to check if operation is destructive
is_destructive() {
    local operation="$1"
    for op in "${DESTRUCTIVE_OPERATIONS[@]}"; do
        if [[ "$operation" == "$op" ]]; then
            return 0
        fi
    done
    return 1
}

# Function to check if namespace is critical
is_critical_namespace() {
    local namespace="$1"
    for ns in "${CRITICAL_NAMESPACES[@]}"; do
        if [[ "$namespace" == "$ns" ]]; then
            return 0
        fi
    done
    return 1
}

# Function to extract namespace from arguments
get_namespace() {
    local args=("$@")
    for i in "${!args[@]}"; do
        if [[ "${args[$i]}" == "-n" ]] || [[ "${args[$i]}" == "--namespace" ]]; then
            echo "${args[$((i+1))]}"
            return
        fi
    done
    echo "default"
}

# Skip safety checks if KUBECTL_SAFE_MODE is disabled
if [[ "${KUBECTL_SAFE_MODE}" == "off" ]]; then
    exec /usr/local/bin/kubectl "$@"
fi

# Check if this is a read-only operation
OPERATION="${1:-}"
if [[ -z "$OPERATION" ]] || ! is_destructive "$OPERATION"; then
    # Safe operation, execute directly
    exec /usr/local/bin/kubectl "$@"
fi

# Extract namespace
NAMESPACE=$(get_namespace "$@")

# Provide warning for destructive operations
echo "⚠️  WARNING: You are about to execute a potentially destructive kubectl operation:"
echo "   Operation: $OPERATION"
echo "   Namespace: $NAMESPACE"
echo "   Full command: kubectl $*"

# Extra warning for critical namespaces
if is_critical_namespace "$NAMESPACE"; then
    echo ""
    echo "🚨 CRITICAL NAMESPACE ALERT: '$NAMESPACE' is a system-critical namespace!"
fi

echo ""
echo "The kubeconfig is mounted read-only, but cluster resources can still be modified."
echo ""
read -p "Are you sure you want to proceed? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Operation cancelled."
    exit 1
fi

# Execute the actual kubectl command
exec /usr/local/bin/kubectl "$@"
