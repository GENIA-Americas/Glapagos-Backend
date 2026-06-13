# Glapagos Backend Architecture

## Overview

A modular Django backend for AI-enabled applications. Provides REST API scaffolding, background job execution, multi-tenant workspace management, and pluggable AI provider integration.

---

## Folder Structure

    Glapagos-Backend/
    api/                        # Django project root
        api/                    # API modules
            ai/                 # AI provider integration
            authentication/     # Login, signup, token management
            contacts/           # Contact management
            datasets/           # File and table dataset handling
            events/             # Event tracking
            health/             # Health check endpoint
            notebooks/          # Notebook management
            users/              # User management
            utils/              # Shared utilities
            workspaces/         # Multi-tenant workspace model
        apps/
            ai/
                clients/        # AI clients (OpenAI, Ollama)
        config/                 # Django settings and URL routing
        locale/                 # i18n translations
        static/                 # Static files
    ml/
        inference/              # ML inference modules
    compose/                    # Docker configurations
    docs/                       # Documentation
    requirements/               # Dependencies by environment
    local.yml                   # Docker Compose - development
    prod.yml                    # Docker Compose - production

---

## Key Components

### API Layer

53 registered endpoints across 9 modules, all under /api/v1/. URL routing is defined in api/config/urls.py and api/config/urls_health.py.

### Authentication

Token-based authentication via api/api/authentication/. Handles login, signup, and session management.

### Multi-tenant Workspaces

Organizations and workspaces with role-based access control. Users operate within a workspace context across all resource types.

### AI Provider Layer

Pluggable AI client architecture under apps/ai/clients/. Switch providers via environment variable - no code changes required.

| Provider | Config | Notes |
|---|---|---|
| OpenAI | AI_PROVIDER=openai | Requires OPENAI_API_KEY |
| Ollama | AI_PROVIDER=ollama | Local inference, no API key |

### Background Jobs

Celery workers with Redis as broker. Used for file uploads, notebook processing, and long-running AI workloads. Configured in local.yml and prod.yml.

### Health Monitoring

GET /health/ performs active checks against database, Redis, and Celery workers. Returns 200 when all services are healthy, 503 when any service is degraded.

---

## Data Layer

- PostgreSQL - primary database, 38 migrations
- Redis - Celery broker and channel layer cache
- File storage - Google Cloud Storage, S3, or local (configurable)

---

## Environment Configuration

| Variable | Purpose |
|---|---|
| AI_PROVIDER | Select AI backend (openai or ollama) |
| DATABASE_URL | PostgreSQL connection string |
| REDIS_URL | Redis connection string |
| DJANGO_SETTINGS_MODULE | Active settings file |
| APP_VERSION | Reported by /health/ |
