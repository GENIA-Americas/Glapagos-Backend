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
