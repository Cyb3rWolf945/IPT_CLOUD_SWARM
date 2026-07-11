# 🗄️ 06 — MinIO — Dedicated Object Storage

> **Data:** 2026-06-22  
> **Adição:** MinIO movido para VM dedicada `minio1`, separado do Redis

---

## Diagramas

| Diagrama | Descrição |
|----------|-----------|
| [01_architecture_minio.mermaid](01_architecture_minio.mermaid) | MinIO dedicado, separado do Redis |

---

## O Que Mudou

| Antes | Depois |
|-------|--------|
| MinIO + Redis em `storage1` | MinIO em `minio1` (192.168.44.51) dedicado |
| Redis e MinIO partilhavam VM | Redis Sentinel cluster puro (storage1/2/3) |
| s3fs → `192.168.44.41:9000` | s3fs → `192.168.44.51:9000` |

---

## Nova VM

| VM | IP | Role |
|----|----|------|
| minio1 | 192.168.44.51 | MinIO Object Storage |

---

## Configuração

| Parâmetro | Valor |
|-----------|-------|
| API Port | 9000 |
| Console Port | 9001 |
| Root User | admin |
| Bucket | gallery |
| Mount | s3fs fuse → `/var/www/html/public_html/gallery/` |

---

## Total de VMs: 10

```
lb1, lb2           — Load Balancers
web1, web2         — Web Applications
db1, db2           — Databases (Patroni HA)
storage1-3         — Redis Sentinel Cluster
minio1             — MinIO Object Storage
```
