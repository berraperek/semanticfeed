# Step 1 — Cleanup + Postgres with pgvector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the old personal-knowledge-tool skeleton into a clean base for the neuroscience paper search. Local Postgres with pgvector runs via docker compose, the `papers` table comes from a fresh migration, and all checks pass.

**Architecture:** The existing FastAPI modular monolith stays. Postgres runs in docker compose; the `pgvector/pgvector` image creates a dev database and a test database. A single fresh Alembic migration enables the `vector` extension and creates `papers`. DB tests run Alembic against the test database.

**Tech Stack:** Python 3.12 (the existing `.venv`), FastAPI, SQLAlchemy 2.x, Alembic, psycopg2-binary, pgvector, pydantic-settings, pytest, ruff, mypy strict, Docker Compose.

**Spec:** `docs/design/neuro-paper-search.md` (section "Cleanup of the existing repo" and step 1).

All paths below are relative to the repo root. Commands run from `apps/api` with `.venv` active, unless noted.

## Global Constraints

- Build on the existing stack; no new infrastructure beyond Postgres + pgvector in docker compose.
- Tests must not hit the network or download models.
- DB tests run against the docker-compose Postgres, using a separate `semanticfeed_test` database.
- `DATABASE_URL` has a local default so `pytest` does not fail on import.
- `papers` columns (no `embedding` yet): `id` int PK, `doi` text unique, `version` int, `title` text, `abstract` text, `authors` text, `category` text, `published_at` date, `source` text, `url` text, `created_at` timestamptz.
- Health/version endpoints live only under `/api/v1`.
- Public repo: no personal details in docs or commit messages.

## Decisions made in this plan

- Compose publishes Postgres on host port **5433**, so it can't collide with a locally installed Postgres on 5432.
- Dev credentials `semanticfeed` / `semanticfeed`. Default URLs:
  - dev: `postgresql://semanticfeed:semanticfeed@localhost:5433/semanticfeed`
  - test: `postgresql://semanticfeed:semanticfeed@localhost:5433/semanticfeed_test`
- Keep `psycopg2-binary`, since it's already installed and plain `postgresql://` URLs use it.
- Python 3.12 everywhere. `.venv` is 3.12 and ruff/mypy already target 3.12; pyright and the README said 3.13.
- `published_at` gets an index, because the feed filters by date.
- The repo-root `.env.example` (an empty duplicate) is deleted. `apps/api/.env.example` carries the real defaults.

## Review Focus

1. **Postgres already on 5432** → compose uses 5433 and every default URL points there (Task 2 test checks the default URL's port).
2. **An existing `apps/api/.env` pointing at the old DB** (whose `alembic_version` names a deleted revision) → the README tells you to copy `.env.example` again, and the default works without any `.env` (Task 1 test).
3. **`pytest` run without docker** → DB tests fail fast with a message naming `docker compose up -d` instead of hanging (Task 2 test via connect timeout).
4. **Tests run twice / dirty test DB** → the fixture upgrades to head (which is idempotent) and empties `papers` before each DB test (Task 2).
5. **Duplicate DOI** → the unique constraint rejects it; step 2's upsert relies on this (Task 2 test).

---

### Task 1: Dependencies, settings default, single health router

**Files:**
- Modify: `apps/api/requirements.txt`, `apps/api/app/core/config.py`, `apps/api/app/main.py`, `apps/api/app/api/v1/endpoints/health.py`, `apps/api/pyrightconfig.json`, `apps/api/.env.example`
- Delete: `.env.example` (repo root)
- Test: `apps/api/tests/test_health.py`, `apps/api/tests/test_config.py`

**Interfaces:**
- Produces: `app.core.config.Settings` with `DATABASE_URL: str` (default = dev URL) and `TEST_DATABASE_URL: str` (default = test URL). The `settings` singleton is unchanged.

- [ ] **Step 1: Write failing tests**

`tests/test_health.py`: point the existing two tests at `/api/v1/health` and `/api/v1/version` (same assertions: `{"status": "ok"}`; `"version"` and `"debug"` in the body). Add `test_root_level_health_removed`: `client.get("/health").status_code == 404`.

`tests/test_config.py`:
```python
def test_database_url_has_local_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    s = Settings(_env_file=None)
    assert s.DATABASE_URL == "postgresql://semanticfeed:semanticfeed@localhost:5433/semanticfeed"
    assert s.TEST_DATABASE_URL.endswith("/semanticfeed_test")
```

- [ ] **Step 2: Run and confirm they fail**

Run: `pytest -v`
Expected: the v1 version test fails (no `debug`), the 404 test fails, and the config test fails (no default / no `TEST_DATABASE_URL`).

- [ ] **Step 3: Implement**
- `config.py`: add the defaults above. Replace `class Config` with `model_config = SettingsConfigDict(env_file=".env")`. Drop the `pyrefly` comment.
- `main.py`: remove the `/health` and `/version` routes; keep `/` and `include_router`.
- `health.py`: `version()` returns `{"version": settings.APP_VERSION, "debug": settings.DEBUG}` with return type `dict[str, str | bool]`.
- `requirements.txt`: add pinned `SQLAlchemy`, `alembic`, `psycopg2-binary` at the versions already in `.venv` (`pip freeze`), plus `pgvector` (latest, then `pip install -r requirements.txt`).
- `pyrightconfig.json`: `"pythonVersion": "3.12"`.
- `apps/api/.env.example`: fill in `APP_NAME=SemanticFeed API`, `APP_VERSION=0.1.0`, `DEBUG=true`, and the dev `DATABASE_URL`.
- Delete the root `.env.example`.

- [ ] **Step 4: Run checks**

Run: `pytest -v && ruff check . && mypy .`
Expected: all pass.

- [ ] **Step 5: Commit** — `chore: pin DB deps, default DATABASE_URL, serve health only under /api/v1`

---

### Task 2: docker compose, `papers` model, fresh migration, DB tests

**Files:**
- Create: `docker-compose.yml` (repo root), `docker/initdb/01-create-test-db.sql`, `apps/api/app/models/paper.py`, `apps/api/alembic/versions/0001_create_papers.py`, `apps/api/tests/conftest.py`, `apps/api/tests/test_db_schema.py`
- Modify: `apps/api/alembic/env.py`, `apps/api/app/models/__init__.py` (create if missing)
- Delete: `apps/api/app/models/content_item.py`, both files in `apps/api/alembic/versions/`

**Interfaces:**
- Consumes: `settings.DATABASE_URL`, `settings.TEST_DATABASE_URL` (Task 1).
- Produces: `app.models.paper.Paper` (table `papers`, the columns from Global Constraints, `doi` unique, index on `published_at`). Alembic revision id `"0001"`. `env.py` uses `config.attributes["url"]` when it's set, and `settings.DATABASE_URL` otherwise. The `db_engine` pytest fixture (session scope, migrated test DB) and the `db_session` fixture (per test, `papers` truncated first) are used by later steps' tests.

- [ ] **Step 1: Compose + init script**

`docker-compose.yml`: one service `db` with image `pgvector/pgvector:pg17`, env `POSTGRES_USER/PASSWORD/DB = semanticfeed`, port `"5433:5432"`, a named volume for data, `./docker/initdb` mounted at `/docker-entrypoint-initdb.d`, and a `pg_isready` healthcheck. The init SQL is `CREATE DATABASE semanticfeed_test;`.

Run (repo root): `docker compose up -d && docker compose ps`
Expected: `db` is `healthy`.

- [ ] **Step 2: Write failing DB tests**

`conftest.py`:
- The `db_engine` fixture connects to `TEST_DATABASE_URL` with `connect_args={"connect_timeout": 3}`. On `OperationalError` it calls `pytest.fail("Test database unreachable — run `docker compose up -d` from the repo root")`. Then it runs `alembic.command.upgrade(cfg, "head")`, where `cfg = Config("alembic.ini")` and `cfg.attributes["url"] = TEST_DATABASE_URL`.
- The `db_session` fixture runs `TRUNCATE papers RESTART IDENTITY` and then yields a `Session`.

`test_db_schema.py`:
- `test_vector_extension_installed`: `SELECT extname FROM pg_extension WHERE extname='vector'` returns one row.
- `test_papers_columns`: the set of column names from `inspect(engine).get_columns("papers")` equals `{"id","doi","version","title","abstract","authors","category","published_at","source","url","created_at"}`.
- `test_duplicate_doi_rejected`: adding two `Paper`s with the same `doi` and committing raises `IntegrityError`.
- `test_default_urls_use_compose_port`: `":5433/"` appears in both default URLs.

- [ ] **Step 3: Run and confirm they fail**

Run: `pytest tests/test_db_schema.py -v`
Expected: fails at import (`app.models.paper` missing) or because there is no `papers` table.

- [ ] **Step 4: Implement**
- `Paper` model in the existing `Mapped`/`mapped_column` style. `created_at` keeps the UTC default pattern from the deleted `ContentItem`.
- `env.py`: import `app.models.paper` instead of `content_item`. Set the URL from `config.attributes.get("url") or settings.DATABASE_URL`.
- Migration `0001_create_papers.py` (`revision = "0001"`, `down_revision = None`): run `op.execute("CREATE EXTENSION IF NOT EXISTS vector")`, then `create_table` and `create_index`. `downgrade` drops the index and table and leaves the extension.
- Delete the old model and the two old migrations.

- [ ] **Step 5: Run checks, including the dev DB**

Run: `pytest -v && ruff check . && mypy . && alembic upgrade head`
Expected: everything passes, and `alembic upgrade head` on the dev DB prints `Running upgrade  -> 0001`. Run `alembic downgrade base && alembic upgrade head` once to check the round trip.

- [ ] **Step 6: Commit** — `feat: add papers table with pgvector-enabled Postgres via docker compose`

---

### Task 3: README and docs for the new purpose

**Files:**
- Modify: `README.md` (full rewrite), `docs/architecture.md` (rewrite)
- Move: the old `docs/architecture.md` → `docs/archive/architecture-v0.md`, and `docs/monolith-vs-microservices.md` → `docs/archive/`

**Interfaces:** none.

- [ ] **Step 1: Move the old docs** to `docs/archive/` with `git mv`. Then write the new files.
- [ ] **Step 2: README** — a one-paragraph pitch (semantic search and interest feed over new bioRxiv neuroscience preprints), a Status table listing design steps 1–7 (step 1 ✅, the rest 🔲), the tech stack (Python 3.12), a quickstart (`docker compose up -d`; `cd apps/api`; venv; `pip install -r requirements.txt`; `cp .env.example .env`; `alembic upgrade head`; `uvicorn app.main:app --reload`), the API table (`GET /`, `/api/v1/health`, `/api/v1/version`), the dev commands (`pytest`, `ruff check .`, `mypy .`), and a link to `docs/design/neuro-paper-search.md`. Note that tests need the compose DB running. Add a note: if an older `.env` exists, re-copy `.env.example`.
- [ ] **Step 3: `docs/architecture.md`** — the components (FastAPI API, Postgres + pgvector, the future `apps/web`), the data flow `bioRxiv → ingest → papers → embed → search/feed`, and a placeholder heading "Embedding model choice" for step 3.
- [ ] **Step 4: Check** — run `grep -rniE "owner|portfolio|career" README.md docs/architecture.md`; expect no output. Every command in the quickstart was already run in Tasks 1–2.
- [ ] **Step 5: Commit** — `docs: rewrite README and architecture for neuroscience paper search`
