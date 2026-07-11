import requests

# IP da máquina que aloja o contentor do Consul (Rede Tailscale)
CONSUL_IP = "100.97.214.63"
CONSUL_KV_URL = f"http://{CONSUL_IP}:8500/v1/kv/swarm/state"

def get_cluster_state():
    """
    Lê o estado atual do cluster diretamente do Consul KV.
    Retorna um dicionário vazio se não encontrar dados ou falhar.
    """
    try:
        # O parâmetro ?raw faz o Consul devolver o JSON puro que lá guardámos
        response = requests.get(f"{CONSUL_KV_URL}?raw", timeout=2)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        print(f"[ERRO - CONSUL] Não foi possível contactar o Consul em {CONSUL_IP}")
    return {}

def save_cluster_state(state):
    """
    Grava ou atualiza o estado do cluster no Consul KV.
    Retorna True se for bem sucedido, False caso contrário.
    """
    try:
        response = requests.put(CONSUL_KV_URL, json=state, timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        print("[ERRO - CONSUL] Falha ao gravar o estado no Consul.")
        return False

def delete_cluster_state():
    """
    Remove a chave de estado do Consul (útil para resets/cleanups).
    """
    try:
        response = requests.delete(CONSUL_KV_URL, timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        print("[ERRO - CONSUL] Falha ao limpar o estado no Consul.")
        return False

def register_node(mc_id, role=None, status="unknown"):
    """Grava ou atualiza a informação de um nó específico no Consul KV"""
    # Se a role for omitida (como no STOP), tentamos ler o que já lá estava para não perder o dado
    url = f"http://{CONSUL_IP}:8500/v1/kv/swarm/nodes/swarm-node-{mc_id}"
    
    current_role = role
    if not current_role:
        try:
            res = requests.get(url, timeout=2)
            if res.status_code == 200:
                current_role = res.json()[0].get('role', 'worker')
        except:
            current_role = "worker"

    node_data = {
        "node_name": f"swarm-node-{mc_id}",
        "role": current_role,
        "status": status
    }
    try:
        requests.put(url, json=node_data, timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False

def delete_node(mc_id):
    """Remove a chave de um nó específico do Consul KV"""
    url = f"http://{CONSUL_IP}:8500/v1/kv/swarm/nodes/swarm-node-{mc_id}"
    try:
        requests.delete(url, timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False

def clear_all_nodes():
    """Wipe total da pasta de nós no Consul KV (?recurse)"""
    url = f"http://{CONSUL_IP}:8500/v1/kv/swarm/nodes/?recurse"
    try:
        requests.delete(url, timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False