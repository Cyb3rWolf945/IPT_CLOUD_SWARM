-- Substitui pelo IP do teu computador Linux no Tailscale
--local LOCAL_IP = "100.97.214.63" 
local API_IP = "__API_IP__"
local url = "http://" .. API_IP .. ":5000/api/nodes"
local MC_ID = tostring(os.getComputerID())

-- Criar a tabela 'data' antes de enviar
local data = {
    mc_id = MC_ID,
    local_ip = API_IP
}

print("A enviar sinal para a API...")

-- Agora o textutils.serializeJSON(data) vai funcionar corretamente
local response = http.post(url, textutils.serializeJSON(data), {["Content-Type"] = "application/json"})

if response then
    print("Sucesso! API respondeu:")
    print(response.readAll())
    response.close()
else
    print("Erro: A API não respondeu. Verifica o IP ou a Firewall.")
end