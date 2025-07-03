# Slack MCP Server Dockerfile
# Multi-stage build for development and production

FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Development stage
FROM base AS development

# Copy project files
COPY . .

# Create virtual environment and install dependencies
RUN uv venv
RUN . .venv/bin/activate && uv sync

# Set environment variables for development
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command for development
CMD ["/bin/bash"]

# Production stage
FROM base AS production

# Copy only necessary files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Create virtual environment and install dependencies
RUN uv venv
RUN . .venv/bin/activate && uv sync --frozen

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash mcp
RUN chown -R mcp:mcp /app
USER mcp

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["uv", "run", "src/slack_mcp_server.py"]
