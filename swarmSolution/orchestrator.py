from flask import Flask, request, jsonify
import subprocess
import os
import requests
import consul_manager

app = Flask(__name__)
cluster_state = {}


def discover_manager():
    """Procura o estado do cluster diretamente no Consul KV"""
    state = consul_manager.get_cluster_state()
    if state and state.get("manager_ip"):
        return state
    return None

@app.route("/test", methods=["GET"])
def get_hostname():

    #erase contents.txt lines
    with open("contents.txt", "w") as f:
        f.truncate()
    #fetch tailscale devices
    command = "tailscale ip --4"
    result = subprocess.check_output(command, shell=True, text=True)
    #write to file lol
    with open("contents.txt", "w") as f:
        f.write(result)

    return result

def run_vagrant_async(command, mc_id, role=None, manager_ip=None, local_ip=None, token=None):
    """Única função assíncrona para gerir o Vagrant com variáveis de ambiente"""
    node_name = f"swarm-node-{mc_id}"
    env = os.environ.copy()
    
    env["MC_NODE_ID"] = str(mc_id)
    if role: env["NODE_ROLE"] = role
    if manager_ip: env["MANAGER_API_IP"] = manager_ip
    if local_ip: env["LOCAL_TAILSCALE_IP"] = local_ip
    if token: env["SWARM_TOKEN"] = token
    
    full_command = command + [node_name]
    print(f"--- [EXEC] A executar comando: {' '.join(full_command)} ---")
    subprocess.Popen(full_command, env=env)


@app.route('/api/nodes/health', methods=['GET'])
def health():
    
    return "health 200", 200

@app.route('/api/nodes', methods=['POST'])
def handle_minecraft_trigger():
    data = request.json
    mc_id = data.get('mc_id')
    local_ip = data.get('local_ip') # Este deve ser o teu IP Tailscale enviado pelo computador do Minecraft
    
    if not mc_id or not local_ip:
        return jsonify({"error": "Faltam parâmetros"}), 400
        
    node_name = f"swarm-node-{mc_id}"
    
    # Agora consulta o Consul centralizado através do discover_manager()
    manager_info = discover_manager()
    
    if manager_info is None:
        role = "manager"
        manager_ip = local_ip
        token = ""
        print(f"--- [ELEIÇÃO - CONSUL] Nenhum manager no Consul. {node_name} será o MANAGER! ---")
        consul_manager.save_cluster_state({"manager_ip": manager_ip, "worker_token": ""})
    else:
        role = "worker"
        manager_ip = manager_info["manager_ip"]
        token = manager_info["worker_token"]
        print(f"--- [ELEIÇÃO - CONSUL] Manager obtido do Consul ({manager_ip}). {node_name} será WORKER. ---")

    # [CONSUL] Regista o nó individualmente com o estado inicial
    consul_manager.register_node(mc_id, role, "provisioning")

    run_vagrant_async(["vagrant", "up"], mc_id, role, manager_ip, local_ip, token)
    return jsonify({"status": "Provisioning started", "role": role}), 202

@app.route('/api/cluster/state', methods=['PUT', 'GET'])
def manage_state():
    if request.method == 'PUT':
        state_data = request.json
        # Grava o estado recebido do Ansible diretamente no Consul
        if consul_manager.save_cluster_state(state_data):
            print(f"--- [CONSUL] Novo estado do cluster persistido: {state_data} ---")
            return jsonify({"status": "State updated in Consul"}), 200
        return jsonify({"status": "Failed to update Consul"}), 500
        
    # No método GET, vai buscar o estado ao Consul
    current_state = consul_manager.get_cluster_state()
    return jsonify(current_state if current_state else {}), 200

@app.route('/api/nodes/stop', methods=['POST'])
def stop_node():
    mc_id = request.json.get('mc_id')
    if not mc_id: return jsonify({"error": "Falta mc_id"}), 400
    print(f"--- [API] A desligar (Halt) swarm-node-{mc_id} ---")
    run_vagrant_async(["vagrant", "halt"], mc_id)
    return jsonify({"status": "Halt initiated", "mc_id": mc_id}), 200

@app.route('/api/nodes/destroy', methods=['POST'])
def destroy_node():
    mc_id = request.json.get('mc_id')
    if not mc_id: return jsonify({"error": "Falta mc_id"}), 400
    print(f"--- [API] A destruir (Destroy) swarm-node-{mc_id} ---")
    
    # Se o nó que vais destruir for o 0 (Manager), limpa o Consul para permitir novas eleições futuras
    if str(mc_id) == "0":
        consul_manager.delete_cluster_state()
        print(f"--- [CONSUL] swarm-node-0 removido. Estado limpo do Consul. ---")
        
    # [CONSUL] Apaga o registo deste nó específico do KV
    consul_manager.delete_node(mc_id)
        
    run_vagrant_async(["vagrant", "destroy", "-f"], mc_id)
    return jsonify({"status": "Destruction initiated", "mc_id": mc_id}), 200

@app.route('/api/nodes/cleanup-all', methods=['POST'])
def cleanup_all():
    print(f"--- [API] EMERGÊNCIA: A destruir todas as VMs ---")
    subprocess.Popen(["vagrant", "destroy", "-f"])
    
    # Limpa completamente o estado centralizado no Consul
    consul_manager.delete_cluster_state()
    # [CONSUL] Limpa a árvore de nós inteira
    consul_manager.clear_all_nodes()
    print(f"--- [CONSUL] WIPE TOTAL: Estado limpo do Consul. ---")
    
    return jsonify({"status": "Cleanup initiated"}), 200

@app.route('/api/nodes/<mc_id>/status', methods=['PUT'])
def update_node_status(mc_id):
    data = request.json
    status = data.get('status', 'unknown')
    role = data.get('role')
    
    # Atualiza o nó específico no Consul para "provisioned"
    consul_manager.register_node(mc_id, role=role, status=status)
    print(f"--- [CONSUL] Ciclo de vida: swarm-node-{mc_id} passou para {status.upper()} ({role}) ---")
    return jsonify({"status": "Node status updated successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
