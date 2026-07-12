from flask import Flask, request, jsonify
import subprocess
import os
import requests
import consul_manager

app = Flask(__name__)

def get_region_id():
    """
    Deduz o ID da região baseado no IP Tailscale local desta máquina orchestrator.
    Substitui pontos por hífens para ser seguro usar no URL do Consul KV.
    """
    try:
        ip = subprocess.check_output("tailscale ip --4", shell=True, text=True).strip()
        return ip.replace(".", "-")
    except Exception:
        return "default-region"

# Define a região atual deste orchestrator no arranque
REGION = get_region_id()
print(f"--- [INFO] Orchestrator iniciado na Região Simulada: {REGION} ---")


def discover_manager(region):
    """Procura o estado do cluster para a região atual no Consul KV"""
    state = consul_manager.get_cluster_state(region)
    if state and state.get("manager_ip"):
        return state
    return None

@app.route("/test", methods=["GET"])
def get_hostname():
    with open("contents.txt", "w") as f:
        f.truncate()
    command = "tailscale ip --4"
    result = subprocess.check_output(command, shell=True, text=True)
    with open("contents.txt", "w") as f:
        f.write(result)
    return result

def run_vagrant_async(command, mc_id, role=None, manager_ip=None, local_ip=None, token=None):
    node_name = f"swarm-node-{mc_id}"
    env = os.environ.copy()
    
    env["MC_NODE_ID"] = str(mc_id)
    if role: env["NODE_ROLE"] = role
    if manager_ip: env["MANAGER_API_IP"] = manager_ip
    if local_ip: env["LOCAL_TAILSCALE_IP"] = local_ip
    if token: env["SWARM_TOKEN"] = token
    # Passa também a região para o Vagrant/Ansible saberem a que região pertencem
    env["NODE_REGION"] = REGION 
    
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
    local_ip = data.get('local_ip') 
    
    if not mc_id or not local_ip:
        return jsonify({"error": "Faltam parâmetros"}), 400
        
    node_name = f"swarm-node-{mc_id}"
    
    # [MULTI-REGION] Procura o manager apenas na região deste orchestrator
    manager_info = discover_manager(REGION)
    
    if manager_info is None:
        role = "manager"
        manager_ip = local_ip
        token = ""
        print(f"--- [ELEIÇÃO - {REGION}] Nenhum manager na região. {node_name} será o MANAGER Regional! ---")
        consul_manager.save_cluster_state(REGION, {"manager_ip": manager_ip, "worker_token": ""})
    else:
        role = "worker"
        manager_ip = manager_info["manager_ip"]
        token = manager_info["worker_token"]
        print(f"--- [ELEIÇÃO - {REGION}] Manager regional obtido ({manager_ip}). {node_name} será WORKER. ---")

    # [CONSUL] Regista o nó dentro da sua região
    consul_manager.register_node(REGION, mc_id, role, "provisioning")

    run_vagrant_async(["vagrant", "up"], mc_id, role, manager_ip, local_ip, token)
    return jsonify({"status": "Provisioning started", "role": role, "region": REGION}), 202

@app.route('/api/cluster/state', methods=['PUT', 'GET'])
def manage_state():
    if request.method == 'PUT':
        state_data = request.json
        if consul_manager.save_cluster_state(REGION, state_data):
            print(f"--- [CONSUL] Novo estado do cluster regional ({REGION}) persistido: {state_data} ---")
            return jsonify({"status": f"State updated in Consul for region {REGION}"}), 200
        return jsonify({"status": "Failed to update Consul"}), 500
        
    current_state = consul_manager.get_cluster_state(REGION)
    return jsonify(current_state if current_state else {}), 200

@app.route('/api/nodes/stop', methods=['POST'])
def stop_node():
    mc_id = request.json.get('mc_id')
    if not mc_id: return jsonify({"error": "Falta mc_id"}), 400
    print(f"--- [API] A desligar (Halt) swarm-node-{mc_id} na região {REGION} ---")
    run_vagrant_async(["vagrant", "halt"], mc_id)
    return jsonify({"status": "Halt initiated", "mc_id": mc_id}), 200

@app.route('/api/nodes/destroy', methods=['POST'])
def destroy_node():
    mc_id = request.json.get('mc_id')
    if not mc_id: return jsonify({"error": "Falta mc_id"}), 400
    print(f"--- [API] A destruir (Destroy) swarm-node-{mc_id} na região {REGION} ---")
    
    if str(mc_id) == "0":
        consul_manager.delete_cluster_state(REGION)
        print(f"--- [CONSUL] swarm-node-0 removido. Estado regional limpo do Consul. ---")
        
    consul_manager.delete_node(REGION, mc_id)
    run_vagrant_async(["vagrant", "destroy", "-f"], mc_id)
    return jsonify({"status": "Destruction initiated", "mc_id": mc_id}), 200

@app.route('/api/nodes/cleanup-all', methods=['POST'])
def cleanup_all():
    print(f"--- [API] EMERGÊNCIA: A destruir todas as VMs locais na região {REGION} ---")
    subprocess.Popen(["vagrant", "destroy", "-f"])
    
    consul_manager.delete_cluster_state(REGION)
    consul_manager.clear_all_nodes(REGION)
    print(f"--- [CONSUL] WIPE REGIONAL: Estado limpo para a região {REGION}. ---")
    
    return jsonify({"status": "Cleanup initiated"}), 200

@app.route('/api/nodes/<mc_id>/status', methods=['PUT'])
def update_node_status(mc_id):
    data = request.json
    status = data.get('status', 'unknown')
    role = data.get('role')
    
    consul_manager.register_node(REGION, mc_id, role=role, status=status)
    print(f"--- [CONSUL] Ciclo de vida: swarm-node-{mc_id} em {REGION} passou para {status.upper()} ({role}) ---")
    return jsonify({"status": "Node status updated successfully"}), 200

if __name__ == '__main__':
    # Removido o duplicado do app.run que tinhas no teu ficheiro
    app.run(host='0.0.0.0', port=5000, debug=True)