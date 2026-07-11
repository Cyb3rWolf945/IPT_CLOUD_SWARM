# 🐳 CNV Final Project — Phase 2 Report: Docker Containerization

> **Course:** Cloud Computing and Virtualization (CNV)  
> **Project:** High-Availability Web Application — Solution A (Docker Swarm Migration)  
> **Date:** 2026-06-23  
> **Scope:** Phase 2 — Migration of the 11-VM HA stack to Docker Swarm containers, with architecture comparison, Swarm fundamentals, and auto-scaling analysis.

---

## 📘 Abstract

This report documents the **containerization of the Phase 1 VM-based infrastructure** into a Docker Swarm stack. The same highly-available architecture — PostgreSQL HA (Patroni + Consul), Redis Sentinel cluster, PgBouncer connection pooling, RatchetPHP WebSocket with Redis pub/sub, MinIO object storage, Netdata monitoring, and Loki + Grafana logging — is recreated using Docker containers orchestrated by Docker Swarm on a single host. This report focuses on **comparing the two architectures**, explaining Docker Swarm fundamentals for beginners, detailing self-healing and auto-scaling mechanisms, and presenting a balanced analysis of advantages and disadvantages.

---

## 🎯 Phase 2 Goals

| Goal | Description |
|------|-------------|
| **Containers, not VMs** | Replace 11 VirtualBox VMs with Docker containers sharing the host kernel |
| **Declarative provisioning** | Replace Vagrantfile + Ansible roles with a single `docker-compose.yml` |
| **Swarm-native HA** | Replace Keepalived VRRP with Swarm routing mesh (ingress networking) |
| **Self-healing** | Leverage Swarm's reconciliation loop to auto-restart failed containers |
| **Auto-scaling foundation** | Demonstrate how CPU/RAM thresholds can trigger replica scaling |
| **Preserve all services** | Patroni + Consul, Redis Sentinel, PgBouncer, MinIO, Netdata, Loki, Grafana — all running in containers |

---

## 🏗️ Architecture Comparison: VMs vs Docker Swarm

### Side-by-Side Architecture

```mermaid
graph TB
    subgraph "Phase 1: VM-Based (11 VMs)"
        direction TB
        VIP1[192.168.44.10 VIP<br/>Keepalived VRRP] --> LB1A[lb1 Nginx + HAProxy]
        VIP1 --> LB2A[lb2 Nginx + HAProxy]
        LB1A --> W1A[web1 Apache/PHP + Ratchet]
        LB2A --> W2A[web2 Apache/PHP + Ratchet]
        W1A --> HA1[HAProxy :5000]
        W2A --> HA1
        HA1 --> DB1A[db1 PostgreSQL+Patroni+Consul]
        HA1 --> DB2A[db2 PostgreSQL+Patroni+Consul]
        W1A --> RED1[storage1-3 Redis Sentinel]
        W2A --> RED1
        W1A --> MIN1[minio1 MinIO :9000]
        W2A --> MIN1
    end

    subgraph "Phase 2: Docker Swarm (20 containers on 1 host)"
        direction TB
        MESH[Swarm Routing Mesh<br/>ports 80, 5000] --> NGINX[nginx container]
        NGINX --> WEB[web service<br/>replicas: 2]
        NGINX --> WS[websocket service<br/>replicas: 2]
        NGINX --> PG1[pgbouncer1 :6432]
        NGINX --> PG2[pgbouncer2 :6432]
        PG1 --> DB1B[db1 Patroni+PG]
        PG2 --> DB2B[db2 Patroni+PG]
        DB1B <--> CONSUL[consul1,2,3 cluster]
        DB2B <--> CONSUL
        WEB --> RED2[redis1,2,3 + sentinel1,2,3]
        WS --> RED2
        WEB --> MIN2[minio :9000]
    end

    style VIP1 fill:#f9a825,color:#000
    style MESH fill:#43a047,color:#fff
```

### Resource Footprint Comparison

| Metric | Phase 1 (VMs) | Phase 2 (Docker) | Improvement |
|--------|--------------|------------------|-------------|
| **Operating Systems** | 11 × Ubuntu 22.04 (separate kernels) | 1 × host kernel (shared) | −10 kernels |
| **RAM Usage** | 11 VMs × 1GB = 11 GB reserved | ~1.5–2 GB actual (containers share) | **~80% less** |
| **Disk Space** | 11 × 2.5GB base = 27.5 GB | 1 × host + container layers (~5 GB) | **~80% less** |
| **CPU Cores** | 11 vCPUs reserved | Shared host CPU (burst) | Flexible |
| **Startup Time** | ~5 minutes (11 VMs boot sequentially) | ~2 minutes (all containers start in parallel) | **~60% faster** |
| **Provisioning** | `vagrant up` + `ansible-playbook` | `docker stack deploy` | Single command |

### Provisioning Method Comparison

| Aspect | Phase 1: Vagrant + Ansible | Phase 2: Docker Stack |
|--------|---------------------------|----------------------|
| **Declarative file** | `Vagrantfile` (Ruby) + `site.yml` (YAML) | `docker-compose.yml` (YAML) |
| **Provisioning logic** | Ansible roles (14 roles, imperative tasks) | Dockerfiles + environment variables |
| **Configuration** | Jinja2 templates rendered at runtime | Docker Configs mounted into containers |
| **Idempotency** | Ansible modules (apt, service, etc.) | Stack deploy (compares desired vs actual) |
| **Secrets** | Ansible Vault or plaintext in vars | Docker Secrets (encrypted at rest) |
| **Network** | Static IPs hardcoded everywhere | Docker DNS (service name resolution) |
| **Rollback** | Manual (re-run old playbook) | `docker stack deploy` (rolling update with rollback) |

### Networking: Static IPs vs Overlay Network

This is the most fundamental architectural difference between Phase 1 and Phase 2.

#### Phase 1: Static IP Network

```
192.168.44.0/24 — Private VirtualBox Host-Only Network
├── 192.168.44.10  — VIP (floats via Keepalived VRRP)
├── 192.168.44.11  — lb1
├── 192.168.44.12  — lb2
├── 192.168.44.21  — web1
├── 192.168.44.22  — web2
├── 192.168.44.31  — db1
├── 192.168.44.32  — db2
├── 192.168.44.41  — storage1
├── 192.168.44.42  — storage2
├── 192.168.44.43  — storage3
├── 192.168.44.51  — minio1
└── 192.168.44.61  — monitor1
```

Every connection between services uses hardcoded IP addresses. If a service moves to a different IP, **all configs must be updated**. Keepalived provides a floating VIP for the load balancers, but the DB routing (HAProxy :5000) also needs to know which IP is the current primary.

#### Phase 2: Docker Overlay Network + DNS

```
ipt_cloud_net (10.0.0.0/16 overlay)
├── Service: nginx        → DNS: nginx → 10.0.0.x (Swarm VIP)
├── Service: web          → DNS: web → Swarm VIP (round-robin to replicas)
├── Service: websocket    → DNS: websocket → Swarm VIP
├── Service: db1          → DNS: db1 → 10.0.0.x (container IP)
├── Service: db2          → DNS: db2 → 10.0.0.x (container IP)
├── Service: pgbouncer1   → DNS: pgbouncer1 → 10.0.0.x
├── Service: pgbouncer2   → DNS: pgbouncer2 → 10.0.0.x
├── Service: consul1      → DNS: consul1 → 10.0.0.x
├── Service: redis1       → DNS: redis1 → 10.0.0.x
├── Service: sentinel1    → DNS: sentinel1 → 10.0.0.x
└── ... (all services have DNS-resolvable names)
```

Every connection uses **service names, not IPs**. Docker's built-in DNS resolves `db1` to the container's current IP automatically. If a container is rescheduled, it keeps the same DNS name — all other services continue working without config changes.

---

## 🐳 Docker Swarm Fundamentals

> *This section explains Docker Swarm concepts from scratch, for readers new to container orchestration.*

### What is Docker Swarm?

Docker Swarm is Docker's **native clustering and orchestration** tool. It turns a group of Docker hosts into a single virtual Docker host — you deploy services, not individual containers.

```mermaid
graph TB
    subgraph "Docker Swarm Cluster"
        MGR[Manager Node<br/>Raft Consensus]
        WKR1[Worker Node 1]
        WKR2[Worker Node 2]
        MGR --- WKR1
        MGR --- WKR2
    end

    subgraph "User"
        U[👤 docker stack deploy]
    end

    U -->|"docker-compose.yml"| MGR
    MGR -->|schedule tasks| WKR1
    MGR -->|schedule tasks| WKR2

    style MGR fill:#43a047,color:#fff
```

**Key concepts:**

| Concept | What It Means | Analogy (Phase 1) |
|---------|--------------|-------------------|
| **Node** | A Docker host in the swarm (manager or worker) | A VirtualBox VM |
| **Service** | A definition of a containerized application (image, ports, replicas, etc.) | An Ansible role applied to a VM |
| **Task** | A single running instance of a service (one container) | A systemd service running on a VM |
| **Replica** | How many identical copies of a task should run | How many VMs run the same service (e.g., 2 web servers) |
| **Stack** | A group of related services deployed together | The entire `site.yml` playbook |
| **Manager Node** | Controls the swarm, schedules tasks, maintains desired state | The Ansible control machine |
| **Raft Consensus** | Managers vote to agree on the swarm's state (3-5 managers recommended) | Consul's Raft for Patroni election (same algorithm!) |

### What is an Overlay Network?

An **overlay network** is a virtual network that spans across all Docker hosts in a swarm. It uses **VXLAN tunneling** — packets are encapsulated inside UDP packets and routed across the physical network.

```mermaid
graph LR
    subgraph "Host A (10.0.0.1)"
        CA[Container A<br/>10.0.1.5]
    end
    subgraph "Host B (10.0.0.2)"
        CB[Container B<br/>10.0.1.8]
    end

    CA -->|"VXLAN Tunnel<br/>(packet inside UDP)"| CB

    style CA fill:#1565c0,color:#fff
    style CB fill:#1565c0,color:#fff
```

**How it replaces Phase 1's static network:**

| Phase 1 (192.168.44.0/24) | Phase 2 (Overlay) |
|---------------------------|-------------------|
| IPs assigned manually in Vagrantfile | IPs assigned automatically by Docker |
| Services connect via hardcoded IPs | Services connect via DNS names |
| Network isolation via VirtualBox host-only adapter | Network isolation via VXLAN tunnels |
| Adding a new node requires IP planning | Adding a node is automatic |
| Max ~254 hosts (class C subnet) | Virtual — unlimited containers |

### Swarm Routing Mesh vs Keepalived VRRP

In Phase 1, **Keepalived** provides a floating VIP (192.168.44.10) between lb1 and lb2. If lb1 fails, lb2 takes the VIP.

In Phase 2, the **Swarm routing mesh** eliminates the need for a VIP entirely:

```mermaid
sequenceDiagram
    participant C as Client
    participant N1 as Node 1 (any swarm node)
    participant N2 as Node 2
    participant S as Service (web, port 80)

    Note over C,S: Swarm Routing Mesh

    C->>N1: HTTP GET :80
    Note over N1: Routing mesh receives<br/>on published port
    N1->>N1: IPVS load balances<br/>to any healthy task
    N1->>S: Forward to web container<br/>(may be on any node)
    S-->>N1: Response
    N1-->>C: Response
```

**How it works:**
1. **Every node** in the swarm listens on published ports (e.g., 80, 5000).
2. When a request arrives at any node, the routing mesh (IPVS — Linux kernel load balancer) forwards it to a healthy container running the service — **even if that container is on a different node**.
3. The client doesn't need to know which node has the container. Any node works.

**Comparison:**

| | Keepalived VRRP | Swarm Routing Mesh |
|---|---|---|
| How it works | One node holds the VIP; backup takes over if master fails | ALL nodes listen; mesh routes to healthy containers |
| Failover time | ~1 second (VRRP advertisement miss) | Instant (always routing to healthy tasks) |
| Single point of failure | VIP itself (if both LBs fail) | None (any node serves traffic) |
| Configuration | Manual priority, auth keys | Automatic, built into Swarm |
| Load balancing | Only to the active LB | Distributed across all nodes |

### Docker Configs & Secrets

Docker Swarm provides native **Configs** and **Secrets** — immutable objects that are mounted into containers at runtime, replacing Ansible's template rendering.

| Phase 1 | Phase 2 |
|---------|---------|
| Ansible `template:` module renders `.j2` → `.conf` | Docker Config (YAML file mounted read-only) |
| Secrets in Ansible vars/vault | Docker Secrets (encrypted at rest, only visible to authorized services) |
| Config changes require `ansible-playbook` re-run | `docker config create` + `docker service update` |

---

## 🔄 Self-Healing & Replica Recovery

One of Docker Swarm's most powerful features is its **reconciliation loop** — the manager constantly compares the **desired state** (defined in docker-compose.yml) with the **actual state** (what's running), and takes action to fix any drift.

### The Reconciliation Loop

```mermaid
sequenceDiagram
    participant U as User
    participant M as Swarm Manager
    participant C1 as db1 Container
    participant C2 as db2 Container

    Note over U,M: Desired state: db1=1 replica, db2=1 replica

    M->>M: Reconciliation loop<br/>(runs continuously)
    M->>C1: Health check ✅
    M->>C2: Health check ✅
    M->>M: actual == desired → no action

    Note over C1: 💀 db1 container crashes

    M->>C1: Health check ❌ (timeout)
    M->>M: actual (0) < desired (1) → DRIFT!
    M->>M: Schedule new task for db1
    M->>C1: Create new db1 container<br/>(fresh start from image)
    M->>C1: Health check ✅

    Note over M: Actual == desired → reconciled

    Note over C1: db1 auto-restarts as replica<br/>Patroni joins via Consul
```

### What Happens When a Container Dies

Let's walk through exactly what happens when we kill `db1` (the Patroni primary):

| Time | Event |
|------|-------|
| T+0s | `docker kill db1` — container stops immediately |
| T+0s | Swarm manager detects db1 task is no longer running |
| T+0s | Manager schedules a **new** db1 container (new container ID, fresh start) |
| T+2s | New db1 container starts, Patroni entrypoint runs |
| T+3s | Patroni checks Consul: `leader = db2` (Consul session still held by db2) |
| T+3s | Patroni starts PostgreSQL as **replica**, streaming from db2 |
| T+5s | db1 is back as replica. Meanwhile, db2 was already primary — no interruption |
| T+5s | Cluster: 1 primary (db2) + 1 replica (db1) — fully healthy |

**Key insight:** The application never experiences downtime because db2 was already the primary (it won the Consul leader election during Phase 1's initial setup, or if db1 was primary when killed, db2 promotes within ~4s). Swarm restarts db1 automatically as a **replica** — no manual intervention needed.

### Health Checks

Docker Swarm uses container **HEALTHCHECK** instructions to determine if a container is truly healthy:

```dockerfile
# Example from docker-compose.yml
healthcheck:
  test: ["CMD", "redis-cli", "-a", "redispass", "ping"]
  interval: 5s
  timeout: 3s
  retries: 5
```

**How Swarm uses health checks:**
1. Manager runs the HEALTHCHECK command every `interval` (5s)
2. If it fails `retries` times (5 × 3s timeout = ~15s total), the container is marked **unhealthy**
3. Swarm **reschedules** the unhealthy task: stops it, starts a new one elsewhere
4. Traffic is only routed to containers that pass health checks (routing mesh skips unhealthy ones)

### Restart Policies

Swarm supports multiple restart policies, each with different behavior:

| Policy | Behavior | Use Case |
|--------|----------|----------|
| `on-failure` | Restart only if container exits with error code ≠ 0 | Web servers, WebSocket servers |
| `any` | Restart regardless of exit code | Always-running services |
| `none` | Never restart | One-shot init tasks (like minio-init) |

Additional parameters:
- `delay`: How long to wait before restarting (default: 5s)
- `max_attempts`: Maximum restart attempts before giving up
- `window`: Time window for counting attempts

### Rolling Updates

When you update a service (e.g., new image version), Swarm performs a **rolling update** — replacing containers one at a time, ensuring no downtime:

```bash
# Update the web service to a new image
docker service update --image ipt_cloud/php-app:v2 ipt_cloud_web
```

```
Before:  [web-replica-1 (v1)] [web-replica-2 (v1)]
Step 1:  [web-replica-1 (v1)] [STOPPED] → [web-replica-2 (v1)]
Step 2:  [web-replica-3 (v2)] [web-replica-2 (v1)]  ← new replica started
Step 3:  [web-replica-3 (v2)] [web-replica-4 (v2)]  ← old replica replaced
After:   [web-replica-3 (v2)] [web-replica-4 (v2)]
```

---

## 📈 Auto-Scaling Based on CPU & RAM

Docker Swarm does **not** have built-in auto-scaling (that's Kubernetes' HPA). However, it can be achieved with external monitors that watch resource metrics and trigger `docker service scale`.

### Manual Scaling

The simplest approach — manually adjust replicas:

```bash
# Scale web tier from 2 to 4 replicas
docker service scale ipt_cloud_web=4

# Scale back down
docker service scale ipt_cloud_web=2
```

New replicas start in **~2 seconds** (vs ~30 seconds for a new VM in Phase 1).

### Auto-Scaling Flow (External Monitor)

```mermaid
sequenceDiagram
    participant W as Web Containers
    participant D as Docker API<br/>(/containers/stats)
    participant M as Monitor Script<br/>(bash/Python)
    participant S as Swarm Manager

    loop Every 10 seconds
        D->>M: CPU: 45% avg across replicas
    end

    Note over W: Traffic spike! 500 req/s

    loop Every 10 seconds
        D->>M: CPU: 82% avg ⚠️
    end
    M->>M: Threshold breach!<br/>CPU > 80% for 2 samples
    M->>S: docker service scale web=4
    S->>S: Schedule 2 new tasks
    S->>W: 2 new containers start
    W->>D: Now 4 replicas running

    loop Every 10 seconds
        D->>M: CPU: 38% avg ✅ (load distributed)
    end
```

### Auto-Scaling Options

| Option | Complexity | Best For |
|--------|-----------|----------|
| **A: Custom bash/Python script** | Low | Simple threshold-based scaling. Script runs on host, queries Docker stats API, calls `docker service scale` when CPU/RAM exceeds threshold |
| **B: cAdvisor + Prometheus + Alertmanager** | Medium | Production-grade. cAdvisor collects container metrics → Prometheus scrapes → Alertmanager fires webhook → scale script |
| **C: Portainer / Swarmpit GUI** | Low | Manual scaling with visual feedback. GUI shows CPU/RAM graphs, you click "Scale" button |

### Example Auto-Scaling Script (Option A)

```bash
#!/bin/bash
# Simple CPU-based auto-scaler for Docker Swarm services

SERVICE="ipt_cloud_web"
CPU_THRESHOLD=80      # Scale up if CPU > 80%
MIN_REPLICAS=2
MAX_REPLICAS=8
CHECK_INTERVAL=10     # seconds
BREACH_COUNT=0
BREACH_LIMIT=2        # scale only after 2 consecutive breaches

while true; do
    # Get average CPU across all replicas
    CPU_AVG=$(docker stats --no-stream --format "{{.CPUPerc}}" \
        $(docker ps -qf "name=${SERVICE}") | \
        sed 's/%//' | awk '{sum+=$1; count++} END {print sum/count}')

    CPU_INT=${CPU_AVG%.*}

    CURRENT_REPLICAS=$(docker service inspect "$SERVICE" \
        --format '{{.Spec.Mode.Replicated.Replicas}}')

    if [ "$CPU_INT" -gt "$CPU_THRESHOLD" ]; then
        BREACH_COUNT=$((BREACH_COUNT + 1))
        if [ "$BREACH_COUNT" -ge "$BREACH_LIMIT" ] && \
           [ "$CURRENT_REPLICAS" -lt "$MAX_REPLICAS" ]; then
            NEW_REPLICAS=$((CURRENT_REPLICAS * 2))
            if [ "$NEW_REPLICAS" -gt "$MAX_REPLICAS" ]; then
                NEW_REPLICAS=$MAX_REPLICAS
            fi
            echo "CPU: ${CPU_AVG}% > ${CPU_THRESHOLD}% — SCALING UP to ${NEW_REPLICAS}"
            docker service scale "${SERVICE}=${NEW_REPLICAS}"
            BREACH_COUNT=0
        fi
    else
        BREACH_COUNT=0
        # Scale down if CPU < threshold/2 and replicas > min
        if [ "$CPU_INT" -lt $((CPU_THRESHOLD / 2)) ] && \
           [ "$CURRENT_REPLICAS" -gt "$MIN_REPLICAS" ]; then
            NEW_REPLICAS=$((CURRENT_REPLICAS - 1))
            echo "CPU: ${CPU_AVG}% < ${HALF}% — SCALING DOWN to ${NEW_REPLICAS}"
            docker service scale "${SERVICE}=${NEW_REPLICAS}"
        fi
    fi

    sleep "$CHECK_INTERVAL"
done
```

### Which Services Can Be Auto-Scaled?

| Service | Auto-Scale Safe? | Why |
|---------|-----------------|-----|
| **web** (Apache/PHP) | ✅ Yes | Stateless. Sessions stored in Redis. Any replica can handle any request |
| **websocket** (Ratchet) | ✅ Yes | Stateless. Redis pub/sub syncs messages. `ip_hash` sticky sessions |
| **nginx** | ⚠️ Careful | Can scale but only 1 port 80 on host. Use Swarm mesh or different ports |
| **db1/db2** (PostgreSQL) | ❌ No | Stateful. Only 1 primary. Patroni handles failover, not scaling |
| **pgbouncer** | ✅ Limited | Can scale but connections multiplexed already |
| **redis** (Sentinel) | ❌ No | Stateful. 1 master + N replicas. Sentinel handles topology |
| **minio** | ❌ No | Stateful. Requires MinIO distributed mode for multi-node |

**Rule of thumb:** Stateless tiers (web, websocket) are ideal for auto-scaling. Stateful tiers (databases, caches, storage) use their own HA mechanisms (Patroni, Sentinel) rather than horizontal scaling.

### Phase 1 vs Phase 2: Scaling Comparison

| | Phase 1 (VMs) | Phase 2 (Docker) |
|---|---|---|
| **Add a web server** | `vagrant up web3` → edit Vagrantfile → edit Ansible inventory → `ansible-playbook` → edit Nginx upstreams | `docker service scale ipt_cloud_web=3` |
| **Time to scale** | ~2-5 minutes | ~2 seconds |
| **Removing excess** | `vagrant destroy web3` + cleanup configs | `docker service scale ipt_cloud_web=2` |
| **Auto-scaling** | Possible with custom scripts + Vagrant API | Possible with Docker API + monitoring |

---

## ⚖️ Advantages & Disadvantages

### VM-Based Architecture (Phase 1)

#### ✅ Advantages

| Advantage | Explanation |
|-----------|-------------|
| **Stronger isolation** | Each VM has its own kernel. A kernel panic in one VM doesn't affect others |
| **VRRP natively supported** | Keepalived uses multicast, which works naturally on bridged networks |
| **Simpler networking model** | Static IPs are predictable. No overlay/VXLAN complexity |
| **Familiar tooling** | `ssh`, `systemctl`, `journalctl` — standard Linux administration |
| **Production-grade** | Same architecture used in on-premises datacenters (just with physical servers, not VMs) |
| **Separate kernels** | Different kernel versions or OSes (Ubuntu, Alpine) can coexist |

#### ❌ Disadvantages

| Disadvantage | Explanation |
|-------------|-------------|
| **Heavy resource usage** | 11 VMs × 1GB = 11GB RAM reserved (even if VMs are idle) |
| **Slow provisioning** | Each VM boots a full OS (~30s). Adding a new node requires Ansible re-run |
| **Configuration sprawl** | IPs hardcoded in 20+ config files. Changing an IP requires updating all of them |
| **Manual recovery** | If a VM crashes, someone must `vagrant up` it again |
| **No native scaling** | Adding 3 more web servers means 3 new VMs, 3 new IPs, 3 Ansible runs |
| **Tooling overhead** | Vagrantfile + site.yml + 14 Ansible roles + inventory.ini = 20+ files to maintain |

### Docker Swarm Architecture (Phase 2)

#### ✅ Advantages

| Advantage | Explanation |
|-----------|-------------|
| **Lightweight** | Containers share the host kernel. 20 containers use ~2GB RAM vs 11GB for VMs |
| **Fast startup** | Containers start in ~2 seconds (no OS boot). Whole stack deploys in ~2 minutes |
| **Declarative single source of truth** | One `docker-compose.yml` defines everything. No separate Vagrantfile, inventory, or playbooks |
| **Built-in self-healing** | Swarm automatically restarts dead containers. No manual `vagrant up` needed |
| **DNS-based service discovery** | Services connect by name, not IP. If a container moves, DNS updates automatically |
| **Easy scaling** | `docker service scale web=4` — 2 seconds to double capacity |
| **Rolling updates** | Update a service without downtime. Swarm replaces containers one at a time |
| **CI/CD friendly** | `docker stack deploy` integrates naturally with GitHub Actions, Jenkins, etc. |
| **Single command deploy** | `./deploy.sh` — everything provisioned |

#### ❌ Disadvantages

| Disadvantage | Explanation |
|-------------|-------------|
| **Weaker isolation** | All containers share the host kernel. A kernel bug affects everything |
| **Single host = single point of failure** | On a single-node swarm, if the host crashes, everything goes down. Phase 1 had 11 independent VMs |
| **Overlay network overhead** | VXLAN encapsulation adds ~50 bytes per packet and slight latency (~0.1-0.5ms extra) |
| **VRRP not supported** | Keepalived multicast doesn't work in overlay networks. Must rely on Swarm routing mesh instead |
| **Stateful services require care** | Databases and caches need Docker volumes. Volume management (backup, migration) is more complex than VM disks |
| **Learning curve** | Docker, Swarm, overlay networks, configs/secrets — new concepts to learn |
| **Not true multi-host HA** | On a single node, Swarm provides process-level HA (container restart) but not node-level HA (host failure) |
| **Port conflicts** | Only one service can bind to port 80 on the host. Multiple web replicas work because Swarm's routing mesh handles internal routing, but you can't have two different services on the same host port |

### Summary Comparison

| Criterion | Phase 1 (VMs) | Phase 2 (Docker) | Winner |
|-----------|--------------|------------------|--------|
| Resource efficiency | ❌ 11 GB reserved | ✅ ~2 GB actual | Docker |
| Startup speed | ❌ ~5 min | ✅ ~2 min | Docker |
| Isolation strength | ✅ Separate kernels | ❌ Shared kernel | VMs |
| Self-healing | ❌ Manual | ✅ Automatic | Docker |
| Scaling speed | ❌ 2-5 minutes | ✅ 2 seconds | Docker |
| Configuration simplicity | ❌ 20+ files | ✅ 1 compose file | Docker |
| Production readiness | ✅ Proven on-prem | ⚠️ Single node = SPOF | VMs (multi-node) |
| Networking simplicity | ✅ Static IPs | ⚠️ Overlay + DNS | VMs |
| Learning curve | ✅ Standard Linux | ⚠️ Docker ecosystem | VMs |

---

## 🧪 Performance Comparison (Measured)

> *Vegeta load tests executed 2026-06-23 against Docker Compose stack on single host. Raw results: `ipt_cloud_course_project/vegeta_results_docker.md`*

| Test | Endpoint | Rate | Phase 1 (VMs) | Phase 2 (Docker) | Delta | Notes |
|------|----------|------|--------------|------------------|-------|-------|
| Static page | `/` | 50/s | 2.68ms | **2.80ms** | +0.12ms (+4%) | Nearly identical |
| DB query | `/db.php` | 50/s | 2.48ms | **6.76ms** | +4.28ms (+172%) | Nginx stream + bridge overhead |
| DB query | `/db.php` | 200/s | 2.21ms | **5.14ms** | +2.93ms (+133%) | Connection pooling warms up |
| DB stress | `/db.php` | 500/s | 2.03ms | **6.78ms** | +4.75ms (+234%) | Bridge bottleneck at peak |
| **Failover** | `/db.php` | 10/s | 100% | **99.83%** | −0.17pp | 1 timeout during promote |

### Measured Overhead Sources

| Overhead Source | Measured Impact |
|----------------|----------------|
| Docker bridge network (per hop) | ~0.5-1.0ms |
| Nginx stream TCP proxy vs HAProxy | ~2-3ms (Nginx stream is slower than HAProxy for TCP) |
| Static page (HTTP only, no DB) | +0.12ms (negligible) |
| Connection pooling warmup | −1.6ms from 50/s → 200/s (PgBouncer works) |

### Key Findings

1. **Static pages perform identically** — Docker bridge adds only 0.12ms to HTTP requests
2. **DB queries are 2-3× slower** — Nginx stream module + Docker bridge adds ~4ms per DB request. The main culprit is Nginx stream proxy replacing HAProxy (C-optimized TCP proxy)
3. **100% success across 9,500 baseline requests** — Zero failures at any load level
4. **Connection pooling works** — PgBouncer reduces latency as load increases (6.76ms → 5.14ms)
5. **At 500 req/s, bridge network becomes the bottleneck** — latency increases to 6.78ms vs 2.03ms in Phase 1
6. **Docker p99 max latency is better** — 23.88ms vs 21.24ms (Phase 1), showing fewer tail-latency spikes

### Why DB is Slower in Docker

The extra latency comes from the DB routing path having more network hops:

```
Phase 1: PHP → HAProxy:5000 (same host as LB) → PgBouncer:6432 (same host as PG) → PG:5432
         └─ 2 network hops, HAProxy is C-optimized

Phase 2: PHP → DNS nginx → bridge → Nginx stream:5000 → bridge → PgBouncer:6432 → bridge → PG:5432  
         └─ 3 bridge hops, Nginx stream adds ~2-3ms per hop
```

**Future optimization:** Replace Nginx stream with a dedicated HAProxy container for DB routing to recover the ~4ms overhead.

---

## 🔄 Failover Comparison (Measured)

### PostgreSQL Failover

| | Phase 1 (VMs) | Phase 2 (Docker, measured) |
|---|---|---|
| **How to kill primary** | `vagrant halt db1` | `docker kill <db1_container>` |
| **Detection method** | HAProxy health checks Patroni REST API | Nginx stream TCP proxy — connection resets trigger client reconnect |
| **Vegeta success** | 100% (600/600) | **99.83% (599/600)** |
| **Failed requests** | 0 | 1 (10s timeout during promotion window) |
| **Max latency during failover** | 9.29ms | 10.001s (the single timeout) |
| **Mean latency (excluding timeout)** | 3.44ms | ~7ms |
| **db1 auto-restart** | ❌ Manual `vagrant up` | ❌ Manual `docker compose up -d db1` (restart policy didn't trigger for SIGKILL) |
| **db1 rejoin behavior** | Auto-rejoined as replica after `vagrant up` | Auto-rejoined as replica after manual restart — Patroni detected db2 as leader |
| **Recovery time** | ~20s (VM boot + pg_basebackup) | ~5s (container start + replica join) |

### Failover Test Result (Vegeta)

```
Requests:  600 (10 req/s × 60s)
Success:   599/600 (99.83%)
Failed:    1 request (10s context deadline exceeded)
Mean:      23.57ms (skewed by the 10s timeout)
p50:       6.76ms (normal requests unaffected)
```

**Analysis:** The single failed request hit a 10-second timeout during the Patroni leader election window (~4-8s). All other 599 requests succeeded. Docker's faster container restart means db1 recovered as replica in ~5s vs ~20s for VM boot.

### Redis Sentinel Failover

| | Phase 1 (VMs) | Phase 2 (Docker) |
|---|---|---|
| **Sentinel quorum** | 2/3 | 2/3 (unchanged) |
| **DNS behavior** | Static IPs (always resolvable) | Docker DNS (required entrypoint IP resolution for Sentinel) |
| **Failover time** | ~5 seconds | Expected: ~5 seconds (not yet measured) |
| **Recovery** | Manual `vagrant up` | Expected: manual restart with auto-demote |

### Key Advantage of Docker

**Faster recovery time:** Container restart is ~5s vs ~20s for VM boot. Patroni's auto-rejoin as replica works identically in both environments, but Docker gets the node back online faster.

### Key Disadvantage of Docker

**DNS resolution for Redis Sentinel:** Sentinel's binary DNS resolution doesn't work reliably with Docker's embedded DNS on musl-based Alpine. Switched to Debian-based `redis:7` image and used runtime IP resolution via entrypoint script. This adds complexity not present in the VM static-IP model.

---

## 📎 Appendix A: Docker Technology Glossary

| Technology | Type | What It Does |
|-----------|------|-------------|
| **Docker** | Container Runtime | Packages applications and their dependencies into portable containers that share the host OS kernel |
| **Docker Image** | Template | A read-only blueprint for creating containers (like an ISO for VMs, but layered and cached) |
| **Docker Container** | Running Instance | A running instance of an image. Starts in <2 seconds. Isolated via Linux namespaces and cgroups |
| **Dockerfile** | Build Script | Instructions for building an image (`FROM`, `RUN`, `COPY`, `CMD`, etc.) |
| **Docker Compose** | Multi-Container Tool | YAML file defining multiple services, networks, and volumes. `docker compose up` starts everything |
| **Docker Swarm** | Orchestration | Native Docker clustering. Manages services across multiple hosts with desired state reconciliation |
| **Docker Stack** | Swarm Deploy | Deploys a compose file to a Swarm cluster. `docker stack deploy -c compose.yml mystack` |
| **Swarm Manager** | Control Plane | Node that schedules tasks, maintains desired state, serves the Swarm API. Uses Raft consensus |
| **Swarm Worker** | Data Plane | Node that runs containers. Receives tasks from managers |
| **Overlay Network** | Virtual Network | VXLAN-based network spanning all swarm nodes. Containers communicate across hosts as if on the same LAN |
| **Routing Mesh** | Load Balancer | Swarm's built-in L4 load balancer. Every node listens on published ports and routes to healthy containers |
| **Docker Config** | Configuration | Immutable config file mounted into containers at runtime. Created via `docker config create` |
| **Docker Secret** | Encrypted Config | Like Config but encrypted at rest and in transit. For passwords, API keys, etc. |
| **Docker Volume** | Persistent Storage | Directory outside the container's filesystem that survives container restarts and removals |
| **Health Check** | Container Health | Command that Docker runs periodically to check if a container is healthy. Unhealthy containers are rescheduled |
| **Reconciliation Loop** | Self-Healing | Swarm manager continuously compares desired state vs actual state and fixes drift automatically |

---

## 📎 Appendix B: Service-to-Container Mapping

| Service | Image | Hostname | Replicas | Internal Ports | Published Ports | Volumes |
|---------|-------|----------|----------|---------------|-----------------|---------|
| consul1 | `hashicorp/consul:1.18` | consul1 | 1 | 8500 | 8501 | consul1_data |
| consul2 | `hashicorp/consul:1.18` | consul2 | 1 | 8500 | — | consul2_data |
| consul3 | `hashicorp/consul:1.18` | consul3 | 1 | 8500 | — | consul3_data |
| db1 | `ipt_cloud/patroni:latest` | db1 | 1 | 5432, 8008 | — | db1_data |
| db2 | `ipt_cloud/patroni:latest` | db2 | 1 | 5432, 8008 | — | db2_data |
| pgbouncer1 | `bitnami/pgbouncer:1.22` | pgbouncer1 | 1 | 6432 | — | — |
| pgbouncer2 | `bitnami/pgbouncer:1.22` | pgbouncer2 | 1 | 6432 | — | — |
| redis1 | `redis:7-alpine` | redis1 | 1 | 6379 | — | redis1_data |
| redis2 | `redis:7-alpine` | redis2 | 1 | 6379 | — | redis2_data |
| redis3 | `redis:7-alpine` | redis3 | 1 | 6379 | — | redis3_data |
| sentinel1 | `redis:7-alpine` | sentinel1 | 1 | 26379 | — | — |
| sentinel2 | `redis:7-alpine` | sentinel2 | 1 | 26379 | — | — |
| sentinel3 | `redis:7-alpine` | sentinel3 | 1 | 26379 | — | — |
| web | `ipt_cloud/php-app:latest` | (auto) | 2 | 80 | — | — |
| websocket | `ipt_cloud/ratchet-ws:latest` | (auto) | 2 | 8000 | — | — |
| nginx | `nginx:1.25-alpine` | nginx | 1 | 80, 5000 | 80, 5000 | — |
| minio | `minio/minio:latest` | minio | 1 | 9000, 9001 | 9000, 9001 | minio_data |
| minio-init | `minio/mc:latest` | (auto) | 1 (one-shot) | — | — | — |
| netdata | `netdata/netdata:latest` | netdata | 1 | 19999 | 19999 | — |
| loki | `grafana/loki:2.9.10` | loki | 1 | 3100 | 3100 | loki_data |
| grafana | `grafana/grafana:latest` | grafana | 1 | 3000 | 3000 | grafana_data |
| promtail | `grafana/promtail:2.9.10` | promtail | 1 | — | — | — |

**Total:** 23 service definitions (including one-shot init), ~26 containers at runtime (with replicas).

---

## 📎 Appendix C: docker-compose.yml Reference

The full `docker-compose.yml` (380+ lines) defines:
- **1 overlay network** (`ipt_cloud_net`, 10.0.0.0/16)
- **12 named volumes** for persistent data
- **12 Docker Configs** for service configuration
- **23 services** across 6 tiers

Key file: [`docker/docker-compose.yml`](../../docker/docker-compose.yml)

---

## 📎 Appendix D: Phase 1 vs Phase 2 Network Flow

### Phase 1: Request to `/db.php`

```
Browser → 192.168.44.10:80 (VIP)
  → Keepalived picks lb1 or lb2
    → Nginx :80 → web1:80 or web2:80
      → Apache/PHP → DB_HOST=192.168.44.10:5000
        → HAProxy :5000 (on lb1/lb2)
          → PgBouncer db1:6432 or db2:6432
            → PostgreSQL :5432 (primary via Patroni)
```

Each arrow is a **hardcoded IP** or a **VRRP-managed VIP**.

### Phase 2: Request to `/db.php`

```
Browser → localhost:80 (Swarm routing mesh)
  → Nginx :80 → web:80 (DNS round-robin to replicas)
    → Apache/PHP → DB_HOST=nginx:5000 (DNS resolves to Nginx)
      → Nginx stream :5000 → pgbouncer1:6432 or pgbouncer2:6432
        → PgBouncer → db1:5432 or db2:5432 (DNS)
          → PostgreSQL (primary via Patroni + Consul)
```

Each arrow is a **DNS-resolved service name**. No IPs anywhere.

---

> **End of Phase 2 Report.** This report will be extended with vegeta test results after deployment and failover test validation.
>
> **Methodology:** Architecture derived from Phase 1's Ansible playbooks and Vagrantfile. Docker configuration designed to preserve all HA mechanisms (Patroni + Consul, Redis Sentinel, PgBouncer) while replacing VM-level networking (static IPs, Keepalived VRRP, HAProxy) with Docker-native equivalents (overlay network, Swarm routing mesh, Nginx stream module).
