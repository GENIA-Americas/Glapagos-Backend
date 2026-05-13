# Glápagos Backend

A modular, extensible Django-based backend designed to serve as the foundation
for AI-enabled applications built on the Glápagos platform.
## The AI Corridor of the Americas

Glápagos is the open-source backbone of the **AI Corridor of the Americas** — 
a collaborative AI development platform built specifically for the regulatory, 
linguistic, and market realities of the Western Hemisphere.

**[→ Read the Corridor Report](https://www.glapagos.com/resources)** · 
**[→ Platform & Vision](https://www.glapagos.com)** · 
**[→ Join the Discussion](https://github.com/GENIA-Americas/Glapagos-Backend/discussions)**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/GENIA-Americas/Glapagos-Backend)

---

## AI Integrations

| Provider | Config | Use case |
|---|---|---|
| OpenAI | `AI_PROVIDER=openai` | Cloud inference |
| Ollama | `AI_PROVIDER=ollama` | Local inference, no API key, data-sensitive deployments |

---

## Languages / Idiomas

- [English README](README.md) (you are here)
- [README en Español](README.es.md)

---
This repository provides:
- A production-ready Django architecture
- Dockerized deployment templates
- API scaffolding
- Background job execution via Celery + Redis
- Environment-based configuration for dev/staging/prod
- Optional integrations for AI/ML services

---

## Quickstart

### 1. Clone the repository
```bash
git clone https://github.com/GENIA-Americas/Glapagos-Backend.git
cd Glapagos-Backend
