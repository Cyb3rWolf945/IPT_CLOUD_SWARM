# Minecraft flow

## Objective

Prepare VMs on the host's machine provisioned with all necessary services to join a cluster all through a Minecraft world.

---

## Context

This is executed upon the execution of Lua scripts developed for this flow in a computer inside Minecraft provided by the devs of the mod "CC:Tweaked".

---

## Prerequisite

- Install Forge/Fabric (47.x), CC:Tweaked mod (1.20.1) and Minecraft (1.20.1)
- Install Ansible
- Install Vagrant
- Install VirtualBox
- Create a folder on .minecraft named "mods" if Forge/Fabric doesn't create it automatically
- Create a world named "SwarmSolution"
- Clone the GitHub repo

---

## Tools


| Provisioning --> Lua Scripts --> Flask API --> Consul --> Vagrant and Ansible |

---

## Flow

### 1. Provisioning

For provisioning a Python script is execute which will populate every single computer placed inside of Minecraft with all Lua Scripts needed.

---

### 2. Lua Scripts

They'll allow to execute some operations related with the VMs created on the host machine such as:

- start
- stop
- destroy

### 3. Flask API

The Lua Scripts will send HTTP POST requests for each operation named before.

---

Just in case:

docker rm consul-swarm

docker run -d --name=consul-swarm \
  -p 8500:8500 \
  -h consul-server \
  hashicorp/consul:latest agent -dev -client=0.0.0.0 -ui