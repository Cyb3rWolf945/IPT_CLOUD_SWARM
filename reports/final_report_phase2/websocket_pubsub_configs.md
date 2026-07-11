# 🔗 WebSocket com Redis Pub/Sub — Real-Time Horizontal Scaling

> **Objetivo:** Sincronizar instâncias RatchetPHP em web1 e web2 via Redis Pub/Sub, eliminando "ilhas" de tempo real. Uma mensagem recebida por uma instância é publicada no Redis e entregue por todas as outras aos seus clientes conectados.

---

## 📁 Ficheiros Necessários

| # | Ficheiro | Propósito |
|---|----------|-----------|
| 1 | `ansible/roles/websocket/tasks/main.yml` | Instalação Ratchet + Composer + serviço systemd |
| 2 | `ansible/roles/websocket/handlers/main.yml` | Restart do Ratchet |
| 3 | `ansible/roles/websocket/templates/websockets_server.php.j2` | Servidor WebSocket com Redis Pub/Sub + Sentinel discovery |
| 4 | `ansible/roles/nginx/templates/nginx.conf.j2` (excerto) | Proxy reverso WebSocket com `ip_hash` |
| 5 | `ansible/site.yml` (excertos) | Atribuição das roles |
| 6 | `Vagrantfile` (excertos) | IPs das VMs web1, web2, storage1-3 |
| 7 | `ansible/inventory.ini` (excertos) | Grupos webservers + redis_cluster |

---

## 1. Tasks Ansible — Instalação do RatchetPHP

**Ficheiro:** `ansible/roles/websocket/tasks/main.yml`

```yaml
---
- name: Garantir que a pasta ws existe no destino
  file:
    path: /var/www/html/ws
    state: directory
    owner: root
    group: root
    mode: '0755'

- name: Copiar composer.json para o destino
  copy:
    src: /home/cyb3rwolf/IPT/final_project_cloud/ipt_cloud_course_project/ws/composer.json
    dest: /var/www/html/ws/composer.json
    owner: root
    group: root
    mode: '0644'

- name: Instalar dependências do Ratchet via Composer
  composer:
    command: require
    arguments: "cboden/ratchet:^0.4.4 predis/predis:^2.0"
    working_dir: /var/www/html/ws
    no_dev: yes
  become: no

- name: Deploy ficheiro do servidor WebSocket (Redis pub/sub)
  template:
    src: websockets_server.php.j2
    dest: /var/www/html/ws/websockets_server.php
    owner: root
    group: root
    mode: '0755'
  notify: restart ratchet

- name: Criar serviço systemd para o Ratchet
  copy:
    content: |
      [Unit]
      Description=RatchetPHP WebSocket Server
      After=network.target

      [Service]
      Type=simple
      User=root
      WorkingDirectory=/var/www/html/ws
      ExecStart=/usr/bin/php /var/www/html/ws/websockets_server.php
      ExecReload=/bin/kill -HUP $MAINPID
      Restart=always
      RestartSec=3

      [Install]
      WantedBy=multi-user.target
    dest: /etc/systemd/system/ratchet.service
    owner: root
    group: root
    mode: '0644'
  notify: restart ratchet

- name: Recarregar systemd e garantir que o Ratchet arranca
  systemd:
    name: ratchet
    state: started
    enabled: yes
    daemon_reload: yes
```

---

## 2. Handler

**Ficheiro:** `ansible/roles/websocket/handlers/main.yml`

```yaml
---
- name: restart ratchet
  systemd:
    name: ratchet
    state: restarted
    daemon_reload: yes
```

---

## 3. Servidor WebSocket — Redis Pub/Sub + Sentinel Discovery

**Ficheiro:** `ansible/roles/websocket/templates/websockets_server.php.j2`

### 3.1 Descoberta do Redis Master via Sentinel

```php
// ─── Redis Sentinel Configuration ───────────────────────────────
$sentinel_hosts = [
    '192.168.44.41:26379',
    '192.168.44.42:26379',
    '192.168.44.43:26379',
];
$redis_password = 'redispass';
$redis_master_name = 'mymaster';

// ─── Discover Redis Master via Sentinel ─────────────────────────
function discover_master($sentinel_hosts, $master_name) {
    foreach ($sentinel_hosts as $host) {
        list($ip, $port) = explode(':', $host);
        try {
            $sentinel = new Redis();
            $sentinel->connect($ip, $port, 2);
            $master = $sentinel->rawCommand(
                'SENTINEL', 'get-master-addr-by-name', $master_name
            );
            if ($master && count($master) === 2) {
                return ['host' => $master[0], 'port' => $master[1]];
            }
        } catch (Exception $e) {
            continue;
        }
    }
    throw new RuntimeException('Could not discover Redis master via Sentinel');
}

$master = discover_master($sentinel_hosts, $redis_master_name);
```

### 3.2 Classe Principal — NotificationServer

```php
class NotificationServer implements MessageComponentInterface
{
    public $clients;
    protected $redis_pub;
    protected $redis_sub;
    protected $server_id;

    public function __construct($redis_master, $redis_password)
    {
        $this->clients = new \SplObjectStorage();
        $this->server_id = gethostname() . ':' . getmypid();

        // Publisher — envia mensagens para o canal Redis
        $this->redis_pub = new Redis();
        $this->redis_pub->connect($redis_master['host'], $redis_master['port']);
        if ($redis_password) {
            $this->redis_pub->auth($redis_password);
        }
    }

    // ─── onOpen: Regista conexão + notifica todos ──────────────
    public function onOpen(ConnectionInterface $conn)
    {
        $query_string = $conn->httpRequest->getUri()->getQuery();
        parse_str($query_string, $params);
        $user_id = $params['user_id'] ?? 'anon_' . $conn->resourceId;

        $this->clients->attach($conn);

        // Guarda no Redis: user → connection
        $info = json_encode([
            'server'       => $this->server_id,
            'resourceId'   => $conn->resourceId,
            'user_id'      => $user_id,
            'connected_at' => date('c'),
        ]);
        $this->redis_pub->hSet('ws:connections', $conn->resourceId, $info);
        $this->redis_pub->hSet('ws:users', $user_id, $conn->resourceId);

        // Broadcast: notifica TODOS os clientes (local + remotos)
        $this->broadcast([
            'type'         => 'system',
            'event'        => 'user_joined',
            'user_id'      => $user_id,
            'online_count' => $this->redis_pub->hLen('ws:connections'),
            'timestamp'    => date('Y-m-d H:i:s'),
        ]);
    }

    // ─── onMessage: Publica no Redis → todas as instâncias ─────
    public function onMessage(ConnectionInterface $from, $message)
    {
        $data = json_decode($message, true);
        if (!$data) return;

        $data['timestamp'] = date('Y-m-d H:i:s');
        $data['sender_resourceId'] = $from->resourceId;

        // Sanitize
        if (isset($data['message'])) {
            $data['message'] = htmlspecialchars(
                $data['message'], ENT_QUOTES, 'UTF-8'
            );
        }

        // 🔥 Publica no canal Redis 'chat'
        //    → Todas as instâncias (web1, web2) recebem via subscriber
        $this->redis_pub->publish('chat', json_encode($data));
    }

    // ─── onClose: Limpa Redis + notifica ───────────────────────
    public function onClose(ConnectionInterface $conn)
    {
        $this->clients->detach($conn);
        $this->redis_pub->hDel('ws:connections', $conn->resourceId);

        $this->broadcast([
            'type'         => 'system',
            'event'        => 'user_left',
            'online_count' => $this->redis_pub->hLen('ws:connections'),
            'timestamp'    => date('Y-m-d H:i:s'),
        ]);
    }

    // ─── broadcast: Envia para TODOS os clientes LOCAIS ────────
    private function broadcast(array $data)
    {
        $json = json_encode($data);
        foreach ($this->clients as $client) {
            $client->send($json);
        }
    }
}
```

### 3.3 Subscriber — Processo Filho e Event Loop

```php
// Fork: processo filho faz SUBSCRIBE bloqueante ao Redis
$sub_pid = pcntl_fork();
if ($sub_pid == 0) {
    $sub = new Redis();
    $sub->connect($master['host'], $master['port']);
    if ($redis_password) {
        $sub->auth($redis_password);
    }
    $sub->setOption(Redis::OPT_READ_TIMEOUT, -1);
    $sub->subscribe(['chat'], function ($redis, $channel, $message) {
        // Escreve mensagem recebida para ficheiro IPC
        file_put_contents(
            '/tmp/ratchet_pubsub_' . getmypid(),
            $message . "\n",
            FILE_APPEND
        );
    });
    exit(0);
}

// Event loop: a cada 50ms verifica mensagens do subscriber
$loop = \React\EventLoop\Factory::create();
$loop->addPeriodicTimer(0.05, function () use ($notification_server) {
    $files = glob('/tmp/ratchet_pubsub_*');
    foreach ($files as $file) {
        $content = @file_get_contents($file);
        if ($content) {
            @unlink($file);
            foreach (explode("\n", trim($content)) as $msg) {
                if ($msg) {
                    // Entrega a todos os clientes LOCAIS
                    foreach ($notification_server->clients as $client) {
                        $client->send($msg);
                    }
                }
            }
        }
    }
});

$server = IoServer::factory(
    new HttpServer(
        new WsServer($notification_server)
    ),
    8000,
    $loop
);
$server->run();
```

---

## 4. Nginx — Proxy Reverso WebSocket

**Ficheiro:** `ansible/roles/nginx/templates/nginx.conf.j2` (excerto)

```nginx
upstream backend_ws {
    ip_hash;  # Sticky sessions — mesmo cliente → mesmo backend
    server 192.168.44.21:8000; # web1 Ratchet
    server 192.168.44.22:8000; # web2 Ratchet
}

server {
    listen 80;

    # ... HTTP proxy para backend_web ...

    # WebSocket proxy — Nginx faz proxy das conexões WS para o Ratchet
    location /ws/ {
        proxy_pass http://backend_ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

### Porquê `ip_hash`

| Mecanismo | Porquê |
|-----------|--------|
| `ip_hash` | Garante que o mesmo cliente (IP) vai sempre para o mesmo backend WebSocket |
| Sem `ip_hash` | O cliente poderia ser redirecionado para web2 após o handshake inicial → quebra a conexão WS |

> **Nota:** `ip_hash` resolve o sticky-session do WebSocket mas **não** é a fonte de HA das mensagens. Quem sincroniza as mensagens entre web1 e web2 é o **Redis Pub/Sub**.

---

## 5. Atribuição no Playbook

**Ficheiro:** `ansible/site.yml` (excertos)

```yaml
# WebSocket corre nos webservers (co-localizado com Apache/PHP)
- hosts: webservers
  become: yes
  roles:
    - webserver          # ← Apache + PHP
    - websocket          # ← RatchetPHP + Redis Pub/Sub

# Nginx (proxy WS) corre nos load balancers
- hosts: loadbalancers
  become: yes
  roles:
    - keepalived
    - nginx              # ← Inclui proxy /ws/ com ip_hash
    - haproxy

# Redis (pub/sub backplane) corre nos storage VMs
- hosts: redis_cluster
  become: yes
  roles:
    - redis
    - redis_sentinel
```

---

## 6. IPs das VMs

**Ficheiro:** `Vagrantfile` (excertos)

```ruby
# Webservers — onde corre o RatchetPHP :8000
config.vm.define "web1" do |web1|
    web1.vm.network "private_network", ip: "192.168.44.21"
end
config.vm.define "web2" do |web2|
    web2.vm.network "private_network", ip: "192.168.44.22"
end

# Storage — Redis (pub/sub backplane)
config.vm.define "storage1" do |storage1|
    storage1.vm.network "private_network", ip: "192.168.44.41"
end
config.vm.define "storage2" do |storage2|
    storage2.vm.network "private_network", ip: "192.168.44.42"
end
config.vm.define "storage3" do |storage3|
    storage3.vm.network "private_network", ip: "192.168.44.43"
end
```

---

## 7. Inventory

**Ficheiro:** `ansible/inventory.ini` (excertos)

```ini
[webservers]
web1 ansible_host=192.168.44.21 ansible_ssh_private_key_file=~/.ssh/vagrant_keys/web1_key
web2 ansible_host=192.168.44.22 ansible_ssh_private_key_file=~/.ssh/vagrant_keys/web2_key

[redis_cluster]
storage1 ansible_host=192.168.44.41 ansible_ssh_private_key_file=~/.ssh/vagrant_keys/storage1_key
storage2 ansible_host=192.168.44.42 ansible_ssh_private_key_file=~/.ssh/vagrant_keys/storage2_key
storage3 ansible_host=192.168.44.43 ansible_ssh_private_key_file=~/.ssh/vagrant_keys/storage3_key
```

---

## 🔄 Fluxo Completo de uma Mensagem WebSocket

```
┌──────────────────────────────────────────────────────────────────────┐
│                      Fluxo Pub/Sub Cross-Instance                     │
│                                                                       │
│  Utilizador A (web1)          Utilizador B (web2)                    │
│       │                            │                                  │
│       │  1. Envia mensagem         │                                  │
│       ▼                            │                                  │
│  ┌──────────────────────┐          │                                  │
│  │ RatchetPHP (web1)    │          │                                  │
│  │ onMessage()          │          │                                  │
│  │                      │          │                                  │
│  │ 2. PUBLISH chat msg  │          │                                  │
│  └────────┬─────────────┘          │                                  │
│           │                        │                                  │
│           ▼                        ▼                                  │
│  ┌──────────────────────────────────────────┐                        │
│  │           Redis Pub/Sub                    │                        │
│  │           Canal: 'chat'                    │                        │
│  │                                            │                        │
│  │  3. Redis entrega a mensagem a TODOS       │                        │
│  │     os subscribers (web1 + web2)            │                        │
│  └────────────────────┬─────────────────────┘                        │
│                       │                                              │
│           ┌───────────┴───────────┐                                  │
│           ▼                       ▼                                  │
│  ┌──────────────────────┐  ┌──────────────────────┐                  │
│  │ RatchetPHP (web1)    │  │ RatchetPHP (web2)    │                  │
│  │ Subscriber recebe    │  │ Subscriber recebe    │                  │
│  │                      │  │                      │                  │
│  │ 4. Broadcast local:  │  │ 4. Broadcast local:  │                  │
│  │    → Utilizador A    │  │    → Utilizador B    │                  │
│  │      (recebe de      │  │      (recebe a msg   │                  │
│  │       volta o eco)   │  │       do web1!)      │                  │
│  └──────────────────────┘  └──────────────────────┘                  │
└──────────────────────────────────────────────────────────────────────┘
```

### Sem Pub/Sub (problema resolvido)

```
web1: [User A] ─── msg ──→ [web1] → entrega só a User A
web2: [User B] ─────────────→ nunca recebe a msg de User A
     ↑ isolado — "ilha" de tempo real
```

### Com Pub/Sub

```
web1: [User A] ─── msg ──→ [web1] → PUBLISH chat → Redis
                                              ↓
web2:                          Redis → SUBSCRIBE chat → [web2] → entrega a User B
                                                                    ↑ User B recebe!
```

---

## 📊 Estruturas de Dados no Redis

| Key | Tipo | Conteúdo |
|-----|------|----------|
| `ws:connections` | Hash | `resourceId → {server, user_id, connected_at}` |
| `ws:users` | Hash | `user_id → resourceId` |
| Canal `chat` | Pub/Sub | Mensagens broadcast entre instâncias |

---

## 🛡️ Porquê Co-localizar Ratchet com Apache e Não VMs Dedicadas

| Alternativa | Problema |
|-------------|----------|
| **VMs dedicadas para WebSocket** | Adiciona 2+ VMs sem resolver o problema de sincronização. Continuaria a ser necessário um backplane de mensagens. |
| **Sticky sessions apenas** | Não sincroniza mensagens entre instâncias. Utilizadores em web1 nunca recebem eventos de web2. |
| **WebSocket sem Redis** | Cada instância é uma ilha isolada. Escala horizontalmente em número de conexões mas não em funcionalidade. |
| **Co-localizado + Redis Pub/Sub** ✅ | Reutiliza o tier web existente. Redis resolve a sincronização cross-instance. |

---

## ✅ Verificação

```bash
# Verificar que o Ratchet está a correr em ambos os webservers
vagrant ssh web1 -c "sudo systemctl status ratchet"
vagrant ssh web2 -c "sudo systemctl status ratchet"

# Verificar que o Ratchet está a escutar no porto 8000
vagrant ssh web1 -c "ss -tlnp | grep 8000"
vagrant ssh web2 -c "ss -tlnp | grep 8000"

# Verificar conexões Redis a partir do Ratchet
vagrant ssh web1 -c "ss -tn | grep 6379"
vagrant ssh web2 -c "ss -tn | grep 6379"

# Verificar subscribers no canal Redis 'chat'
vagrant ssh storage1 -c "redis-cli -a redispass PUBSUB CHANNELS"
# Deve mostrar 'chat'

vagrant ssh storage1 -c "redis-cli -a redispass PUBSUB NUMSUB chat"
# Deve mostrar 2 subscribers (web1 + web2)

# Testar mensagem via redis-cli (simula um publisher externo)
vagrant ssh storage1 -c "redis-cli -a redispass PUBLISH chat '{\"type\":\"test\",\"message\":\"hello from redis-cli\"}'"

# Verificar conexões WebSocket no Redis
vagrant ssh storage1 -c "redis-cli -a redispass HGETALL ws:connections"
vagrant ssh storage1 -c "redis-cli -a redispass HLEN ws:connections"
```
