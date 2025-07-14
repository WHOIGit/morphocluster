FROM nvidia/cuda:12.5.1-cudnn-devel-ubuntu22.04

WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3.10-venv \
    python3-pip \
    curl \
    supervisor \
    netcat-openbsd \
    rsync \
    openssh-server \
    nodejs \
    npm \
    build-essential \
    pkg-config \
    libhdf5-dev \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Setup SSH
RUN mkdir /var/run/sshd
RUN mkdir /root/.ssh && chmod 700 /root/.ssh

COPY docker/morphocluster/run.sh docker/wait-for ./
COPY docker/morphocluster/activate ./
COPY docker/morphocluster/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Make activate script executable
RUN chmod +x /code/activate

# Create Python virtual environment
RUN python3.10 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create pyproject.toml for uv
COPY pyproject.toml requirements.txt ./

# Install Python dependencies
RUN uv pip install -r requirements.txt

# Install the application
COPY versioneer.py setup.py setup.cfg MANIFEST.in README.rst ./
COPY tests ./tests
COPY morphocluster ./morphocluster
COPY migrations ./migrations
RUN pip install -e .

# Build frontend
RUN cd morphocluster/frontend && \
    echo Building frontend... && \
    echo NPM version: `npm --version` && \
    npm ci && \
    npm run build

COPY docker/morphocluster/config_docker.py morphocluster/

CMD ["/code/run.sh"]