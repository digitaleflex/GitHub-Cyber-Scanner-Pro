# IOS XR IS-IS Configuration Reference

## Basic IS-IS Configuration

### Single-Level IS-IS
```
router isis CORE
 is-type level-2-only
 net 49.0001.0000.0000.0001.00
 log adjacency-changes
 address-family ipv4 unicast
  metric-style wide
  router-id Loopback0
 !
 address-family ipv6 unicast
  metric-style wide
 !
 interface Loopback0
  passive
  address-family ipv4 unicast
  !
  address-family ipv6 unicast
  !
 !
 interface HundredGigE0/0/0/0
  circuit-type level-2-only
  point-to-point
  address-family ipv4 unicast
   metric 10
  !
  address-family ipv6 unicast
   metric 10
  !
 !
!
```

### Multi-Level IS-IS
```
router isis CORE
 is-type level-1-2
 net 49.0001.0000.0000.0001.00
 log adjacency-changes
 address-family ipv4 unicast
  metric-style wide
  router-id Loopback0
 !
 interface Loopback0
  passive
  address-family ipv4 unicast
  !
 !
 interface TenGigE0/0/0/0
  circuit-type level-1
  address-family ipv4 unicast
   metric 10
  !
 !
 interface HundredGigE0/0/0/0
  circuit-type level-2-only
  point-to-point
  address-family ipv4 unicast
   metric 10
  !
 !
!
```

## IS-IS Authentication

### Interface Authentication
```
router isis CORE
 interface HundredGigE0/0/0/0
  address-family ipv4 unicast
   authentication mode md5 level-2
   authentication key-chain ISIS-KEYS level-2
  !
 !
!

key chain ISIS-KEYS
 key 1
  key-string <password>
  accept-lifetime 00:00:00 Jan 1 2024 infinite
  send-lifetime 00:00:00 Jan 1 2024 infinite
 !
!
```

### Area/Domain Authentication
```
router isis CORE
 area-password md5 <password>
 domain-password md5 <password>
!
```

## IS-IS Route Redistribution

### Redistribute BGP into IS-IS
```
router isis CORE
 address-family ipv4 unicast
  redistribute bgp 65001 route-policy BGP-TO-ISIS
 !
!

route-policy BGP-TO-ISIS
  set tag 65001
  set metric 100
  pass
end-policy
!
```

### Redistribute Connected
```
router isis CORE
 address-family ipv4 unicast
  redistribute connected route-policy CONN-TO-ISIS
 !
!

route-policy CONN-TO-ISIS
  if destination in (REDIST-PREFIXES) then
    set metric 10
    pass
  else
    drop
  endif
end-policy
!
```

## IS-IS Fast Reroute (TI-LFA)

### Enable TI-LFA
```
router isis CORE
 fast-reroute per-prefix level 2
 fast-reroute per-prefix tiebreak node-protecting index 100
 fast-reroute per-prefix tiebreak srlg-disjoint index 200
!
```

### Interface-Level FRR
```
interface HundredGigE0/0/0/0
 address-family ipv4 unicast
  fast-reroute per-prefix level 2
 !
!
```

## IS-IS Segment Routing Integration

### Enable SR with IS-IS
```
router isis CORE
 address-family ipv4 unicast
  mpls traffic-eng level-2-only
  mpls traffic-eng router-id Loopback0
  prefix-sid index 100
 !
!
```

## IS-IS Show Commands

```
show isis                         -- IS-IS process info
show isis neighbors               -- IS-IS neighbors
show isis neighbors detail        -- Detailed neighbor info
show isis interface               -- IS-IS interfaces
show isis interface brief         -- Brief interface summary
show isis database                -- IS-IS LSDB
show isis database verbose        -- Detailed LSDB
show isis database level 1        -- Level 1 LSDB
show isis database level 2        -- Level 2 LSDB
show isis topology                -- IS-IS topology
show isis route                   -- IS-IS routes
show route isis                   -- IS-IS routes in RIB
show isis hostname                -- IS-IS hostname mapping
show isis adjacency               -- Adjacency status
```

## IS-IS Troubleshooting

```
show isis neighbors               -- Check adjacency state (UP = good)
show isis interface               -- Verify interface IS-IS config
show isis database                -- Check LSDB consistency
debug isis adj-packets            -- Adjacency debugging
debug isis spf-events             -- SPF calculation debugging
clear isis process                -- Reset IS-IS process (disruptive)
```

## Common IS-IS Scenarios

### Scenario 1: Service Provider Core
```
router isis CORE
 is-type level-2-only
 net 49.0001.0000.0000.0001.00
 log adjacency-changes
 lsp-mtu 9000
 address-family ipv4 unicast
  metric-style wide
  router-id Loopback0
  maximum-paths 32
 !
 address-family ipv6 unicast
  metric-style wide
 !
 interface Loopback0
  passive
  address-family ipv4 unicast
  !
  address-family ipv6 unicast
  !
 !
 interface HundredGigE0/0/0/0
  circuit-type level-2-only
  point-to-point
  address-family ipv4 unicast
   metric 10
  !
  address-family ipv6 unicast
   metric 10
  !
 !
!
```

### Scenario 2: IS-IS with BFD
```
router isis CORE
 interface HundredGigE0/0/0/0
  bfd fast-detect multiplier 3 minimum-interval 150
  address-family ipv4 unicast
  !
 !
!
```
