-- Substitui pelo IP do teu computador Linux no Tailscale
local API_IP = "__API_IP__"
local url = "http://" .. API_IP .. ":5000/api/nodes"
local MC_ID = tostring(os.getComputerID())

local requested_role = nil

-- Ciclo para pedir a role até o utilizador escrever uma opção válida
while true do
    print("----------------------------------------")
    print("O que queres criar no Node " .. MC_ID .. "?")
    print(" -> Escreve 'manager'")
    print(" -> Escreve 'worker'")
    print(" -> Ou deixa em branco (Enter) para automatico")
    print("----------------------------------------")
    write("Escolha: ")
    
    local input = string.lower(io.read())
    
    -- Limpa espaços em branco acidentais
    input = input:match("^%s*(.-)%s*$") 
    
    if input == "manager" or input == "worker" then
        requested_role = input
        break -- Sai do ciclo, a escolha é válida
    elseif input == "" or input == "automatico" then
        requested_role = nil
        break -- Sai do ciclo, entra em modo automático
    else
        print("\n[ERRO] Escolha invalida. Tenta novamente.")
        sleep(1) -- Pequena pausa para leres o erro
    end
end

-- Criar a tabela 'data'
local data = {
    mc_id = MC_ID,
    local_ip = API_IP
}

-- Se o utilizador pediu uma role específica, adicionamos à payload
if requested_role then
    data.role = requested_role
    print("\nA enviar sinal para forçar a criação de um [" .. string.upper(requested_role) .. "]...")
else
    print("\nA enviar sinal em modo [AUTOMATICO] para a API...")
end

local response = http.post(url, textutils.serializeJSON(data), {["Content-Type"] = "application/json"})

if response then
    print("Sucesso! API respondeu:")
    print(response.readAll())
    response.close()
else
    print("Erro: A API não respondeu. Verifica o IP ou a Firewall.")
end