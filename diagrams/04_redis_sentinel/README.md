# 🔴 04 — Redis Sentinel — HA for Session Caching

> **Data:** 2026-06-22  
> **Adição:** 3-node Redis cluster com Sentinel para failover automático

---

## Diagramas

| Diagrama | Descrição |
|----------|-----------|
| [01_architecture_sentinel.mermaid](01_architecture_sentinel.mermaid) | Arquitetura Redis Sentinel (9 VMs total) |
| [02_failover.mermaid](02_failover.mermaid) | Failover — master morre, Sentinel promove réplica |
| [03_recovery.mermaid](03_recovery.mermaid) | Recuperação — nó morto volta, Sentinel corrige split-brain |

---

## VMs Adicionadas

| VM | IP | Role |
|----|----|------|
| storage2 | 192.168.44.42 | Redis + Sentinel |
| storage3 | 192.168.44.43 | Redis + Sentinel |

---

## Configuração

| Parâmetro | Valor |
|-----------|-------|
| Nós Redis | 3 (1 master + 2 replicas) |
| Nós Sentinel | 3 (co-localizados) |
| Quorum | 2 |
| `down-after-milliseconds` | 5000 (5s) |
| `failover-timeout` | 30000 (30s) |
| `requirepass` | redispass (proteção master) |
| PHP `session.save_path` | `tcp://sentinel:26379` (3 sentinels) |

---

## Resultados do Teste de Failover

| Métrica | Resultado |
|---------|-----------|
| Vegeta rate | 10 req/s, 30s |
| **Sucesso** | **100% — 0 falhas** |
| Latência máxima | 12.69ms |
| Latência média | 2.61ms |
| Master morto | storage1 (Redis master) |
| Novo master | **storage3** (promovido pelo Sentinel) |

### Timeline

| Hora | Evento |
|------|--------|
| 22:30:28 | `systemctl stop redis-server` no storage1 |
| ~22:30:33 | Sentinel detecta master down (5s timeout) |
| ~22:30:34 | Sentinel promove storage3 a master |
| ~22:31:00 | `systemctl start redis-server` no storage1 |
| ~22:31:10 | Sentinel deteta split-brain → demote storage1 → replica |

---

## Comparação: PostgreSQL HA vs Redis HA

| | PostgreSQL | Redis |
|---|---|---|
| **HA Tool** | Patroni + Consul | Redis Sentinel |
| **Nós** | 2 (db1, db2) | 3 (storage1-3) |
| **Consenso** | Consul lock | Sentinel quorum (2/3) |
| **Failover time** | ~4s | ~5s |
| **App impact** | 0 failures | 0 failures |
| **Recovery** | Auto-rejoin replica | Auto-demote + replica |
