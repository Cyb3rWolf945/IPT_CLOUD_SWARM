# 📊 01 — Initial Stack & Load Tests

> **Data:** 2026-06-22  
> **VM Stack:** lb1, lb2, web1, web2, db1, db2, storage1

---

## Arquitetura Inicial

A stack separou a camada de base de dados (db1/db2) da camada web.

| Diagrama | Descrição |
|----------|-----------|
| [01_architecture.mermaid](01_architecture.mermaid) | Arquitetura completa da stack inicial |
| [02_load_test_flow.mermaid](02_load_test_flow.mermaid) | Fluxo de dados durante os testes vegeta |

---

## Resultados dos Load Tests

| Teste | Rate | Sucesso | Latência Média | p99 |
|-------|------|---------|---------------|-----|
| LB `/` | 50/s | 100% | 2.68ms | 4.53ms |
| DB `/db.php` | 50/s | 100% | 2.48ms | 5.17ms |
| DB `/db.php` | 200/s | 100% | 2.21ms | 3.66ms |
| DB `/db.php` | **500/s** | 100% | 2.03ms | 4.99ms |

**Conclusão:** A DB separada não é o bottleneck. 500 req/s com 2ms de latência.

> 📄 Resultados completos: [`vegeta_results_with_database.md`](../../vegeta_results_with_database.md)
