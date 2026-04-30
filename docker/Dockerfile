# Smart Agent Wiki - Dockerfile
# Phase 5: Team Deployment

FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml requirements.txt* ./
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -e . || pip install --no-cache-dir \
    fastapi>=0.115.0 \
    uvicorn[standard]>=0.30.0 \
    sqlalchemy>=2.0.0 \
    asyncpg>=0.29.0 \
    aiosqlite>=0.20.0 \
    alembic>=1.13.0 \
    pyjwt>=2.10.0 \
    bcrypt>=4.2.0 \
    redis>=5.0.0 \
    python-multipart>=0.0.9 \
    httpx>=0.27.0 \
    typer>=0.12.0 \
    rich>=13.0.0 \
    faster-whisper>=1.0.0 \
    cryptography>=44.0.0

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application
COPY src/ ./src/
COPY pyproject.toml ./

# Create data directories
RUN mkdir -p /app/data/vaults /app/data/backups

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DATABASE_URL=postgresql://saw:saw@db:5432/saw
ENV REDIS_URL=redis://redis:6379/0

# Health check endpoint port
EXPOSE 8000

# Run application
CMD ["uvicorn", "saw.drivers.web.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]