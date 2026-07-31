# IOS XR BGP Configuration Reference

## Basic BGP Configuration

### Single AF BGP
```
router bgp 65001
 bgp router-id 1.1.1.1
 bgp log-neighbor-changes
 address-family ipv4 unicast
  network 10.0.0.0/24
  network 192.168.1.0/24
 !
 neighbor 10.0.0.2
  remote-as 65002
  description "Peer to AS65002"
  address-family ipv4 unicast
   route-policy PASS-ALL in
   route-policy PASS-ALL out
  !
 !
!
```

### Multi-AF BGP (IPv4 + IPv6)
```
router bgp 65001
 bgp router-id 1.1.1.1
 address-family ipv4 unicast
 !
 address-family ipv6 unicast
 !
 neighbor 10.0.0.2
  remote-as 65002
  address-family ipv4 unicast
  !
  address-family ipv6 unicast
  !
 !
 neighbor 2001:db8::2
  remote-as 65002
  address-family ipv6 unicast
  !
 !
!
```

## BGP Peer Groups and Templates

### Session Group (Common session parameters)
```
router bgp 65001
 neighbor-group EBGP-GROUP
  remote-as 65002
  ebgp-multihop 2
  update-source Loopback0
  bfd fast-detect multiplier 3 minimum-interval 150
  address-family ipv4 unicast
  !
 !
 neighbor 10.0.0.2
  use neighbor-group EBGP-GROUP
 !
 neighbor 10.0.0.3
  use neighbor-group EBGP-GROUP
 !
!
```

### AF Group (Common AF parameters)
```
router bgp 65001
 af-group IPV4-UNICAST-GROUP ipv4 unicast
  route-policy EBGP-IN in
  route-policy EBGP-OUT out
  soft-reconfiguration inbound always
 !
 neighbor 10.0.0.2
  remote-as 65002
  use af-group IPV4-UNICAST-GROUP
 !
!
```

### Neighbor Template (Complete template)
```
router bgp 65001
 neighbor-template IBGP-TEMPLATE
  remote-as 65001
  update-source Loopback0
  next-hop-self
  address-family ipv4 unicast
   route-policy IBGP-IN in
   route-policy IBGP-OUT out
  !
 !
 neighbor 10.0.0.2
  use neighbor-template IBGP-TEMPLATE
 !
!
```

## Route Policies

### Basic Pass-All Policy
```
route-policy PASS-ALL
  pass
end-policy
!
```

### Prefix Filter
```
prefix-set CUSTOMER-PREFIXES
  192.168.0.0/16 le 24,
  10.0.0.0/8 le 24
end-set
!

route-policy FILTER-CUSTOMER
  if destination in CUSTOMER-PREFIXES then
    pass
  else
    drop
  endif
end-policy
!
```

### Set Local Preference
```
route-policy SET-LOCAL-PREF
  if destination in (IMPORTANT-PREFIXES) then
    set local-preference 200
    pass
  else
    set local-preference 100
    pass
  endif
end-policy
!
```

### AS Path Prepend
```
route-policy PREPEND-AS
  if destination in (BACKUP-PREFIXES) then
    prepend as-path 65001 65001 65001
    pass
  else
    pass
  endif
end-policy
!
```

### Community Matching
```
extcommunity-set standard GOLD-COMMUNITY
  rt 65001:100
end-set
!

route-policy MATCH-COMMUNITY
  if extcommunity matches-any GOLD-COMMUNITY then
    set local-preference 200
    pass
  else
    pass
  endif
end-policy
!
```

### Add Community
```
route-policy ADD-COMMUNITY
  set community (65001:100) additive
  set extcommunity rt 65001:100 additive
  pass
end-policy
!
```

## BGP Best Practices

### EBGP Hardening
```
router bgp 65001
 neighbor 10.0.0.2
  remote-as 65002
  ttl-security hops 1
  password type 7 <encrypted-password>
  bfd fast-detect multiplier 3 minimum-interval 150
  graceful-restart
  address-family ipv4 unicast
   route-policy EBGP-IN in
   route-policy EBGP-OUT out
   soft-reconfiguration inbound always
  !
 !
!
```

### Route Reflectors
```
router bgp 65001
 neighbor 10.0.0.10
  remote-as 65001
  route-reflector-client
  address-family ipv4 unicast
   next-hop-self
   route-policy RR-OUT out
  !
 !
!
```

### BGP PIC (Prefix Independent Convergence)
```
router bgp 65001
 bgp additional-paths select route-policy ADDPATH-POLICY
 bgp additional-paths send receive
 address-family ipv4 unicast
  additional-paths send
  additional-paths receive
 !
!
```

## BGP Show Commands

```
show bgp summary                    -- BGP neighbor summary
show bgp neighbors                  -- Detailed neighbor info
show bgp <prefix>                   -- Specific prefix
show bgp <neighbor> routes          -- Routes from neighbor
show bgp <neighbor> advertised-routes  -- Routes advertised to neighbor
show bgp vpnv4 unicast summary      -- VPNv4 summary
show bgp l2vpn evpn summary         -- EVPN summary
show bgp <prefix> detail            -- Detailed prefix info
show bgp process summary            -- BGP process status
```

## BGP Troubleshooting

```
clear bgp <neighbor> soft in        -- Soft reset inbound
clear bgp <neighbor> soft out       -- Soft reset outbound
clear bgp * soft                    -- Soft reset all neighbors
show bgp <neighbor>                 -- Check neighbor state
show bgp <neighbor> received-routes -- Received routes (with soft-reconfig)
show route bgp                      -- BGP routes in RIB
show cef <prefix>                   -- CEF forwarding entry
```

## Common BGP Scenarios

### Scenario 1: EBGP Peering
```
router bgp 65001
 bgp router-id 1.1.1.1
 address-family ipv4 unicast
 !
 neighbor 10.0.0.2
  remote-as 65002
  description "EBGP to ISP-A"
  bfd fast-detect multiplier 3 minimum-interval 150
  address-family ipv4 unicast
   route-policy EBGP-IN in
   route-policy EBGP-OUT out
   soft-reconfiguration inbound always
  !
 !
!
```

### Scenario 2: IBGP Full Mesh
```
router bgp 65001
 bgp router-id 1.1.1.1
 address-family ipv4 unicast
 !
 neighbor 10.0.0.2
  remote-as 65001
  update-source Loopback0
  next-hop-self
  address-family ipv4 unicast
  !
 !
 neighbor 10.0.0.3
  remote-as 65001
  update-source Loopback0
  next-hop-self
  address-family ipv4 unicast
  !
 !
!
```

### Scenario 3: Route Reflector
```
router bgp 65001
 bgp router-id 1.1.1.1
 address-family ipv4 unicast
 !
 neighbor 10.0.0.2
  remote-as 65001
  route-reflector-client
  update-source Loopback0
  address-family ipv4 unicast
   next-hop-self
  !
 !
!
```
