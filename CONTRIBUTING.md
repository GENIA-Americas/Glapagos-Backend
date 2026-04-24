Thank you for considering a contribution to Glápagos Backend. This project is built and maintained by the team at GENIA Americas and open to contributions from the community.

Before you start
For small fixes (typos, documentation, minor bugs) — just open a PR directly.
For larger changes (new integrations, architectural changes, new features) — please open an issue first so we can discuss direction together. This saves everyone time.

Getting your environment running
bashgit clone https://github.com/GENIA-Americas/Glapagos-Backend.git
cd Glapagos-Backend
cp .env.example .env
docker compose up --build
Run the test suite:
bashdocker compose exec web python manage.py test

Contribution workflow

Fork the repository
Create a feature branch: git checkout -b feature/your-feature-name
Make your changes
Run the tests and make sure nothing is broken
Commit with a clear message: git commit -m 'Add: brief description'
Push your branch: git push origin feature/your-feature-name
Open a pull request against main


Commit message conventions
Use a short prefix to categorize your commit:
PrefixWhen to useAdd:New feature or fileFix:Bug fixUpdate:Change to existing functionalityRemove:Deleting somethingDocs:Documentation onlyRefactor:Code change that doesn't affect behavior

Code style

Follow PEP 8 for Python
Run black . before committing (we use Black for formatting)
Keep functions focused — if it does more than one thing, split it


What we're looking for
See the open issues for current priorities. Issues tagged good first issue are explicitly set aside for new contributors.
Areas where contributions are especially welcome:

Additional AI provider integrations (Anthropic, Cohere, Mistral, local/Ollama)
WebSocket support for streaming LLM responses
Deployment guides (Railway, Render, Fly.io, GCP Cloud Run)
Internationalization and multilingual support
Performance improvements and benchmarks
Test coverage improvements


Questions?
Open a GitHub Discussion or reach out at admin@genia.ai

GOOD FIRST ISSUES (paste these directly into GitHub Issues)

Issue #1
Title: Add Ollama integration for local LLM inference
Labels: good first issue, enhancement, ai
Body:
We'd like to add an optional integration for Ollama so users can run local LLMs without an external API key. This should follow the same pattern as the existing OpenAI hook — a thin wrapper in apps/ai/ that can be dropped in via env var configuration.
Acceptance criteria:

 OllamaClient class in apps/ai/clients/
 Environment variable: AI_PROVIDER=ollama + OLLAMA_BASE_URL
 Basic test coverage
 Documentation in README under AI integrations


Issue #2
Title: Add Railway one-click deploy button to README
Labels: good first issue, documentation
Body:
Railway supports one-click deploy buttons via a railway.json config file. Adding this would lower the barrier for new users to try the project instantly.
Acceptance criteria:

 railway.json config at repo root
 Deploy button added to README
 Environment variable mapping documented


Issue #3
Title: Write a deployment guide for Fly.io
Labels: good first issue, documentation
Body:
We want a docs/deployment/fly.md guide that walks through deploying the full stack (Django + Celery + Redis) to Fly.io. Should cover secrets management, volume setup for PostgreSQL, and worker deployment.

Issue #4
Title: Add health check endpoint
Labels: good first issue, enhancement
Body:
Add a /health/ endpoint that returns the status of all connected services (database, Redis, Celery). Should return 200 with a JSON payload when healthy, 503 when any service is down.
json{
  "status": "healthy",
  "database": "ok",
  "redis": "ok",
  "celery": "ok"
}

Issue #5
Title: Add Spanish translation to README
Labels: good first issue, documentation, i18n
Body:
Given our focus on Latin America, we'd like a README.es.md — a full Spanish translation of the main README. Native Spanish speakers preferred to ensure natural phrasing.
