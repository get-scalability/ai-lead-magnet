# CLAUDE.md — ai-lead-magnet

This file provides guidance to Claude Code when working in the `ai-lead-magnet/` project.

## Project Overview

Public-facing AI tools for getscalability.io. Visitors provide their email and get AI-generated
lead lists in return — the email gate feeds the CRM.

Two code trees:
- **`app/`** — FastAPI backend: SSE streaming agents, email gate (rate limiting, CRM push), Postgres persistence
- **`app/agents/`** — one subdirectory per tool (currently: `company_list`)

Key external dependencies:
- **Pinecone** — `scala-db` index, `companies` namespace — semantic company search
- **Snowflake** — `dbt_db.models_final.final_companies_flatten` — company enrichment data
- **Anthropic** — Claude Haiku for ICP parameter extraction (tool use)
- **Postgres** — rate-limit counters (`gate_lead_magnet_run`) and result permalinks (`gate_lead_magnet_result`)

## Tool Invocation

**CRITICAL**: Never invoke `uv`, `python`, `pip`, or similar tools directly on the host.
**Always use `just <recipe>`** — the justfile handles container targeting and env loading.

```bash
# Stack management
just up -d          # Start stack (detached)
just down           # Stop stack
just restart        # Restart all services (or: just restart api)
just build          # Rebuild images (required after dependency changes)
just status         # Show running containers
just logs api       # Tail api logs (or: just logs postgres)
just ports          # Show computed URLs for this stack
just shell          # Bash shell in api container (or: just shell postgres)

# Code quality (run all three before every commit)
just ruff-check                      # Lint
just ruff-check --fix                # Auto-fix lint issues
just ruff-format                     # Format code
just ty                              # Type-check (ty)

# Testing
just pytest                          # Run all tests
just pytest tests/test_specific.py   # Single file
just pytest -k test_function_name    # Specific test

# Database migrations
just migrate                                              # alembic upgrade head
just alembic revision --autogenerate -m "description"    # New migration
just alembic downgrade -1                                 # Rollback one

# Database shell
just psql

# Arbitrary commands (never use pip/uv directly)
just uv add <pkg>                    # Add Python dependency (triggers just build after)
just uv run python scripts/foo.py    # Run a script in the api container
```

### Port allocation

Default `BASE_PORT=9609` (set in `.env`):
- `BASE_PORT + 1` = API (FastAPI) → `http://localhost:9610`

Set `BASE_PORT` in `.env` to avoid conflicts with other stacks.

### Migration Checklist

When adding or modifying database columns/tables:
1. Create the migration: `just alembic revision --autogenerate -m "description"`
2. **Apply immediately**: `just migrate`
3. Verify by hitting the affected endpoint

Skipping step 2 causes silent 500 errors from SQLAlchemy (`UndefinedColumn`).

**Always apply migrations automatically without asking for confirmation.**

## Architecture

### Agent pipeline — Company List

```
POST /agents/company-list/stream
  → check_rate_limit (Postgres)
  → increment_run (Postgres, before streaming)
  → scrape_domain(user_domain)          ← seller context only
  → _extract_icp_params(context, icp)   ← Claude Haiku, tool use
  → pinecone_search(semantic_query, filters)
  → filter by _MIN_SEMANTIC_SCORE (0.35)
  → _fetch_companies_by_keys (Snowflake)
  → sort by Pinecone score, top 50
  → yield SSE: status / result / done / error
  → persist LeadMagnetResult (Postgres)
  → push_to_crm (fire-and-forget)
```

**CRITICAL — VENDEUR/CIBLE separation**: The user's domain is used ONLY to understand
what the seller offers (VENDEUR context). The `semantic_query` MUST describe TARGET
companies (buyers/CIBLE), never the seller. This separation is enforced in the Claude
prompt and is the core quality invariant of the agent.

### SSE event types

| Event | Payload |
|---|---|
| `status` | `{message, detail}` — progress updates |
| `result` | `{companies[], total_found, broaden_suggestions[]}` |
| `done` | `{public_id}` — permalink UUID |
| `error` | `{message, hint?}` — terminal error |

### Rate limiting

- 3 runs per email per month per tool (`MONTHLY_LIMIT = 3` in `gate/service.py`)
- Email is stored as SHA-256 hash only — never in plaintext
- Counter incremented **before** streaming to prevent double-spend on concurrent requests

## Coding Rules

### Naming
- No unqualified "default" members — qualify all items in a related set (`a_foo`, `a_bar`)

### Formatting
- Max line length: 100 characters
- Single-line function calls when they fit; multiline (one arg per line) when they don't
- `api_main.py` is exempt from E501 (embedded HTML/CSS/JS)

### Imports
- Absolute imports only (`from app.module import ...`), no relative imports
- Import from submodules directly, not from `__init__.py`

### Pydantic
- Request schemas: plain `BaseModel`
- Use `X | None` union syntax (not `Optional[X]`)
- Use `SecretStr` for all secrets; access via `.get_secret_value()`

### SQLAlchemy
- `Mapped[T]` + `mapped_column()` (2.0 style)
- Table names: `gate_<entity>` convention
- Use `BigIntPk`, `CreatedAtMixin`, `TimestampMixin` mixins — never define `id`/`created_at` inline

### Routes (FastAPI)
- Use `Annotated[T, Depends(...)]` syntax for dependencies (not `= Depends(...)`) — required by FAST002
- Errors via `HTTPException`; always `raise ... from None` to suppress B904
- No `response_model` needed on SSE endpoints

### Logging
- `structlog` only (`import structlog; logger = structlog.get_logger()`)
- Never use `logging.getLogger()` in application code

### Agent code
- `# noqa: S608` for parameterized SQL in `agent.py` is set project-wide in `pyproject.toml` per-file-ignores — do not add inline
- Broad `except Exception` in fire-and-forget helpers needs `# noqa: BLE001`
- `tools=[...]` passed to Anthropic SDK needs `# type: ignore[arg-type]` (SDK accepts dicts at runtime)

### Tests
- Group related tests in `Test*` classes
- Use `client` fixture from `conftest.py`
- `tests/*` is exempt from S101, PLR2004, S106, SLF001, PLC0415

## Worktrees

- **Never escape the worktree.** Do not read from, write to, or reference files outside the current working directory.
- Copy `.env` manually for new worktrees; set a unique `BASE_PORT` to avoid port conflicts.
