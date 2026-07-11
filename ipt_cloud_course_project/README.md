# Cloud Computing and Virtualization - Project Base App

This repo contains the demo web application that should be used as base in the final project (versions A + B). It consists of a web app (`/app`), and a websockets server (`/ws`). These run in a single Linux VM provisioned with Vagrant and shell scripts.

## Pre-requisites
Install the latest versions of VirtualBox, VirtualBox Extension Pack and Vagrant:
* VirtualBox: https://www.virtualbox.org/wiki/Downloads
* VirtualBox Extension Pack: https://www.virtualbox.org/wiki/Downloads
* Vagrant:  https://developer.hashicorp.com/vagrant/install

**Note**: After upgrading VirtualBox it is recommended to upgrade the guest additions as well. 

## Vagrant
The VM is defined in the Vagrantfile. Currently uses Ubuntu Server 22.04 and both services run on it. The provisioning is defined in the `provision/web.sh` script, which will:
* Install Apache2 HTTP Server
* Install PHP (and other libraries)
* Install PostgreSQL
  * Create a database and user
  * Import the `provision/dump.sql` script
* Run composer to install dependencies
* Setup the web app in apache2
* Update the `DEPLOY_DATE` in the `.env` file

You are free to change it as needed to achieve your desired configuration. If RAM/CPU is an issue, you might want to consider using a lighter distro, such as Alpine Linux, for some of your VMs (see [generic/alpine38](https://app.vagrantup.com/generic/boxes/alpine38) or [boxomatic/alpine-3.18](https://app.vagrantup.com/boxomatic/boxes/alpine-3.18), note that the package manager and other commands are different so you need to Google).

After provisioning, the web app should be accessible at http://192.168.44.10. In this base version, you must manually start the WebSockets server (see below).

## Web App
The web app is a set of small php pages (security was not a concern) that ilustrate typical functionalities of a modern application, namely:
* Static / simple pages
* Sessions
* Database layer
* File uploads
* Data via WebSockets

Dependencies are installed via `composer`, and settings are defined in the `.env` file.

## WebSockets Server
The websockets server is a simple one file server, which receives messages on port 8000 and broadcasts to all connected clients. Dependencies are also installed via composer. It uses `Ratchet` as the websockets server, and should be started in the CLI with:
```bash
vagrant ssh
cd /vagrant/ws
php websockets_server.php
# you may want to configure it as a daemon / service to autostart by default
```

## Load Testing
If you want to load test the web app, you can download tools such as [hey](https://github.com/rakyll/hey), or [vegeta](https://github.com/tsenart/vegeta), and run sets of requests against specific endpoints.

Example under Win10, using Git BASH:
```bash
# create a folder to dl the tools (outside of the project)
mkdir HTTPLoad
cd HTTPLoad

# download hey and vegeta
curl -o hey.exe https://hey-release.s3.us-east-2.amazonaws.com/hey_windows_amd64
curl -LJO https://github.com/tsenart/vegeta/releases/download/v12.8.3/vegeta-12.8.3-windows-amd64.zip
unzip vegeta-12.8.3-windows-amd64.zip
rm vegeta-12.8.3-windows-amd64.zip

# check help (under other cli you might use hey.exe...)
./hey -h
./vegeta -h

# run hey with default settings
./hey http://192.168.44.10/db.php

Summary:
  Total:        5.4095 secs
  Slowest:      4.9218 secs
  Fastest:      0.1381 secs
  Average:      0.7955 secs
  Requests/sec: 36.9719

Response time histogram:
  0.138 [1]     |
  0.616 [119]   |■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
  1.095 [50]    |■■■■■■■■■■■■■■■■■
  1.573 [11]    |■■■■
  2.052 [2]     |■
  2.530 [0]     |
  3.008 [6]     |■■
  3.487 [0]     |
  3.965 [1]     |
  4.443 [7]     |■■
  4.922 [3]     |■

Latency distribution:
  10% in 0.1739 secs
  25% in 0.2481 secs
  50% in 0.5157 secs
  75% in 0.7591 secs
  90% in 1.3820 secs
  95% in 3.9908 secs
  99% in 4.9216 secs

Details (average, fastest, slowest):
  DNS+dialup:   0.0006 secs, 0.1381 secs, 4.9218 secs
  DNS-lookup:   0.0000 secs, 0.0000 secs, 0.0000 secs
  req write:    0.0000 secs, 0.0000 secs, 0.0004 secs
  resp wait:    0.7947 secs, 0.1378 secs, 4.9170 secs
  resp read:    0.0002 secs, 0.0001 secs, 0.0011 secs

Status code distribution:
  [200] 200 responses

# Run vegeta test (from vegeta -h)
 echo "GET http://192.168.44.10/db.php" | ./vegeta attack -duration=5s | tee results.bin | ./vegeta report
Requests      [total, rate, throughput]         250, 50.19, 44.65
Duration      [total, attack, wait]             5.599s, 4.981s, 618.628ms
Latencies     [min, mean, 50, 90, 95, 99, max]  125.287ms, 444.677ms, 213.447ms, 1.186s, 2.453s, 3.427s, 3.466s
Bytes In      [total, mean]                     1039250, 4157.00
Bytes Out     [total, mean]                     0, 0.00
Success       [ratio]                           100.00%
Status Codes  [code:count]                      200:250
Error Set:

# Generate vegeta report based on previous test
./vegeta report -type=json results.bin > metrics.json

# Plot results as latency vs time elapsed (to plot.html)
cat results.bin | ./vegeta plot > plot.html

# Show histogram (terminal)
cat results.bin | ./vegeta report -type="hist[0,100ms,200ms,300ms]"
Bucket           #    %       Histogram
[0s,     100ms]  0    0.00%
[100ms,  200ms]  103  41.20%  ##############################
[200ms,  300ms]  80   32.00%  ########################
[300ms,  +Inf]   67   26.80%  ####################
```
