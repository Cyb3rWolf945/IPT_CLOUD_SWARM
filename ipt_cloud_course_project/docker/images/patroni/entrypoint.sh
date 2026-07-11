#!/bin/bash
# ==========================================
# Patroni + PostgreSQL Entrypoint
# Starts Patroni which manages PostgreSQL
# ==========================================
set -e

# Substitute environment variables in the Patroni config template
CONFIG_FILE="/etc/patroni/patroni.yml"

# Retrieve the current container's IP address
MY_IP=$(hostname -i | awk '{print $1}')

# Generate the config from template
sed -e "s|\${HOSTNAME}|${HOSTNAME}|g" \
    -e "s|\${MY_IP}|${MY_IP}|g" \
    -e "s|\${PATRONI_SCOPE}|${PATRONI_SCOPE:-project_o_cluster}|g" \
    -e "s|\${PATRONI_NAMESPACE}|${PATRONI_NAMESPACE:-/db/}|g" \
    -e "s|\${PATRONI_RESTAPI_PORT}|${PATRONI_RESTAPI_PORT:-8008}|g" \
    -e "s|\${CONSUL_HOST}|${CONSUL_HOST:-consul1}|g" \
    -e "s|\${CONSUL_PORT}|${CONSUL_PORT:-8500}|g" \
    -e "s|\${DB_USER}|${DB_USER:-app_user}|g" \
    -e "s|\${DB_PASS}|${DB_PASS:-app_password}|g" \
    -e "s|\${REPLICATOR_PASS}|${REPLICATOR_PASS:-replicator_pass}|g" \
    -e "s|\${PG_DATA_DIR}|${PG_DATA_DIR:-/var/lib/postgresql/data}|g" \
    -e "s|\${PG_BIN_DIR}|${PG_BIN_DIR:-/usr/lib/postgresql/14/bin}|g" \
    /etc/patroni/patroni.yml.template > "$CONFIG_FILE"

echo "=== Patroni Configuration ==="
cat "$CONFIG_FILE"
echo "=============================="

# Initialize DB if data directory is empty (first boot)
if [ ! -f "${PG_DATA_DIR:-/var/lib/postgresql/data}/PG_VERSION" ]; then
    echo "First boot: initializing PostgreSQL data directory..."
    # Patroni will handle initdb on first start
fi

# Drop to postgres user to run Patroni
exec su -s /bin/bash postgres -c "patroni $CONFIG_FILE"
