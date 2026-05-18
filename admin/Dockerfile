FROM oven/bun:1.3.11-alpine AS base

WORKDIR /app



# Development stage with hot reload
FROM base AS dev

COPY config/entrypoint-dev.sh /entrypoint.sh

EXPOSE 5173

ENTRYPOINT [ "/entrypoint.sh" ]
CMD ["bun", "run", "dev", "--host", "0.0.0.0"]



# Dist build stage 1: Build the Vite app with Bun
FROM base AS builder

WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile
COPY . .

RUN bun run build



# Dist build stage 2: Serve the app with Nginx
FROM oven/bun:1.3.11-alpine AS dist
WORKDIR /app

# Install Nginx
RUN apk add --no-cache nginx

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Install tools for entry point
RUN bun add @import-meta-env/cli@0.7.3

# Copy nginx config and entrypoint
COPY config/nginx.conf /etc/nginx/http.d/default.conf.template
COPY config/entrypoint-dist.sh /entrypoint.sh
COPY .env.example .env.example

RUN chmod +x /entrypoint.sh

EXPOSE 8080

CMD ["/entrypoint.sh"]
