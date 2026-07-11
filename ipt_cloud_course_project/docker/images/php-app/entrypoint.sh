#!/bin/bash
# ==========================================
# PHP-App Entrypoint
# Generates .env from template with Docker service names
# ==========================================
set -e

# Generate .env file from template
sed -e "s|\${DB_HOST}|${DB_HOST:-pgbouncer1}|g" \
    -e "s|\${DB_PORT}|${DB_PORT:-6432}|g" \
    -e "s|\${DB_NAME}|${DB_NAME:-project_o}|g" \
    -e "s|\${DB_USER}|${DB_USER:-app_user}|g" \
    -e "s|\${DB_PASS}|${DB_PASS:-app_password}|g" \
    -e "s|\${WS_HOST}|${WS_HOST:-nginx}|g" \
    -e "s|\${WS_PORT}|${WS_PORT:-80}|g" \
    -e "s|\${DEPLOY_DATE}|$(date -u +"%Y-%m-%dT%H:%M:%SZ")|g" \
    /var/www/html/.env.template > /var/www/html/.env

echo "=== Generated .env ==="
cat /var/www/html/.env

exec "$@"
