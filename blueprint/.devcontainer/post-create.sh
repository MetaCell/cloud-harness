#!/bin/bash
# Post-create setup script for Blueprint dev container
# This delegates to the main CloudHarness post-create script

set -e

echo "Setting up Blueprint development environment..."

# Run the main CloudHarness post-create script
# This handles all the common setup: bashrc, atuin, starship, tmux, k8s, docker, etc.
if [ -f /usr/local/share/dev-scripts/post-create.sh ]; then
    /usr/local/share/dev-scripts/post-create.sh
else
    echo "Warning: CloudHarness post-create.sh not found"
    exit 1
fi

# Add any blueprint-specific setup here if needed in the future
# For now, everything is handled by the main post-create script

echo ""
echo "✓ Blueprint development environment ready!"
echo ""
