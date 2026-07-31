# vSmart Controller and vBond Orchestrator Reference

## vSmart Controller

### Role
- Receives OMP routes from all edge routers
- Applies control policies
- Distributes OMP routes and policies to edge routers
- Centralized control plane for the SD-WAN fabric

### Deployment
- Active/Standby: One active, one standby
- Active/Active: Multiple active controllers (recommended)
- Minimum: 1 (lab), Recommended: 3 (production)

### vSmart Configuration (CLI)
```
sdwan
 system
  system-ip 2.2.2.2
  site-id 1000
  org-name MyOrg
  controller-group default
  vbond 10.10.20.102 port 12346
 !
!
```

### vSmart Show Commands
```
show sdwan control connections        -- Edge router connections
show sdwan omp summary                -- OMP summary
show sdwan omp routes                 -- OMP routes received
show sdwan omp tlocs                  -- OMP TLOCs received
show sdwan omp peers                  -- OMP peer status
show sdwan system status              -- System status
```

### vSmart Policy Distribution
```
vManage → vSmart → Edge Routers
  ↓         ↓          ↓
Templates  Policies   OMP Routes
```

## vBond Orchestrator

### Role
- First point of contact for new edge routers
- Authenticates devices with vManage
- Performs NAT traversal
- Introduces devices to vSmart controllers
- Does NOT participate in data plane

### Deployment
- Single instance sufficient for most deployments
- Can be deployed active/standby for HA
- Must be reachable from all edge routers

### vBond Configuration (CLI)
```
sdwan
 system
  system-ip 3.3.3.3
  site-id 1001
  org-name MyOrg
  controller-group default
 !
!
```

### vBond Show Commands
```
show sdwan control connections        -- Edge router connections
show sdwan system status              -- System status
show sdwan control local-properties   -- Local properties
```

## OMP (Overlay Management Protocol)

### OMP Peers
- Edge routers establish OMP sessions with vSmart controllers
- vSmart controllers establish OMP sessions with each other
- OMP runs over DTLS/TLS on UDP port 12346

### OMP Route Types

#### OMP Routes (Prefixes)
- Advertised by edge routers
- Include: prefix, next-hop, TLOC, VPN, origin, path attributes
- Distributed to all edge routers by vSmart

#### TLOC Routes
- Advertised by edge routers
- Include: TLOC (system-ip:color:encap), IP address, site-id
- Used to establish IPsec tunnels between edge routers

#### Service Routes
- Advertised by edge routers
- Include: service type, TLOC, VPN
- Used for service insertion (firewall, IDS, etc.)

### OMP Advertisement

#### From Edge to vSmart
```
Edge Router → vSmart:
  - OMP Routes (local prefixes)
  - TLOC Routes (transport interfaces)
  - Service Routes (services offered)
```

#### From vSmart to Edge
```
vSmart → Edge Router:
  - OMP Routes (from all edges)
  - TLOC Routes (from all edges)
  - Service Routes (from all edges)
  - Policies (centralized policies)
```

### OMP Best Path Selection
1. **Origin Type**: OMP > Connected > Static > BGP
2. **Preference**: Lower is better
3. **Site ID**: Lower is better
4. **TLOC**: Prefer same color
5. **ECMP**: Equal cost multipath

## TLOC (Transport Locator)

### TLOC Format
```
<system-ip>:<color>:<encapsulation>

Examples:
1.1.1.1:mpls:ipsec
1.1.1.1:internet:ipsec
1.1.1.1:lte:ipsec
```

### TLOC Colors
| Color | Use Case | Default Preference |
|-------|----------|-------------------|
| mpls | MPLS transport | 1 |
| internet | Internet transport | 1 |
| biz-internet | Business internet | 1 |
| public-internet | Public internet | 1 |
| lte | LTE/4G transport | 1 |
| 3g | 3G transport | 1 |
| metro-ethernet | Metro Ethernet | 1 |

### TLOC Extensions
- **TLOC Extension**: Used when multiple interfaces share same color
- **Format**: `<system-ip>:<color>:<encapsulation>:<extension>`
- **Example**: `1.1.1.1:internet:ipsec:1`

### TLOC Advertisement
```
Edge Router advertises TLOC to vSmart:
  - System IP
  - Color (mpls, internet, lte, etc.)
  - Encapsulation (ipsec, gre)
  - IP address
  - Site ID
  - Preference
```

## Control Connections

### Edge to vSmart
```
Edge Router → vSmart:
  Protocol: DTLS/TLS
  Port: 12346
  Purpose: OMP route exchange
  State: Up (established)
```

### Edge to vBond
```
Edge Router → vBond:
  Protocol: DTLS
  Port: 12346
  Purpose: Initial authentication, NAT traversal
  State: Up (established)
```

### vSmart to vSmart
```
vSmart → vSmart:
  Protocol: DTLS/TLS
  Port: 12346
  Purpose: OMP route synchronization
  State: Up (established)
```

## Common Scenarios

### Scenario 1: Add vSmart Controller
```
vManage Configuration:
1. Navigate to Configuration > Devices
2. Click Add Device > vSmart
3. Configure system-ip, site-id, org-name
4. Generate certificate
5. Activate device
```

### Scenario 2: Add vBond Orchestrator
```
vManage Configuration:
1. Navigate to Configuration > Devices
2. Click Add Device > vBond
3. Configure system-ip, site-id, org-name
4. Generate certificate
5. Activate device
```

### Scenario 3: Verify OMP Status
```
show sdwan omp summary
show sdwan omp routes
show sdwan omp tlocs
show sdwan omp peers
show sdwan control connections
```

## Best Practices

1. **Deploy multiple vSmart controllers** for HA (minimum 3)
2. **Use unique system-ips** for all controllers
3. **Monitor OMP peer status** regularly
4. **Use consistent org-name** across all devices
5. **Test controller failover** in lab before production
6. **Document controller topology** for troubleshooting
7. **Monitor vSmart CPU/memory** for controller health
8. **Use DTLS/TLS** for all control connections
9. **Verify NAT traversal** through vBond
10. **Test in DevNet sandbox** before production
