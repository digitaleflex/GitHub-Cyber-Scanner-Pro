# IOS XR MPLS and Segment Routing Reference

## MPLS Basic Configuration

### Enable MPLS
```
mpls ldp
 router-id 1.1.1.1
 address-family ipv4
  discovery transport-address interface Loopback0
  interface HundredGigE0/0/0/0
  !
  interface HundredGigE0/0/0/1
  !
 !
!

interface HundredGigE0/0/0/0
 mpls ldp auto-config
!
```

### MPLS Traffic Engineering
```
mpls traffic-eng
 router-id Loopback0
!

interface HundredGigE0/0/0/0
 mpls traffic-eng tunnels
 mpls traffic-eng backup-frr
!
```

## Segment Routing (SR-MPLS)

### Enable SR-MPLS
```
segment-routing mpls
!
```

### SR with IS-IS
```
router isis CORE
 is-type level-2-only
 net 49.0001.0000.0000.0001.00
 address-family ipv4 unicast
  metric-style wide
  mpls traffic-eng level-2-only
  mpls traffic-eng router-id Loopback0
  prefix-sid index 100
 !
!
```

### SR with OSPF
```
router ospf 1
 router-id 1.1.1.1
 address-family ipv4 unicast
  prefix-sid index 100
 !
!
```

### SR Global Block (SRGB)
```
segment-routing mpls
 connected-prefix-sid-map ipv4
  10.0.0.0/24 100
 !
!
```

### SR Local Block (SRLB)
```
segment-routing mpls
 srlb 15000 16999
!
```

### SR Traffic Engineering (SR-TE)

#### SR-TE Policy
```
segment-routing traffic-eng
 policy SR-TE-POLICY-1
  color 100 end-point 2.2.2.2
  candidate-paths
   preference 100
    explicit-name PATH1
     segment-list
      index 10 sid 16002
      index 20 sid 16003
      index 30 sid 16004
     !
    !
   !
  !
 !
!
```

#### SR-TE with PCEP
```
segment-routing traffic-eng
 pce address ipv4 10.0.0.100
  source-address 1.1.1.1
 !
!
```

## Segment Routing over IPv6 (SRv6)

### Enable SRv6
```
segment-routing srv6
 locator SRv6-LOC
  prefix 2001:db8::/48
  behavior usid
 !
!
```

### SRv6 with IS-IS
```
router isis CORE
 address-family ipv6 unicast
  segment-routing srv6 locator SRv6-LOC
 !
!
```

### SRv6 Endpoint Behavior
```
segment-routing srv6
 locator SRv6-LOC
  prefix 2001:db8::/48
  behavior End
  behavior End.X interface HundredGigE0/0/0/0
  behavior End.DT4 vrf CUSTOMER-A
  behavior End.DT6 vrf CUSTOMER-B
 !
!
```

### SRv6 L3VPN
```
router bgp 65001
 address-family vpnv4 unicast
  segment-routing srv6
   locator SRv6-LOC
  !
 !
 neighbor 10.0.0.2
  remote-as 65002
  address-family vpnv4 unicast
   segment-routing srv6
    locator SRv6-LOC
   !
  !
 !
 vrf CUSTOMER-A
  rd 65001:100
  address-family ipv4 unicast
   segment-routing srv6
    locator SRv6-LOC
   !
  !
 !
!
```

## MPLS L2VPN

### L2VPN Pseudowire
```
l2vpn
 bridge group CUSTOMER
  bridge-domain VLAN100
   interface GigabitEthernet0/0/0/0.100
   !
   neighbor 2.2.2.2 pw-id 100
   !
  !
 !
!
```

### L2VPN EVPN
```
l2vpn
 bridge group EVPN-BG
  bridge-domain EVPN-BD
   evi 100
   interface Bundle-Ether10.100
   !
  !
 !
!
```

## MPLS Show Commands

```
show mpls ldp neighbor              -- LDP neighbors
show mpls ldp discovery             -- LDP discovery
show mpls ldp bindings             -- LDP label bindings
show mpls forwarding               -- MPLS forwarding table
show mpls traffic-eng tunnels      -- TE tunnels
show segment-routing mpls state    -- SR-MPLS state
show segment-routing mpls lb       -- Label blocks
show segment-routing mpls mapping  -- SID mapping
show segment-routing traffic-eng policy  -- SR-TE policies
show segment-routing srv6 locator  -- SRv6 locators
show l2vpn bridge-domain           -- L2VPN bridge domains
```

## MPLS Troubleshooting

```
show mpls ldp neighbor detail      -- Detailed LDP neighbor
show mpls forwarding labels <label> -- Specific label
show mpls traffic-eng fast-reroute -- FRR status
debug mpls ldp                     -- LDP debugging
debug mpls traffic-eng             -- TE debugging
```

## Common MPLS/SR Scenarios

### Scenario 1: SR-MPLS Core
```
segment-routing mpls
!
router isis CORE
 is-type level-2-only
 net 49.0001.0000.0000.0001.00
 address-family ipv4 unicast
  metric-style wide
  mpls traffic-eng level-2-only
  mpls traffic-eng router-id Loopback0
  prefix-sid index 100
 !
 interface Loopback0
  passive
  address-family ipv4 unicast
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

### Scenario 2: SR-TE Policy
```
segment-routing traffic-eng
 policy CORE-POLICY
  color 100 end-point 2.2.2.2
  candidate-paths
   preference 100
    dynamic
     constraints
      metric te
      affinity include-any RED
     !
    !
   !
  !
 !
!
```

### Scenario 3: SRv6 L3VPN
```
segment-routing srv6
 locator SRv6-LOC
  prefix 2001:db8::/48
  behavior usid
 !
!
router bgp 65001
 address-family vpnv4 unicast
  segment-routing srv6
   locator SRv6-LOC
  !
 !
 vrf CUSTOMER-A
  rd 65001:100
  address-family ipv4 unicast
   segment-routing srv6
    locator SRv6-LOC
   !
  !
 !
!
```
