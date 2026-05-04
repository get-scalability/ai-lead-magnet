# ai-agents development commands
#
# Port allocation: CONDUCTOR_PORT or BASE_PORT (default 9601) + offset
#   +0 = admin (Vite)      (override via ADMIN_PORT in .env)
#   +1 = api (FastAPI)
#   +2 = rabbitmq management UI
#   +3 = mcp-scala-db
#   +4 = mcp-crm
#
# Conductor auto-detection: when CONDUCTOR_PORT is set, it takes precedence.
# Both CONDUCTOR_PORT and BASE_PORT mean "first service port".

set dotenv-load := true
set positional-arguments := true
set shell := ["bash", "-cu"]

_base := env("CONDUCTOR_PORT", env("BASE_PORT", "9601"))

# Show available recipes
default:
    @just --list

# --- Stack management ---

# Start the development stack
up *ARGS:
    #!/usr/bin/env bash
    set -euo pipefail
    base={{ _base }}
    export ADMIN_PORT=${ADMIN_PORT:-$base}
    export API_PORT=$((base + 1))
    export RABBITMQ_MGMT_PORT=$((base + 2))
    export MCP_SCALA_DB_PORT=$((base + 3))
    export MCP_CRM_PORT=$((base + 4))
    docker compose up "$@"

# Stop the development stack
down *ARGS:
    docker compose down "$@"

# Restart services (optionally a specific one: just restart api)
restart *ARGS:
    docker compose restart "$@"

# Build images (optionally a specific one: just build api)
build *ARGS:
    docker compose build "$@"

# Show running services
status:
    docker compose ps

# Tail logs (optionally for a specific service: just logs api)
logs *ARGS:
    docker compose logs "$@"

# Show computed ports and project name
ports:
    #!/usr/bin/env bash
    set -euo pipefail
    base={{ _base }}
    project=${COMPOSE_PROJECT_NAME:-$(basename "$PWD")}
    admin_port=${ADMIN_PORT:-$base}
    echo "Project:        $project"
    echo "Admin:          http://localhost:$admin_port  (set ADMIN_PORT in .env to override)"
    echo "API:            http://localhost:$((base + 1))"
    echo "RabbitMQ:       http://localhost:$((base + 2))"
    echo "MCP Scala DB:   http://localhost:$((base + 3))"
    echo "MCP CRM:        http://localhost:$((base + 4))"

# --- Code quality ---

# Run ruff check
ruff-check *ARGS:
    docker compose exec -u root api uv run ruff check "$@"

# Format code with ruff
ruff-format *ARGS:
    docker compose exec -u root api uv run ruff format "$@"

# Run ty type checker
ty *ARGS:
    docker compose exec -u root api uv run ty check "$@"

# Lint admin with ESLint
eslint *ARGS:
    docker compose exec admin bun run lint "$@"

# Type-check admin with tsc
tsc *ARGS:
    docker compose exec admin bunx --bun tsc -b "$@"

# --- Testing ---

# Run pytest in the api container
pytest *ARGS:
    docker compose exec -u root api uv run pytest "$@"

# --- Database ---

# Run alembic upgrade head in the api container
migrate:
    docker compose exec -u root api uv run alembic upgrade head

# Run arbitrary alembic commands (e.g. just alembic downgrade -1)
alembic *ARGS:
    docker compose exec -u root api uv run alembic "$@"

# Open a psql shell to the database
psql *ARGS:
    docker compose exec postgres psql -U scala_user -d ai_agents "$@"

# --- Operations ---

# Open a bash shell in a container (default: api)
shell SERVICE="api":
    docker compose exec -u root {{ SERVICE }} bash

# Run arbitrary uv commands in the api container (e.g. just uv run python scripts/foo.py)
uv *ARGS:
    docker compose exec -u root api uv "$@"

# Run arbitrary bun commands in the admin container (e.g. just bun add <pkg>)
bun *ARGS:
    docker compose exec admin bun "$@"

# --- Maintenance ---

# Remove volumes from Compose projects with no running containers
clean-volumes:
    #!/usr/bin/env bash
    set -euo pipefail
    fmt='{{"{{"}}.Label "com.docker.compose.project"{{"}}"}}'
    # Collect project names that have running containers
    active=$(docker ps --format "$fmt" | sort -u)
    # Collect all Compose-managed volume project names
    all_projects=$(docker volume ls --filter "label=com.docker.compose.project" \
        --format "$fmt" | sort -u)
    removed=0
    for project in $all_projects; do
        if [[ "$project" == "ai-agents" ]]; then
            echo "Skipping $project (main project)"
            continue
        fi
        if echo "$active" | grep -qx "$project"; then
            echo "Skipping $project (running)"
            continue
        fi
        vols=$(docker volume ls --filter "label=com.docker.compose.project=$project" -q)
        count=$(echo "$vols" | wc -l)
        echo "Removing $count volumes from $project"
        echo "$vols" | xargs docker volume rm
        removed=$((removed + count))
    done
    if [[ $removed -eq 0 ]]; then
        echo "No orphaned volumes found."
    else
        echo "Removed $removed volumes."
    fi

# --- Worktree setup ---

# Copy .env and set COMPOSE_PROJECT_NAME (supports Conductor and git worktrees)
setup:
    #!/usr/bin/env bash
    set -euo pipefail
    if [[ -n "${CONDUCTOR_ROOT_PATH:-}" ]]; then
        src="$CONDUCTOR_ROOT_PATH/.env"
    else
        src="$(git worktree list --porcelain | head -1 | sed 's/^worktree //')/.env"
    fi
    if [[ "$(realpath "$src" 2>/dev/null)" == "$(realpath .env 2>/dev/null)" ]]; then
        echo ".env already in place, nothing to do."
        exit 0
    fi
    if [[ -f "$src" ]]; then
        cp "$src" .env
        echo "Copied .env from $src"
    else
        echo "Error: $src not found"
        exit 1
    fi
    # Set COMPOSE_PROJECT_NAME for worktree isolation (unless already defined)
    if ! grep -q '^COMPOSE_PROJECT_NAME=' .env 2>/dev/null; then
        project="ai-agents-$(basename "$PWD")"
        echo "COMPOSE_PROJECT_NAME=$project" >> .env
        echo "Set COMPOSE_PROJECT_NAME=$project"
    fi
    # Set BASE_PORT for worktree port isolation (skip if Conductor manages ports)
    if ! grep -q '^CONDUCTOR_PORT=' .env 2>/dev/null \
       && [[ -z "${CONDUCTOR_PORT:-}" ]] \
       && ! grep -q '^BASE_PORT=' .env 2>/dev/null; then
        used=$(git worktree list --porcelain \
            | grep '^worktree ' | sed 's/^worktree //' \
            | while read -r wt; do
                grep -m1 '^BASE_PORT=' "$wt/.env" 2>/dev/null || true
              done \
            | sed 's/^BASE_PORT=//' | tr -d '"' | tr -d "'" | sort -n)
        port=9701
        while echo "$used" | grep -qx "$port"; do
            port=$((port + 100))
        done
        echo "BASE_PORT=$port" >> .env
        echo "Set BASE_PORT=$port"
    fi
