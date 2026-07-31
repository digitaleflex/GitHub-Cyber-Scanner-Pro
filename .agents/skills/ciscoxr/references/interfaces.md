# IOS XR Interface Configuration Reference

## Interface Naming Convention

### Physical Interfaces
```
<type><slot>/<rack>/<module>/<port>

Examples:
GigabitEthernet0/0/0/0    -- Slot 0, Rack 0, Module 0, Port 0
TenGigE0/0/0/1            -- 10GE interface
HundredGigE0/0/0/0        -- 100GE interface
FourHundredGigE0/0/0/0    -- 400GE interface (Cisco 8000)
```

### Logical Interfaces
```
Bundle-Ether<id>          -- LAG/Bond interface
Loopback<id>              -- Loopback interface
Tunnel-te<id>             -- Traffic Engineering tunnel
Tunnel-ip<id>             -- IP tunnel
BVI<id>                   -- Bridge Virtual Interface
```

## Basic Interface Configuration

### Physical Interface
```
interface GigabitEthernet0/0/0/0
 description "Uplink to Core Router"
 ipv4 address 10.0.0.1 255.255.255.252
 ipv6 address 2001:db8::1/64
 mtu 9216
 no shutdown
!
```

### Loopback Interface
```
interface Loopback0
 description "Router ID Interface"
 ipv4 address 1.1.1.1 255.255.255.255
 ipv6 address 2001:db8::1:1/128
!
```

## Sub-Interfaces

### 802.1Q VLAN Sub-Interface
```
interface GigabitEthernet0/0/0/0.100 l2transport
 description "Customer VLAN 100"
 encapsulation dot1q 100
!

interface GigabitEthernet0/0/0/0.100
 description "Routed VLAN 100"
 encapsulation dot1q 100
 ipv4 address 192.168.100.1 255.255.255.0
!
```

### QinQ (Double Tag) Sub-Interface
```
interface GigabitEthernet0/0/0/0.200 l2transport
 description "QinQ Service"
 encapsulation dot1q 100 second-dot1q 200
!
```

### Untagged Sub-Interface
```
interface GigabitEthernet0/0/0/0.1 l2transport
 encapsulation untagged
!
```

## Bundle-Ether (LAG) Configuration

### Create Bundle Interface
```
interface Bundle-Ether10
 description "Core LAG"
 ipv4 address 10.0.0.1 255.255.255.252
 lacp period short
!
```

### Add Members to Bundle
```
interface TenGigE0/0/0/0
 bundle id 10 mode active
!
interface TenGigE0/0/0/1
 bundle id 10 mode active
!
```

### Bundle Modes
- `active`: LACP active mode (recommended)
- `passive`: LACP passive mode
- `on`: Static bundle (no LACP)

### Bundle Load-Balancing
```
load-balancing
 hash-field
  l3 source-ip destination-ip
  l4 source-port destination-port
 !
!
```

## Ethernet Services (EVC)

### Create EFP (Ethernet Flow Point)
```
interface GigabitEthernet0/0/0/0
 service instance 100 ethernet
  description "Customer A - VLAN 100"
  encapsulation dot1q 100
  bridge-domain 100
 !
!
```

### EFP Encapsulation Options
```
encapsulation dot1q 100                    -- Single tag
encapsulation dot1q 100 second-dot1q 200   -- Double tag
encapsulation untagged                      -- Untagged
encapsulation default                       -- All frames
encapsulation dot1q 100-200                -- Range
encapsulation dot1q 100,200,300            -- List
```

## Interface Features

### MTU Configuration
```
interface GigabitEthernet0/0/0/0
 mtu 9216              -- System MTU
 ipv4 mtu 9000         -- IPv4 MTU (must be <= system MTU)
!
```

### Speed and Duplex
```
interface GigabitEthernet0/0/0/0
 negotiation auto      -- Auto-negotiation (default)
 speed 1000            -- Force 1Gbps
 duplex full           -- Force full duplex
!
```

### Link Debounce
```
interface GigabitEthernet0/0/0/0
 link debounce time 100    -- 100ms debounce
!
```

### Error Disable Recovery
```
errdisable recovery
 cause all
 interval 300    -- 5 minutes
!
```

## Interface Monitoring

### Show Commands
```
show interfaces                           -- All interfaces
show interfaces brief                     -- Brief summary
show interfaces <name>                    -- Specific interface
show interfaces <name> counters           -- Interface counters
show interfaces <name> errors             -- Error statistics
show interfaces <name> transceiver        -- Optical transceiver info
show interfaces <name> transceiver detail -- Detailed optical stats
show bundle                               -- Bundle status
show lacp neighbor                        -- LACP neighbor info
```

### Interface Counters
```
show controllers <interface>              -- Hardware counters
show controllers <interface> counters     -- Detailed counters
clear counters <interface>                -- Clear counters
```

## Common Interface Scenarios

### Scenario 1: Point-to-Point Link
```
interface HundredGigE0/0/0/0
 description "P2P to PE-Router-2"
 ipv4 address 10.0.0.1 255.255.255.252
 mtu 9216
 no shutdown
!
```

### Scenario 2: Multi-VLAN Trunk
```
interface TenGigE0/0/0/0
 description "Trunk to Switch"
!
interface TenGigE0/0/0/0.10
 encapsulation dot1q 10
 ipv4 address 192.168.10.1 255.255.255.0
!
interface TenGigE0/0/0/0.20
 encapsulation dot1q 20
 ipv4 address 192.168.20.1 255.255.255.0
!
```

### Scenario 3: LAG with LACP
```
interface Bundle-Ether100
 description "Server LAG"
 ipv4 address 10.100.0.1 255.255.255.0
 lacp period short
!
interface TenGigE0/0/0/0
 bundle id 100 mode active
!
interface TenGigE0/0/0/1
 bundle id 100 mode active
!
```

### Scenario 4: Service Provider Access
```
interface GigabitEthernet0/0/0/0
 description "Access Port"
!
interface GigabitEthernet0/0/0/0.100 l2transport
 encapsulation dot1q 100
 rewrite ingress tag pop 1 symmetric
 bridge-domain 100
!
interface GigabitEthernet0/0/0/0.200 l2transport
 encapsulation dot1q 200
 rewrite ingress tag pop 1 symmetric
 bridge-domain 200
!
```

## Best Practices

1. **Always add descriptions** to interfaces
2. **Use consistent MTU** across the path (9216 for MPLS/SR networks)
3. **Use LACP active mode** for bundles (not static)
4. **Configure loopback interfaces** for router IDs and BGP peering
5. **Use sub-interfaces** for VLAN routing (not switchports)
6. **Monitor optical levels** on fiber interfaces
7. **Enable link debounce** on unstable links
8. **Document interface assignments** in descriptions
9. **Use /31 subnets** for point-to-point links (RFC 3021)
10. **Verify transceiver compatibility** before deployment
