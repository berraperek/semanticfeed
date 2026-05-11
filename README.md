# SemanticFeed

> An AI-powered personal knowledge management system that helps you save, understand, and retrieve information without getting overwhelmed.

SemanticFeed ingests articles, PDFs, notes, and links — then automatically summarizes, classifies, and ranks them. When you need something back, semantic search and RAG let you query your knowledge base in natural language.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Endpoints](#api-endpoints)
- [Development](#development)
- [Design Decisions](#design-decisions)
- [Roadmap](#roadmap)

---

## Features

| Feature | Status |
|---|---|
| URL ingestion | 🔲 Planned |
| PDF ingestion | 🔲 Planned |
| Content summarization (LLM) | 🔲 Planned |
| Topic classification | 🔲 Planned |
| Difficulty detection | 🔲 Planned |
| Reading time estimation | 🔲 Planned |
| Semantic search (pgvector) | 🔲 Planned |
| Priority ranking | 🔲 Planned |
| RAG-based Q&A | 🔲 Planned |
| REST API | ✅ In progress |
| Database models + migrations | ✅ In progress |

---

## Architecture

SemanticFeed uses a **modular monolith** architecture. All logic lives in a single deployable FastAPI application, but code is organized by domain (ingestion, processing, search, etc.) to keep things maintainable and easy to extract later if needed.

See [`docs/monolith-vs-microservices.md`](docs/monolith-vs-microservices.md) for the reasoning behind this decision.

High-level data flow:

```
User → API → Ingestion Layer → Processing (LLM) → PostgreSQL + pgvector
                                                          ↑
                                               Semantic Search / RAG
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| Language | Python 3.13 |
| Database | PostgreSQL |
| Vector search | pgvector |
| ORM | SQLAlchemy 2.x (declarative, mapped columns) |
| Migrations | Alembic |
| Config management | pydantic-settings |
| Caching / queues | Redis *(planned)* |
| Containerization | Docker *(planned)* |
| Testing | pytest |
| Linting | Ruff |
| Type checking | mypy (strict) |

---

## Project Structure

```
semanticfeed/
├── apps/
│   └── api/                    # FastAPI application
│       ├── app/
│       │   ├── api/            # Route handlers (versioned)
│       │   ├── core/
│       │   │   └── config.py   # Environment-based settings (pydantic-settings)
│       │   ├── db/
│       │   │   ├── base.py     # SQLAlchemy DeclarativeBase
│       │   │   └── session.py  # Engine + SessionLocal factory
│       │   ├── models/
│       │   │   └── content_item.py  # ContentItem ORM model
│       │   └── main.py         # FastAPI app entry point
│       ├── alembic/            # Database migrations
│       │   └── env.py
│       ├── tests/
│       │   └── test_health.py
│       ├── .env.example        # Environment variable template
│       ├── pyproject.toml      # Tool config (ruff, mypy, pytest)
│       └── requirements.txt
├── services/                   # Future: background workers, AI engine
├── infrastructure/             # Future: Terraform, k8s configs
├── docker/                     # Future: Dockerfiles, compose files
├── scripts/                    # Future: seed scripts, utilities
├── tests/                      # Future: integration/e2e tests
├── docs/
│   ├── architecture.md
│   ├── day-1-notes.md
│   └── monolith-vs-microservices.md
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.13+
- PostgreSQL running locally (or via Docker)

### 1. Clone the repository

```bash
git clone https://github.com/berraperek/semanticfeed.git
cd semanticfeed
```

### 2. Set up the virtual environment

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
APP_NAME=SemanticFeed API
APP_VERSION=0.1.0
DEBUG=true
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/semanticfeed
```

### 4. Run database migrations

```bash
alembic upgrade head
```

### 5. Start the development server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

Interactive docs: `http://localhost:8000/docs`

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Root — returns app name |
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |
| `GET` | `/version` | Version info — returns version and debug flag |

More endpoints coming as features are built.

---

## Development

### Run tests

```bash
pytest
```

### Lint

```bash
ruff check .
ruff check --fix .   # auto-fix
```

### Type check

```bash
mypy .
```

### Run all checks (CI-style)

```bash
ruff check . && mypy . && pytest
```

### Create a new migration

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

---

## Design Decisions

**Modular monolith over microservices** — At this stage, development speed and simplicity matter more than independent scaling. The code is organized by domain to make a future split straightforward if needed.

**SQLAlchemy 2.x with mapped columns** — Using the modern `Mapped[T]` + `mapped_column()` API for type-safe, IDE-friendly ORM models.

**pydantic-settings for config** — All configuration comes from environment variables. No hardcoded values. `.env` files are supported for local development.

**Alembic for migrations** — Schema changes are tracked and versioned. `autogenerate` picks up changes from SQLAlchemy models automatically.

**Strict mypy + Ruff** — Enforced from day one to keep the codebase healthy as it grows.

---

## Roadmap

- [ ] `ContentItem` CRUD endpoints
- [ ] URL ingestion pipeline
- [ ] PDF ingestion pipeline  
- [ ] LLM summarization (OpenAI / local model)
- [ ] Topic classification
- [ ] pgvector integration for semantic search
- [ ] RAG-based Q&A endpoint
- [ ] Authentication (JWT)
- [ ] Docker Compose setup
- [ ] CI/CD pipeline