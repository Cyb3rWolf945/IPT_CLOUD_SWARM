# 🔌 05 — WebSocket HA — RatchetPHP + Redis pub/sub

> **Data:** 2026-06-22  
> **Adição:** RatchetPHP co-localizado em web1/web2, mensagens sincronizadas via Redis pub/sub

---

## Diagramas

| Diagrama | Descrição |
|----------|-----------|
| [01_architecture_websocket.mermaid](01_architecture_websocket.mermaid) | Arquitetura WebSocket com Redis pub/sub |
| [02_message_flow.mermaid](02_message_flow.mermaid) | Fluxo de mensagens cross-instance via Redis |
| [03_failover.mermaid](03_failover.mermaid) | Failover — web1 morre, browser reconecta ao web2 |

---

## O Que Foi Implementado

| Camada | Tecnologia |
|--------|-----------|
| **Servidor** | RatchetPHP (co-localizado em web1 + web2) |
| **Mensagens** | Redis pub/sub — canal `chat` |
| **User tracking** | Redis `ws:users:{session}` → connection info |
| **HA** | Nginx `ip_hash` → sticky sessions |
| **Recuperação** | systemd auto-restart + JS exponential backoff |
| **Provisionamento** | Ansible role `websocket` |

---

## Configuração

| Parâmetro | Valor |
|-----------|-------|
| Porta | 8000 (Ratchet) |
| Proxy | Nginx location `/ws/` → upstream `backend_ws` |
| Sticky sessions | `ip_hash` (mesmo browser → mesmo backend) |
| Redis channel | `chat` (pub/sub) |
| Redis keys | `ws:connections`, `ws:users` |

---

## Resultados do Teste

| Teste | Resultado |
|-------|-----------|
| Ratchet running on both web1 + web2 | ✅ |
| Connected to Redis Sentinel master (192.168.44.43) | ✅ |
| Kill web1 Ratchet → web2 handles | ✅ |
| Browser reconnects via Nginx `ip_hash` | ✅ |
| Web1 recovers → systemd auto-restart | ✅ |
| Cross-instance messaging via Redis pub/sub | ✅ |
| User tracking stored in Redis | ✅ |

---

## Porquê Co-localizado (sem VMs novas)?

| Alternativa | Problema |
|-------------|----------|
| VMs dedicadas (ws1, ws2) | +2 VMs, complexidade desnecessária |
| **Co-localizado web1/web2** ✅ | Já temos HA, Nginx já faz proxy, sem VMs novas |
