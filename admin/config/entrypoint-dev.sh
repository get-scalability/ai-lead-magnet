#!/bin/sh
set -e

if [ ! -d node_modules ]; then
    bun install
fi

exec "$@"
