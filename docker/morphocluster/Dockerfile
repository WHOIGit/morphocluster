FROM nvidia/cuda:12.6.1-cudnn-devel-ubuntu24.04

WORKDIR /code
USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-setuptools \
    python3-pip \
    curl \
    supervisor \
    netcat-openbsd \
    rsync \
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

COPY docker/morphocluster/run.sh docker/wait-for ./
COPY docker/morphocluster/activate ./
COPY docker/morphocluster/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Make activate script executable
RUN chmod +x /code/activate

# Copy project files for installation
COPY pyproject.toml uv.lock versioneer.py setup.cfg MANIFEST.in README.rst ./
COPY tests ./tests
COPY morphocluster ./morphocluster
COPY migrations ./migrations

# Install the application with dependencies from lockfile
RUN uv sync --frozen

# Set PATH to use uv's virtual environment
ENV PATH="/code/.venv/bin:$PATH"

# Build frontend
RUN cd morphocluster/frontend && \
    echo Building frontend... && \
    echo NPM version: `npm --version` && \
    npm install && \
    npm run build

COPY docker/morphocluster/config_docker.py morphocluster/

CMD ["/code/run.sh"]