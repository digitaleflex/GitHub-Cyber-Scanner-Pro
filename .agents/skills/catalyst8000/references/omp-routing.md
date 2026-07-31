# OMP Routing Reference

## OMP Protocol Overview

### What is OMP?
- Overlay Management Protocol (OMP)
- Proprietary Cisco protocol based on BGP
- Runs between edge routers and vSmart controllers
- Distributes routes, TLOCs, and services across the SD-WAN fabric
- Uses TCP port 12346 with DTLS/TLS encryption

### OMP Peering
```
Edge Router ←→ vSmart Controller
  ↓ OMP Session
  - OMP Routes (prefixes)
  - TLOC Routes (transport locators)
  - Service Routes (services)
```

## OMP Route Types

### OMP Routes (Prefix Routes)
- Advertised by edge routers to vSmart
- Include: prefix, next-hop, TLOC, VPN, origin, path attributes
- Distributed to all edge routers by vSmart

#### Route Advertisement
```
Edge Router → vSmart:
  - Connected routes (directly connected networks)
  - Static routes (configured static routes)
  - BGP routes (redistributed from BGP)
  - OSPF routes (redistributed from OSPF)
  - EIGRP routes (redistributed from EIGRP)
```

### TLOC Routes
- Advertised by edge routers to vSmart
- Include: TLOC (system-ip:color:encap), IP address, site-id
- Used to establish IPsec tunnels between edge routers

#### TLOC Attributes
| Attribute | Description |
|-----------|-------------|
| **TLOC** | system-ip:color:encapsulation |
| **IP Address** | Transport interface IP |
| **Site ID** | Site identifier |
| **Preference** | Route preference (lower = better) |
| **Weight** | Load balancing weight |
| **Tag** | Route tag for policy matching |

### Service Routes
- Advertised by edge routers to vSmart
- Include: service type, TLOC, VPN
- Used for service insertion (firewall, IDS, etc.)

## OMP Best Path Selection

### Selection Criteria (in order)
1. **Origin Type**: OMP > Connected > Static > BGP > OSPF > EIGRP
2. **Preference**: Lower is better (default: 1 for OMP)
3. **Site ID**: Lower is better
4. **TLOC**: Prefer same color
5. **ECMP**: Equal cost multipath (up to 4 paths)

### OMP Route Attributes
| Attribute | Description | Default |
|-----------|-------------|---------|
| **Origin** | Route source | OMP |
| **Preference** | Route preference | 1 |
| **Site ID** | Originating site | Configured |
| **TLOC** | Next-hop TLOC | Auto |
| **VPN** | VPN ID | 0 |
| **Tag** | Route tag | 0 |

## OMP Configuration

### Route Redistribution
```
sdwan
 router bgp 65001
  address-family ipv4 unicast
   redistribute omp
  !
 !
 router ospf 1
  redistribute omp
 !
!
```

### OMP Advertisement Control
```
sdwan
 omp
  advertise static
  advertise connected
  advertise bgp
  advertise ospf
  advertise eigrp
 !
!
```

### OMP Graceful Restart
```
sdwan
 omp
  graceful-restart
   restart-time 300
   stalepath-time 300
  !
 !
!
```

## OMP Show Commands

### OMP Summary
```
show sdwan omp summary                  -- OMP summary
show sdwan omp routes                   -- OMP routes
show sdwan omp routes vpn 0             -- VPN 0 routes
show sdwan omp routes vpn 100           -- VPN 100 routes
```

### OMP TLOCs
```
show sdwan omp tlocs                    -- OMP TLOCs
show sdwan omp tlocs vpn 0              -- VPN 0 TLOCs
show sdwan omp tlocs detail             -- Detailed TLOC info
```

### OMP Peers
```
show sdwan omp peers                    -- OMP peers
show sdwan omp peers detail             -- Detailed peer info
```

### OMP Services
```
show sdwan omp services                 -- OMP services
show sdwan omp services detail          -- Detailed service info
```

## OMP Troubleshooting

### Common Issues

#### OMP Session Down
```
show sdwan omp peers                    -- Check peer status
show sdwan control connections          -- Check control connections
show sdwan system status                -- Check system status
ping <vsmart-ip>                        -- Check connectivity
```

#### Routes Not Advertised
```
show sdwan omp routes                   -- Check advertised routes
show sdwan omp tlocs                    -- Check TLOCs
show running-config sdwan               -- Check configuration
show sdwan policy from-vsmart           -- Check policies
```

#### Route Not Installed
```
show ip route omp                       -- Check routing table
show sdwan omp routes <prefix>          -- Check specific route
show sdwan bfd sessions                 -- Check BFD sessions
show sdwan ipsec local-sa               -- Check IPsec SAs
```

### Debug Commands
```
debug sdwan omp events                  -- OMP event debugging
debug sdwan omp packets                 -- OMP packet debugging
debug sdwan control connections         -- Control connection debugging
undebug all                             -- Disable all debugging
```

## OMP Best Practices

1. **Use consistent system-ip** scheme across fabric
2. **Monitor OMP peer status** regularly
3. **Use route filtering** to control route advertisement
4. **Configure graceful restart** for controller failover
5. **Test route redistribution** in lab before production
6. **Document OMP topology** for troubleshooting
7. **Monitor OMP route count** for scalability
8. **Use route tags** for policy matching
9. **Test OMP failover** in lab before production
10. **Test in DevNet sandbox** before production
