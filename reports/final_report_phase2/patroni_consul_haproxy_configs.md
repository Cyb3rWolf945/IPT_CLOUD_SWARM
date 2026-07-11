# 🗄️ PostgreSQL High Availability — Patroni + Consul + HAProxy

> **Objetivo:** Separar a camada de base de dados com alta disponibilidade. Patroni gere os roles PostgreSQL, Consul fornece consenso distribuído para leader election segura, e HAProxy encaminha tráfego TCP apenas para o primary.

---

## 📁 Ficheiros Necessários

| # | Ficheiro | Propósito |
|---|----------|-----------|
| 1 | `ansible/roles/patroni/templates/patroni.yml.j2` | Config do Patroni (HA do PostgreSQL) |
| 2 | `ansible/roles/patroni/templates/patroni.service.j2` | Serviço systemd do Patroni |
| 3 | `ansible/roles/patroni/tasks/main.yml` | Instalação e deploy do Patroni |
| 4 | `ansible/roles/patroni/handlers/main.yml` | Restart do Patroni |
| 5 | `ansible/roles/consul/consul.hcl.j2` | Cluster Consul (Raft consensus) |
| 6 | `ansible/roles/consul/tasks/main.yml` | Instalação e deploy do Consul |
| 7 | `ansible/roles/haproxy/templates/haproxy.cfg.j2` | HAProxy TCP proxy :5000 |
| 8 | `ansible/roles/haproxy/tasks/main.yml` | Instalação e deploy do HAProxy |
| 9 | `ansible/roles/haproxy/handlers/main.yml` | Restart do HAProxy |
| 10 | `ansible/roles/postgres/tasks/main.yml` | Instalação base do PostgreSQL |
| 11 | `ansible/roles/pgbouncer/templates/pgbouncer.ini.j2` | Connection pooling |
| 12 | `ansible/roles/webserver/templates/.env.j2` | DB_HOST da app PHP |
| 13 | `ansible/site.yml` (excertos) | Atribuição das roles |
| 14 | `Vagrantfile` (excertos) | IPs das VMs db1, db2, lb1, lb2, web1, web2 |
| 15 | `ansible/inventory.ini` (excertos) | Mapeamento hostname → IP |

---

## 1. Patroni — Gestor de HA do PostgreSQL

### 1.1 Configuração Principal

**Ficheiro:** `ansible/roles/patroni/templates/patroni.yml.j2`

```yaml
scope: project_o_cluster
namespace: /db/
name: {{ inventory_hostname }}

restapi:
  listen: 0.0.0.0:8008
  connect_address: {{ ansible_host }}:8008

consul:
  host: 127.0.0.1:8500
  register_service: true

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
  initdb:
    - encoding: UTF8
    - locale: C
  pg_hba:
    - host all all 0.0.0.0/0 md5
    - host replication replicator 192.168.44.0/24 md5
  users:
    app_user:
      password: app_password
      options: [CREATEDB, LOGIN]

postgresql:
  listen: 0.0.0.0:5432
  connect_address: {{ ansible_host }}:5432
  data_dir: /var/lib/postgresql/data
  bin_dir: /usr/lib/postgresql/14/bin
  pg_hba:
    - host all all 0.0.0.0/0 md5
    - host replication replicator 0.0.0.0/0 md5
  authentication:
    replication:
      username: replicator
      password: replpassword
    superuser:
      username: postgres
      password: postgres
```

### Parâmetros Chave

| Parâmetro | Valor | Significado |
|-----------|-------|-------------|
| `ttl` | 30s | Tempo de vida do leader lock no Consul |
| `loop_wait` | 10s | Intervalo entre verificações do lock |
| `retry_timeout` | 10s | Tempo máximo para tentar adquirir o lock |
| `maximum_lag_on_failover` | 1 MB | Lag máximo permitido para uma réplica ser promovida |

### Como o Leader Election Funciona

```
┌──────────────────────────────────────────────────────────┐
│                     Consul (Raft)                         │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Key: /db/project_o_cluster/leader               │    │
│  │  Value: "db1"                                     │    │
│  │  Session: <uuid> (renovada a cada ttl/2 = 15s)   │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
         │                              │
    ┌────▼────┐                    ┌────▼────┐
    │  db1    │                    │  db2    │
    │ PRIMARY │                    │ REPLICA │
    │  :5432  │◀─── streaming ────│  :5432  │
    │  :8008  │     replication   │  :8008  │
    └─────────┘                    └─────────┘
```

- Patroni no **db1** adquire o leader lock no Consul → promove-se a **PRIMARY**
- Patroni no **db2** não consegue o lock → permanece **REPLICA**, faz streaming do db1
- `/primary` no REST API :8008 → HTTP 200 (primary) ou 503 (replica)
- Se db1 falha → lock expira (TTL 30s) → db2 adquire lock → promove-se a PRIMARY

### 1.2 Serviço systemd

**Ficheiro:** `ansible/roles/patroni/templates/patroni.service.j2`

```ini
[Unit]
Description=Patroni
After=network.target consul.service

[Service]
Type=simple
User=postgres
Group=postgres
ExecStart=/usr/local/bin/patroni /etc/patroni.yml
Restart=always

[Install]
WantedBy=multi-user.target
```

- `After=consul.service` — Patroni só arranca depois do Consul estar pronto

### 1.3 Tasks Ansible

**Ficheiro:** `ansible/roles/patroni/tasks/main.yml`

```yaml
---
- name: Instalar dependências base
  apt:
    name:
      - python3-pip
      - python3-psycopg2
      - libpq-dev
      - gcc
      - postgresql
    state: present

- name: Garantir que o serviço PostgreSQL não arranca automaticamente
  service:
    name: postgresql
    state: stopped
    enabled: no

- name: Instalar Patroni com suporte a Consul via pip
  pip:
    name: "patroni[consul]"
    state: latest

- name: Garantir diretório de dados do Postgres
  file:
    path: /var/lib/postgresql/data
    state: directory
    owner: postgres
    group: postgres
    mode: '0700'

- name: Criar ficheiro de configuração do Patroni
  template:
    src: patroni.yml.j2
    dest: /etc/patroni.yml
  notify: restart patroni

- name: Criar ficheiro de serviço systemd para o Patroni
  template:
    src: patroni.service.j2
    dest: /etc/systemd/system/patroni.service
  notify: restart patroni

- name: Iniciar e ativar o serviço Patroni
  systemd:
    name: patroni
    state: started
    enabled: yes
    daemon_reload: yes
```

### 1.4 Handler

**Ficheiro:** `ansible/roles/patroni/handlers/main.yml`

```yaml
---
- name: restart patroni
  systemd:
    name: patroni
    state: restarted
```

---

## 2. Consul — Distributed Consensus (Leader Election)

### 2.1 Configuração do Cluster

**Ficheiro:** `ansible/roles/consul/consul.hcl.j2`

```hcl
datacenter = "project_o_dc"
data_dir = "/opt/consul"

bind_addr = "{{ ansible_host }}"
client_addr = "0.0.0.0"

server = true
bootstrap_expect = 2

retry_join = ["192.168.44.31", "192.168.44.32"]

ui_config {
  enabled = true
}
```

### Parâmetros Chave

| Parâmetro | Valor | Significado |
|-----------|-------|-------------|
| `server` | `true` | Ambos os nós são servidores de consenso (não agents) |
| `bootstrap_expect` | `2` | Espera 2 servidores para formar quorum |
| `retry_join` | `["192.168.44.31", "192.168.44.32"]` | db1 e db2 procuram-se mutuamente |

### 2.2 Tasks Ansible

**Ficheiro:** `ansible/roles/consul/tasks/main.yml`

```yaml
---
- name: Instalar dependencias base
  apt:
    name:
      - curl
      - gnupg2
      - software-properties-common
    state: present

- name: Adicionar chave GPG oficial da HashiCorp
  apt_key:
    url: https://apt.releases.hashicorp.com/gpg
    state: present

- name: Adicionar repositorio da HashiCorp
  apt_repository:
    repo: "deb [arch=amd64] https://apt.releases.hashicorp.com jammy main"
    state: present

- name: Instalar Consul
  apt:
    name: consul
    state: present
    update_cache: yes

- name: Aplicar configuracao do cluster Consul
  template:
    src: consul.hcl.j2
    dest: /etc/consul.d/consul.hcl
    owner: consul
    group: consul
    mode: '0644'
  notify: restart consul

- name: Garantir que o Consul arranca com o sistema
  service:
    name: consul
    state: started
    enabled: yes
```

---

## 3. HAProxy — TCP Proxy para o Primary

### 3.1 Configuração

**Ficheiro:** `ansible/roles/haproxy/templates/haproxy.cfg.j2`

```haproxy
global
    log /dev/log local0
    user haproxy
    group haproxy
    daemon

defaults
    log global
    mode tcp
    timeout connect 5s
    timeout client 1m
    timeout server 1m

frontend db_proxy
    bind *:5000
    default_backend db_cluster

backend db_cluster
    option httpchk GET /primary
    server db1 192.168.44.31:6432 check port 8008
    server db2 192.168.44.32:6432 check port 8008
```

### Como o Health Check Funciona

```
HAProxy (lb1/lb2)                      Patroni REST API
     │                                      │
     │──── GET /primary ──────────────► db1:8008
     │◄─── HTTP 200 ──────────────────  (db1 é PRIMARY)
     │                                      │
     │──── GET /primary ──────────────► db2:8008
     │◄─── HTTP 503 ──────────────────  (db2 é REPLICA)
     │                                      │
     │  HAProxy só encaminha TCP para db1:6432 (PgBouncer do primary)
```

- `option httpchk GET /primary` — HAProxy faz HTTP GET ao Patroni REST API
- `check port 8008` — health check no port 8008 (REST API), mas encaminha para `:6432` (PgBouncer)
- Patroni responde **HTTP 200** se for primary, **503** se for replica
- **Zero risco** de escrever na replica

### 3.2 Tasks Ansible

**Ficheiro:** `ansible/roles/haproxy/tasks/main.yml`

```yaml
---
- name: Instalar HAProxy
  apt:
    name: haproxy
    state: present

- name: Copiar config do HAProxy
  template:
    src: haproxy.cfg.j2
    dest: /etc/haproxy/haproxy.cfg
  notify: restart haproxy

- name: Garantir que o HAProxy arranca
  service:
    name: haproxy
    state: started
    enabled: yes
```

### 3.3 Handler

**Ficheiro:** `ansible/roles/haproxy/handlers/main.yml`

```yaml
---
- name: restart haproxy
  service:
    name: haproxy
    state: restarted
```

---

## 4. PgBouncer — Connection Pooling

**Ficheiro:** `ansible/roles/pgbouncer/templates/pgbouncer.ini.j2`

```ini
[databases]
* = host=127.0.0.1 port=5432

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
admin_users = postgres
pool_mode = transaction
max_client_conn = 500
default_pool_size = 50
reserve_pool_size = 25
reserve_pool_timeout = 3
log_connections = 1
log_disconnections = 1
verbose = 0
stats_period = 60
server_idle_timeout = 300
client_idle_timeout = 0
ignore_startup_parameters = extra_float_digits
```

- Co-localizado com cada PostgreSQL (`host=127.0.0.1`)
- `pool_mode = transaction` — conexão devolvida ao pool após cada transação
- `default_pool_size = 50` — 50 conexões persistentes para o PostgreSQL

---

## 5. .env da Aplicação PHP

**Ficheiro:** `ansible/roles/webserver/templates/.env.j2`

```bash
DB_HOST={{ db_host | default('192.168.44.10') }}
DB_PORT={{ db_port | default('5000') }}
DB_NAME={{ db_name | default('project_o') }}
DB_USER={{ db_user | default('app_user') }}
DB_PASS={{ db_password | default('app_password') }}
```

**Ponto crítico:** `DB_HOST=192.168.44.10:5000` — a aplicação **nunca** liga diretamente ao PostgreSQL. Liga-se ao **VIP:5000** (HAProxy), que por sua vez só encaminha para o primary.

---

## 6. PostgreSQL Base

**Ficheiro:** `ansible/roles/postgres/tasks/main.yml`

```yaml
---
- name: Instalar PostgreSQL e dependências
  apt:
    name:
      - postgresql
      - postgresql-contrib
      - python3-psycopg2
      - acl
    state: present

- name: Garantir que o PostgreSQL escuta na rede (IPv4)
  lineinfile:
    path: /etc/postgresql/14/main/postgresql.conf
    regexp: "^#?listen_addresses"
    line: "listen_addresses = '*'"
  notify: restart postgres

- name: Permitir ligações de rede na base de dados (pg_hba.conf com TRUST)
  blockinfile:
    path: /etc/postgresql/14/main/pg_hba.conf
    block: |
      host    all    all    192.168.44.0/24    trust
  notify: restart postgres

- name: Garantir que o PostgreSQL está a correr
  service:
    name: postgresql
    state: started
    enabled: yes

- name: Criar a base de dados do projeto
  postgresql_db:
    name: project_o
  become_user: postgres

- name: Criar o utilizador da base de dados
  postgresql_user:
    name: app_user
    password: app_password
```

> **Nota:** A role `postgres` corre **antes** da role `patroni`. O Patroni depois desliga o PostgreSQL clássico e assume a gestão.

---

## 7. Atribuição no Playbook

**Ficheiro:** `ansible/site.yml` (excertos relevantes)

```yaml
# HAProxy corre NOS LOAD BALANCERS
- hosts: loadbalancers
  become: yes
  roles:
    - keepalived
    - nginx
    - haproxy            # ← HAProxy :5000 nos lb1/lb2

# Patroni + Consul + PgBouncer correm NAS DATABASES
- hosts: databases
  become: yes
  roles:
    - postgres           # ← Instala PostgreSQL base
    - consul             # ← Consul para leader election
    - patroni            # ← Patroni gere HA (assume controlo do PG)
    - pgbouncer          # ← Connection pooling

# .env é aplicado nos webservers
- hosts: webservers
  become: yes
  roles:
    - webserver          # ← Inclui o template .env.j2
    - websocket
```

---

## 8. IPs das VMs

**Ficheiro:** `Vagrantfile` (excertos)

```ruby
# Load Balancers (onde corre o HAProxy :5000)
config.vm.define "lb1" do |lb1|
    lb1.vm.network "private_network", ip: "192.168.44.11"
end
config.vm.define "lb2" do |lb2|
    lb2.vm.network "private_network", ip: "192.168.44.12"
end

# Databases (onde correm Patroni + Consul + PgBouncer)
config.vm.define "db1" do |db1|
    db1.vm.network "private_network", ip: "192.168.44.31"
end
config.vm.define "db2" do |db2|
    db2.vm.network "private_network", ip: "192.168.44.32"
end

# Webservers (onde a app PHP lê DB_HOST=192.168.44.10:5000)
config.vm.define "web1" do |web1|
    web1.vm.network "private_network", ip: "192.168.44.21"
end
config.vm.define "web2" do |web2|
    web2.vm.network "private_network", ip: "192.168.44.22"
end
```

---

## 9. Inventory

**Ficheiro:** `ansible/inventory.ini` (excertos)

```ini
[loadbalancers]
lb1 ansible_host=192.168.44.11 ansible_ssh_private_key_file=~/.ssh/vagrant_keys/lb1_key
lb2 ansible_host=192.168.44.12 ansible_ssh_private_key_file=~/.ssh/vagrant_keys/lb2_key

[webservers]
web1 ansible_host=192.168.44.21 ansible_ssh_private_key_file=~/.ssh/vagrant_keys/web1_key
web2 ansible_host=192.168.44.22 ansible_ssh_private_key_file=~/.ssh/vagrant_keys/web2_key

[databases]
db1 ansible_host=192.168.44.31 ansible_ssh_private_key_file=~/.ssh/vagrant_keys/db1_key
db2 ansible_host=192.168.44.32 ansible_ssh_private_key_file=~/.ssh/vagrant_keys/db2_key
```

---

## 🔄 Fluxo Completo do Pedido DB

```
web1 ou web2 (PHP)
  │
  │  $_ENV['DB_HOST'] = '192.168.44.10'
  │  $_ENV['DB_PORT'] = '5000'
  │
  ▼
VIP 192.168.44.10:5000 (Keepalived)
  │
  ▼
HAProxy :5000 (lb1 ou lb2)
  │  health check: GET /primary → db1:8008 (HTTP 200) / db2:8008 (HTTP 503)
  │  só encaminha para o PRIMARY
  │
  ▼
PgBouncer :6432 (db1 — primary)
  │  host=127.0.0.1 port=5432
  │
  ▼
PostgreSQL :5432 (db1 — PRIMARY)
  │
  └── streaming replication ──► PostgreSQL :5432 (db2 — REPLICA)
```

---

## 🧪 Failover: O Que Acontece Quando o Primary Morre

```
T+0s   — db1 (PRIMARY) crash
T+0s   — HAProxy health check GET /primary → db1:8008 falha (timeout)
T+0s   — HAProxy marca db1 como DOWN, começa a encaminhar para db2:6432
         (mas db2 ainda é REPLICA — ligações falham momentaneamente)
T+0s   — Sessão Consul do db1 começa a expirar (TTL = 30s)
T+~4s  — Patroni no db2 detecta que o lock expirou
T+~4s  — db2 adquire o leader lock no Consul
T+~4s  — db2 promove-se a PRIMARY
T+~4s  — GET /primary → db2:8008 passa a HTTP 200
T+~5s  — HAProxy health check passa em db2 → tráfego TCP retoma
```

### Resultado do Teste Vegeta

```
Requisições:  600 (10 req/s × 60s)
Sucesso:      600/600 (100%)
Falhas:       0
Conclusão:    Failover transparente — zero pedidos perdidos
```

---

## 🛡️ Prevenção de Split-Brain

O mecanismo que previne split-brain é o **leader lock** no Consul:

1. Só o nó que detém o lock pode ser PRIMARY (accept writes)
2. O lock é mantido por uma **session** Consul com TTL de 30s
3. O Patroni renova a session a cada `ttl/2 = 15s`
4. Se o primary falha → session expira → lock é libertado
5. Uma réplica adquire o lock → Patroni promove-a a PRIMARY
6. Se o primary antigo recuperar, **já não tem o lock** → Patroni força-o a REPLICA

**Sem Consul (Raft),** dois nós poderiam decidir simultaneamente que são primary → split-brain. Com Consul, a decisão é coordenada por consenso.

---

## ✅ Verificação

```bash
# Verificar qual é o primary
vagrant ssh lb1 -c "curl -s http://192.168.44.31:8008/primary"
vagrant ssh lb1 -c "curl -s http://192.168.44.32:8008/primary"

# Verificar estado do cluster Patroni
vagrant ssh db1 -c "sudo patronictl -c /etc/patroni.yml list"

# Verificar membros do cluster Consul
vagrant ssh db1 -c "consul members"

# Testar failover — matar o primary
vagrant halt db1
# Aguardar ~5s e verificar que db2 é o novo primary
vagrant ssh db2 -c "sudo patronictl -c /etc/patroni.yml list"
```
