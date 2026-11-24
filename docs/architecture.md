# Architecture

## Components

- **API (`apps/api`)**: a FastAPI modular monolith. Routers are versioned under `/api/v1`, and settings come from pydantic-settings with local defaults.
- **Database**: PostgreSQL 17 with the `pgvector` extension, run through `docker-compose.yml` on `localhost:5433`. The dev database is `semanticfeed`; tests use `semanticfeed_test`.
- **Web app (`apps/web`, step 5)**: Next.js (TypeScript, App Router). It calls the API over HTTP, and the API allows its origin through CORS.

## Data flow

```
bioRxiv API ──ingest──▶ papers ──embed──▶ papers.embedding (pgvector)
                                              │
                    query / saved interest ──▶ cosine distance (<=>) ──▶ ranked papers
```

1. **Ingest** (step 2): fetch the bioRxiv `neuroscience` category for a date window and upsert by `doi`, keeping the latest version.
2. **Embed** (step 3): embed `title + [SEP] + abstract` for papers without an embedding.
3. **Search** (step 4): embed the query and order papers by cosine distance.
4. **Feed** (step 6): run each saved interest as a search, limited to the last N days.

## Data model

`papers`: `id`, `doi` (unique), `version`, `title`, `abstract`, `authors`, `category`, `published_at` (indexed), `source`, `url`, `created_at`. The `embedding vector(D)` column is added in step 3.

## Embedding model choice

*To be decided at the start of step 3,* by comparing SPECTER2 and a small general sentence-transformers model on the same queries. The comparison and the result will be recorded here.
