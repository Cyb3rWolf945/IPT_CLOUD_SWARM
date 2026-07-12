import requests
import base64
import json

# IP da máquina que aloja o contentor do Consul (Rede Tailscale)
CONSUL_IP = "100.97.214.63"
BASE_URL = f"http://{CONSUL_IP}:8500/v1/kv/swarm/regions"

def get_cluster_state(region):
    """Lê o estado atual do cluster de uma região específica do Consul KV."""
    try:
        response = requests.get(f"{BASE_URL}/{region}/state?raw", timeout=2)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        print(f"[ERRO - CONSUL] Não foi possível contactar o Consul em {CONSUL_IP} para a região {region}")
    return {}

def save_cluster_state(region, state):
    """Grava ou atualiza o estado do cluster de uma região no Consul KV."""
    try:
        response = requests.put(f"{BASE_URL}/{region}/state", json=state, timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        print(f"[ERRO - CONSUL] Falha ao gravar o estado no Consul para a região {region}.")
        return False

def delete_cluster_state(region):
    """Remove a chave de estado de uma região do Consul."""
    try:
        response = requests.delete(f"{BASE_URL}/{region}/state", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        print(f"[ERRO - CONSUL] Falha ao limpar o estado no Consul para a região {region}.")
        return False

def register_node(region, mc_id, role=None, status="unknown"):
    """Grava ou atualiza a informação de um nó numa região específica."""
    url = f"{BASE_URL}/{region}/nodes/swarm-node-{mc_id}"
    
    current_role = role
    if not current_role:
        try:
            res = requests.get(url, timeout=2)
            if res.status_code == 200 and res.json():
                # Decodifica o valor que vem em Base64 da resposta em formato de lista do Consul
                val_b64 = res.json()[0].get('Value')
                if val_b64:
                    old_data = json.loads(base64.b64decode(val_b64).decode('utf-8'))
                    current_role = old_data.get('role', 'worker')
        except:
            current_role = "worker"

    node_data = {
        "node_name": f"swarm-node-{mc_id}",
        "role": current_role,
        "status": status,
        "region": region
    }
    try:
        requests.put(url, json=node_data, timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False

def delete_node(region, mc_id):
    """Remove a chave de um nó específico de uma região."""
    url = f"{BASE_URL}/{region}/nodes/swarm-node-{mc_id}"
    try:
        requests.delete(url, timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False

def clear_all_nodes(region):
    """Wipe total da pasta de nós de uma região específica."""
    url = f"{BASE_URL}/{region}/nodes/?recurse"
    try:
        requests.delete(url, timeout=2)
        return True
    except requests.exceptions.RequestException:
        return Falseimport requests
import base64
import json

# IP da máquina que aloja o contentor do Consul (Rede Tailscale)
CONSUL_IP = "100.97.214.63"
BASE_URL = f"http://{CONSUL_IP}:8500/v1/kv/swarm/regions"

def get_cluster_state(region):
    """Lê o estado atual do cluster de uma região específica do Consul KV."""
    try:
        response = requests.get(f"{BASE_URL}/{region}/state?raw", timeout=2)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        print(f"[ERRO - CONSUL] Não foi possível contactar o Consul em {CONSUL_IP} para a região {region}")
    return {}

def save_cluster_state(region, state):
    """Grava ou atualiza o estado do cluster de uma região no Consul KV."""
    try:
        response = requests.put(f"{BASE_URL}/{region}/state", json=state, timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        print(f"[ERRO - CONSUL] Falha ao gravar o estado no Consul para a região {region}.")
        return False

def delete_cluster_state(region):
    """Remove a chave de estado de uma região do Consul."""
    try:
        response = requests.delete(f"{BASE_URL}/{region}/state", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        print(f"[ERRO - CONSUL] Falha ao limpar o estado no Consul para a região {region}.")
        return False

def register_node(region, mc_id, role=None, status="unknown"):
    """Grava ou atualiza a informação de um nó numa região específica."""
    url = f"{BASE_URL}/{region}/nodes/swarm-node-{mc_id}"
    
    current_role = role
    if not current_role:
        try:
            res = requests.get(url, timeout=2)
            if res.status_code == 200 and res.json():
                # Decodifica o valor que vem em Base64 da resposta em formato de lista do Consul
                val_b64 = res.json()[0].get('Value')
                if val_b64:
                    old_data = json.loads(base64.b64decode(val_b64).decode('utf-8'))
                    current_role = old_data.get('role', 'worker')
        except:
            current_role = "worker"

    node_data = {
        "node_name": f"swarm-node-{mc_id}",
        "role": current_role,
        "status": status,
        "region": region
    }
    try:
        requests.put(url, json=node_data, timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False

def delete_node(region, mc_id):
    """Remove a chave de um nó específico de uma região."""
    url = f"{BASE_URL}/{region}/nodes/swarm-node-{mc_id}"
    try:
        requests.delete(url, timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False

def clear_all_nodes(region):
    """Wipe total da pasta de nós de uma região específica."""
    url = f"{BASE_URL}/{region}/nodes/?recurse"
    try:
        requests.delete(url, timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False