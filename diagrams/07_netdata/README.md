# 📊 07 — Netdata — Real-Time Monitoring Dashboard

> **Data:** 2026-06-23  
> **Adição:** Netdata agents em todas as 10 VMs, centralizados num parent dedicado `monitor1`

---

## Diagramas

| Diagrama | Descrição |
|----------|-----------|
| [01_architecture_netdata.mermaid](01_architecture_netdata.mermaid) | Arquitetura com monitor1, streaming das 10 VMs, proxy Nginx |
| [02_netdata_streaming_flow.mermaid](02_netdata_streaming_flow.mermaid) | Fluxo: registo → stream → dashboard → acesso via VIP |

---

## O Que Adicionámos

| Antes | Depois |
|-------|--------|
| Sem GUI de monitorização | Netdata dashboard unificado via VIP |
| Diagnóstico manual (`htop`, `curl`) | Métricas em tempo real de todas as VMs |
| Sem visibilidade cross-VM | Parent node agrega CPU, RAM, disco, rede de 10 VMs |

---

## Nova VM

| VM | IP | Role |
|----|----|------|
| monitor1 | 192.168.44.61 | Netdata Parent — recebe streams, dashboard central |

---

## Como Funciona

1. **Netdata agent** instalado em cada VM (lb1, lb2, web1, web2, db1, db2, storage1-3, minio1)
2. Cada agente faz **stream** das métricas para `monitor1:19999` a cada 1 segundo
3. **monitor1** (parent) agrega todas as métricas numa dashboard unificada
4. **Nginx** (lb1/lb2) faz proxy de `/netdata/` → `monitor1:19999`
5. Utilizador acede a `http://192.168.44.10/netdata/` via VIP

---

## Configuração

| Parâmetro | Valor |
|-----------|-------|
| Netdata port | 19999 |
| Parent host | monitor1 (192.168.44.61) |
| Stream API key | netdata-monitoring-key |
| Stream interval | 1 segundo |
| Reconnect delay | 5 segundos |
| Buffer size | 1 MB |
| Dashboard URL | `http://192.168.44.10/netdata/` |
| Ansible role | `netdata` (modo: agent / parent) |

---

## Total de VMs: 11

```
lb1, lb2           — Load Balancers (+ Netdata agents)
web1, web2         — Web Applications (+ Netdata agents)
db1, db2           — Databases Patroni HA (+ Netdata agents)
storage1-3         — Redis Sentinel Cluster (+ Netdata agents)
minio1             — MinIO Object Storage (+ Netdata agent)
monitor1           — Netdata Parent (dashboard central)
```
