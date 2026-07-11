#!/bin/bash
# ================================================================
# deploy.sh — Docker Swarm Stack Deployment
# Initializes Swarm, builds images, deploys the stack
# ================================================================
set -e
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
STACK_NAME="ipt_cloud"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

echo "==============================================="
echo "  IPT Cloud — Phase 2: Docker Swarm Deployment"
echo "==============================================="
echo ""

# ─── 1. Check Docker ────────────────────────────────────────────
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed."
    exit 1
fi

echo "[1/5] Checking Docker Swarm status..."
if ! docker info --format '{{.Swarm.LocalNodeState}}' 2>/dev/null | grep -q "active"; then
    echo "  → Initializing Docker Swarm..."
    docker swarm init 2>/dev/null || {
        echo "  → Swarm already initialized or error. Continuing..."
    }
else
    echo "  → Swarm is active."
fi

# ─── 2. Load env ────────────────────────────────────────────────
echo ""
echo "[2/5] Loading environment variables..."
if [ -f "$ROOT_DIR/.env" ]; then
    set -a
    source "$ROOT_DIR/.env"
    set +a
    echo "  → .env loaded."
else
    echo "  → WARNING: .env not found, using defaults."
fi

# ─── 3. Build custom images ─────────────────────────────────────
echo ""
echo "[3/5] Building custom Docker images..."
cd "$ROOT_DIR/.."

echo "  → Building ipt_cloud/patroni..."
docker build -t ipt_cloud/patroni:latest -f docker/images/patroni/Dockerfile . 2>&1 | tail -3

echo "  → Building ipt_cloud/php-app..."
docker build -t ipt_cloud/php-app:latest -f docker/images/php-app/Dockerfile . 2>&1 | tail -3

echo "  → Building ipt_cloud/ratchet-ws..."
docker build -t ipt_cloud/ratchet-ws:latest -f docker/images/ratchet-ws/Dockerfile . 2>&1 | tail -3

# ─── 4. Deploy stack ────────────────────────────────────────────
echo ""
echo "[4/5] Deploying stack '$STACK_NAME'..."
docker stack deploy -c "$COMPOSE_FILE" "$STACK_NAME"

echo ""
echo "  → Waiting for services to initialize (30s)..."
sleep 30

# ─── 5. Check status ────────────────────────────────────────────
echo ""
echo "[5/5] Stack Status:"
echo "==============================================="
docker stack services "$STACK_NAME" --format "table {{.Name}}\t{{.Replicas}}\t{{.Image}}"

echo ""
echo "==============================================="
echo "  Deployment complete!"
echo ""
echo "  🌐 Web App:      http://localhost/"
echo "  🐳 Portainer:    http://localhost:9000/"
echo "  📊 Netdata:      http://localhost:19999/"
echo "  📈 Grafana:      http://localhost:3000/ (anonymous access)"
echo "  🗄️  MinIO Console: http://localhost:9001/ (admin / ipt_cloud_2026)"
echo "  🔍 Consul UI:    http://localhost:8501/"
echo ""
echo "  Run vegeta tests:"
echo "    echo 'GET http://localhost/' | vegeta attack -duration=30s -rate=50 | vegeta report"
echo "    echo 'GET http://localhost/db.php' | vegeta attack -duration=30s -rate=50 | vegeta report"
echo ""
echo "  To tear down:"
echo "    docker stack rm $STACK_NAME"
echo "==============================================="
