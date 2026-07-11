# 📊 08 — Loki + Grafana — Centralized Logging

> **Data:** 2026-06-23  
> **Adição:** Loki (log aggregator) + Grafana (dashboard) no `monitor1`, Promtail agents em todas as 11 VMs

---

## Diagramas

| Diagrama | Descrição |
|----------|-----------|
| [01_architecture_loki.mermaid](01_architecture_loki.mermaid) | Arquitetura completa com fluxos de logs (Promtail → Loki) + métricas (Netdata) + dashboards |
| [02_loki_log_flow.mermaid](02_loki_log_flow.mermaid) | Fluxo detalhado: scrape → push → store → query → dashboard |

---

## O Que Adicionámos

| Antes | Depois |
|-------|--------|
| Logs só via SSH + `journalctl`/`tail` | Logs centralizados com pesquisa por VM, tier e texto livre |
| Sem dashboard de logs | Grafana Explore — filtrar `{host="web1"}` e ver logs em tempo real |
| Diagnóstico manual (VM a VM) | Todos os logs de 11 VMs num só Grafana |
| Sem retenção de logs | 7 dias de retenção automática no Loki |

---

## VMs Modificadas

| VM | IP | Alteração |
|----|----|-----------|
| monitor1 | 192.168.44.61 | **Loki** (log aggregator, :3100) + **Grafana** (dashboard, :3000) + **Promtail** (agent, logs locais) |
| lb1, lb2 | .11, .12 | Promtail — Nginx access/error logs → Loki |
| web1, web2 | .21, .22 | Promtail — Apache access/error logs → Loki |
| db1, db2 | .31, .32 | Promtail — PostgreSQL logs → Loki |
| storage1-3 | .41-43 | Promtail — Redis + Sentinel logs → Loki |
| minio1 | .51 | Promtail — MinIO logs → Loki |

---

## Como Funciona

1. **Promtail agent** instalado em cada VM (via Ansible role `promtail`)
2. Cada agente lê logs específicos do serviço que corre na VM (ex: Nginx nos LBs, PostgreSQL nos DBs)
3. Promtail etiqueta cada linha com `host={{ inventory_hostname }}` e `tier=<grupo>`
4. Logs são enviados para **Loki** em `monitor1:3100` via HTTP POST
5. **Loki** armazena logs em chunks no disco (`/var/lib/loki/`), com índice TSDB, 7 dias de retenção
6. **Grafana** (provisionado com datasource Loki) lê os logs e mostra no Explore
7. Utilizador acede a `http://192.168.44.10/grafana/` via VIP + Nginx proxy

---

## Configuração

| Componente | Parâmetro | Valor |
|-----------|-----------|-------|
| **Loki** | Port | 3100 |
| | Storage | Filesystem (`/var/lib/loki/`) |
| | Index | TSDB (v13 schema) |
| | Retention | 7 dias (168h) |
| | Replication factor | 1 (single node) |
| **Grafana** | Port | 3000 |
| | Datasource | Loki → `http://localhost:3100` |
| | Proxy sub-path | `/grafana/` (via Nginx VIP) |
| | Anonymous access | Enabled (viewer) |
| **Promtail** | Push URL | `http://192.168.44.61:3100/loki/api/v1/push` |
| | Labels | `host`, `tier`, `job` |
| | Log paths | Per-tier (ver tabela abaixo) |
| | Batch interval | Default (5s or 1MB) |

### Per-Tier Log Sources

| Tier | Log Paths |
|------|-----------|
| loadbalancers | `/var/log/nginx/access.log`, `/var/log/nginx/error.log` |
| webservers | `/var/log/apache2/access.log`, `/var/log/apache2/error.log` |
| databases | `/var/log/postgresql/postgresql-14-main.log` |
| redis_cluster | `/var/log/redis/redis-server.log`, `/var/log/redis/redis-sentinel.log` |
| minio | `/var/log/minio/minio.log` |
| monitoring | `/var/log/netdata/*.log`, `/var/log/grafana/grafana.log`, `/var/log/loki/loki.log` |
| **All VMs** | `/var/log/syslog`, `/var/log/auth.log` (built-in) |

---

## Como Usar

1. Aceder a `http://192.168.44.10/grafana/` no browser
2. Sidebar → **Explore** → selecionar datasource **Loki**
3. Filtrar por VM: `{host="web1"}`
4. Filtrar por tier: `{tier="databases"}`
5. Pesquisa livre: `{host="db1"} |= "ERROR"`
6. Ver logs em tempo real (Live mode)

---

## Total de VMs: 11 (sem alteração)

```
lb1, lb2           — Load Balancers + Netdata agents + Promtail
web1, web2         — Web Applications + Netdata agents + Promtail
db1, db2           — Databases Patroni HA + Netdata agents + Promtail
storage1-3         — Redis Sentinel Cluster + Netdata agents + Promtail
minio1             — MinIO Object Storage + Netdata agent + Promtail
monitor1           — Netdata Parent + Loki + Grafana + Promtail
```
