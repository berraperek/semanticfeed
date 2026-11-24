# SemanticFeed

> Semantic search and a daily interest feed over newly published neuroscience preprints.

Neuroscience preprints come out faster than anyone can browse them, and keyword search misses papers that describe the same idea in different words. SemanticFeed pulls new papers from the [bioRxiv](https://www.biorxiv.org/) neuroscience category and embeds their titles and abstracts. You can then:

- **Search** in plain language, e.g. *"hippocampal replay during sleep"*, and get the closest papers ranked by semantic similarity.
- **Follow a feed** of your saved interests, which shows the new papers from the last few days that are closest to each one.

Everything runs locally. Embeddings are computed with a local model, so no paid API is needed.

---

## Status

The project is built in small steps that each end with something that runs. The full design is in [`docs/design/neuro-paper-search.md`](docs/design/neuro-paper-search.md).

| Step | What | Status |
|---|---|---|
| 1 | Cleanup + Postgres with pgvector (`papers` table) | ✅ Done |
| 2 | Ingest bioRxiv neuroscience papers | 🔲 Planned |
| 3 | Embed papers (model chosen by side-by-side comparison) | 🔲 Planned |
| 4 | Search API (`/api/v1/search`) | 🔲 Planned |
| 5 | Web app (Next.js) with a search page | 🔲 Planned |
| 6 | Interest feed | 🔲 Planned |
| 7 | Daily refresh | 🔲 Planned |

After the MVP: a public demo, "similar papers", a topic map, trend charts, and optional LLM summaries.

---

## Architecture

```
bioRxiv API → ingest → papers (Postgres) → embed → pgvector
                                                     ↓
                               search API / interest feed → web app
```

The API is a modular FastAPI monolith. More detail is in [`docs/architecture.md`](docs/architecture.md).

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI, Python 3.12 |
| Database | PostgreSQL 17 + pgvector (Docker Compose) |
| ORM / migrations | SQLAlchemy 2.x, Alembic |
| Config | pydantic-settings |
| Web app | Next.js *(step 5)* |
| Quality | pytest, Ruff, mypy (strict) |

## Project Structure

```
semanticfeed/
├── apps/api/               # FastAPI application
│   ├── app/
│   │   ├── api/            # Versioned routers (/api/v1)
│   │   ├── core/config.py  # Settings (env / .env, local defaults)
│   │   ├── db/             # SQLAlchemy base + session
│   │   └── models/         # ORM models (Paper)
│   ├── alembic/            # Migrations
│   └── tests/
├── docker/initdb/          # Creates the test database on first start
├── docker-compose.yml      # Postgres + pgvector on localhost:5433
└── docs/                   # Design, plans, architecture
```

---

## Getting Started

Prerequisites: Python 3.12 and Docker.

```bash
git clone https://github.com/berraperek/semanticfeed.git
cd semanticfeed
docker compose up -d          # Postgres + pgvector on port 5433
```

```bash
cd apps/api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`, with interactive docs at `/docs`.

> **Upgrading from an older checkout?** Copy `.env.example` to `.env` again. The database moved to the compose service on port 5433, and the old migrations were replaced.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | App name |
| `GET` | `/api/v1/health` | Health check, returns `{"status": "ok"}` |
| `GET` | `/api/v1/version` | Version and debug flag |

## Development

Tests need the compose database running (`docker compose up -d`). They use a separate `semanticfeed_test` database.

```bash
ruff check . && mypy . && pytest
```

Create a migration after changing a model:

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

## Design Decisions

- **Modular monolith.** One deployable FastAPI app, organized by domain. That's simpler at this stage, and parts can be split out later if needed.
- **pgvector inside Postgres.** Papers and their embeddings live in one database, so search is a single SQL query with no separate vector store.
- **Local embeddings.** There's no dependency on a paid API for the core search loop.
- **Strict mypy + Ruff from day one.** This keeps the codebase healthy as it grows.
