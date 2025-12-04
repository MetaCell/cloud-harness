#!/bin/bash

# Script to set up and activate a runtime virtual environment
# This allows users to install additional packages at runtime without affecting the global environment

VENV_DIR="$HOME/.local/venv"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating runtime virtual environment at $VENV_DIR..."
    python -m venv --system-site-packages "$VENV_DIR"
fi

# Activate the virtual environment
echo "Activating runtime virtual environment..."
source "$VENV_DIR/bin/activate"

# Ensure pip is up to date in the virtual environment
pip install --upgrade pip

echo "Runtime virtual environment is now active."
echo "You can install additional packages with 'pip install <package>'"
echo "To deactivate, run 'deactivate'"