# Smart Agent Wiki Docker Image
# Lightweight image for running SAW in containerized environments
#
# Usage:
#   docker build -t saw:latest .
#   docker run -it saw:latest saw init
#   docker run -v $(pwd)/wiki:/wiki saw:latest saw ingest /wiki/documents
#
# License: MIT

FROM python:3.11-slim-bookworm

# Metadata
LABEL maintainer="chensaics"
LABEL version="3.4.0"
LABEL description="Smart Agent Wiki - Intelligent Multi-Agent Knowledge Platform"
LABEL homepage="https://github.com/chensaics/smart_agent_wiki"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Smart Agent Wiki
RUN pip install smart-agent-wiki

# Create working directory
WORKDIR /wiki

# Expose ports
# 8000 - Web UI backend
# 3000 - Web UI frontend (if bundled)
EXPOSE 8000 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD saw --version || exit 1

# Set entrypoint
ENTRYPOINT ["saw"]
CMD ["--help"]
