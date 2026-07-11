# 🧪 Phase 2 — Performance Testing Diagrams

> **Date:** 2026-06-23  
> **Tests:** Vegeta load tests against Docker Compose stack

---

## Diagram Index

| # | Diagram | Description |
|---|---------|-------------|
| 1 | `01_docker_load_test_flow.mermaid` | Vegeta → Swarm mesh → Nginx → web replicas → PgBouncer → Patroni |
| 2 | `02_docker_failover_test.mermaid` | Kill db1 mid-test → db2 promotes → 1 timeout, 599 succeed |
| 3 | `03_performance_comparison.mermaid` | Phase 1 (VMs) vs Phase 2 (Docker) latency comparison charts |
