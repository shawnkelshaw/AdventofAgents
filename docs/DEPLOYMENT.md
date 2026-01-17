# Deployment Considerations

This document outlines production considerations for deploying the AdventofAgents multi-agent system. The current implementation is designed for **local development and demonstrations**.

---

## Current State (Development)

| Feature | Status | Notes |
|---------|--------|-------|
| CORS | `allow_origins=["*"]` | Accepts all origins |
| Authentication | None | No auth required |
| Rate Limiting | None | No request throttling |
| Session Storage | In-memory | Lost on restart |
| Health Checks | None | No `/health` endpoint |
| Logging | Basic | Console output only |

---

## Production Requirements

### 1. CORS Configuration

**Risk:** Cross-site request forgery, unauthorized API access

```python
# server.py - Replace allow_origins=["*"] with:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-production-domain.com",
        "https://your-app.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
```

---

### 2. Authentication

**Risk:** Unauthorized access to LLM-powered endpoints (cost, abuse)

**Options:**
- API Key authentication (simple)
- OAuth2/OpenID Connect (enterprise)
- JWT tokens (stateless)

```python
# Example: API key middleware
from starlette.middleware import Middleware
from starlette.responses import JSONResponse

@app.middleware("http")
async def auth_middleware(request, call_next):
    api_key = request.headers.get("X-API-Key")
    if api_key != os.getenv("API_KEY"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return await call_next(request)
```

---

### 3. Rate Limiting

**Risk:** DoS attacks, excessive LLM API costs

```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.route("/")
@limiter.limit("10/minute")
async def homepage(request):
    ...
```

---

### 4. Persistent Session Storage

**Risk:** State loss on server restart, no horizontal scaling

**Options:**
- Redis (recommended for production)
- PostgreSQL
- DynamoDB

```python
# Replace InMemoryTaskStore with Redis-backed store
from a2a.server.tasks import RedisTaskStore

task_store = RedisTaskStore(redis_url=os.getenv("REDIS_URL"))
```

---

### 5. Health Checks

**Required for:** Kubernetes, load balancers, monitoring

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.9"}
```

---

### 6. Structured Logging

**Options:** structlog, python-json-logger

```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
```

---

## Deployment Checklist

- [ ] Set environment-specific CORS origins
- [ ] Add API key or OAuth authentication
- [ ] Configure rate limiting (10-50 req/min for LLM endpoints)
- [ ] Set up Redis for session persistence
- [ ] Add health check endpoint
- [ ] Configure structured logging
- [ ] Set up monitoring (Datadog, New Relic, etc.)
- [ ] Use HTTPS (TLS termination at load balancer)
- [ ] Set resource limits for containers
- [ ] Configure autoscaling policies

---

## Quick Start for Production

```bash
# Environment variables
export GOOGLE_API_KEY="..."
export API_KEY="your-secret-api-key"
export REDIS_URL="redis://localhost:6379"
export CORS_ORIGINS="https://your-app.com"

# Run with gunicorn for production
pip install gunicorn
gunicorn server:create_app() -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:10010
```

---

**Last Updated:** January 17, 2026
