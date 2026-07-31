# IOS XR OSPF Configuration Reference

## Basic OSPF Configuration

### Single Area OSPF
```
router ospf 1
 router-id 1.1.1.1
 log adjacency-changes
 area 0
  interface Loopback0
   passive-interface
  !
  interface GigabitEthernet0/0/0/0
   network point-to-point
   cost 10
  !
  interface GigabitEthernet0/0/0/1
   cost 20
  !
 !
!
```

### Multi-Area OSPF
```
router ospf 1
 router-id 1.1.1.1
 area 0
  interface Loopback0
   passive-interface
  !
  interface TenGigE0/0/0/0
   network point-to-point
  !
 !
 area 1
  interface GigabitEthernet0/0/0/0
   cost 10
  !
  interface GigabitEthernet0/0/0/1
   cost 20
  !
 !
!
```

## OSPF Network Types

### Point-to-Point
```
interface GigabitEthernet0/0/0/0
 ip ospf network point-to-point
!
```

### Broadcast
```
interface GigabitEthernet0/0/0/0
 ip ospf network broadcast
 ip ospf priority 100    -- DR priority (0 = never DR)
!
```

### Point-to-Multipoint
```
interface GigabitEthernet0/0/0/0
 ip ospf network point-to-multipoint
!
```

## OSPF Authentication

### Simple Password
```
router ospf 1
 area 0
  authentication
  interface GigabitEthernet0/0/0/0
   authentication key-chain OSPF-KEYS
  !
 !
!

key chain OSPF-KEYS
 key 1
  key-string <password>
  accept-lifetime 00:00:00 Jan 1 2024 infinite
  send-lifetime 00:00:00 Jan 1 2024 infinite
 !
!
```

### MD5 Authentication
```
router ospf 1
 area 0
  authentication message-digest
  interface GigabitEthernet0/0/0/0
   authentication message-digest key-chain OSPF-MD5
  !
 !
!
```

## OSPF Virtual Links

### Configure Virtual Link
```
router ospf 1
 area 1
  virtual-link 2.2.2.2    -- Router ID of ABR
 !
!
```

## OSPF Route Redistribution

### Redistribute BGP into OSPF
```
router ospf 1
 redistribute bgp 65001 route-policy BGP-TO-OSPF
!

route-policy BGP-TO-OSPF
  set tag 65001
  set metric 100
  set metric-type type-2
  pass
end-policy
!
```

### Redistribute Connected
```
router ospf 1
 redistribute connected route-policy CONN-TO-OSPF
!

route-policy CONN-TO-OSPF
  if destination in (REDIST-PREFIXES) then
    set metric 10
    pass
  else
    drop
  endif
end-policy
!
```

## OSPF Stub Areas

### Stub Area
```
router ospf 1
 area 1
  stub
  interface GigabitEthernet0/0/0/0
  !
 !
!
```

### Totally Stubby Area
```
router ospf 1
 area 1
  stub no-summary
  interface GigabitEthernet0/0/0/0
  !
 !
!
```

### NSSA Area
```
router ospf 1
 area 1
  nssa
  interface GigabitEthernet0/0/0/0
  !
 !
!
```

## OSPF Show Commands

```
show ospf                         -- OSPF process info
show ospf neighbor                -- OSPF neighbors
show ospf neighbor detail         -- Detailed neighbor info
show ospf interface               -- OSPF interfaces
show ospf interface brief         -- Brief interface summary
show ospf database                -- OSPF LSDB
show ospf database router         -- Router LSAs
show ospf database network        -- Network LSAs
show ospf database summary        -- Summary LSAs
show ospf database external       -- External LSAs
show route ospf                   -- OSPF routes in RIB
show ospf summary-address         -- Summary addresses
show ospf virtual-links           -- Virtual link status
```

## OSPF Troubleshooting

```
show ospf neighbor                -- Check neighbor state (FULL = good)
show ospf interface               -- Verify interface OSPF config
show ospf database                -- Check LSDB consistency
debug ospf adj                    -- Adjacency debugging
debug ospf spf                    -- SPF calculation debugging
clear ospf process                -- Reset OSPF process (disruptive)
```

## Common OSPF Scenarios

### Scenario 1: Core OSPF Deployment
```
router ospf 1
 router-id 1.1.1.1
 log adjacency-changes
 maximum paths 32
 auto-cost reference-bandwidth 100000    -- 100G reference
 area 0
  interface Loopback0
   passive-interface
  !
  interface HundredGigE0/0/0/0
   network point-to-point
   cost 1
  !
  interface HundredGigE0/0/0/1
   network point-to-point
   cost 1
  !
 !
!
```

### Scenario 2: ABR with Multiple Areas
```
router ospf 1
 router-id 1.1.1.1
 area 0
  interface Loopback0
   passive-interface
  !
  interface TenGigE0/0/0/0
   network point-to-point
  !
 !
 area 1
  interface GigabitEthernet0/0/0/0
   cost 10
  !
  interface GigabitEthernet0/0/0/1
   cost 20
  !
 !
 area 2
  interface GigabitEthernet0/0/0/2
   cost 30
  !
 !
!
```
