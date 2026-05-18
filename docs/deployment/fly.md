# Deploying Glápagos Backend to Fly.io

This guide walks you through deploying the full Glápagos Backend stack (Django + Celery + Redis + PostgreSQL) to [Fly.io](https://fly.io).

---

## Prerequisites

- [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/) installed
- A Fly.io account (sign up at https://fly.io/app/sign-up)
- Basic familiarity with the Glápagos Backend project structure

---

## Architecture Overview

The deployment consists of four Fly.io machines:

| Service   | Purpose                         | Fly.io Resource   |
|-----------|---------------------------------|-------------------|
| Django    | API server (Gunicorn)           | Fly Machine       |
| Celery    | Background task worker          | Fly Machine       |
| Celery Beat | Periodic task scheduler       | Fly Machine       |
| Redis     | Message broker & cache          | Upstash Redis     |
| PostgreSQL| Primary database                | Fly Postgres      |

---

## Step 1: Install and Authenticate

```bash
# Install Fly CLI (macOS)
brew install flyctl

# Install Fly CLI (Linux)
curl -L https://fly.io/install.sh | sh

# Install Fly CLI (Windows)
pwsh -c "iwr https://fly.io/install.ps1 | iex"

# Log in to your Fly.io account
fly auth login
```

---

## Step 2: Create the Fly.io App

```bash
# Launch the app (do NOT deploy yet — we need to configure first)
fly launch --no-deploy

# When prompted:
# - Choose an app name (e.g., galapagos-backend)
# - Select a region closest to your users
# - Do NOT add a Postgres database yet (we'll do that separately)
# - Do NOT add a Redis database yet
```

This generates a `fly.toml` file. We'll customize it below.

---

## Step 3: Set Up PostgreSQL

Fly.io provides managed PostgreSQL via **Fly Postgres**:

```bash
# Create a Postgres cluster
fly postgres create

# When prompted:
# - Choose a name (e.g., galapagos-db)
# - Select the same region as your app
# - Choose a machine size (shared-cpu-1x is fine for development)
# - Set a strong password or generate one

# Attach the database to your app
fly postgres attach galapagos-db
```

This automatically sets the `DATABASE_URL` secret in your app. The Glápagos Backend uses individual `DB_*` environment variables, so we'll map them in the secrets step.

---

## Step 4: Set Up Redis

We recommend **Upstash Redis** for a serverless Redis compatible with Fly.io:

```bash
# Create a Redis instance
fly redis create

# When prompted:
# - Choose a name (e.g., galapagos-redis)
# - Select the same region as your app
# - Choose a plan (free tier available)

# Attach Redis to your app
fly redis attach galapagos-redis
```

This sets the `REDIS_URL` secret automatically.

---

## Step 5: Configure the `fly.toml`

Replace the generated `fly.toml` with the following configuration:

```toml
app = "galapagos-backend"
primary_region = "sjc"

[build]
  dockerfile = "compose/production/django/Dockerfile"

[env]
  PORT = "8000"
  DJANGO_SETTINGS_MODULE = "config.settings.production"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 0

[checks]
  [checks.alive]
    type = "http"
    port = 8000
    path = "/health/"
    interval = "30s"
    timeout = "5s"
    grace_period = "10s"

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

> **Note:** Replace `sjc` with the region you selected. See [Fly.io regions](https://fly.io/docs/reference/regions/) for available options.

---

## Step 6: Configure Secrets (Environment Variables)

Set all required environment variables as Fly.io secrets:

```bash
# Core Django settings
fly secrets set DJANGO_DEBUG=False
fly secrets set ENVIRONMENT=PRODUCTION
fly secrets set DJANGO_ADMIN_URL="your-secret-admin-url"
fly secrets set SECRET_KEY="your-secret-key-here"

# Database — map from the DATABASE_URL that Fly Postgres attached
# Fly Postgres sets DATABASE_URL automatically.
# We need to also set the individual DB_* variables that the app expects:
fly secrets set DB_ENGINE=django.db.backends.postgresql
fly secrets set DB_DATABASE="$(echo $DATABASE_URL | sed -n 's|.*://[^:]*:[^@]*@\([^:/]*\):\([0-9]*\)/\([^?]*\).*|\3|p')"
fly secrets set DB_USER="$(echo $DATABASE_URL | sed -n 's|.*://\([^:]*\):.*|\1|p')"
fly secrets set DB_PASSWORD="$(echo $DATABASE_URL | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')"
fly secrets set DB_HOST="$(echo $DATABASE_URL | sed -n 's|.*://[^:]*:[^@]*@\([^:/]*\):.*|\1|p')"
fly secrets set DB_PORT="$(echo $DATABASE_URL | sed -n 's|.*://[^:]*:[^@]*@[^:]*:\([0-9]*\)/.*|\1|p')"

# Redis — the Celery broker and channel layer
fly secrets set REDIS_CHANNEL_LAYER_HOST="$(echo $REDIS_URL | sed -n 's|redis://\([^:]*\):.*/.*|\1|p')"

# Celery
fly secrets set CELERY_BROKER_URL="$REDIS_URL"
fly secrets set CELERY_RESULT_BACKEND="$REDIS_URL"

# CORS — comma-separated list of allowed origins
fly secrets set CORS_ALLOWED_ORIGINS="https://your-frontend-domain.com"

# Sentry (optional)
fly secrets set SENTRY_DSN="https://your-sentry-dsn@sentry.io/project-id"

# Email
fly secrets set EMAIL_NO_REPLY="noreply@yourdomain.com"
```

> **Tip:** You can also use the Fly.io dashboard at https://fly.io/apps/<your-app>/secrets to set secrets via the web UI.

---

## Step 7: Deploy the Django API

```bash
fly deploy
```

On first deploy, Fly.io builds the Docker image from `compose/production/django/Dockerfile`, runs migrations, collects static files, and starts Gunicorn.

---

## Step 8: Run Database Migrations

The production `start` script runs migrations automatically on boot. However, if you need to run them manually:

```bash
fly ssh console --command "python manage.py migrate"
```

---

## Step 9: Create a Superuser

```bash
fly ssh console --command "python manage.py createsuperuser"
```

Follow the interactive prompts to set the username, email, and password.

---

## Step 10: Deploy the Celery Worker

Create a separate `fly.toml` for the Celery worker (e.g., `fly.worker.toml`):

```toml
app = "galapagos-backend-worker"
primary_region = "sjc"

[build]
  dockerfile = "compose/production/django/Dockerfile"

[env]
  PORT = "8000"
  DJANGO_SETTINGS_MODULE = "config.settings.production"

# No HTTP service needed for workers
[deploy]
  release_command = "python manage.py migrate"

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

Deploy the worker:

```bash
# Create the worker app (if not already created)
fly apps create galapagos-backend-worker

# Copy secrets from the main app
fly secrets set --app galapagos-backend-worker \
  DJANGO_DEBUG=False \
  ENVIRONMENT=PRODUCTION \
  SECRET_KEY="your-secret-key-here" \
  DB_ENGINE=django.db.backends.postgresql \
  DB_DATABASE="your-db-name" \
  DB_USER="your-db-user" \
  DB_PASSWORD="your-db-password" \
  DB_HOST="your-db-host" \
  DB_PORT="5432" \
  REDIS_CHANNEL_LAYER_HOST="your-redis-host" \
  CELERY_BROKER_URL="redis://your-redis-host:6379/0" \
  CELERY_RESULT_BACKEND="redis://your-redis-host:6379/0"

# Deploy with a Celery worker entrypoint
fly deploy --config fly.worker.toml --app galapagos-backend-worker
```

Then override the start command for the worker in the Fly.io dashboard or via:

```bash
fly machines list --app galapagos-backend-worker
# Note the machine ID, then:
fly machine update <machine-id> --app galapagos-backend-worker \
  --command "celery -A config.celery_app worker -l INFO"
```

---

## Step 11: Deploy Celery Beat

Similarly, create `fly.beat.toml`:

```toml
app = "galapagos-backend-beat"
primary_region = "sjc"

[build]
  dockerfile = "compose/production/django/Dockerfile"

[env]
  PORT = "8000"
  DJANGO_SETTINGS_MODULE = "config.settings.production"

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

Deploy and run with the beat entrypoint:

```bash
fly apps create galapagos-backend-beat

# Copy the same secrets as the worker
fly secrets set --app galapagos-backend-beat \
  DJANGO_DEBUG=False \
  ENVIRONMENT=PRODUCTION \
  SECRET_KEY="your-secret-key-here" \
  DB_ENGINE=django.db.backends.postgresql \
  DB_DATABASE="your-db-name" \
  DB_USER="your-db-user" \
  DB_PASSWORD="your-db-password" \
  DB_HOST="your-db-host" \
  DB_PORT="5432" \
  REDIS_CHANNEL_LAYER_HOST="your-redis-host" \
  CELERY_BROKER_URL="redis://your-redis-host:6379/0" \
  CELERY_RESULT_BACKEND="redis://your-redis-host:6379/0"

fly deploy --config fly.beat.toml --app galapagos-backend-beat

# Override the start command for beat
fly machines list --app galapagos-backend-beat
fly machine update <machine-id> --app galapagos-backend-beat \
  --command "celery -A config.celery_app beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler"
```

---

## Step 12: Persistent Volumes for PostgreSQL

Fly Postgres manages its own storage. However, if you need to attach a persistent volume for file uploads or other data:

```bash
# Create a volume
fly volumes create data --size 1

# Mount it in fly.toml
# [mounts]
#   source = "data"
#   destination = "/data"
```

> **Note:** For production media storage, this project uses **AWS S3** via `django-storages`. Configure the AWS secrets below instead of using local volumes for media files.

```bash
fly secrets set AWS_ACCESS_KEY_ID="your-access-key"
fly secrets set AWS_SECRET_ACCESS_KEY="your-secret-key"
fly secrets set AWS_STORAGE_BUCKET_NAME="your-bucket-name"
fly secrets set AWS_S3_REGION_NAME="us-east-2"
```

---

## Step 13: Verify the Deployment

```bash
# Check app status
fly status

# Check logs
fly logs

# Test the health endpoint
curl https://galapagos-backend.fly.dev/health/

# Open a shell to debug
fly ssh console
```

---

## Scaling

### Horizontal Scaling

```bash
# Scale the Django API to 2 machines
fly scale count 2

# Scale the Celery worker
fly scale count 2 --app galapagos-backend-worker
```

### Vertical Scaling

```bash
# Upgrade to a larger machine
fly scale vm shared-cpu-2x --memory 512

# For the worker
fly scale vm shared-cpu-2x --memory 512 --app galapagos-backend-worker
```

---

## Troubleshooting

### App won't start
```bash
# Check recent logs
fly logs --app galapagos-backend

# SSH into the machine
fly ssh console
```

### Database connection errors
```bash
# Verify the database is running
fly postgres status --app galapagos-db

# Check if DATABASE_URL is set
fly secrets list --app galapagos-backend
```

### Celery tasks not running
```bash
# Check worker logs
fly logs --app galapagos-backend-worker

# Verify Redis connectivity
fly ssh console --app galapagos-backend-worker --command "python -c \"import redis; r=redis.from_url('$REDIS_URL'); print(r.ping())\""
```

### Static files not serving
The production settings use **WhiteNoise** for static file serving. Ensure `collectstatic` runs during build:
```bash
fly ssh console --command "python manage.py collectstatic --noinput"
```

---

## Cost Estimate

For a small production deployment on Fly.io:

| Resource              | Plan         | Estimated Monthly Cost |
|-----------------------|--------------|------------------------|
| Django API (1x 256MB) | Shared CPU   | ~$1.94                 |
| Celery Worker (1x 256MB) | Shared CPU | ~$1.94               |
| Celery Beat (1x 256MB)   | Shared CPU | ~$1.94               |
| Fly Postgres          | Development  | ~$1.94                 |
| Upstash Redis         | Free tier    | $0                     |
| **Total**             |              | **~$7.76/month**       |

> Prices are approximate as of 2026. Check [Fly.io pricing](https://fly.io/docs/about/pricing/) for current rates.

---

## Further Reading

- [Fly.io Documentation](https://fly.io/docs/)
- [Fly Postgres Guide](https://fly.io/docs/postgres/)
- [Fly Machines](https://fly.io/docs/machines/)
- [Celery Deployment Guide](https://docs.celeryq.dev/en/stable/userguide/deployment.html)
