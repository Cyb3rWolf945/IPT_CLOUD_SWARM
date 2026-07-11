# 🐳 Phase 2 — Docker Containerization

> **IPT Cloud Course — Final Project**  
> **Date:** 2026-06-23  
> **Stack:** Docker Swarm (single-node) replicating the 11-VM Phase 1 infrastructure

---

## 🚀 Quick Start

```bash
# Initialize Swarm + build images + deploy stack
./scripts/deploy.sh

# Or do it manually:
docker swarm init
docker build -t ipt_cloud/patroni:latest -f images/patroni/Dockerfile ..
docker build -t ipt_cloud/php-app:latest -f images/php-app/Dockerfile ..
docker build -t ipt_cloud/ratchet-ws:latest -f images/ratchet-ws/Dockerfile ..
docker stack deploy -c docker-compose.yml ipt_cloud

# Check services
docker stack services ipt_cloud

# View logs
docker service logs ipt_cloud_web
docker service logs ipt_cloud_db

# Tear down
docker stack rm ipt_cloud
```

---

## 📁 Structure

```
docker/
├── docker-compose.yml          # Main Swarm stack definition (20 services)
├── .env                        # Environment variables
├── Dockerfile                  # (in images/ subdirs)
├── configs/                    # Service configuration files
│   ├── nginx.conf              # Nginx reverse proxy (HTTP + Stream/TCP)
│   ├── apache.conf             # Apache VirtualHost
│   ├── consul.hcl              # Consul agent config (3-node cluster)
│   ├── pgbouncer.ini           # PgBouncer connection pooler
│   ├── pgbouncer-users.txt     # PgBouncer user credentials
│   ├── redis-master.conf       # Redis master config
│   ├── redis-replica.conf      # Redis replica config
│   ├── sentinel.conf           # Redis Sentinel config
│   ├── loki-config.yaml        # Loki log aggregator
│   ├── grafana-datasources.yaml # Grafana Loki datasource
│   ├── promtail-config.yaml    # Promtail log shipper
│   └── app.env.template        # PHP app .env template
├── images/
│   ├── patroni/                # PostgreSQL 14 + Patroni (Consul DCS)
│   │   ├── Dockerfile
│   │   ├── entrypoint.sh
│   │   └── patroni.yml.j2      # Patroni config template
│   ├── php-app/                # Apache + PHP 8.1
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   └── ratchet-ws/             # RatchetPHP WebSocket server
│       ├── Dockerfile
│       └── websockets_server.php
└── scripts/
    └── deploy.sh               # One-command deployment
```

---

## 🏗️ Architecture

### Service Map (VM → Docker)

| Phase 1 VM | IP | Docker Service | Type | Notes |
|-----------|-----|---------------|------|-------|
| lb1, lb2 | .11, .12 | **nginx** | Reverse Proxy | HTTP :80 + Stream :5000 (replaces Keepalived + HAProxy) |
| web1, web2 | .21, .22 | **web** (×2 replicas) | Apache/PHP | Swarm replica scaling |
| web1, web2 | .21, .22 | **websocket** (×2 replicas) | RatchetPHP :8000 | Redis pub/sub sync |
| db1, db2 | .31, .32 | **db** (×2 replicas) | PostgreSQL+Patroni | Consul DCS for leader election |
| db1, db2 | .31, .32 | **pgbouncer** (×2 replicas)| PgBouncer :6432 | Connection pooling |
| (co-located) | — | **consul** (×3 replicas) | Consul Cluster | 3-node quorum for Patroni DCS |
| storage1-3 | .41-.43 | **redis-master, redis-replica** | Redis Cluster | 1 master + 2 replicas |
| storage1-3 | .41-.43 | **sentinel** (×3 replicas) | Redis Sentinel | Quorum=2, monitors redis-master |
| minio1 | .51 | **minio** | Object Storage | :9000 API + :9001 Console |
| monitor1 | .61 | **netdata** | Monitoring | Parent mode, monitors Docker host |
| monitor1 | .61 | **portainer** | Docker GUI | :9000, Swarm management |
| monitor1 | .61 | **loki** | Log Aggregator | :3100, 7-day retention |
| monitor1 | .61 | **grafana** | Dashboards | :3000, Loki datasource |
| monitor1 | .61 | **promtail** | Log Shipper | Scrapes Docker container logs |

### Network

- **Overlay network**: `ipt_cloud_net` (10.0.0.0/16)
- Service discovery: Docker DNS (`db1` resolves to container IP)
- Swarm routing mesh: published ports (80, 5000, etc.) reachable on any node
- Keepalived VRRP → Replaced by Swarm ingress networking (no floating VIP needed)

### Key Differences from Phase 1

| Aspect | Phase 1 (VMs) | Phase 2 (Docker) |
|--------|--------------|------------------|
| **Provisioning** | Vagrant + Ansible (SSH) | `docker stack deploy` (declarative) |
| **HA/Failover** | Keepalived VRRP + HAProxy | Swarm routing mesh + Nginx stream |
| **Service Discovery** | Static IPs + Consul | Docker DNS + Consul (for Patroni only) |
| **Scaling** | Manual `vagrant up` new VM | `docker service scale web=4` |
| **Self-healing** | systemd on each VM | Swarm reconciliation loop |
| **Netdata** | Agent on every VM | Single parent (Docker host metrics) |
| **Promtail** | Agent on every VM | Single instance (Docker log scraper) |
| **Resource usage** | 11 VMs × 1GB = 11GB | ~20 containers sharing host kernel |
| **Startup time** | ~5 min (11 VMs boot) | ~2 min (all containers) |

---

## 🛠️ Manual Commands

```bash
# Scale web tier
docker service scale ipt_cloud_web=4

# Check logs for a specific service
docker service logs ipt_cloud_db

# Inspect a service
docker service inspect ipt_cloud_web

# Restart a service
docker service update --force ipt_cloud_web

# Monitor resource usage
docker stats

# Check Consul cluster
curl http://localhost:8501/v1/status/leader

# Check Patroni leader
curl http://localhost:8008/primary   # via db's port (if published)

# Test Redis Sentinel
docker exec $(docker ps -qf "name=ipt_cloud_sentinel") redis-cli -p 26379 SENTINEL master mymaster
```

---

## 🧪 Load Testing

```bash
# Install vegeta
wget https://github.com/tsenart/vegeta/releases/download/v12.12.0/vegeta_12.12.0_linux_amd64.tar.gz
tar xzf vegeta_12.12.0_linux_amd64.tar.gz

# Run tests
echo "GET http://localhost/" | ./vegeta attack -duration=30s -rate=50 | ./vegeta report
echo "GET http://localhost/db.php" | ./vegeta attack -duration=30s -rate=500 | ./vegeta report
```

---

## 🧹 Cleanup

```bash
docker stack rm ipt_cloud
docker volume prune -f    # Remove all unused volumes (WARNING: deletes DB data!)
docker swarm leave --force
```
