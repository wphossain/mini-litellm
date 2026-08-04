# =============================================================================
# Mini LiteLLM Gateway — Multi-stage Dockerfile
# Stage 1: Build React Dashboard (Node.js)
# Stage 2: Build Python dependencies (Python/Alpine)
# Stage 3: Runtime image (Python/Alpine) containing Gateway + Static Dashboard
# =============================================================================

# ---- Stage 1: Build Dashboard ----
FROM node:20-alpine AS dashboard-builder

WORKDIR /dashboard

COPY dashboard/package*.json ./
RUN npm ci --silent || npm install

COPY dashboard/ ./
RUN npm run build

# ---- Stage 2: Build Python Virtual Environment ----
FROM python:3.12-alpine AS python-builder

RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

WORKDIR /app

COPY requirements.txt .
RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- Stage 3: Runtime Image ----
FROM python:3.12-alpine

RUN apk add --no-cache libstdc++ ca-certificates

WORKDIR /app

# Copy Python virtual env
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy dashboard dist from Stage 1 into /app/dashboard/dist
COPY --from=dashboard-builder /dashboard/dist /app/dashboard/dist

# Copy Gateway code
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
