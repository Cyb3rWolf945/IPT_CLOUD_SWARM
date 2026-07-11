# Graph Report - .  (2026-06-21)

## Corpus Check
- Corpus is ~16,977 words - fits in a single context window. You may not need a graph.

## Summary
- 586 nodes · 1194 edges · 43 communities (26 shown, 17 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 81 edges (avg confidence: 0.81)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Moment.js Date Library|Moment.js Date Library]]
- [[_COMMUNITY_Bootstrap Alert & Button|Bootstrap Alert & Button]]
- [[_COMMUNITY_Bootstrap Core Utilities|Bootstrap Core Utilities]]
- [[_COMMUNITY_Bootstrap Config & Data|Bootstrap Config & Data]]
- [[_COMMUNITY_Project Architecture & Specs|Project Architecture & Specs]]
- [[_COMMUNITY_Bootstrap jQuery Bridge|Bootstrap jQuery Bridge]]
- [[_COMMUNITY_Bootstrap Alert Dismiss|Bootstrap Alert Dismiss]]
- [[_COMMUNITY_Bootstrap Carousel|Bootstrap Carousel]]
- [[_COMMUNITY_Bootstrap Keyboard Nav|Bootstrap Keyboard Nav]]
- [[_COMMUNITY_Architecture Diagrams|Architecture Diagrams]]
- [[_COMMUNITY_Network Infrastructure|Network Infrastructure]]
- [[_COMMUNITY_Bootstrap ScrollSpy|Bootstrap ScrollSpy]]
- [[_COMMUNITY_Bootstrap Touch Swipe|Bootstrap Touch Swipe]]
- [[_COMMUNITY_HA Stack Components|HA Stack Components]]
- [[_COMMUNITY_Bootstrap Offcanvas|Bootstrap Offcanvas]]
- [[_COMMUNITY_WebSocket Server (PHP)|WebSocket Server (PHP)]]
- [[_COMMUNITY_WebSocket Client (JS)|WebSocket Client (JS)]]
- [[_COMMUNITY_Web App & Gallery Assets|Web App & Gallery Assets]]
- [[_COMMUNITY_Gallery & Upload UI|Gallery & Upload UI]]
- [[_COMMUNITY_Composer Dependencies (App)|Composer Dependencies (App)]]
- [[_COMMUNITY_IPT Branding|IPT Branding]]
- [[_COMMUNITY_Composer Dependencies (WS)|Composer Dependencies (WS)]]
- [[_COMMUNITY_Provisioning Scripts|Provisioning Scripts]]
- [[_COMMUNITY_README PHP & Composer|README: PHP & Composer]]
- [[_COMMUNITY_README Load Testing|README: Load Testing]]
- [[_COMMUNITY_Checkpoint1 Diagram|Checkpoint1 Diagram]]
- [[_COMMUNITY_Original Architecture|Original Architecture]]
- [[_COMMUNITY_HA Pattern|HA Pattern]]
- [[_COMMUNITY_Horizontal Scaling|Horizontal Scaling]]
- [[_COMMUNITY_Service Discovery|Service Discovery]]
- [[_COMMUNITY_README Vagrant|README: Vagrant]]

## God Nodes (most connected - your core abstractions)
1. `$()` - 87 edges
2. `$()` - 80 edges
3. `cs` - 38 edges
4. `on()` - 33 edges
5. `xt` - 28 edges
6. `trigger()` - 22 edges
7. `qi` - 22 edges
8. `remove()` - 20 edges
9. `c()` - 20 edges
10. `G()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `CNV Final Project 2026 v1 Specification` --semantically_similar_to--> `CNV Final Project 2026 v2 Specification`  [INFERRED] [semantically similar]
  cnv-final-project-2026.pdf → cnv-final-project-2026-v2.pdf
- `Solution A Initial Implementation Plan (9 steps: VM roles, Ansible provisioning, Keepalived VIP, stateless PHP, shared storage, DB replication, WebSocket scaling, monitoring, failover testing)` --references--> `Ansible site.yml Master Playbook`  [EXTRACTED]
  checkpoint1/checkpoint1.pdf → ipt_cloud_course_project/ansible/site.yml
- `Project O Architecture Analysis` --references--> `Project O - Base PHP Web Application`  [EXTRACTED]
  checkpoint1/checkpoint1.pdf → ipt_cloud_course_project/README.md
- `CNV Final Project 2026 v2 Specification` --references--> `Project O - Base PHP Web Application`  [EXTRACTED]
  cnv-final-project-2026-v2.pdf → ipt_cloud_course_project/README.md
- `Solution A: Virtual Machines (On-Premises IaaS Simulation)` --references--> `Consul Service Discovery Daemon`  [EXTRACTED]
  cnv-final-project-2026-v2.pdf → ipt_cloud_course_project/ansible/roles/consul/tasks/main.yml

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Load Balancer High-Availability Stack (Keepalived + Nginx + HAProxy)** — tasks_main_keepalived_service, tasks_main_nginx_service, tasks_main_haproxy_service, ansible_site_loadbalancers [EXTRACTED 1.00]
- **Database High-Availability Stack (PostgreSQL + Patroni + Consul)** — tasks_main_postgres_service, tasks_main_patroni_service, tasks_main_consul_service, ansible_site_databases [EXTRACTED 1.00]
- **Storage Stack (Redis Sessions + MinIO Object Storage)** — tasks_main_redis_service, tasks_main_minio_service, tasks_main_minio_gallery_bucket, ansible_site_storage [EXTRACTED 1.00]

## Communities (43 total, 17 thin omitted)

### Community 0 - "Moment.js Date Library"
Cohesion: 0.06
Nodes (65): $(), a(), ae(), bn(), bt(), c(), ce(), cn() (+57 more)

### Community 1 - "Bootstrap Alert & Button"
Cohesion: 0.05
Nodes (5): Bt, cs, on(), trigger(), us

### Community 2 - "Bootstrap Core Utilities"
Cohesion: 0.08
Nodes (45): $(), Ae(), be(), Ce(), D(), De(), di(), $e() (+37 more)

### Community 3 - "Bootstrap Config & Data"
Cohesion: 0.06
Nodes (8): getDataAttributes(), H, j(), Jn, Q, remove(), ui(), r()

### Community 4 - "Project Architecture & Specs"
Cohesion: 0.07
Nodes (39): databases Host Group, loadbalancers Host Group, Ansible site.yml Master Playbook, storage Host Group, webservers Host Group, System Improvement Requirements (horizontal scaling, Redis sessions, shared storage, DB HA, LB HA, Ansible automation, Prometheus monitoring), Original Project O Limitations (single server, local sessions, local uploads, single DB, no LB, no automation), Project O Architecture Analysis (+31 more)

### Community 5 - "Bootstrap jQuery Bridge"
Cohesion: 0.07
Nodes (3): qi, W, Y

### Community 8 - "Bootstrap Keyboard Nav"
Cohesion: 0.16
Nodes (7): getElementFromSelector(), getMultipleElementsFromSelector(), getSelectorFromElement(), Ks, B(), n(), q()

### Community 9 - "Architecture Diagrams"
Cohesion: 0.12
Nodes (23): Browser (Users), Database, Database Cluster (Primary + replica, repmgr / Patroni), GlusterFS (distributed file system), HAProxy (load balancer), Keepalived (HA for Load Balancer), Load Balancer (nginx / HAProxy) with Virtual IP, Monolithic Architecture (+15 more)

### Community 10 - "Network Infrastructure"
Cohesion: 0.20
Nodes (18): Backend Subnet 192.168.60.0/24, Consul Service Discovery, Data & Services Tier, Floating Virtual IP 192.168.56.100, Frontend Subnet 192.168.56.0/24, HAProxy Load Balancer, Internet Gateway, Keepalived High Availability (+10 more)

### Community 13 - "HA Stack Components"
Cohesion: 0.24
Nodes (11): Consul Service Discovery (192.168.56.40/41/42), etcd Distributed Consensus (192.168.56.40/41/42), HAProxy Load Balancer (192.168.56.20/21), Keepalived VIP Failover, MinIO Object Storage (192.168.56.50), Nginx Web Servers (Web1 192.168.56.30 / Web2 192.168.56.31), Patroni PostgreSQL HA Manager, PHP-FPM Application Runtime (+3 more)

### Community 15 - "WebSocket Server (PHP)"
Cohesion: 0.31
Nodes (4): ConnectionInterface, Exception, MessageComponentInterface, NotificationServer

### Community 16 - "WebSocket Client (JS)"
Cohesion: 0.20
Nodes (7): messageForm, messageInput, notificationDiv, predefinedColors, senderColors, socket, statusDiv

### Community 19 - "Gallery & Upload UI"
Cohesion: 0.50
Nodes (3): Photo Gallery Section, Public Web App, upload.php

### Community 22 - "IPT Branding"
Cohesion: 1.00
Nodes (3): Instituto Politécnico de Tomar, ipt.png, Web Application Branding

## Knowledge Gaps
- **42 isolated node(s):** `vlucas/phpdotenv`, `senderColors`, `predefinedColors`, `messageForm`, `messageInput` (+37 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `$()` connect `Bootstrap Core Utilities` to `Bootstrap Alert & Button`, `Bootstrap Config & Data`, `Bootstrap jQuery Bridge`, `Bootstrap Alert Dismiss`, `Bootstrap Carousel`, `Bootstrap Keyboard Nav`, `Bootstrap ScrollSpy`, `Bootstrap Touch Swipe`, `Bootstrap Offcanvas`?**
  _High betweenness centrality (0.270) - this node is a cross-community bridge._
- **Why does `$()` connect `Moment.js Date Library` to `Bootstrap Keyboard Nav`, `Bootstrap Config & Data`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Why does `cs` connect `Bootstrap Alert & Button` to `Bootstrap Core Utilities`, `Bootstrap Config & Data`, `Bootstrap jQuery Bridge`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **What connects `vlucas/phpdotenv`, `senderColors`, `predefinedColors` to the rest of the system?**
  _47 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Moment.js Date Library` be split into smaller, more focused modules?**
  _Cohesion score 0.06293285155073773 - nodes in this community are weakly interconnected._
- **Should `Bootstrap Alert & Button` be split into smaller, more focused modules?**
  _Cohesion score 0.053946053946053944 - nodes in this community are weakly interconnected._
- **Should `Bootstrap Core Utilities` be split into smaller, more focused modules?**
  _Cohesion score 0.08355367530407191 - nodes in this community are weakly interconnected._