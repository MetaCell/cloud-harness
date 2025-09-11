#!/bin/bash

# VS Code Python environment setup script
# This script ensures the virtual environment is properly set up for VS Code integration
echo "Running VS Code Python environment setup..."
VENV_DIR="$HOME/.local/venv"

# Create the virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment for VS Code..."
    /workspace/dev-scripts/runtime-venv.sh
fi

# Create a Python interpreter symlink that VS Code can reliably find
mkdir -p "$HOME/.local/bin"
ln -sf "$VENV_DIR/bin/python" "$HOME/.local/bin/python-venv"

# Ensure the virtual environment has necessary development packages
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel

echo "Python virtual environment ready for VS Code integration."
echo "Python interpreter: $VENV_DIR/bin/python"
