# AlphaShield Dockerfile
# Multi-stage build for optimized production image

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM python:3.11-slim as production

WORKDIR /app

# Create non-root user for security
RUN groupadd --gid 1000 alphashield && \
    useradd --uid 1000 --gid alphashield --shell /bin/bash --create-home alphashield

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=alphashield:alphashield . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    ENVIRONMENT=production

# Switch to non-root user
USER alphashield

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import alphashield; print('OK')" || exit 1

# Default command (can be overridden)
CMD ["python", "-m", "alphashield"]

# =============================================================================
# Stage 3: Development
# =============================================================================
FROM production as development

USER root

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Switch back to non-root user
USER alphashield

ENV ENVIRONMENT=development

# Development command
CMD ["pytest", "tests/", "-v"]

# =============================================================================
# Stage 4: CI (for running tests in CI/CD)
# =============================================================================
FROM development as ci

USER root

# Install additional CI tools
RUN pip install --no-cache-dir \
    pytest-cov \
    coverage \
    ruff \
    black \
    mypy

USER alphashield

ENV ENVIRONMENT=ci

CMD ["pytest", "tests/", "--cov=alphashield", "--cov-report=xml", "-v"]
