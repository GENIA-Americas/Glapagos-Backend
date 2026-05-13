# Glápagos Backend

Un backend modular y extensible basado en Django, diseñado como la base
para aplicaciones habilitadas con IA construidas sobre la plataforma Glápagos.

Este repositorio incluye:

* Una arquitectura Django lista para producción
* Plantillas de despliegue con Docker
* Estructura de API lista para usar
* Ejecución de tareas en segundo plano con Celery + Redis
* Configuración por entornos: desarrollo / staging / producción
* Integraciones opcionales para servicios de IA/ML

---

## Inicio Rápido

### 1. Clonar el repositorio

```bash
git clone https://github.com/GENIA-Americas/Glapagos-Backend.git
cd Glapagos-Backend
```

### 2. Configurar variables de entorno

Copia el archivo de ejemplo y edítalo:

```bash
cp .env.example .env
```

Variables clave:

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `AI_PROVIDER` | Proveedor de IA (`openai` \| `ollama`) | `openai` |
| `OLLAMA_BASE_URL` | URL del servidor Ollama local | `http://localhost:11434` |
| `OLLAMA_MODEL` | Modelo Ollama a usar | `llama3` |
| `REDIS_URL` | URL de conexión a Redis | `redis://localhost:6379/0` |
| `DATABASE_URL` | URL de la base de datos | `postgres://...` |
| `APP_VERSION` | Versión de la app (para `/health/`) | `unknown` |

### 3. Levantar con Docker Compose

```bash
# Entorno de desarrollo
docker compose -f local.yml up --build

# Entorno de producción
docker compose -f prod.yml up -d
```

### 4. Levantar manualmente (sin Docker)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

---

## Integraciones de IA

Glápagos soporta múltiples proveedores de IA mediante una capa de abstracción
configurable con variables de entorno. No se requiere cambiar el código.

### OpenAI (predeterminado)

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

### Ollama — LLMs locales sin clave API

[Ollama](https://ollama.ai/) permite ejecutar modelos de lenguaje de forma
local, sin depender de servicios externos. Ideal para entornos con restricciones
de conectividad o datos sensibles.

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

Primero, instala y lanza Ollama:

```bash
# Instalar (macOS / Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Descargar el modelo
ollama pull llama3

# Iniciar el servidor
ollama serve
```

El cliente Ollama (`apps/ai/clients/ollama_client.py`) implementa la misma
interfaz que el hook de OpenAI, con los métodos:

- `complete(prompt, **kwargs)` → respuesta completa como string
- `stream(prompt, **kwargs)` → generador de tokens
- `health_check()` → estado del servidor y disponibilidad del modelo

---

## Endpoints de la API

### `GET /health/`

Devuelve el estado de todos los servicios conectados.

**Respuesta exitosa (HTTP 200):**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-05-12T14:30:00+00:00",
  "services": {
    "database": { "status": "ok", "latency_ms": 1.8, "error": null },
    "redis":    { "status": "ok", "latency_ms": 0.6, "error": null },
    "celery":   { "status": "ok", "workers": 2,      "error": null }
  }
}
```

**Respuesta degradada (HTTP 503):**

```json
{
  "status": "degraded",
  "services": {
    "database": { "status": "error", "latency_ms": 5001.0, "error": "could not connect to server" },
    ...
  }
}
```

---

## Despliegue

### Railway (un clic)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/GENIA-Americas/Glapagos-Backend)

Consulta `railway.json` en la raíz del repositorio para la configuración
de variables de entorno requeridas.

### Fly.io

Consulta la guía completa en [`docs/deployment/fly.md`](docs/deployment/fly.md).

Cubre: manejo de secretos, volúmenes para PostgreSQL y despliegue de workers
Celery.

### Docker Compose (producción)

```bash
docker compose -f prod.yml up -d

# Ver logs
docker compose -f prod.yml logs -f

# Ejecutar migraciones
docker compose -f prod.yml exec django python manage.py migrate
```

---

## Estructura del Proyecto

```
Glapagos-Backend/
├── api/                    # Vistas y rutas de la API REST
│   └── health/             # Endpoint /health/
├── apps/
│   └── ai/
│       └── clients/        # Clientes de IA (OpenAI, Ollama, ...)
├── ml/
│   └── inference/          # Módulos de inferencia ML
├── compose/                # Configuraciones Docker
├── docs/
│   └── deployment/         # Guías de despliegue por plataforma
├── requirements/           # Dependencias por entorno
├── local.yml               # Docker Compose — desarrollo
└── prod.yml                # Docker Compose — producción
```

---

## Cómo Contribuir

¡Las contribuciones son bienvenidas! Somos una plataforma construida
**para las Américas**, y valoramos especialmente las contribuciones de
desarrolladores de la región.

1. Haz un fork del repositorio
2. Crea tu rama: `git checkout -b feature/mi-funcionalidad`
3. Haz commit de tus cambios: `git commit -m 'Agrega mi funcionalidad'`
4. Haz push: `git push origin feature/mi-funcionalidad`
5. Abre un Pull Request

Consulta [`CONTRIBUTING.md`](CONTRIBUTING.md) para las pautas completas y
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) para nuestro código de conducta.

### Primeros Issues (Good First Issues)

Si es tu primera contribución, revisa los issues etiquetados como
[`good first issue`](https://github.com/GENIA-Americas/Glapagos-Backend/issues?q=label%3A%22good+first+issue%22).

---

## Licencia

MIT — consulta [`LICENSE`](LICENSE) para más detalles.

---

## Sobre Glápagos

Glápagos es la columna vertebral tecnológica del **Corredor de IA de las Américas**,
coordinado por [RaceFor.AI](https://racefor.ai) y
[GENIA Americas](https://genia.ai).

Construimos infraestructura de IA diseñada específicamente para las realidades
regulatorias, lingüísticas y de mercado del hemisferio occidental — no adaptada
a ellas desde afuera.

**[glapagos.com](https://www.glapagos.com)** · [admin@genia.ai](mailto:admin@genia.ai)
