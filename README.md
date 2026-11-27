# Glápagos Backend

A modular, extensible Django backend for AI-enabled applications on the Glápagos platform — the open-source backbone of the **AI Corridor of the Americas**, built for the regulatory, linguistic, and market realities of the Western Hemisphere.

**Platform:** [glapagos.com](https://www.glapagos.com) · **Corridor Report:** [glapagos.com/resources](https://www.glapagos.com/resources) · **Community:** [Discussions](https://github.com/GENIA-Americas/Glapagos-Backend/discussions)

---

## Hosted demo

A demo of an earlier build of this backend runs at `https://glapagos-backend.onrender.com` on a free Render instance. It is not a production deployment:

- The first request after a period of inactivity can take about a minute while the instance wakes.
- The demo has no persistent database. It uses a temporary SQLite file, so data can reset when the service restarts.
- The hosted build is older than `main`, so some paths differ.

| Endpoint | Path on the hosted demo | Notes |
|---|---|---|
| Health | `/health/` | `main` serves the health check at `/api/v1/health/` |
| Organizations | `/api/v1/organizations/` | Authentication required |
| Workspaces | `/api/v1/workspaces/` | Authentication required |

Availability is not tracked in this repository. The full list of endpoints for `main` is in [docs/api.md](docs/api.md).

---

## What's Included

- Django project structure with Docker, Celery, and CI
- Dockerized deployment templates
- API scaffolding
- Background jobs via Celery + Redis
- Environment-based config for dev/staging/prod
- Optional AI/ML service integrations

---

## AI Integrations

| Provider | Config | Use Case |
|---|---|---|
| OpenAI | `AI_PROVIDER=openai` | Cloud inference |
| Ollama | `AI_PROVIDER=ollama` | Local inference, no API key, data-sensitive deployments |

---

## Languages / Idiomas

- [English README](README.md) (you are here)
- [README en Español](README.es.md)

---

## Quickstart

### 1. Clone the repository

```bash
git clone https://github.com/GENIA-Americas/Glapagos-Backend.git
cd Glapagos-Backend
```
