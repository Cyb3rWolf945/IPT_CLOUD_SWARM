from flask import Flask, request, jsonify
import subprocess
import os
import requests
import consul_manager
import base64
import json

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

def discover_any_manager():
    """Procura recursivamente no Consul se alguma região já tem um manager ativo"""
    try:
        url = f"http://{consul_manager.CONSUL_IP}:8500/v1/kv/swarm/regions/?recurse"
        res = requests.get(url, timeout=2)
        if res.status_code == 200:
            for item in res.json():
                # Se for uma chave de estado e tiver valor
                if item['Key'].endswith('/state') and item.get('Value'):
                    decoded_bytes = base64.b64decode(item['Value'])
                    state = json.loads(decoded_bytes.decode('utf-8'))
                    if state.get("manager_ip"):
                        return state
    except Exception as e:
        print(f"[ASTRONAUTA] Erro ao varrer gestores globais: {e}")
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

def run_vagrant_async(command, mc_id, role=None, manager_ip=None, local_ip=None, token=None, swarm_port=None):
    node_name = f"swarm-node-{mc_id}"
    env = os.environ.copy()
    
    env["MC_NODE_ID"] = str(mc_id)
    if role: env["NODE_ROLE"] = role
    if manager_ip: env["MANAGER_API_IP"] = manager_ip
    if local_ip: env["LOCAL_TAILSCALE_IP"] = local_ip
    if token: env["SWARM_TOKEN"] = token
    # Garantimos que a porta é passada para o processo
    env["SWARM_PORT"] = str(swarm_port) if swarm_port else "2377"
    env["NODE_REGION"] = REGION 
    
    full_command = command + [node_name]
    subprocess.Popen(full_command, env=env)


@app.route('/api/nodes/health', methods=['GET'])
def health():
    return "health 200", 200

@app.route('/api/nodes', methods=['POST'])
def handle_minecraft_trigger():
    data = request.json
    mc_id = data.get('mc_id')
    local_ip = data.get('local_ip') 
    requested_role = data.get('role') # Pode ser None, 'manager' ou 'worker'
    
    if not mc_id or not local_ip:
        return jsonify({"error": "Faltam parâmetros"}), 400
        
    node_name = f"swarm-node-{mc_id}"
    
    # Pesquisa o estado atual do cluster
    my_manager_info = discover_manager(REGION)
    any_manager_info = discover_any_manager()
    
    # As portas baseiam-se no ID (fundamental para não colidirem no teu PC sozinho)
    calculated_port = 2377 if str(mc_id) == "0" else (2377 + int(mc_id))
    
    # ==========================================
    # 1. DETERMINAR A ROLE FINAL
    # ==========================================
    role = None
    if requested_role:
        # Se o utilizador pediu explicitamente no Lua, a palavra dele é lei
        role = requested_role.lower()
        print(f"--- [OVERRIDE MANUAL] Role forçada para: {role} ---")
    else:
        # Modo Piloto Automático Original
        if not my_manager_info and not any_manager_info:
            role = "manager" # Ninguém tem, eu sou o manager global
        elif not my_manager_info and any_manager_info:
            role = "manager" # Outros têm, mas eu não. Sou a ponte regional
        else:
            role = "worker"  # Já tenho manager na minha região
        print(f"--- [PILOTO AUTOMÁTICO] Role deduzida: {role} ---")

    # ==========================================
    # 2. APLICAR LÓGICA DE CLUSTER COM BASE NA ROLE
    # ==========================================
    if role == "manager":
        if not my_manager_info and not any_manager_info:
            # Líder Primário Absoluto
            manager_ip = local_ip
            swarm_port = calculated_port
            token = ""
            print(f"--- [ELEIÇÃO LÍDER GLOBAL] {node_name} será o Manager Primário na porta {swarm_port}! ---")
            consul_manager.save_cluster_state(REGION, {
                "manager_ip": manager_ip, 
                "swarm_port": swarm_port,
                "manager_token": "", 
                "worker_token": ""
            })
            
        else:
            # Manager Secundário
            target = my_manager_info if my_manager_info else any_manager_info
            manager_ip = target["manager_ip"]
            swarm_port = target.get("swarm_port", 2377) 
            token = target["manager_token"]
            print(f"--- [CONEXÃO MANAGER SECUNDÁRIO] {node_name} liga-se a {manager_ip}:{swarm_port} ---")
            
            # Atualiza o estado da tua região se fores o primeiro manager local
            if not my_manager_info:
                consul_manager.save_cluster_state(REGION, {
                    "manager_ip": local_ip, 
                    "swarm_port": calculated_port, 
                    "manager_token": token, 
                    "worker_token": target["worker_token"]
                })
                
    elif role == "worker":
        # Trabalhador
        target = my_manager_info if my_manager_info else any_manager_info
        
        if not target:
            # Segurança: não podes ter um worker se ninguém criou um manager primeiro
            return jsonify({"error": "Erro: Nenhum Manager ativo detetado no mundo. Cria um manager primeiro!"}), 400
            
        manager_ip = target["manager_ip"]
        swarm_port = target.get("swarm_port", 2377)
        token = target.get("worker_token", "")
        print(f"--- [WORKER LOCAL] {node_name} junta-se ao cluster via {manager_ip}:{swarm_port} ---")
        
    else:
        return jsonify({"error": "Role inválida fornecida"}), 400

    # ==========================================
    # 3. LANÇAR VM
    # ==========================================
    consul_manager.register_node(REGION, mc_id, role, "provisioning")
    run_vagrant_async(["vagrant", "up"], mc_id, role, manager_ip, local_ip, token, swarm_port)
    
    return jsonify({"status": "Provisioning started", "role": role, "mode": "manual" if requested_role else "auto"}), 202

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
    app.run(host='0.0.0.0', port=5000, debug=True)