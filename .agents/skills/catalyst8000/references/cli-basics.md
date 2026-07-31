# Catalyst 8000 CLI Basics

## Accessing the Router

### SSH Access
```bash
ssh admin@<cat8000v-ip>
```

### Console Access
```bash
# Via hypervisor console
# ESXi: VM Console
# KVM: virsh console <vm-name>
```

## CLI Modes

### EXEC Mode
```
Cat8000v#
```
- View-only commands
- `show`, `ping`, `traceroute`, `clear`

### Configuration Mode
```
Cat8000v# configure terminal
Cat8000v(config)#
```
- All configuration commands
- Changes applied immediately (no commit model like IOS XR)

### SD-WAN Specific Modes
```
Cat8000v(config)# sdwan
Cat8000v(config-sdwan)#
```

## Basic SD-WAN Configuration

### System Settings
```
sdwan
 system
  system-ip 1.1.1.1
  site-id 100
  org-name MyOrg
  controller-group default
  vbond 10.10.20.102 port 12346
 !
!
```

### Interface Configuration
```
interface GigabitEthernet1
 ip address 10.10.20.110 255.255.255.0
 no shutdown
!

interface GigabitEthernet2
 ip address dhcp
 no shutdown
!
```

### Transport Interface
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

### Service Interface
```
sdwan
 interface GigabitEthernet3
  no tunnel-interface
  ipv4 address 192.168.1.1/24
  allow-service all
 !
!
```

## Essential Show Commands

### System Status
```
show version                          -- IOS XE version
show sdwan system status              -- SD-WAN system status
show sdwan control local-properties   -- Local control properties
show sdwan control connections        -- Control connections
show sdwan control summary            -- Control connection summary
```

### Interface Status
```
show ip interface brief               -- Interface summary
show interfaces                       -- Detailed interface info
show sdwan interface                  -- SD-WAN interface status
```

### BFD Status
```
show sdwan bfd sessions               -- BFD sessions
show sdwan bfd summary                -- BFD summary
show sdwan bfd history                -- BFD history
```

### OMP Status
```
show sdwan omp summary                -- OMP summary
show sdwan omp routes                 -- OMP routes
show sdwan omp tlocs                  -- OMP TLOCs
show sdwan omp peers                  -- OMP peers
```

### Tunnel Status
```
show sdwan ipsec local-sa             -- Local IPsec SA
show sdwan ipsec outbound-sa          -- Outbound IPsec SA
show sdwan tunnel sla                 -- Tunnel SLA
show sdwan tunnel statistics          -- Tunnel statistics
```

### Policy Status
```
show sdwan policy from-vsmart         -- Policies from vSmart
show sdwan policy access-list-associations  -- ACL associations
show sdwan policy data-policy         -- Data policy status
```

## Configuration Management

### Save Configuration
```
write memory                          -- Save to startup-config
copy running-config startup-config    -- Alternative save command
```

### View Configuration
```
show running-config                   -- Full running config
show running-config sdwan             -- SD-WAN config only
show running-config interface         -- Interface config only
```

### Clear Commands
```
clear sdwan bfd session               -- Clear BFD sessions
clear sdwan ipsec local-sa            -- Clear IPsec SA
clear sdwan omp routes                -- Clear OMP routes
clear sdwan control connections       -- Clear control connections
```

## Common CLI Scenarios

### Scenario 1: Basic Cat8000v Setup
```
sdwan
 system
  system-ip 1.1.1.1
  site-id 100
  org-name MyOrg
  controller-group default
  vbond 10.10.20.102 port 12346
 !
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

### Scenario 2: Verify SD-WAN Status
```
show sdwan system status
show sdwan control connections
show sdwan bfd sessions
show sdwan omp peers
show sdwan omp routes
```

## Best Practices

1. **Use consistent system-ip** scheme (e.g., loopback IP)
2. **Use meaningful site-ids** (e.g., branch number)
3. **Configure both MPLS and Internet** transports for redundancy
4. **Monitor BFD sessions** for tunnel health
5. **Use show commands** before making changes
6. **Save configuration** after changes
7. **Document all changes** with comments
8. **Test in DevNet sandbox** before production
9. **Use vManage templates** for consistency
10. **Monitor control connections** to vSmart/vBond
