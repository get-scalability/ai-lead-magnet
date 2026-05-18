#!/bin/sh
set -e

# Inject runtime env vars into built assets (reads var names from .env.example)
bunx --bun import-meta-env --example .env.example

# Render nginx config from template — only substitutes ${API_URL}, leaving nginx
# variables like $host and $uri untouched
export API_URL="${API_URL:-http://api:8000}"
envsubst '${API_URL}' \
    < /etc/nginx/http.d/default.conf.template \
    > /etc/nginx/http.d/default.conf

exec nginx -g "daemon off;"
