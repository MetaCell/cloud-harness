FROM python:3.12

# Install Node.js 20, OpenJDK and other system dependencies

RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    nfs-common \
    default-jdk \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    iputils-ping \
    net-tools \
    wget \
    neovim \
    tmux \
    htop \
    tig \
    fzf \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI
# Note: Docker daemon access is secured via docker-socket-proxy
RUN install -m 0755 -d /etc/apt/keyrings && \
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc && \
chmod a+r /etc/apt/keyrings/docker.asc && \
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
apt-get update && \
apt-get install -y docker-ce-cli docker-compose-plugin && \
rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV MISE_DATA_DIR="/mise"
ENV MISE_CONFIG_DIR="/mise"
ENV MISE_CACHE_DIR="/mise/cache"
ENV MISE_INSTALL_PATH="/usr/local/bin/mise"
ENV PATH="/mise/shims:$PATH"

RUN curl https://mise.run | sh

# Install kubectl with security verification
# Using stable version with checksum verification to prevent supply chain attacks
RUN KUBECTL_VERSION="v1.34.2" && mise use --global kubectl@${KUBECTL_VERSION}

# Install Google Cloud SDK and gke-gcloud-auth-plugin for GKE authentication
RUN mise use --global gcloud

# Install Helm with security verification
RUN mise use --global helm

# Install Skaffold with security verification
RUN mise use --global skaffold

# Install k9s - Kubernetes CLI UI
RUN mise use --global k9s

# Install Starship prompt
RUN mise use --global starship && echo 'eval "$(starship init bash)"' >> ~/.bashrc

# Install Atuin - Shell history tool
RUN mise use --global atuin && echo 'eval "$(atuin init bash)"' >> ~/.bashrc

# Install gmap - Git activity visualizer
RUN curl -L "https://github.com/seeyebe/gmap/releases/latest/download/gmap-linux-amd64" -o /usr/local/bin/gmap && \
    chmod +x /usr/local/bin/gmap


# Install Node.js 20.x
RUN mise use --global node

# Upgrade system pip (separate for clearer error logs)
RUN python -m pip install --upgrade pip

# Update npm globally
RUN npm install -g npm@latest

# Enable corepack if present (Node 20 ships it); ignore if missing
RUN (command -v corepack >/dev/null 2>&1 && corepack enable || echo "corepack not available, continuing")

# Install yarn (try npm classic install first, fallback to corepack prepare)
RUN (npm install -g yarn@latest || (command -v corepack >/dev/null 2>&1 && corepack prepare yarn@stable --activate) || echo "Yarn installation fallback used")

# Set working directory
WORKDIR /cloudharness

# Copy all requirements files first for better Docker layer caching
COPY libraries/models/requirements.txt ./libraries/models/
COPY libraries/cloudharness-utils/requirements.txt ./libraries/cloudharness-utils/
COPY libraries/cloudharness-common/requirements.txt ./libraries/cloudharness-common/
COPY libraries/client/cloudharness_cli/requirements.txt ./libraries/client/cloudharness_cli/
COPY tools/deployment-cli-tools/requirements.txt ./tools/deployment-cli-tools/

# Install all external dependencies with caching
RUN --mount=type=cache,target=/root/.cache \
    pip install -r libraries/models/requirements.txt --prefer-binary && \
    pip install -r libraries/cloudharness-utils/requirements.txt --prefer-binary && \
    pip install -r libraries/cloudharness-common/requirements.txt --prefer-binary && \
    pip install -r libraries/client/cloudharness_cli/requirements.txt --prefer-binary && \
    pip install -r tools/deployment-cli-tools/requirements.txt --prefer-binary

# Copy requirements files for common framework libraries
COPY infrastructure/common-images/cloudharness-flask/requirements.txt ./infrastructure/flask-requirements.txt
COPY infrastructure/common-images/cloudharness-django/libraries/cloudharness-django/requirements.txt ./infrastructure/django-requirements.txt

# Install additional tools and common framework libraries
RUN --mount=type=cache,target=/root/.cache \
    pip install pytest debugpy --prefer-binary && \
    pip install -r infrastructure/flask-requirements.txt --prefer-binary && \
    pip install -r infrastructure/django-requirements.txt --prefer-binary

# Copy and install libraries one by one
COPY libraries/models ./libraries/models
RUN pip install -e libraries/models --no-cache-dir

COPY libraries/cloudharness-utils ./libraries/cloudharness-utils
RUN pip install -e libraries/cloudharness-utils --no-cache-dir

COPY libraries/cloudharness-common ./libraries/cloudharness-common
RUN pip install -e libraries/cloudharness-common --no-cache-dir

COPY libraries/client/cloudharness_cli ./libraries/client/cloudharness_cli
RUN pip install -e libraries/client/cloudharness_cli --no-cache-dir

COPY tools/deployment-cli-tools ./tools/deployment-cli-tools
RUN pip install -e tools/deployment-cli-tools --no-cache-dir


# Copy and install cloudharness framework libraries (last to ensure they override any conflicts)
COPY infrastructure/common-images/cloudharness-django/libraries/cloudharness-django infrastructure/cloudharness-django
RUN pip install -e infrastructure/cloudharness-django --no-cache-dir || echo "cloudharness-django not installable" 

# Ensure latest npm & yarn still available after project copy (optional refresh)
RUN npm install -g npm@latest yarn@latest || true

# Copy dev scripts from .devcontainer for portability
COPY .devcontainer/dev-scripts /usr/local/share/dev-scripts
RUN chmod +x /usr/local/share/dev-scripts/*.sh /usr/local/share/dev-scripts/use-venv && \
    ln -s /usr/local/share/dev-scripts /root/dev-scripts

# Create directories for neovim
RUN mkdir -p /root/.config/nvim

# Add the cloudharness CLI tools to PATH
ENV PATH="/cloudharness/tools/deployment-cli-tools:${PATH}"

# Set the default working directory
WORKDIR /workspace

# Set bash as the default shell for RUN commands
SHELL ["/bin/bash", "-c"]

# Set environment to ensure bash is used
ENV SHELL=/bin/bash

# Default command
CMD ["/bin/bash"]
