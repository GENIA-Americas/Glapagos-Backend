# Glápagos Backend

A modular, extensible Django backend for AI-enabled applications on the Glápagos platform — the open-source backbone of the **AI Corridor of the Americas**, built for the regulatory, linguistic, and market realities of the Western Hemisphere.

**Platform:** [glapagos.com](https://www.glapagos.com) · **Corridor Report:** [glapagos.com/resources](https://www.glapagos.com/resources) · **Community:** [Discussions](https://github.com/GENIA-Americas/Glapagos-Backend/discussions)

---

## Live API

| Endpoint | URL | Auth |
|---|---|---|
| Health | [/health/](https://glapagos-backend.onrender.com/health/) | ![Live](https://img.shields.io/badge/API-Live-brightgreen) |
| Organizations | [/api/v1/organizations/](https://glapagos-backend.onrender.com/api/v1/organizations/) | Required |
| Workspaces | [/api/v1/workspaces/](https://glapagos-backend.onrender.com/api/v1/workspaces/) | Required |

---

## What's Included

- Production-ready Django architecture
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
