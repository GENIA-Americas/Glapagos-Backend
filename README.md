# Glápagos Backend

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

A modular, extensible Django-based backend designed to serve as the foundation
for AI-enabled applications built on the Glápagos platform.

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
```

## Environment Variables

To run this project, you will need to add the following environment variables. In a production environment like Railway, these can be configured via Railway services.

| Variable | Description | Example / Default |
|---|---|---|
| `SECRET_KEY` | Django secret key for cryptographic signing. | `your-secret-key-here` |
| `DEBUG` | Set to `True` for development, `False` for production. | `False` |
| `ALLOWED_HOSTS` | Comma-separated list of host/domain names that the Django site can serve. | `127.0.0.1,localhost,.railway.app` |
| `DATABASE_URL` | PostgreSQL connection string. | `postgres://user:pass@host:port/dbname` |
| `REDIS_URL` | Redis connection string for caching. | `redis://default:pass@host:port` |
| `CELERY_BROKER_URL` | URL for Celery message broker. | `redis://default:pass@host:port` |

**Note for Celery setup:** 
To deploy Celery workers alongside the web server, create a secondary service pointing to this repository and set its start command to: `cd api && celery -A config worker -l info`.
