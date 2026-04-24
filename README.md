# Glápagos Backend

> A modular Django backend built for the AI era — production-ready, Dockerized, and wired for intelligent workloads from day one.

![production-ready](https://img.shields.io/badge/status-production--ready-00d9a3?style=flat-square)
![Django](https://img.shields.io/badge/Django-4.x-092E20?style=flat-square&logo=django)
![Celery](https://img.shields.io/badge/Celery%20%2B%20Redis-async-blue?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-first-2496ED?style=flat-square&logo=docker)
![License](https://img.shields.io/badge/license-MIT-gray?style=flat-square)

---

## What's inside

| Feature | Description |
|---|---|
| 🏗 **Battle-tested Architecture** | Opinionated, modular Django structure that scales from prototype to production |
| 🐳 **Zero-friction Deploy** | Composable Docker templates for dev, staging, and prod environments |
| ⚡ **Async Job Engine** | Background task execution via Celery + Redis — run ML inference without blocking |
| 🤖 **AI-native Integrations** | Optional hooks for LLMs, vector stores, and ML pipelines — plug in what you need |
| 🔌 **REST Scaffolding** | Pre-wired API layer with auth, pagination, and serializer patterns ready to extend |
| ⚙️ **Environment-aware Config** | `.env`-driven config with distinct profiles for every deployment stage |

---

## Quickstart

### 1. Clone the repository

```bash
git clone https://github.com/GENIA-Americas/Glapagos-Backend.git
cd Glapagos-Backend
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your secrets
```

### 3. Spin up all services

```bash
docker compose up --build
```

### 4. Apply migrations and create a superuser

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

> **Your API is live at** `http://localhost:8000/api/`  
> **Django admin at** `http://localhost:8000/admin/`

---

## Stack

### Backend
- [Django 4.x](https://www.djangoproject.com/) — web framework
- [Django REST Framework](https://www.django-rest-framework.org/) — API layer
- [PostgreSQL](https://www.postgresql.org/) — primary database
- [Celery](https://docs.celeryq.dev/) — distributed task queue
- [Redis](https://redis.io/) — message broker + cache

### Infrastructure
- [Docker Compose](https://docs.docker.com/compose/) — multi-service orchestration
- [Nginx](https://nginx.org/) — reverse proxy
- [Gunicorn](https://gunicorn.org/) — WSGI server
- [GitHub Actions](https://github.com/features/actions) — CI/CD pipelines

### AI / ML (optional)
- OpenAI / Anthropic SDKs — LLM integrations
- Vector store hooks — for retrieval-augmented generation
- Async inference via Celery — keep your API fast while models run in the background

---

## Project layout

```
Glapagos-Backend/
├── apps/           # Domain modules (users, api, tasks…)
├── config/         # Settings split by environment
├── docker/         # Compose files + Dockerfiles
├── scripts/        # Dev utilities + CI helpers
├── .env.example    # Env var template
└── manage.py
```

---

## Environment configuration

The project uses a split-settings pattern. Set `DJANGO_SETTINGS_MODULE` to target the right profile:

| Value | Use case |
|---|---|
| `config.settings.development` | Local development with debug tools |
| `config.settings.staging` | Pre-production testing |
| `config.settings.production` | Live deployment with hardened settings |

Copy `.env.example` to `.env` and fill in your values before running any environment.

---

## Running background workers

Celery workers and the beat scheduler run as separate Docker services. They start automatically with `docker compose up`. To run them manually:

```bash
# Worker
docker compose exec celery celery -A config worker --loglevel=info

# Beat scheduler (for periodic tasks)
docker compose exec celery celery -A config beat --loglevel=info
```

---

## Running tests

```bash
docker compose exec web python manage.py test
```

---

## Contributing

PRs are welcome. For major changes, please open an issue first to discuss what you'd like to change.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a pull request

---

## License

[MIT](LICENSE) © [GENIA Americas](https://github.com/GENIA-Americas)

---

<p align="center">If this project helped you, consider giving it a ⭐ — it helps others find it.</p> 🦎 
