# Development Scripts

This directory contains scripts to help with the CloudHarness development environment.

## Runtime Virtual Environment

The CloudHarness development container comes with all CloudHarness libraries and common dependencies pre-installed globally. However, if you need to install additional packages for development or testing, you should use the runtime virtual environment to avoid conflicts.

## VS Code Integration

When using VS Code with dev containers, the virtual environment is automatically configured:

- The Python interpreter is set to `/root/.local/venv/bin/python`
- New terminals automatically activate the virtual environment
- The Python analysis paths include both the virtual environment and CloudHarness libraries
- All Python extensions work seamlessly with the virtual environment

### Usage

1. **Set up and activate the runtime virtual environment:**
   ```bash
   /usr/local/share/dev-scripts/runtime-venv.sh
   ```

2. **Activate an existing runtime virtual environment:**
   ```bash
   source /usr/local/share/dev-scripts/use-venv
   ```

3. **VS Code setup (automatically runs in dev container):**
   ```bash
   /usr/local/share/dev-scripts/vscode-setup.sh
   ```

4. **Install additional packages (while venv is active):**
   ```bash
   pip install <package-name>
   ```

5. **Deactivate the virtual environment:**
   ```bash
   deactivate
   ```

### How it works

- The runtime virtual environment is created in `$HOME/.local/venv` inside the container
- This location is persisted if you mount a home directory volume
- Global CloudHarness libraries remain accessible due to the PYTHONPATH configuration
- Additional packages installed in the virtual environment take precedence when there are conflicts
- The virtual environment inherits from the global site-packages, so you still have access to all pre-installed libraries
- VS Code dev container automatically configures the Python interpreter and analysis paths

### Best Practices

- Use the runtime virtual environment for experimental packages or project-specific dependencies
- Keep the global environment clean by not installing additional packages directly with pip outside the venv
- Document any additional dependencies in your project's requirements.txt file
- The virtual environment is automatically activated in new VS Code terminals when using dev containers
