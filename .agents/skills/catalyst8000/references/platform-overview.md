# Catalyst 8000 Platform Overview

## Platform Family

### Catalyst 8000v (Virtual)
- **Cat8000v** - Virtual SD-WAN edge router for cloud/VM deployment
- **Cat8000v-L** - Low-throughput variant for small branches
- **Cat8000v-H** - High-throughput variant for large branches/hubs
- **Cat8000-E** - Physical edge router (hardware appliance)

### Supported Hypervisors
- VMware ESXi
- KVM
- Hyper-V
- AWS EC2
- Azure
- Google Cloud Platform

## SD-WAN Fabric Components

### Control Plane
| Component | Function | Port | Protocol |
|-----------|----------|------|----------|
| **vManage** | Network management, monitoring, policy | 443 | HTTPS |
| **vSmart** | OMP controller, policy distribution | 12346 | DTLS/TLS |
| **vBond** | Initial orchestrator, NAT traversal | 12346 | DTLS |

### Data Plane
| Component | Function | Port | Protocol |
|-----------|----------|------|----------|
| **Cat8000v** | WAN edge router, data forwarding | 12346 (BFD) | IPsec/BFD |
| **IPsec** | Encrypted data tunnels | UDP 500/4500 | IPsec |
| **BFD** | Fast failure detection | UDP 12346 | BFD |
| **DTLS** | Control plane encryption | UDP 12346 | DTLS/TLS |

## Device Roles

### vEdge (Legacy)
- Viptela-based edge routers
- Viptela OS
- Being replaced by Catalyst 8000v

### cEdge (IOS XE)
- Catalyst 8000v routers
- IOS XE SD-WAN software
- Supports all SD-WAN features

### vSmart Controller
- Receives routes from edge routers via OMP
- Distributes routes and policies to edges
- Can be deployed in active/standby or active/active

### vBond Orchestrator
- First point of contact for new devices
- Performs NAT traversal
- Introduces devices to vSmart and vManage

### vManage NMS
- Single pane of glass for the fabric
- Configuration templates
- Policy management
- Monitoring and troubleshooting

## Architecture Modes

### Centralized Control
```
vManage → vSmart → vBond → Cat8000v
              ↓
         OMP Routes
         Policies
```

### Full Mesh
- All edge routers establish IPsec tunnels with each other
- Default behavior for same TLOC color
- Controlled by OMP and topology

### Hub-and-Spoke
- Spokes connect only to hubs
- Hubs connect to each other
- Configured via OMP policy

### Mesh Groups
- Selective full mesh between specific routers
- Reduces tunnel count in large fabrics

## Key SD-WAN Concepts

### TLOC (Transport Locator)
- Unique identifier for a transport interface
- Format: `<system-ip>:<color>:<encapsulation>`
- Example: `1.1.1.1:mpls:ipsec`

### OMP (Overlay Management Protocol)
- Runs between edge routers and vSmart controllers
- Advertises:
  - OMP routes (prefixes)
  - TLOC routes (transport locators)
  - Service routes (services offered)

### BFD (Bidirectional Forwarding Detection)
- Fast failure detection over IPsec tunnels
- Default interval: 1000ms, multiplier: 3
- Can be tuned to 300ms for faster detection

### SLA Classes
- Define performance thresholds for application traffic
- Metrics: latency, loss, jitter
- Used in application-aware routing policies

## Platform Specifications

| Feature | Cat8000v-L | Cat8000v | Cat8000v-H |
|---------|-----------|----------|------------|
| **Throughput** | Up to 50 Mbps | Up to 200 Mbps | Up to 1 Gbps |
| **Tunnels** | Up to 100 | Up to 200 | Up to 500 |
| **CPU** | 2 vCPU | 4 vCPU | 8 vCPU |
| **Memory** | 4 GB | 8 GB | 16 GB |
| **Interfaces** | 2-4 | 4-8 | 8-16 |

## DevNet Sandbox Topology

### SD-WAN 20.10 Sandbox
```
┌─────────────────────────────────────────────┐
│  vManage: 10.10.20.100                      │
│  vSmart:  10.10.20.101                      │
│  vBond:   10.10.20.102                      │
│                                              │
│  edge1:   10.10.20.110 (Cat8000v)           │
│  edge2:   10.10.20.120 (Cat8000v)           │
│  edge3:   10.10.20.130 (Cat8000v)           │
│  edge4:   10.10.20.140 (Cat8000v)           │
└─────────────────────────────────────────────┘
```

### Always-On Sandbox
- **vManage:** `https://sandbox-sdwan.cisco.com`
- **Username:** `admin`
- **Password:** `C1sco12345`
- Pre-configured fabric with 4 edge routers
- Ready for API testing and automation

## Best Practices

1. **Use feature templates** for consistent configuration
2. **Validate templates** before attaching to devices
3. **Use device templates** to bundle feature templates
4. **Monitor BFD sessions** after any transport changes
5. **Test policies** in vManage before pushing to fabric
6. **Use maintenance windows** for fabric-wide changes
7. **Document rollback procedures** before making changes
8. **Monitor vSmart CPU/memory** for controller health
9. **Use SLA classes** for application-aware routing
10. **Test in DevNet sandbox** before production deployment
