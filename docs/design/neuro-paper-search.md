# SemanticFeed → Neuroscience Paper Search & Feed — Design

Date: 2026-11-24
Status: Draft, awaiting approval

## Intent and why

Repurpose the `semanticfeed` repo from a generic personal-knowledge tool into a
tool for **semantic search and a daily feed over newly published neuroscience
preprints**.

Why: neuroscience preprint volume is high and keyword search misses papers
that use different terminology for the same idea. Embedding-based search lets a
reader describe a topic in plain language and find related work, and a feed of
saved interests surfaces relevant new papers without manual browsing.

The project is software and data only; no recording hardware is involved.

**Delivery is incremental: every step ends with something that runs.**

## Goals

1. **Search:** type a natural-language question and get the closest recent
   neuroscience papers, ranked by semantic similarity.
2. **Feed (version A):** save a few interests written as sentences, and see the
   papers from the last N days that are closest to them.
3. A clean, readable repo: a README that explains the idea, passing tests and
   type checks, and setup in a couple of commands.

## Non-goals (for this MVP)

- LLM summaries, RAG / Q&A, PDF or full-text processing.
- Authentication or multiple users.
- Public hosting. The MVP runs locally; a public demo is the first step after it.
- Version B of the feed (learning from papers you liked). It comes after the
  MVP and is described at the end so the MVP doesn't block it.
- Hardware or signal-recording work.

## Anti-goals (failure even if it "works")

- A step that leaves the repo broken or half-built.
- Depending on a paid or keyed external API for the core loop. Embeddings run
  locally.
- Infrastructure nobody needs yet (Redis, queues, microservices, k8s).

## Constraints

- Build on the existing stack: Python, FastAPI, SQLAlchemy 2.x, Alembic,
  pydantic-settings, ruff, mypy strict, pytest.
- Postgres with **pgvector**, run locally through `docker compose`.
- Tests must not hit the network or download models. Use fixtures and a fake
  embedder.

## Approaches considered

**Search and feed share one pipeline** (fetch → embed → rank by cosine
similarity). The feed is "search with saved queries, limited to recent papers".
Chosen order: search first (steps 1–5), then the feed on top (steps 6–7).

**Data source**
- *bioRxiv `neuroscience` category* (chosen first): free JSON API with no key, a
  steady daily volume of papers, and abstracts included.
- *arXiv q-bio.NC*: more computational, but lower volume. Added later as a second
  source through the `source` column.
- *PubMed*: huge and noisy for "new preprints"; skipped.

**Feed interests**
- *A, interests written as sentences* (chosen for the MVP): reuses the search
  code exactly.
- *B, papers you liked* (later): builds an interest vector from liked papers;
  needs a like UI.

**UI**
- *A separate Next.js (React + TypeScript) app in `apps/web`* (chosen): a richer
  UI with a clean API/UI split, and it deploys easily when the demo step comes.
  The cost is a second app to build and maintain.
- *Server-rendered Jinja2 pages from FastAPI*: no frontend build at all, but a
  plainer UI and the UI is tied to the API.

## Cleanup of the existing repo (step 1)

Keep: the modular router (`app/api/router.py` → `v1/router.py` → `endpoints/`),
`core/config.py`, `db/base.py`, `db/session.py`, the Alembic setup, and the
tooling config.

Fix:
- Add the missing deps to `requirements.txt`: `sqlalchemy`, `alembic`,
  `psycopg[binary]`, `pgvector`.
- Remove the duplicate `/health` and `/version` from `main.py`. Keep them only
  under `/api/v1`, and point the tests at `/api/v1/...`.

Remove / replace:
- Delete the `ContentItem` model and both existing migrations (one of them is an
  empty `pass`). Start a fresh migration history.
- Rewrite the README for the new purpose.
- Delete `docs/day-1-notes.md`. Move `docs/monolith-vs-microservices.md` and the
  old `docs/architecture.md` into `docs/archive/`. Write a new short
  `docs/architecture.md`.

## Data model

`papers`
- `id` int PK
- `doi` text, **unique** (the upsert key)
- `version` int (bioRxiv version; keep the latest)
- `title` text
- `abstract` text
- `authors` text (as returned: a semicolon-separated string)
- `category` text
- `published_at` date (bioRxiv `date` field)
- `source` text (`"biorxiv"` for now)
- `url` text (`https://www.biorxiv.org/content/{doi}v{version}`)
- `embedding` vector(D), nullable (added in step 3; D depends on the model)
- `created_at` timestamptz

`interests` (step 6)
- `id` int PK, `text` text, `embedding` vector(D), `created_at` timestamptz

## The steps (each ends with something that runs)

1. **Cleanup + Postgres with pgvector.** Do the cleanup above. Add
   `docker-compose.yml` with the `pgvector/pgvector` image, the `papers` table
   (without `embedding`), and the pgvector extension enabled in a migration.
   *Done when:* `docker compose up -d`, `alembic upgrade head`, `pytest`, `ruff`
   and `mypy` all pass.
2. **Ingestion.** `python -m app.ingest --days 7` calls
   `https://api.biorxiv.org/details/biorxiv/{start}/{end}/{cursor}?category=neuroscience`,
   pages through with the cursor (100 papers per page), and upserts by `doi`,
   keeping the higher `version`. Running it twice causes no duplicates. The
   first run backfills about 6 months (`--days 180`, roughly 10–20k papers);
   daily runs use a small window.
   *Done when:* the command prints how many papers it inserted or updated, and a
   test using a saved JSON fixture passes.
3. **Embeddings.** Start with a quick side-by-side check: embed a sample of
   papers with SPECTER2 and with a small general model, run the same handful
   of queries through both, compare the top results, and pick one. Record the
   comparison in `docs/architecture.md`. Then build an `Embedder` interface (`embed_documents`, `embed_query`)
   with one real implementation and one fake for tests. Embed
   `title + [SEP] + abstract` for papers that have no embedding yet, in batches.
   Run it with `python -m app.embed`, or as the last part of ingestion.
   *Done when:* every paper has an embedding and the command prints the count.
4. **Search API.** `GET /api/v1/search?q=...&limit=10&days=` embeds the query and
   orders by pgvector cosine distance (`<=>`). It returns the title, authors,
   date, URL, a shortened abstract and a score. *Done when:* `curl` returns
   sensible results, and a test using the fake embedder passes.
5. **Web app + search page.** Scaffold `apps/web` (Next.js, TypeScript,
   App Router). The API URL comes from an env var, and FastAPI allows the web
   origin through CORS. `/` shows a search box and a result list linking to
   bioRxiv. *Done when:* `npm run dev` plus the API lets you search in the
   browser, and `npm run lint` / type check pass.
6. **Feed A.** CRUD API for interests (`/api/v1/interests`) and an `/interests`
   page in the web app. The `/api/v1/feed` endpoint and the `/feed` page show,
   for each interest, the top-k papers from the last N days (default 7). Papers
   matched by several interests appear once, under the best match, with that
   interest named. *Done when:* adding an interest makes matching papers show up
   in `/feed`.
7. **Daily refresh.** A documented local cron/launchd line or a Makefile target
   that runs ingest + embed daily. *Done when:* the README explains it and it
   has run once by itself.

Each step is its own commit (or a small PR) and updates the README "Status"
table.

## Later (not in this MVP)

- **Public demo** (first after the MVP): host the API, Postgres with pgvector,
  and the web app on free or low-cost tiers. Check current provider limits at
  that point. The embedding model's memory use decides where the API can run.

- **Feed B:** a `likes` table. The interest vector becomes the mean of liked
  papers' embeddings, optionally mixed with interest sentences.
- arXiv q-bio.NC as a second source.
- An HNSW index once the table passes about 50k rows. Below that, an exact scan
  is fast enough.
- **Similar papers:** a link on each result that runs a nearest-neighbour
  search from that paper's stored embedding.
- **Topic map:** UMAP projection plus clustering of paper embeddings, shown as
  an interactive 2D map with cluster labels.
- **Trends:** paper counts per topic cluster over time, built from the clusters
  and `published_at`.
- **Summaries / Q&A:** LLM summaries of a result set, or questions answered
  over the retrieved abstracts (RAG). This needs a paid API, so it stays opt-in.
- Filters (date range, subcategory).

The MVP keeps this open because it stores every embedding with its
`published_at`. The search code also takes a vector, not only text, so
"similar papers" can reuse it.

## Decisions

- **Tests and the database.** Tests that touch the database (ingest upsert,
  search) run against the docker-compose Postgres, using a separate
  `semanticfeed_test` database. Parsing tests and the fake embedder need no DB.
  `DATABASE_URL` gets a local default so that `pytest` doesn't fail on import.
- **bioRxiv dates.** `published_at` is bioRxiv's `date` field, which is the date
  that version was posted. A revised preprint can therefore show up as "new"
  again. That is acceptable for a feed of new work.

## Open implementation details

- **Embedding model.** Chosen by the comparison at the start of step 3. The
  candidates are SPECTER2 (`allenai/specter2_base`), which is trained on
  scientific papers and has a proximity adapter for papers and an ad-hoc query
  adapter for queries, and a small general sentence-transformers model
  (e.g. `all-MiniLM-L6-v2`). D is fixed in that step's migration.
- Exact package versions, module layout inside `app/`, and the styling of the
  pages (keep them minimal).
- HTTP client choice (`httpx` is already installed), plus retry and timeout
  details for the bioRxiv API.
