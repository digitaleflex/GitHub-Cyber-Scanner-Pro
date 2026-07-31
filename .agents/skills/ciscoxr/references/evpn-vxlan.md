# IOS XR EVPN and VXLAN Reference

## EVPN Control Plane

### EVPN BGP Configuration
```
router bgp 65001
 bgp router-id 1.1.1.1
 address-family l2vpn evpn
 !
 neighbor 10.0.0.2
  remote-as 65001
  update-source Loopback0
  address-family l2vpn evpn
   route-policy EVPN-IN in
   route-policy EVPN-OUT out
  !
 !
!
```

### EVPN Route Policies
```
route-policy EVPN-IN
  pass
end-policy
!
route-policy EVPN-OUT
  pass
end-policy
!
```

## VXLAN Configuration

### NVE Interface
```
interface nve1
 source-interface Loopback0
 member vfi VFI-100
  vpn-id 100
 !
 member vfi VFI-200
  vpn-id 200
 !
!
```

### VFI Configuration
```
l2vpn
 vfi VFI-100
  vpn-id 100
  autodiscovery bgp
   rd 1.1.1.1:100
   route-target import 65001:100
   route-target export 65001:100
  !
 !
 vfi VFI-200
  vpn-id 200
  autodiscovery bgp
   rd 1.1.1.1:200
   route-target import 65001:200
   route-target export 65001:200
  !
 !
!
```

### Bridge Domain with EVPN
```
l2vpn
 bridge group EVPN-BG
  bridge-domain BD-100
   evi 100
   interface nve1
   !
   interface HundredGigE0/0/0/0.100 l2transport
    encapsulation dot1q 100
   !
  !
  bridge-domain BD-200
   evi 200
   interface nve1
   !
   interface HundredGigE0/0/0/0.200 l2transport
    encapsulation dot1q 200
   !
  !
 !
!
```

## EVPN IRB (Integrated Routing and Bridging)

### IRB Configuration
```
interface BVI100
 ipv4 address 192.168.100.1 255.255.255.0
!

l2vpn
 bridge group EVPN-BG
  bridge-domain BD-100
   evi 100
   interface BVI100
   !
   interface nve1
   !
   interface HundredGigE0/0/0/0.100 l2transport
    encapsulation dot1q 100
   !
  !
 !
!
```

## EVPN Show Commands

```
show l2vpn vfi                     -- VFI status
show l2vpn bridge-domain           -- Bridge domain status
show l2vpn evpn evi                -- EVPN EVI status
show l2vpn evpn mac                -- EVPN MAC table
show l2vpn evpn mac detail         -- Detailed MAC info
show bgp l2vpn evpn summary        -- EVPN BGP summary
show bgp l2vpn evpn                -- EVPN routes
show bgp l2vpn evpn route-type 2   -- MAC routes
show bgp l2vpn evpn route-type 3   -- IMET routes
show bgp l2vpn evpn route-type 4   -- ES routes
show bgp l2vpn evpn route-type 5   -- IP prefix routes
show nve peers                     -- NVE peer status
show nve interface detail          -- NVE interface details
```

## EVPN Troubleshooting

```
show l2vpn evpn mac                 -- Check MAC learning
show l2vpn evpn mac <mac>           -- Specific MAC
show l2vpn evpn evi <evi>           -- Specific EVI
show bgp l2vpn evpn                 -- EVPN BGP routes
debug l2vpn evpn                    -- EVPN debugging
debug nve                           -- NVE debugging
```

## EVPN Scenarios

### Scenario 1: EVPN VXLAN Fabric
```
router bgp 65001
 bgp router-id 1.1.1.1
 address-family l2vpn evpn
 !
 neighbor 10.0.0.2
  remote-as 65001
  update-source Loopback0
  address-family l2vpn evpn
  !
 !
 neighbor 10.0.0.3
  remote-as 65001
  update-source Loopback0
  address-family l2vpn evpn
  !
 !
!

interface nve1
 source-interface Loopback0
 member vfi VFI-100
  vpn-id 100
 !
!

l2vpn
 vfi VFI-100
  vpn-id 100
  autodiscovery bgp
   rd 1.1.1.1:100
   route-target import 65001:100
   route-target export 65001:100
  !
 !
 bridge group EVPN-BG
  bridge-domain BD-100
   evi 100
   interface nve1
   !
   interface HundredGigE0/0/0/0.100 l2transport
    encapsulation dot1q 100
   !
  !
 !
!
```

### Scenario 2: EVPN IRB
```
interface BVI100
 ipv4 address 192.168.100.1 255.255.255.0
!

l2vpn
 bridge group EVPN-BG
  bridge-domain BD-100
   evi 100
   interface BVI100
   !
   interface nve1
   !
   interface HundredGigE0/0/0/0.100 l2transport
    encapsulation dot1q 100
   !
  !
 !
!
```
