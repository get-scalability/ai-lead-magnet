FROM ghcr.io/astral-sh/uv:0.11.1 AS uv-base



FROM python:3.14.3-alpine3.23 AS app-base
ARG TARGETARCH

# Update installed packages
ENV BUILD_VERSION=1
RUN --mount=type=cache,id=apk-$TARGETARCH,sharing=locked,target=/var/cache/apk \
    set -ex; \
    ln -fs /var/cache/apk /etc/apk/cache; \
    apk update; \
    apk upgrade

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV SHELL=/bin/sh
ENV TZ=UTC
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/usr/local/venv

# Install non-dev dependencies (snowflake-connector-python needs build tools)
RUN --mount=from=uv-base,source=/uv,target=/bin/uv \
    --mount=type=cache,id=uv-$TARGETARCH,target=/root/.cache/uv \
    --mount=type=cache,id=apk-$TARGETARCH,sharing=locked,target=/var/cache/apk \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    set -ex; \
    BUILD_DEPS=" \
        build-base \
        linux-headers \
    "; \
    RUN_DEPS=" \
    "; \
    apk update; \
    apk add --virtual .build-deps $BUILD_DEPS $RUN_DEPS; \
    uv sync --frozen --no-group dev --no-install-project; \
    EXTRA_RUN_DEPS="$( \
        scanelf --needed --nobanner --recursive /usr/local/venv \
        | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
        | sort -u \
        | xargs -r apk info --installed \
        | sort -u \
    )"; \
    apk add $EXTRA_RUN_DEPS $RUN_DEPS; \
    apk del .build-deps

ENV PATH="/usr/local/venv/bin:$PATH"
ENV PYTHONPATH=/app

RUN addgroup -S web && adduser -S web -G web



FROM app-base AS app-dev
ARG TARGETARCH

# Install uv on the dev image
COPY --from=uv-base /uv /uvx /bin/

# Install dev dependencies
RUN --mount=type=cache,id=uv-$TARGETARCH,target=/root/.cache/uv \
    --mount=type=cache,id=apk-$TARGETARCH,sharing=locked,target=/var/cache/apk \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    set -ex; \
    BUILD_DEPS=" \
        build-base \
        linux-headers \
    "; \
    RUN_DEPS=" \
    "; \
    apk update; \
    apk add --virtual .build-deps $BUILD_DEPS $RUN_DEPS; \
    uv sync --frozen --group dev --no-install-project; \
    EXTRA_RUN_DEPS="$( \
        scanelf --needed --nobanner --recursive /usr/local/venv \
        | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
        | sort -u \
        | xargs -r apk info --installed \
        | sort -u \
    )"; \
    apk add $EXTRA_RUN_DEPS $RUN_DEPS; \
    apk del .build-deps

USER web
EXPOSE 8080



FROM app-base AS app-dist

COPY app/ /app/app/
COPY mcp_servers/ /app/mcp_servers/
COPY scripts/ /app/scripts/
COPY alembic.ini /app/

USER web
EXPOSE 8080
