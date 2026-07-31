# IOS XR VRF and VLAN Configuration Reference

## VRF Configuration

### Basic VRF
```
vrf CUSTOMER-A
 description "Customer A VRF"
 address-family ipv4 unicast
  import route-policy IMPORT-CUST-A
  export route-policy EXPORT-CUST-A
 !
 address-family ipv6 unicast
  import route-policy IMPORT-CUST-A-V6
  export route-policy EXPORT-CUST-A-V6
 !
!
```

### VRF with Route Distinguisher and Targets
```
vrf CUSTOMER-A
 rd 65001:100
 address-family ipv4 unicast
  import route-target 65001:100
  export route-target 65001:100
 !
!
```

### VRF with Interface Assignment
```
vrf CUSTOMER-A
 description "Customer A VRF"
 address-family ipv4 unicast
 !
!

interface GigabitEthernet0/0/0/0.100
 description "Customer A Access"
 vrf CUSTOMER-A
 encapsulation dot1q 100
 ipv4 address 192.168.100.1 255.255.255.0
!
```

### VRF with BGP
```
router bgp 65001
 bgp router-id 1.1.1.1
 vrf CUSTOMER-A
  rd 65001:100
  address-family ipv4 unicast
   redistribute connected
  !
  neighbor 192.168.100.2
   remote-as 65002
   address-family ipv4 unicast
    route-policy CUST-A-IN in
    route-policy CUST-A-OUT out
   !
  !
 !
!
```

## VRF Lite (Multi-VRF)

### Multiple VRFs on Single Router
```
vrf CUSTOMER-A
 rd 65001:100
 address-family ipv4 unicast
  import route-target 65001:100
  export route-target 65001:100
 !
!

vrf CUSTOMER-B
 rd 65001:200
 address-family ipv4 unicast
  import route-target 65001:200
  export route-target 65001:200
 !
!

interface GigabitEthernet0/0/0/0.100
 vrf CUSTOMER-A
 encapsulation dot1q 100
 ipv4 address 192.168.100.1 255.255.255.0
!

interface GigabitEthernet0/0/0/0.200
 vrf CUSTOMER-B
 encapsulation dot1q 200
 ipv4 address 192.168.200.1 255.255.255.0
!
```

## VRF Import/Export Policies

### Import Policy
```
route-policy IMPORT-CUST-A
  if extcommunity matches-any CUST-A-COMMUNITY then
    pass
  else
    drop
  endif
end-policy
!

extcommunity-set standard CUST-A-COMMUNITY
  rt 65001:100
end-set
!
```

### Export Policy
```
route-policy EXPORT-CUST-A
  set extcommunity rt 65001:100 additive
  pass
end-policy
!
```

## VLAN Configuration

### Basic VLAN
```
vlan 100
 name CUSTOMER-A
!

vlan 200
 name CUSTOMER-B
!
```

### VLAN Interface (SVI)
```
interface Vlan100
 description "Customer A SVI"
 ipv4 address 192.168.100.1 255.255.255.0
!
```

### QinQ Configuration
```
interface GigabitEthernet0/0/0/0.100 l2transport
 description "QinQ Service"
 encapsulation dot1q 100 second-dot1q 200
 rewrite ingress tag pop 2 symmetric
 bridge-domain 100
!
```

## Bridge Domain Configuration

### Basic Bridge Domain
```
l2vpn
 bridge group CUSTOMER-A
  bridge-domain BD-100
   interface GigabitEthernet0/0/0/0.100
   !
   interface TenGigE0/0/0/0.100
   !
  !
 !
!
```

### Bridge Domain with Split Horizon
```
l2vpn
 bridge group CUSTOMER-A
  bridge-domain BD-100
   split-horizon group SPLIT-100
   interface GigabitEthernet0/0/0/0.100
   !
   interface TenGigE0/0/0/0.100
   !
  !
 !
!
```

## VRF Show Commands

```
show vrf                           -- All VRFs
show vrf detail                    -- Detailed VRF info
show vrf <name>                    -- Specific VRF
show vrf <name> interface          -- VRF interfaces
show route vrf <name>              -- VRF routing table
show bgp vrf <name> summary        -- VRF BGP summary
show cef vrf <name>                -- VRF CEF table
show l2vpn bridge-domain           -- Bridge domains
show l2vpn bridge-domain detail    -- Detailed bridge domain
```

## VRF Troubleshooting

```
show vrf                           -- Verify VRF exists
show vrf <name> interface          -- Check interface assignment
show route vrf <name>              -- Check VRF routes
ping vrf <name> <ip>               -- Ping from VRF
traceroute vrf <name> <ip>         -- Traceroute from VRF
```

## Common VRF Scenarios

### Scenario 1: Provider Edge (PE) Router
```
vrf CUSTOMER-A
 rd 65001:100
 address-family ipv4 unicast
  import route-target 65001:100
  export route-target 65001:100
 !
!

router bgp 65001
 bgp router-id 1.1.1.1
 address-family vpnv4 unicast
 !
 vrf CUSTOMER-A
  rd 65001:100
  address-family ipv4 unicast
   redistribute connected
  !
  neighbor 192.168.100.2
   remote-as 65002
   address-family ipv4 unicast
   !
  !
 !
!

interface GigabitEthernet0/0/0/0.100
 vrf CUSTOMER-A
 encapsulation dot1q 100
 ipv4 address 192.168.100.1 255.255.255.0
!
```

### Scenario 2: VRF Leaking
```
vrf CUSTOMER-A
 rd 65001:100
 address-family ipv4 unicast
  import route-target 65001:100
  import route-target 65001:999
  export route-target 65001:100
 !
!

vrf CUSTOMER-B
 rd 65001:200
 address-family ipv4 unicast
  import route-target 65001:200
  import route-target 65001:999
  export route-target 65001:200
 !
!
```

### Scenario 3: VRF with OSPF
```
vrf CUSTOMER-A
 rd 65001:100
 address-family ipv4 unicast
 !
!

router ospf 100 vrf CUSTOMER-A
 router-id 1.1.1.1
 area 0
  interface GigabitEthernet0/0/0/0.100
   network point-to-point
  !
  interface Loopback100
   passive-interface
  !
 !
!
```
