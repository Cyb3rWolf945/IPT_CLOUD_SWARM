# 1. ir buscar o caminho relativo
    #1.1. verificar linux or windows (so isto por agora)
    #1.2. verificar se o minecraft existe
# 2. criar uma pasta (auto increment no nome)
# 3. adicionar startup.lua a cada pasta

# adicionar os 3 files by default (start, stop and destroy)

from pathlib import Path
import platform
import os
from time import sleep
import shutil
import subprocess


def hehe():
    system = platform.system()
    provisioning_start = Path.cwd() / "provisioning_pcs_minicraft"
    list_lua = ["test_trigger_start.lua", "test_trigger_destroy.lua", "test_trigger_stop.lua", "control_panel.lua", "startup.lua"]
    #check system operating system
    if system == "Windows":
        mc = Path.home() / "AppData" / "Roaming" / ".minecraft" / "saves" / "SwarmSolution" / "computercraft" / "computer"
    elif system == "Linux":
        mc = Path.home() / ".minecraft" / "versions" / "CCTweaked" / "saves" / "SwarmSolution" / "computercraft" / "computer"
    else:
        mc = None


    #verify minecraft path
    if mc and mc.exists():
        print("path: ", mc)

        api_ip = subprocess.check_output(
        ["tailscale", "ip", "--4"],
        text=True).strip()

        print("API_IP --> ", api_ip)

        while True:
            list = os.listdir(mc)

            #if list is not None
            if list and len(list) > 0:
                for l in os.listdir(mc):
                    check_contents(l)
                    dst = mc / l
                    #just copy all provisioning files to every directory
                    for item in list_lua:
                        print("teste", provisioning_start, " ", item)
                        with open(provisioning_start / item, "r") as f:
                            ye = f.read()
                        ye = ye.replace("__API_IP__", api_ip)

                        with open(dst / item, "w") as f:
                            f.write(ye)
                        
                    print("directory: ", l)
            sleep(30)

                    

def check_contents(l):
    system = platform.system()
    print(system)
    if system == "Windows":
        mc = Path.home() / "AppData" / "Roaming" / ".minecraft" / "saves" / "SwarmSolution" / "computercraft" / "computer" / l
    elif system == "Linux":
        mc = Path.home() / ".minecraft" / "versions" / "CCTweaked" / "saves" / "SwarmSolution" / "computercraft" / "computer" / l
    else:
        mc = None
    print(os.listdir(mc))



hehe()