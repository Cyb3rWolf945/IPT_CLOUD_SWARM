# 🔄 02 — Patroni + Consul — Mecanismo de Eleição

> **Data:** 2026-06-22  
> **Teste:** Kill do primary (db1) a meio de ataque vegeta

---

## Diagramas da Eleição

| Diagrama | Descrição |
|----------|-----------|
| [01_election_normal.mermaid](01_election_normal.mermaid) | Estado normal — db2 primary, db1 replica |
| [02_election_failover.mermaid](02_election_failover.mermaid) | 🔴 Failover — db1 morre, db2 promove-se |
| [03_election_recovery.mermaid](03_election_recovery.mermaid) | 🟢 Recuperação — db1 volta como replica |

---

## Timeline do Failover (via journalctl Patroni)

| Hora (UTC) | Evento |
|-----------|--------|
| 20:30:48 | `vagrant halt db1` — primary abaixo |
| 20:30:56 | db2 detecta: `FATAL: the database system is shutting down` |
| 20:31:00 | db2: **`promoted self to leader by acquiring session lock`** |
| 20:31:01 | db2 regista-se como primary no Consul |
| 20:34:00 | `vagrant up db1` — db1 volta |
| 20:34:20 | db1 auto-rejoin como **replica**, streaming do db2 |

## ⏱️ Tempos

| Métrica | Tempo |
|---------|-------|
| Perda de conexão → deteção | ~8s |
| Deteção → promoção completa | **~4s** |
| Failover total | **~4 segundos** |
| Nó antigo volta → replica | ~20s (inclui clone) |

---

## Resultado do Teste Vegeta Durante Failover

| Métrica | Resultado |
|---------|-----------|
| Pedidos totais | 600 (10 req/s, 60s) |
| **Sucesso** | **100% — 0 falhas** |
| Latência máxima | 9.29ms |
| Latência média | 3.44ms |

**Conclusão:** O failover Patroni + Consul é **transparente para a aplicação**. O HAProxy re-rotou para o novo primary sem pedidos falhados.
