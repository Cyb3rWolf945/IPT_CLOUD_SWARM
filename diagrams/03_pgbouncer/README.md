# 🏊 03 — PgBouncer Connection Pooler

> **Data:** 2026-06-22  
> **Adição:** PgBouncer co-localizado nos DBs, atrás do HAProxy

---

## Diagramas

| Diagrama | Descrição |
|----------|-----------|
| [01_architecture_pgbouncer.mermaid](01_architecture_pgbouncer.mermaid) | Nova arquitetura com PgBouncer |
| [02_pgbouncer_connection_flow.mermaid](02_pgbouncer_connection_flow.mermaid) | Fluxo de connection pooling |

---

## Onde Foi Colocado?

```
PHP → HAProxy :5000 → PgBouncer :6432 → PostgreSQL :5432
         (lb1/lb2)     (db1 + db2, local)   (mesmo nó)
```

**Atrás do HAProxy, co-localizado com PostgreSQL em cada nó.**

---

## Configuração da Pool

| Parâmetro | Valor | Justificação |
|-----------|-------|-------------|
| `pool_mode` | `transaction` | Conexão devolvida à pool após cada transação |
| `max_client_conn` | 500 | Aguenta o pico de 500 req/s do teste vegeta |
| `default_pool_size` | 50 | Conexões PostgreSQL sempre prontas |
| `reserve_pool_size` | 25 | +25 se o pool base esgotar |
| **Pool máxima** | **75** | 500 clientes PHP partilham 50-75 conexões DB |
| `auth_type` | `md5` | Compatível com o pg_hba do Patroni |

---

## Resultados com PgBouncer (500 req/s)

| Métrica | Sem PgBouncer | Com PgBouncer |
|---------|--------------|---------------|
| Conexões PostgreSQL | ~500 diretas | **50-75 via pool** |
| Sucesso | 100% | 100% |
| Latência média | 2.03ms | **2.03ms** |
| p99 | 4.99ms | **3.61ms** |
| <5ms | 99.02% | **99.68%** |

**Conclusão:** O PgBouncer reduziu as conexões PostgreSQL em **85%+** (500 → 50-75) com **0ms de overhead** e ligeira melhoria no p99.

---

## Porquê Atrás do HAProxy?

| Alternativa | Problema |
|-------------|----------|
| PgBouncer à frente do HAProxy | Não sabe quem é o primary após failover |
| PgBouncer nas webs | +1 salto de rede, single point |
| **PgBouncer nos DBs atrás do HAProxy** ✅ | Pool local, HAProxy faz health check, failover automático |
