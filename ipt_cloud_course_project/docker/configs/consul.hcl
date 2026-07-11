# Consul Agent Configuration (Docker)
# Used by Patroni for leader election / DCS
datacenter = "dc1"
data_dir = "/consul/data"
log_level = "INFO"

# Bind to all interfaces inside the container
bind_addr = "0.0.0.0"
client_addr = "0.0.0.0"

# Advertise the container IP (eth0 on Docker bridge)
advertise_addr = "{{ GetInterfaceIP \"eth0\" }}"

# Connect to Consul servers to form a cluster
retry_join = [
  "tasks.consul"
]

# Bootstrap expectation: 3 nodes for quorum
bootstrap_expect = 3

# Server mode (all 3 nodes are servers for HA)
server = true
ui_config {
  enabled = true
}

# Enable Consul Connect (service mesh) — optional
connect {
  enabled = false
}

# Performance tuning
performance {
  raft_multiplier = 1
}
