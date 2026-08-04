# =============================================================================
# Mini LiteLLM Gateway — Production Dockerfile
# Stage 1: Build React Dashboard
# Stage 2: Runtime Image (Python 3.12 Alpine)
# =============================================================================

# ---- Stage 1: Build Dashboard ----
FROM node:20-alpine AS dashboard-builder

WORKDIR /dashboard-src

# Copy package files and install
COPY dashboard/package*.json ./
RUN npm install

# Copy source and build
COPY dashboard/ ./
RUN npm run build && ls -la /dashboard-src/dist

# ---- Stage 2: Python Runtime ----
FROM python:3.12-alpine

WORKDIR /app

# Install build deps for python, install requirements, then cleanup
COPY requirements.txt .
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del gcc musl-dev libffi-dev openssl-dev

# Copy compiled static dashboard files from Stage 1 into /app/dashboard/dist
COPY --from=dashboard-builder /dashboard-src/dist /app/dashboard/dist

# Verify the build directory was copied properly
RUN ls -la /app/dashboard/dist

# Copy Gateway python source
COPY main.py .
COPY config.yaml .
COPY app/ ./app/

# Non-root user
RUN addgroup -S gateway && adduser -S gateway -G gateway && \
    mkdir -p /app/logs && chown -R gateway:gateway /app

USER gateway

EXPOSE 4000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:4000/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4000", "--log-level", "info"]
