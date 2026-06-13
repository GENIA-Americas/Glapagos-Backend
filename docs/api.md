# Glapagos Backend API

All endpoints are under /api/v1/ unless noted. All responses are JSON. Authentication is required except where noted.

Base URL (local): http://localhost:8000/api/v1/
Base URL (production): https://glapagos-backend.onrender.com/api/v1/

---

## Health

### GET /health/

No authentication required. Performs active checks against all connected services.

Response 200 - all services healthy:

    {
      "status": "healthy",
      "version": "1.0.0",
      "timestamp": "2026-06-13T14:30:00+00:00",
      "services": {
        "database": { "status": "ok", "latency_ms": 1.8, "error": null },
        "redis":    { "status": "ok", "latency_ms": 0.6, "error": null },
        "celery":   { "status": "ok", "workers": 2,      "error": null }
      }
    }

Response 503 - one or more services degraded:

    {
      "status": "degraded",
      "version": "1.0.0",
      "timestamp": "2026-06-13T14:30:00+00:00",
      "services": {
        "database": { "status": "error", "latency_ms": 5001.0, "error": "could not connect to server" },
        "redis":    { "status": "ok",    "latency_ms": 0.6,    "error": null },
        "celery":   { "status": "error", "workers": 0,         "error": "No Celery workers responded to ping" }
      }
    }

---

## Modules

| Module | Source |
|---|---|
| Authentication | api/api/authentication/urls.py |
| Users | api/api/users/urls.py |
| Workspaces | api/api/workspaces/urls.py |
| Datasets | api/api/datasets/urls.py |
| Notebooks | api/api/notebooks/urls.py |
| AI | api/api/ai/urls.py |
| Contacts | api/api/contacts/urls.py |
| Events | api/api/events/urls.py |

---

## Authentication

Token-based. Include the token in the request header:

    Authorization: Token <your-token>

---

## Error Responses

| Code | Meaning |
|---|---|
| 400 | Bad request - invalid input |
| 401 | Unauthorized - missing or invalid token |
| 403 | Forbidden - insufficient permissions |
| 404 | Not found |
| 503 | Service unavailable - health check degraded |
