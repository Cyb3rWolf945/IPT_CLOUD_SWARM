# 🔄 Keepalived nos Load Balancers — Fase 1 (VMs)

> **Objetivo:** VIP `192.168.44.10` a flutuar entre `lb1` (MASTER) e `lb2` (BACKUP) via VRRP.

---

## 📁 Ficheiros Necessários

| # | Ficheiro | Propósito |
|---|----------|-----------|
| 1 | `ansible/roles/keepalived/templates/keepalived.conf.j2` | Template VRRP |
| 2 | `ansible/roles/keepalived/tasks/main.yml` | Instalação e deploy da config |
| 3 | `ansible/roles/keepalived/handlers/main.yml` | Restart do serviço |
| 4 | `ansible/site.yml` (excerto) | Atribuição da role aos load balancers |
| 5 | `Vagrantfile` (excerto) | IPs estáticos das VMs |
| 6 | `ansible/inventory.ini` (excerto) | Mapeamento hostname → IP |

---

## 1. Template VRRP

**Ficheiro:** `ansible/roles/keepalived/templates/keepalived.conf.j2`

```nginx
vrrp_instance VI_1 {
    state {{ 'MASTER' if inventory_hostname == 'lb1' else 'BACKUP' }}
    
    interface eth1 
    
    virtual_router_id 51
    priority {{ 101 if inventory_hostname == 'lb1' else 100 }}
    advert_int 1
    
    authentication {
        auth_type PASS
        auth_pass ipt_cloud_2026
    }
    
    virtual_ipaddress {
        192.168.44.10/24
    }
}
```

### Lógica do Template

| Variável Jinja2 | lb1 | lb2 |
|-----------------|-----|-----|
| `state` | `MASTER` | `BACKUP` |
| `priority` | `101` | `100` |

- O template usa `inventory_hostname` para decidir qual o papel de cada nó
- `advert_int 1` → anúncios VRRP a cada 1 segundo → failover em ~1s

---

## 2. Tasks Ansible

**Ficheiro:** `ansible/roles/keepalived/tasks/main.yml`

```yaml
---
- name: Instalar keepalived
  apt:
    name: keepalived
    state: present

- name: Configurar keepalived
  template:
    src: keepalived.conf.j2
    dest: /etc/keepalived/keepalived.conf
  notify: restart keepalived
```

---

## 3. Handler

**Ficheiro:** `ansible/roles/keepalived/handlers/main.yml`

```yaml
---
- name: restart keepalived
  service:
    name: keepalived
    state: restarted
```

- O handler é disparado sempre que o template `keepalived.conf.j2` é alterado

---

## 4. Atribuição no Playbook

**Ficheiro:** `ansible/site.yml` (excerto)

```yaml
- hosts: loadbalancers
  become: yes
  roles:
    - keepalived
    - nginx
    - haproxy
```

- A role `keepalived` é a **primeira** a ser aplicada nos load balancers
- Corre em **lb1** e **lb2**

---

## 5. IPs das VMs

**Ficheiro:** `Vagrantfile` (excerto)

```ruby
config.vm.define "lb1" do |lb1|
    lb1.vm.hostname = "lb1"
    lb1.vm.network "private_network", ip: "192.168.44.11"
end

config.vm.define "lb2" do |lb2|
    lb2.vm.hostname = "lb2"
    lb2.vm.network "private_network", ip: "192.168.44.12"
end
```

---

## 6. Inventory

**Ficheiro:** `ansible/inventory.ini` (excerto)

```ini
[loadbalancers]
lb1 ansible_host=192.168.44.11 ansible_ssh_private_key_file=~/.ssh/vagrant_keys/lb1_key
lb2 ansible_host=192.168.44.12 ansible_ssh_private_key_file=~/.ssh/vagrant_keys/lb2_key
```

---

## 🔍 Comportamento em Funcionamento

```
Estado normal:
┌─────────────────────────────────────────┐
│  lb1 (MASTER, prio 101)                 │
│  ↑ 192.168.44.11 (eth1)                │
│  ↑ 192.168.44.10 (VIP)                 │
│  Envia VRRP advertisements a cada 1s    │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  lb2 (BACKUP, prio 100)                 │
│  ↑ 192.168.44.12 (eth1)                │
│  Ouve advertisements. Se não receber    │
│  durante 3s (3 × advert_int), assume.   │
└─────────────────────────────────────────┘

Se lb1 falhar (T+0s):
  T+0s  — lb1 deixa de enviar VRRP advertisements
  T+3s  — lb2 detecta falta de anúncios (3 × advert_int)
  T+3s  — lb2 promove-se a MASTER, assume VIP 192.168.44.10
  T+3s  — Tráfego retoma (clientes nem notam, IP é o mesmo)

Quando lb1 recupera (preempt):
  lb1 volta como MASTER (priority 101 > 100), reassume o VIP
```

---

## ✅ Verificação

Depois do `vagrant up` + `ansible-playbook site.yml`:

```bash
# Verificar que o VIP está no lb1
vagrant ssh lb1 -c "ip addr show eth1 | grep 192.168.44.10"

# Verificar estado do VRRP
vagrant ssh lb1 -c "sudo systemctl status keepalived"
vagrant ssh lb2 -c "sudo systemctl status keepalived"

# Testar failover — matar lb1 e ver VIP migrar para lb2
vagrant halt lb1
vagrant ssh lb2 -c "ip addr show eth1 | grep 192.168.44.10"
```
