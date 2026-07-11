# 🐳 Phase 2 — Docker Architecture Diagrams

> **Date:** 2026-06-23  
> **Stack:** Docker Swarm single-node, 23 services, 1 overlay network

---

## Diagram Index

| # | Diagram | Description |
|---|---------|-------------|
| 1 | `01_architecture_docker.mermaid` | Full Docker Swarm architecture — all services, overlay network, volumes |
| 2 | `02_docker_swarm_recovery.mermaid` | Self-healing sequence — container dies → Swarm reschedules |
| 3 | `03_auto_scaling_flow.mermaid` | Auto-scaling — CPU threshold breached → new replicas created |
| 4 | `04_vm_vs_docker_comparison.mermaid` | Side-by-side Phase 1 (VMs) vs Phase 2 (Docker) comparison |

---

## 1. Full Docker Swarm Architecture

Shows the complete stack across the overlay network. Note how the Swarm Routing Mesh replaces both Keepalived VRRP and partially HAProxy.

All services communicate via DNS names (not IPs) on the `ipt_cloud_net` overlay. Persistent data lives in Docker volumes.

## 2. Swarm Self-Healing

Demonstrates Docker Swarm's reconciliation loop: the manager detects a dead container, creates a new one, and Patroni automatically rejoins the cluster — no human intervention.

## 3. Auto-Scaling Flow

When CPU exceeds 80% threshold, a monitoring script triggers `docker service scale`, spawning new web replicas in seconds. Stateless services (web, websocket) scale horizontally; stateful services (PostgreSQL, Redis) rely on their own HA.

## 4. VM vs Docker Comparison

Side-by-side visualization of the two architectures: 11 VMs with static IPs and Keepalived vs 20+ containers with DNS-based service discovery and Swarm routing mesh.
