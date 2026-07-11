local pc_id = os.getComputerID()
local url = "http://100.97.214.63:5000/api/nodes" 
local url2 = "http://100.97.214.63:5000/health"



--http.post(url2, textutils.serializeJSON({mc_id = pc_id}), {["Content-Type"] = "application/json"})
http.get(url2)
print("hehe enviado hihi")