# Transport and Tunnels Reference

## IPsec Tunnels

### Tunnel Establishment
```
Edge Router → vBond (DTLS)
  ↓ Authentication
Edge Router → vSmart (DTLS/TLS)
  ↓ OMP Exchange
Edge Router ↔ Edge Router (IPsec)
  ↓ BFD Sessions
Data Plane Established
```

### IPsec Configuration
```
sdwan
 interface GigabitEthernet1
  tunnel-interface GigabitEthernet1
   encapsulation ipsec
   color mpls
   carrier default
   allow-service all
   hold-time 60
   hello-interval 1000
   dead-interval 3
   retransmit-interval 300
   nat-interval 60
  !
 !
!
```

### IPsec Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| **IKE Version** | IKEv2 | Internet Key Exchange |
| **Encryption** | AES-256-GCM | Data encryption |
| **Authentication** | SHA-256 | Integrity check |
| **DH Group** | 14 (2048-bit) | Key exchange |
| **Lifetime** | 86400 seconds | SA lifetime |
| **Rekey Margin** | 3600 seconds | Rekey before expiry |

### IPsec Show Commands
```
show sdwan ipsec local-sa             -- Local IPsec SAs
show sdwan ipsec outbound-sa          -- Outbound IPsec SAs
show sdwan ipsec inbound-sa           -- Inbound IPsec SAs
show sdwan ipsec connections          -- IPsec connections
show sdwan ipsec summary              -- IPsec summary
```

## BFD (Bidirectional Forwarding Detection)

### BFD Configuration
```
sdwan
 bfd
  all
   interval 1000
   multiplier 3
   poll-interval 30000
  !
 !
!
```

### BFD Parameters
| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| **Interval** | 1000ms | 300-60000ms | Hello interval |
| **Multiplier** | 3 | 3-50 | Detection multiplier |
| **Poll Interval** | 30000ms | 1000-60000ms | Poll interval |

### BFD Tuning
```
sdwan
 bfd
  all
   interval 300        -- Fast detection (300ms)
   multiplier 3        -- 3 missed = down (900ms total)
  !
 !
!
```

### BFD Show Commands
```
show sdwan bfd sessions                 -- BFD sessions
show sdwan bfd summary                  -- BFD summary
show sdwan bfd history                  -- BFD history
show sdwan bfd clients                  -- BFD clients
show sdwan bfd sessions detail          -- Detailed BFD info
```

## TLOC Extensions

### TLOC Extension Configuration
```
sdwan
 interface GigabitEthernet1
  tunnel-interface GigabitEthernet1
   encapsulation ipsec
   color internet
   tloc-extension 1
   carrier default
   allow-service all
  !
 !
!
```

### TLOC Extension Use Cases
- Multiple interfaces with same color
- Different ISPs with same color
- Load balancing across transports
- Redundancy with same transport type

## DTLS/TLS Configuration

### Control Plane Security
```
sdwan
 system
  controller-group default
  vbond 10.10.20.102 port 12346
 !
!
```

### DTLS Parameters
| Parameter | Value | Description |
|-----------|-------|-------------|
| **Port** | 12346 | DTLS/TLS port |
| **Version** | DTLS 1.2 | Datagram TLS |
| **Fallback** | TLS 1.2 | TCP fallback |
| **Certificate** | vManage-signed | Device authentication |

## Transport Interface Types

### MPLS Transport
```
sdwan
 interface GigabitEthernet1
  tunnel-interface GigabitEthernet1
   encapsulation ipsec
   color mpls
   carrier default
   allow-service all
  !
 !
!
```

### Internet Transport
```
sdwan
 interface GigabitEthernet2
  tunnel-interface GigabitEthernet2
   encapsulation ipsec
   color internet
   carrier default
   allow-service all
  !
 !
!
```

### LTE/5G Transport
```
sdwan
 interface Cellular0
  tunnel-interface Cellular0
   encapsulation ipsec
   color lte
   carrier default
   allow-service all
  !
 !
!
```

### Metro Ethernet Transport
```
sdwan
 interface GigabitEthernet3
  tunnel-interface GigabitEthernet3
   encapsulation ipsec
   color metro-ethernet
   carrier default
   allow-service all
  !
 !
!
```

## Tunnel SLA

### SLA Configuration
```
sdwan
 tunnel-sla
  name Voice-SLA
   latency 150
   loss 1
   jitter 30
  !
  name Video-SLA
   latency 200
   loss 2
   jitter 50
  !
 !
!
```

### SLA Show Commands
```
show sdwan tunnel sla                  -- Tunnel SLA status
show sdwan tunnel sla detail           -- Detailed SLA info
show sdwan tunnel statistics           -- Tunnel statistics
```

## Common Scenarios

### Scenario 1: Dual Transport (MPLS + Internet)
```
sdwan
 interface GigabitEthernet1
  tunnel-interface GigabitEthernet1
   encapsulation ipsec
   color mpls
   carrier default
   allow-service all
  !
 !
 interface GigabitEthernet2
  tunnel-interface GigabitEthernet2
   encapsulation ipsec
   color internet
   carrier default
   allow-service all
  !
 !
!
```

### Scenario 2: BFD Tuning for Fast Failover
```
sdwan
 bfd
  all
   interval 300
   multiplier 3
  !
 !
!
```

### Scenario 3: Verify Tunnel Status
```
show sdwan ipsec local-sa
show sdwan bfd sessions
show sdwan tunnel sla
show sdwan tunnel statistics
```

## Best Practices

1. **Use both MPLS and Internet** transports for redundancy
2. **Tune BFD** for fast failover (300ms interval, 3 multiplier)
3. **Monitor IPsec SAs** for tunnel health
4. **Use TLOC extensions** for multiple interfaces with same color
5. **Configure SLA classes** for application-aware routing
6. **Test tunnel failover** in lab before production
7. **Monitor BFD sessions** regularly
8. **Use consistent colors** across the fabric
9. **Document transport topology** for troubleshooting
10. **Test in DevNet sandbox** before production
