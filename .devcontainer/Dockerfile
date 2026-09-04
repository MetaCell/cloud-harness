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

# Install kubectl with security verification
# Using stable version with checksum verification to prevent supply chain attacks
RUN KUBECTL_VERSION="v1.34.2" && \
    curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" && \
    curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl.sha256" && \
    echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check || (echo "kubectl checksum verification failed" && exit 1) && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl kubectl.sha256 && \
    kubectl version --client

# Install Google Cloud SDK and gke-gcloud-auth-plugin for GKE authentication
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | \
    tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    apt-get update && \
    apt-get install -y google-cloud-cli google-cloud-sdk-gke-gcloud-auth-plugin && \
    rm -rf /var/lib/apt/lists/* && \
    gcloud version && \
    gke-gcloud-auth-plugin --version

# Install Helm with security verification
RUN HELM_VERSION="v4.0.0" && \
    HELM_CHECKSUM="c77e9e7c1cc96e066bd240d190d1beed9a6b08060b2043ef0862c4f865eca08f" && \
    curl -LO "https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz" && \
    echo "${HELM_CHECKSUM} helm-${HELM_VERSION}-linux-amd64.tar.gz" | sha256sum --check || (echo "Helm checksum verification failed" && exit 1) && \
    tar -zxvf helm-${HELM_VERSION}-linux-amd64.tar.gz && \
    mv linux-amd64/helm /usr/local/bin/helm && \
    rm -rf linux-amd64 helm-${HELM_VERSION}-linux-amd64.tar.gz && \
    helm version

# Install Skaffold with security verification
RUN SKAFFOLD_VERSION="v2.14.2" && \
    SKAFFOLD_CHECKSUM="2209463bafd0e021907c1efe72063d6b9ca3244a72b437a51aff061b0b97087a" && \
    curl -LO "https://storage.googleapis.com/skaffold/releases/${SKAFFOLD_VERSION}/skaffold-linux-amd64" && \
    echo "${SKAFFOLD_CHECKSUM} skaffold-linux-amd64" | sha256sum --check || (echo "Skaffold checksum verification failed" && exit 1) && \
    install -o root -g root -m 0755 skaffold-linux-amd64 /usr/local/bin/skaffold && \
    rm skaffold-linux-amd64 && \
    skaffold version

# Install k9s - Kubernetes CLI UI
RUN K9S_VERSION="v0.32.5" && \
    K9S_CHECKSUM="33c31bf5feba292b59b8dabe5547cb52ab565521ee5619b52eb4bd4bf226cea3" && \
    curl -LO "https://github.com/derailed/k9s/releases/download/${K9S_VERSION}/k9s_Linux_amd64.tar.gz" && \
    echo "${K9S_CHECKSUM} k9s_Linux_amd64.tar.gz" | sha256sum --check || (echo "k9s checksum verification failed" && exit 1) && \
    tar -xzf k9s_Linux_amd64.tar.gz k9s && \
    install -o root -g root -m 0755 k9s /usr/local/bin/k9s && \
    rm k9s_Linux_amd64.tar.gz k9s && \
    k9s version

# Install Starship prompt
RUN STARSHIP_VERSION="v1.20.1" && \
    curl -LO "https://github.com/starship/starship/releases/download/${STARSHIP_VERSION}/starship-x86_64-unknown-linux-gnu.tar.gz" && \
    tar -xzf starship-x86_64-unknown-linux-gnu.tar.gz && \
    install -o root -g root -m 0755 starship /usr/local/bin/starship && \
    rm starship-x86_64-unknown-linux-gnu.tar.gz starship && \
    starship --version

# Install Atuin - Shell history tool
RUN ATUIN_VERSION="v18.3.0" && \
    curl -LO "https://github.com/atuinsh/atuin/releases/download/${ATUIN_VERSION}/atuin-x86_64-unknown-linux-gnu.tar.gz" && \
    tar -xzf atuin-x86_64-unknown-linux-gnu.tar.gz && \
    install -o root -g root -m 0755 atuin-x86_64-unknown-linux-gnu/atuin /usr/local/bin/atuin && \
    rm -rf atuin-x86_64-unknown-linux-gnu.tar.gz atuin-x86_64-unknown-linux-gnu && \
    atuin --version

# Install gmap - Git activity visualizer
RUN curl -L "https://github.com/seeyebe/gmap/releases/latest/download/gmap-linux-amd64" -o /usr/local/bin/gmap && \
    chmod +x /usr/local/bin/gmap

# Install asdf version manager
RUN git clone https://github.com/asdf-vm/asdf.git /root/.asdf --branch v0.14.1

# Install bash-preexec (required for atuin history capture)
RUN curl -sL https://raw.githubusercontent.com/rcaloras/bash-preexec/master/bash-preexec.sh -o /root/.bash-preexec.sh

# Install Node.js 20.x

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

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
