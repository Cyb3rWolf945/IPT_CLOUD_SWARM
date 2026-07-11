# 🗄️ Patroni + Consul — Fluxo de Eleição

> **Resultados do teste vegeta com DB — 2026-06-22**

---

## 📊 Estado Atual do Cluster (Consul KV)

```
db/project_o_cluster/
├── leader   = "db2"          ← 🔐 Quem detém o lock é o PRIMARY
├── status   = {"db1": replica slot, "db2": primary slot}
└── members/
    ├── db1  = role: replica,  streaming do db2
    └── db2  = role: primary,  detém o lock
```

---

## 🎯 Resumo do Mecanismo de Eleição

| # | Fase | Quem Decide | Ação |
|---|------|------------|------|
| 1 | **Lock Inicial** | Consul KV | Só um nó detém a sessão `leader`. Esse é o **PRIMARY** |
| 2 | **Monitorização** | Patroni (cada nó) | Polling ao Consul a cada `loop_wait: 10s` |
| 3 | **Deteção de Falha** | Patroni (réplica) | Sessão do líder expira (`ttl: 30s`) → lock libertado |
| 4 | **Eleição** | Patroni (réplica) | `acquire session lock` → agarra o lock |
| 5 | **Promoção** | Patroni → PostgreSQL | `pg_ctl promote` → réplica torna-se master |
| 6 | **Re-rota** | HAProxy | Health check `/primary` → novo master encontrado |
| 7 | **Auto-Cura** | Patroni (nó que voltou) | Detecta que não é líder → faz `pg_basebackup` → replica |

---

## ⏱️ Tempos Medidos (Teste Vegeta)

| Evento | Tempo |
|--------|-------|
| Perda de conexão ao primary → deteção pela réplica | ~8s |
| Deteção → lock adquirido + promoção | ~4s |
| **Failover total (deteção → promoção)** | **~4 segundos** |
| Nó antigo volta → rejoin como replica | ~20s (inclui clone) |

---

## 🧪 Resultado do Teste de Failover

- **600 pedidos** a 10 req/s durante 60 segundos
- Primary (`db1`) morto a meio do ataque
- **0 pedidos falhados** — 100% sucesso
- Latência máxima durante failover: **9.29ms**
- Latência média: **3.44ms**

---

## 📁 Diagramas

| Ficheiro | Descrição |
|----------|-----------|
| [`01_architecture.mermaid`](01_architecture.mermaid) | Arquitetura geral do sistema |
| [`02_election_normal.mermaid`](02_election_normal.mermaid) | Estado normal — db2 primary, db1 replica |
| [`03_election_failover.mermaid`](03_election_failover.mermaid) | Failover — db2 morre, db1 promove-se |
| [`04_election_recovery.mermaid`](04_election_recovery.mermaid) | Recuperação — db2 volta como replica |

---

## 🔧 Configuração Relevante (patroni.yml)

```yaml
consul:
  host: 127.0.0.1:8500          # Consul agent local
  register_service: true

bootstrap:
  dcs:
    ttl: 30                      # Sessão expira após 30s
    loop_wait: 10                # Polling a cada 10s
    retry_timeout: 10            # Timeout entre tentativas
    maximum_lag_on_failover: 1048576
```

