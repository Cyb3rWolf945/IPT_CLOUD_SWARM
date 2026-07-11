local API_IP = "http://" + "__API_IP__" + "/api/nodes/health" -- IP do PC que corre esta API

print("A verificar a saude da API...")

-- http.get aceita apenas: URL e Opcionalmente Headers
local response = http.get(API_BASE, {["Content-Type"] = "application/json"})

if response then
    print("Resposta da API: " .. response.readAll())
    response.close()
else
    print("Erro na ligacao com a API.")
end
