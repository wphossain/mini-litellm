# =============================================================================
# Mini LiteLLM Gateway — Dockerfile
# Multi-stage build: builder → runtime (Alpine for minimal footprint)
# =============================================================================

FROM python:3.12-alpine AS builder

# Build dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

WORKDIR /app

# Install dependencies into a virtual env
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- Runtime Stage ----
FROM python:3.12-alpine

# Runtime libs only
RUN apk add --no-cache libstdc++ ca-certificates

WORKDIR /app

# Copy virtual env from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY main.py .
COPY config.yaml .
COPY app/ ./app/

# Create non-root user
RUN addgroup -S gateway && adduser -S gateway -G gateway && \
    mkdir -p /app/logs && chown -R gateway:gateway /app

USER gateway

EXPOSE 4000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4000", "--log-level", "info"]
