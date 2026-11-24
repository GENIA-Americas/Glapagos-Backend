# Glápagos Backend

A modular, extensible Django backend for AI-enabled applications on the Glápagos platform — the open-source backbone of the **AI Corridor of the Americas**, built for the regulatory, linguistic, and market realities of the Western Hemisphere.

**Platform:** [glapagos.com](https://www.glapagos.com) · **Corridor Report:** [glapagos.com/resources](https://www.glapagos.com/resources) · **Community:** [Discussions](https://github.com/GENIA-Americas/Glapagos-Backend/discussions)

---

## Hosted instance

A deployment of this backend has run at `https://glapagos-backend.onrender.com`. Availability is not tracked in this repository, so check the hosting dashboard for current status.

| Endpoint | Path | Notes |
|---|---|---|
| Health | `/api/v1/health/` | Checks database, Redis, and Celery worker connectivity |
| Organizations | `/api/v1/organizations/` | Authentication required |
| Workspaces | `/api/v1/workspaces/` | Authentication required |

The full list of endpoints is in [docs/api.md](docs/api.md).

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
