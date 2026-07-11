-- Substitui pelo IP do teu computador central no Tailscale se mudar
--local TAILSCALE_IP = "100.97.214.63"
local API_IP = "__API_IP__"
local API_URL = "http://" .. API_IP .. ":5000/api/nodes/stop"
local MC_ID = tostring(os.getComputerID())

print("A enviar sinal de paragem para swarm-node-" .. MC_ID .. "...")

local payload = { mc_id = MC_ID }

local response = http.post(
    API_URL, 
    textutils.serializeJSON(payload), 
    {["Content-Type"] = "application/json"}
)

if response then
    print("API respondeu: " .. response.readAll())
    response.close()
else
    print("Erro: Falha na ligação à API. Verifica o Tailscale/Firewall.")
end