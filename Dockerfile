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
    vim \
    wget \
    && rm -rf /var/lib/apt/lists/*

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
COPY infrastructure/common-images/cloudharness-fastapi/libraries/fastapi/requirements.txt ./infrastructure/fastapi-requirements.txt
COPY infrastructure/common-images/cloudharness-flask/requirements.txt ./infrastructure/flask-requirements.txt

# Install additional tools and common framework libraries
RUN --mount=type=cache,target=/root/.cache \
    pip install pytest debugpy --prefer-binary && \
    pip install -r infrastructure/fastapi-requirements.txt --prefer-binary && \
    pip install -r infrastructure/flask-requirements.txt --prefer-binary

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

# Copy dev scripts for runtime virtual environment
COPY dev-scripts ./dev-scripts
RUN chmod +x ./dev-scripts/runtime-venv.sh ./dev-scripts/use-venv ./dev-scripts/vscode-setup.sh

# Add the cloudharness CLI tools to PATH
ENV PATH="/cloudharness/tools/deployment-cli-tools:${PATH}"

# Set the default working directory
WORKDIR /workspace

# Default command
CMD ["/bin/bash"]
