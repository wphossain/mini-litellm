# Mini LiteLLM Gateway

Lightweight, production-ready, OpenAI-compatible AI Gateway using **LiteLLM SDK** (not the official Proxy).

Built for **Northflank Free**, **Render Free**, **Railway**, **Docker**, and **VPS** — all under **150MB idle RAM**.

---

## Features

- OpenAI-compatible API (`/v1/chat/completions`, `/v1/embeddings`, `/v1/images`, `/v1/audio/*`, `/v1/models`)
- Multi-provider support (OpenAI, Anthropic, Gemini, OpenRouter, Mistral, Groq, DeepSeek, Ollama, vLLM, and more)
- Model aliases (`gpt-5` → `openai/gpt-5`)
- API key rotation (round-robin, random, least-used, priority)
- Automatic provider fallback chain
- Retry with exponential backoff + jitter
- Load balancing (round-robin, random, weighted, priority, latency-based)
- Health checks with circuit breaker
- Rate limiting (token bucket)
- Admin REST API
- Works with LobeHub, Open WebUI, LibreChat, Cherry Studio, Cursor, VS Code, Claude Desktop

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/wphossain/mini-litellm.git
cd mini-litellm
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run

```bash
# Docker (recommended)
docker compose up -d

# Or directly with Python
pip install -r requirements.txt
python main.py
```

### 4. Use

```bash
curl http://localhost:4000/v1/models \
  -H "Authorization: Bearer sk-master-key-change-me"

curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-master-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Hello!"}]}'
```

---

## Configuration

Everything lives in `config.yaml`. Key sections:

| Section | Description |
|---------|-------------|
| `gateway` | Host, port, log level, streaming |
| `auth` | Master key, admin key, readonly key |
| `rate_limiting` | Token bucket config |
| `cors` | Allowed origins & methods |
| `model_aliases` | Friendly name → provider/model mapping |
| `providers` | All provider configs (API keys, priority, weights) |
| `fallback` | Provider failover chain |
| `health_check` | Health monitoring intervals & thresholds |
| `rotation` | API key rotation strategy |

Secrets use `${ENV_VAR}` syntax resolved from `.env` or OS environment.

---

## Supported Providers

| Provider | Type | Status |
|----------|------|--------|
| OpenAI | `openai` | Built-in |
| Anthropic | `anthropic` | Built-in |
| Google Gemini | `gemini` | Built-in |
| OpenRouter | `openrouter` | Built-in |
| Mistral AI | `mistral` | Built-in |
| Groq | `groq` | Built-in |
| DeepSeek | `deepseek` | Built-in |
| NVIDIA NIM | `openai_compatible` | Built-in |
| Azure OpenAI | `azure` | Built-in |
| Ollama | `ollama` | Built-in |
| LM Studio | `openai_compatible` | Built-in |
| vLLM | `openai_compatible` | Built-in |
| Any OpenAI-compatible | `openai_compatible` | Built-in |

---

## Deployment

### Docker Compose

```bash
docker compose up -d
```

### Render / Railway / Northflank

1. Push to GitHub
2. Connect the repo
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn main:app --host 0.0.0.0 --port ${PORT:-4000}`
5. Add environment variables from `.env.example`

### VPS (Ubuntu)

```bash
apt update && apt install -y python3.12 python3.12-venv
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env
uvicorn main:app --host 0.0.0.0 --port 4000
```

---

## Client Setup

### LobeHub / Open WebUI / LibreChat

Set OpenAI API Base URL to: `http://localhost:4000/v1`

### VS Code / Cursor / Continue / Claude Desktop / Roo Code

```json
{
  "provider": "openai",
  "apiBase": "http://localhost:4000/v1",
  "apiKey": "sk-master-key-change-me"
}
```

---

## Admin API

```bash
# List providers
curl http://localhost:4000/admin/providers -H "Authorization: Bearer sk-admin-master"

# Toggle provider
curl -X POST http://localhost:4000/admin/providers/toggle \
  -H "Authorization: Bearer sk-admin-master" \
  -H "Content-Type: application/json" \
  -d '{"provider_name":"gemini","enabled":false}'

# View logs
curl http://localhost:4000/admin/logs -H "Authorization: Bearer sk-admin-master"

# View stats
curl http://localhost:4000/admin/stats -H "Authorization: Bearer sk-admin-master"
```

---

## Architecture

```
Request → FastAPI → Auth → Rate Limit → Gateway Service
                                              │
                            ┌─────────────────┼──────────────────┐
                            ▼                  ▼                   ▼
                      Model Alias         Fallback Chain     Load Balancer
                            │                  │                   │
                            ▼                  ▼                   ▼
                      Provider Registry ── Key Rotation ── LiteLLM SDK
                            │
                            ▼
                      OpenAI / Anthropic / Gemini / etc.
```

---

## Comparison

| Feature | Official LiteLLM Proxy | Mini LiteLLM |
|---------|----------------------|-------------|
| Base memory | ~400MB+ | ~80–150MB |
| Database | PostgreSQL/Prisma | None (in-memory) |
| Redis | Required | Optional |
| Setup time | 5–10 minutes | 30 seconds |
| Free tier hosting | ❌ | ✅ |
| Provider plugins | ✅ | ✅ |
| OpenAI compatible | ✅ | ✅ |
| Admin Dashboard | ✅ | React SPA (WIP) |

---

## License

MIT
