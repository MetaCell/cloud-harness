#!/bin/bash
# Docker mount validator for socket proxy setup
# This provides client-side validation of mount paths before API calls
# Use: alias docker='/usr/local/share/dev-scripts/docker-mount-validator.sh'

# Location of real docker binary
REAL_DOCKER="/usr/bin/docker"

# Define allowed mount paths (workspace only)
ALLOWED_MOUNT_PATHS=(
    "/workspace"
    "${WORKSPACE_ROOT:-/workspace}"
)

# Define blocked mount paths (everything else on host)
BLOCKED_MOUNT_PATHS=(
    "/"
    "/root"
    "/home"
    "/etc"
    "/usr"
    "/var"
    "/bin"
    "/sbin"
    "/boot"
    "/sys"
    "/proc"
    "/dev"
    "/opt"
    "/srv"
    "/mnt"
    "/media"
)

# Skip validation if disabled
if [[ "${DOCKER_MOUNT_VALIDATION}" == "off" ]]; then
    exec "$REAL_DOCKER" "$@"
fi

# Only validate 'run' and 'create' commands
OPERATION="${1:-}"
if [[ "$OPERATION" != "run" ]] && [[ "$OPERATION" != "create" ]]; then
    exec "$REAL_DOCKER" "$@"
fi

# Function to check mount path safety
check_mount_path() {
    local source_path="$1"
    
    # Skip if it's a named volume (no leading /)
    if [[ "$source_path" != /* ]]; then
        return 0
    fi
    
    # Check if it's in blocked paths
    for blocked in "${BLOCKED_MOUNT_PATHS[@]}"; do
        if [[ "$source_path" == "$blocked" ]] || [[ "$source_path" == "$blocked"/* ]]; then
            # Check if it's within an allowed subpath
            local is_allowed=false
            for allowed in "${ALLOWED_MOUNT_PATHS[@]}"; do
                if [[ "$source_path" == "$allowed"* ]]; then
                    is_allowed=true
                    break
                fi
            done
            
            if [[ "$is_allowed" == false ]]; then
                echo "❌ MOUNT VALIDATION FAILED:"
                echo "   Attempting to mount: $source_path"
                echo "   Only /workspace paths are allowed for security."
                echo ""
                echo "To bypass this check (NOT RECOMMENDED):"
                echo "   DOCKER_MOUNT_VALIDATION=off docker $*"
                return 1
            fi
        fi
    done
    
    # Check if it's explicitly allowed
    local is_allowed=false
    for allowed in "${ALLOWED_MOUNT_PATHS[@]}"; do
        if [[ "$source_path" == "$allowed"* ]]; then
            is_allowed=true
            break
        fi
    done
    
    if [[ "$is_allowed" == false ]]; then
        echo "❌ MOUNT VALIDATION FAILED:"
        echo "   Attempting to mount: $source_path"
        echo "   Only /workspace paths are allowed for security."
        echo ""
        echo "To bypass this check (NOT RECOMMENDED):"
        echo "   DOCKER_MOUNT_VALIDATION=off docker $*"
        return 1
    fi
    
    return 0
}

# Parse arguments to find mounts
args=("$@")
for i in "${!args[@]}"; do
    arg="${args[$i]}"
    
    # Check -v and --volume flags
    if [[ "$arg" == "-v" ]] || [[ "$arg" == "--volume" ]]; then
        mount_spec="${args[$((i+1))]}"
        source_path="${mount_spec%%:*}"
        
        if ! check_mount_path "$source_path"; then
            exit 1
        fi
    fi
    
    # Check --mount flag
    if [[ "$arg" == "--mount" ]]; then
        mount_spec="${args[$((i+1))]}"
        if [[ "$mount_spec" =~ source=([^,]+) ]]; then
            source_path="${BASH_REMATCH[1]}"
            
            if ! check_mount_path "$source_path"; then
                exit 1
            fi
        fi
    fi
done

# All checks passed, execute docker command
exec "$REAL_DOCKER" "$@"
