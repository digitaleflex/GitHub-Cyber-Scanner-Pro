# Sensor Build Recipes — step-by-step

Verified build recipes for each sensor type. Copy-paste ready.

---

## Recipe A — Linux transparent-bridge sensor (production-grade)

**Target:** a 1U Linux box (Ubuntu 22.04/24.04 or RHEL 9) with 2 NICs + a bypass tap, placed inline on a critical uplink. Runs netwatch 24/7, streams metrics centrally.

### Hardware
- 2× 10 GbE NICs (e.g. Intel X550 or Solarflare) — faster than the monitored link
- Bypass tap (Solarflare/Intel/Silicom bypass NIC OR standalone hardware tap)
- 16 GB RAM, 8+ cores for 1G; more for 10G

### 1. Install tools
```bash
# NetWatch pre-built binary (Linux x86_64)
curl -fsSL -o /tmp/nw.tar.gz \
  https://github.com/matthart1983/netwatch/releases/download/v0.26.1/netwatch-linux-x86_64-static.tar.gz
tar -xzf /tmp/nw.tar.gz -C /tmp
install -m 0755 /tmp/netwatch-linux-x86_64-static /usr/local/bin/netwatch
# (or use the non-static build if your distro has libpcap)

# RustNet (optional, for process-attribution TUI)
cargo install rustnet-monitor 2>/dev/null || sudo apt install rustnet 2>/dev/null

# tshark / dumpcap (for scripted capture)
sudo apt install -y tshark          # Debian/Ubuntu
sudo dnf install -y wireshark-cli   # RHEL/Fedora
```

### 2. Persistent bridge (Ubuntu netplan)
See `scripts/bridge-setup.sh` for the full script; here's the netplan:
```yaml
# /etc/netplan/01-bridge.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0: {dhcp4: no}
    eth1: {dhcp4: no}
  bridges:
    br0:
      interfaces: [eth0, eth1]
      stp: false
      forward-delay: 0
      addresses: [10.255.1.10/24]
      routes:
        - to: default
          via: 10.255.1.1
```
```bash
sudo netplan apply
# Verify transparency: the upstream device should still ping unchanged
```

### 3. Disable offloads (so the sensor sees real frames)
```bash
for i in eth0 eth1 br0; do
  sudo ethtool -K $i gro off tso off lro off gso off 2>/dev/null
done
# Make it persistent via a NetworkManager dispatcher script or systemd unit
# (see scripts/bridge-setup.sh for the persistent variant)
```

### 4. Pin netwatch to the bridge interface + run headless streaming
```bash
# Pin capture to br0 via config (netwatch has no -i flag; interface is config/TUI-selected)
mkdir -p ~/.config/netwatch
netwatch --generate-config 2>/dev/null || true   # creates config.toml
sed -i 's/^capture_interface = ""/capture_interface = "br0"/' ~/.config/netwatch/config.toml
# Verify:
grep capture_interface ~/.config/netwatch/config.toml

# Streaming to central Prometheus + NetWatch Cloud (interface comes from config)
sudo netwatch daemon --metrics \
  --remote https://netwatch.corp/api --api-key "$NW_KEY"
```
For interactive incident work, SSH in and run the TUI:
```bash
ssh sensor@10.255.1.10
sudo netwatch
```

### 5. systemd unit for headless streaming
```ini
# /etc/systemd/system/netwatch-sensor.service
[Unit]
Description=NetWatch inline bridge sensor
After=network-online.target
[Service]
# Pin capture to br0 via config (netwatch has no -i flag; interface is config-selected)
ExecStartPre=/bin/sh -c 'mkdir -p /root/.config/netwatch && /usr/local/bin/netwatch --generate-config 2>/dev/null; sed -i "s/^capture_interface = .*/capture_interface = \"br0\"/" /root/.config/netwatch/config.toml'
ExecStart=/usr/local/bin/netwatch daemon --metrics --remote https://netwatch.corp/api --api-key ${NW_KEY}
EnvironmentFile=/etc/netwatch/env
Restart=always
[Install]
WantedBy=multi-user.target
```
```bash
echo "NW_KEY=your-key-here" | sudo tee /etc/netwatch/env
sudo systemctl daemon-reload && sudo systemctl enable --now netwatch-sensor
```

---

## Recipe B — Windows SPAN-destination sensor

**Target:** a Windows Server 2019+ or Windows 11 box plugged into a SPAN destination port on a Cisco switch. Runs RustNet for live TUI + Pktmon for headless capture.

### 1. Install prerequisites
```powershell
# Install Npcap (required by RustNet) — download from https://npcap.com
# During install, enable "WinPcap API-compatible Mode"

# Install RustNet
choco install rustnet

# Pktmon is already built in — nothing to install
# Optional: Wireshark + Npcap for tshark
choco install wireshark
```

### 2. Identify the SPAN destination interface
```powershell
pktmon list                     # find the interface name plugged into the SPAN port
# e.g. "Ethernet 2"
Get-NetAdapter | Format-Table Name, InterfaceDescription, LinkSpeed
```

### 3. Configure SPAN on the Cisco switch (source)
```
monitor session 1 source interface Gi1/0/1 both
monitor session 1 destination interface Gi1/0/24      ! Windows sensor plugged here
```

### 4. Live TUI (RustNet)
```powershell
# Run as Administrator
rustnet -i "Ethernet 2"
# Tabs: 1 Overview 2 Details 3 Interfaces 4 Graph 5 Help
# Filter: port:443 sni:github.com process:chrome
```

### 5. Headless capture to disk (Pktmon)
```powershell
# As Administrator
pktmon filter add F1 -t TCP -p 443
pktmon start --capture --comp nics -m real-time     # live console
# OR capture to disk:
pktmon start --capture --comp nics --pkt-size 0 -f C:\caps\cap.etl
# ... later ...
pktmon stop
pktmon etl2pcap C:\caps\cap.etl -o C:\caps\cap.pcapng
# Analyze with tshark:
tshark -r C:\caps\cap.pcapng -Y "tcp.analysis.retransmission"
```

### 6. Scheduled 24/7 capture (Task Scheduler)
```powershell
# See scripts/pktmon-sensor.ps1 for a rotating-capture script
# Schedule it via Task Scheduler at startup:
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\scripts\pktmon-sensor.ps1"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "PktmonSensor" -Action $action -Trigger $trigger -RunLevel Highest -User SYSTEM
```

---

## Recipe C — Windows L3-gateway sensor (single NIC, inline)

**Target:** a Windows box that becomes the default gateway for a subnet, hairpin-routing traffic through one NIC. See `scripts/win-l3-gateway.ps1`.

```powershell
# Enable IP forwarding
Set-NetIPInterface -InterfaceAlias "Ethernet" -Forwarding Enabled

# Assign the gateway IP that hosts will point at
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 10.0.0.1 -PrefixLength 24

# (Optional) NAT to an upstream if the sensor isn't the real router
New-NetNat -Name "SensorNAT" -InternalIPInterfaceAddressPrefix 10.0.0.0/24

# Point observed hosts' default gateway at 10.0.0.1 (DHCP option 3 or manual)

# Run RustNet on the interface (sees both directions, hairpin)
rustnet -i "Ethernet"
```

### Caveats
- You must re-gateway every observed host (invasive)
- It's a routed hop — TTL decrements, ARP doesn't traverse
- SPOF — if the sensor dies, the subnet loses its gateway (mitigate with VRRP to a backup, or keepalived on a Linux backup)

---

## Recipe D — Linux L3-gateway sensor (single NIC, inline)

```bash
# Enable IP forwarding
echo "net.ipv4.ip_forward=1" | sudo tee /etc/sysctl.d/99-forward.conf
sudo sysctl -p /etc/sysctl.d/99-forward.conf

# Assign the gateway IP on eth0
sudo ip addr add 10.0.0.1/24 dev eth0

# Point hosts at 10.0.0.1 as their default gateway (DHCP option 3 or manual)

# Optional NAT to upstream (if sensor isn't the real next-hop)
sudo iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth1 -j MASQUERADE  # if 2nd NIC exists

# Run netwatch (sees both directions on the one NIC)
sudo netwatch
```

---

## Recipe E — Headless streaming sensor (Linux, Prometheus + remote)

For a sensor that does nothing but stream metrics to a central dashboard — no TUI.

```bash
# Prometheus scrape target (local) + remote streaming (central)
sudo netwatch daemon --metrics --remote https://netwatch.corp/api --api-key "$NW_KEY"
# Local /metrics on 127.0.0.1:9464 — scrape with Prometheus:
#   scrape_configs:
#     - job_name: 'netwatch'
#       static_configs: [{ targets: ['sensor-host:9464'] }]
```

---

## Recipe F — VM-based sensor on a hypervisor (vSwitch mirror)

For VM-to-VM traffic without touching physical NICs.

### Hyper-V
```powershell
# Sensor VM's vNIC = destination, target VM's vNIC = source
Set-VMNetworkAdapter -VMName SensorVM -PortMirroring Destination
Set-VMNetworkAdapter -VMName TargetVM  -PortMirroring Source
# Inside SensorVM (Linux): sudo netwatch
# Inside SensorVM (Windows): rustnet -i "Ethernet"
```

### KVM/libvirt
```bash
# Mirror a bridge port to the sensor VM's vNIC (libvirt net commands)
# See libvirt docs for `virsh net-update` with `<mirror>` element on the bridge
```

### ESXi
- vSphere Distributed Switch → port mirroring session → sensor VM port as destination

---

## Verification checklist (run after building any sensor)

```bash
# Linux
ip -s link show br0              # RX/TX counters climbing = traffic flowing
bridge link                       # eth0, eth1 listed as enslaved to br0
sudo netwatch             # Packets tab shows traffic = capture working
ethtool -k br0 | grep -E 'gro|tso|lro|gso'   # all off = offloads disabled
# From the Cisco device: ping should still work unchanged (proves transparency)

# Windows
pktmon counters --comp nics       # counters climbing = traffic flowing
rustnet -i "Ethernet 2"          # Overview tab shows connections = capture working
# From the Cisco device: ping should still work (SPAN: passive, nothing to break)
```

If counters climb but the sensor tool shows no traffic, you're capturing on the wrong interface (e.g. on `eth0` instead of `br0`) or the SPAN direction is `rx`-only.
