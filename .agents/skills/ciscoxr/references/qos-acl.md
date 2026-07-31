# IOS XR QoS and ACL Reference

## QoS Configuration

### Class Maps

#### Match Class Map
```
class-map match-any VOICE
 match dscp ef
!

class-map match-any VIDEO
 match dscp af41
 match dscp cs4
!

class-map match-any DATA
 match dscp default
 match dscp af11
 match dscp af12
!
```

#### Match All Class Map
```
class-map match-all CRITICAL
 match dscp cs6
 match protocol bgp
!
```

### Policy Maps

#### Ingress Policing
```
policy-map POLICE-INGRESS
 class VOICE
  police rate 10 mbps
   conform-action transmit
   exceed-action drop
  !
 class VIDEO
  police rate 50 mbps
   conform-action transmit
   exceed-action drop
  !
 class class-default
  police rate 100 mbps
   conform-action transmit
   exceed-action drop
  !
!
```

#### Egress Shaping
```
policy-map SHAPE-EGRESS
 class VOICE
  priority level 1
  bandwidth percent 20
 !
 class VIDEO
  bandwidth percent 30
 !
 class DATA
  bandwidth percent 40
  random-detect dscp-based
 !
 class class-default
  bandwidth percent 10
 !
!
```

#### Hierarchical QoS
```
policy-map CHILD-POLICY
 class VOICE
  priority level 1
  bandwidth percent 20
 !
 class class-default
  bandwidth percent 80
 !
!

policy-map PARENT-POLICY
 class class-default
  shape average 1000 mbps
  service-policy CHILD-POLICY
 !
!
```

### Applying QoS

#### Interface Level
```
interface HundredGigE0/0/0/0
 service-policy input POLICE-INGRESS
 service-policy output SHAPE-EGRESS
!
```

#### Sub-Interface Level
```
interface HundredGigE0/0/0/0.100
 service-policy input POLICE-INGRESS
 service-policy output SHAPE-EGRESS
!
```

#### Bundle Level
```
interface Bundle-Ether10
 service-policy input POLICE-INGRESS
 service-policy output SHAPE-EGRESS
!
```

## ACL Configuration

### IPv4 ACL

#### Standard ACL
```
ipv4 access-list STANDARD-ACL
 10 permit 192.168.1.0 0.0.0.255
 20 deny any
!
```

#### Extended ACL
```
ipv4 access-list EXTENDED-ACL
 10 permit tcp 192.168.1.0 0.0.0.255 any eq 80
 20 permit tcp 192.168.1.0 0.0.0.255 any eq 443
 30 permit icmp 192.168.1.0 0.0.0.255 any
 40 deny any
!
```

#### ACL with Logging
```
ipv4 access-list LOG-ACL
 10 permit tcp any any eq 22 log
 20 deny any log
!
```

### IPv6 ACL
```
ipv6 access-list IPV6-ACL
 10 permit tcp 2001:db8::/32 any eq 80
 20 permit tcp 2001:db8::/32 any eq 443
 30 permit icmp 2001:db8::/32 any
 40 deny any
!
```

### ACL Interface Application
```
interface GigabitEthernet0/0/0/0
 ipv4 access-group EXTENDED-ACL ingress
 ipv4 access-group EXTENDED-ACL egress
 ipv6 access-group IPV6-ACL ingress
!
```

### ACL for VTY Lines
```
ipv4 access-list VTY-ACL
 10 permit 10.0.0.0 0.255.255.255
 20 deny any
!

line default
 access-class ingress VTY-ACL
 transport input ssh
!
```

## QoS Show Commands

```
show policy-map                      -- All policy maps
show policy-map interface            -- Policy map application
show policy-map interface <intf>     -- Specific interface
show policy-map interface <intf> input   -- Input policy
show policy-map interface <intf> output  -- Output policy
show policy-map target               -- Target policy stats
show access-lists                    -- All ACLs
show access-lists ipv4               -- IPv4 ACLs
show access-lists ipv6               -- IPv6 ACLs
```

## QoS Troubleshooting

```
show policy-map interface <intf>     -- Check policy application
show policy-map interface <intf> statistics  -- Traffic stats
clear policy-map interface <intf> statistics  -- Clear stats
show access-lists                    -- Verify ACL entries
show access-lists <name>             -- Specific ACL
```

## Common QoS Scenarios

### Scenario 1: Service Provider Edge QoS
```
class-map match-any GOLD
 match dscp ef
 match dscp cs5
!

class-map match-any SILVER
 match dscp af21
 match dscp af22
!

class-map match-any BRONZE
 match dscp default
!

policy-map PE-INGRESS
 class GOLD
  police rate 100 mbps
   conform-action transmit
   exceed-action drop
  !
 class SILVER
  police rate 50 mbps
   conform-action transmit
   exceed-action drop
  !
 class BRONZE
  police rate 10 mbps
   conform-action transmit
   exceed-action drop
  !
!

policy-map PE-EGRESS
 class GOLD
  priority level 1
  bandwidth percent 50
 !
 class SILVER
  bandwidth percent 30
  random-detect dscp-based
 !
 class BRONZE
  bandwidth percent 20
  random-detect dscp-based
 !
!

interface HundredGigE0/0/0/0
 description "PE Uplink"
 service-policy input PE-INGRESS
 service-policy output PE-EGRESS
!
```

### Scenario 2: ACL-Based Traffic Filtering
```
ipv4 access-list BLOCK-BAD-TRAFFIC
 10 deny tcp any any eq 23
 20 deny tcp any any eq 135
 30 deny tcp any any eq 139
 40 deny tcp any any eq 445
 50 deny udp any any eq 137
 60 deny udp any any eq 138
 70 permit ip any any
!

interface GigabitEthernet0/0/0/0
 ipv4 access-group BLOCK-BAD-TRAFFIC ingress
!
```
