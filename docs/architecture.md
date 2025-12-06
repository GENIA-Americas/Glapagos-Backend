# Glápagos Backend Architecture

## Overview
The Glápagos Backend is a modular Django-based backend designed to support AI-enabled applications.  
It provides API scaffolding, background job execution, Dockerized deployment, and optional AI/ML integrations.

## Folder Structure

Glapagos-Backend/
├── api/ # Django REST API endpoints
├── castroquiles/ # Core Django app
├── ml/ # AI/ML models and inference modules
│ └── inference/
├── compose/ # Docker Compose files
├── docs/ # Documentation
├── requirements.txt # Python dependencies
├── docker-build.sh # Docker build script
├── *.yml # Environment configurations
└── ...


## Features
- **Django architecture** for scalable API design
- **Celery + Redis** for background jobs
- **Environment-based configs** for dev/staging/prod
- **Dockerized deployment** for easy containerization
- **Optional ML/AI modules** under `ml/inference/`

## Usage
```bash
# Clone the repository
git clone https://github.com/GENIA-Americas/Glapagos-Backend.git
cd Glapagos-Backend

# Install dependencies
pip install -r requirements.txt

# Run Docker or local server
# e.g., docker-compose up
