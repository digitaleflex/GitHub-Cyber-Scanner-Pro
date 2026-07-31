# IOS XR Telemetry and Automation Reference

## Model-Driven Telemetry (MDT)

### Telemetry Destination
```
telemetry model-driven
 destination-group DGRP-COLLECTOR
  address-family ipv4 10.0.0.100 port 57500
   encoding self-describing-gpb
   protocol grpc
  !
 !
!
```

### Sensor Groups
```
telemetry model-driven
 sensor-group SGRP-INTERFACES
  sensor-path interfaces interface
 !
 sensor-group SGRP-BGP
  sensor-path bgp neighbors neighbor
 !
 sensor-group SGRP-CEF
  sensor-path cef forwarding
 !
!
```

### Subscriptions

#### Subscription with Single Sensor
```
telemetry model-driven
 subscription SUB-INTERFACES
  sensor-group-id SGRP-INTERFACES sample-interval 15000
  destination-id DGRP-COLLECTOR
 !
!
```

#### Subscription with Multiple Sensors
```
telemetry model-driven
 subscription SUB-MULTI
  sensor-group-id SGRP-INTERFACES sample-interval 15000
  sensor-group-id SGRP-BGP sample-interval 30000
  destination-id DGRP-COLLECTOR
 !
!
```

#### On-Change Subscription
```
telemetry model-driven
 subscription SUB-BGP-ONCHANGE
  sensor-group-id SGRP-BGP sample-interval 0
  destination-id DGRP-COLLECTOR
  source-interface Loopback0
 !
!
```

### Common YANG Paths

| Path | Description |
|------|-------------|
| `interfaces interface` | Interface statistics |
| `bgp neighbors neighbor` | BGP neighbor state |
| `bgp instances instance af safi` | BGP routes |
| `processes process` | Process CPU/memory |
| `cpu-utilization` | CPU utilization |
| `memory-summary` | Memory usage |
| `platform-inventory` | Hardware inventory |
| `environmental-sensor` | Environmental sensors |
| `controllers optics` | Optical transceiver data |
| `controllers otn` | OTN controller data |
| `ipv4 network-instances` | IPv4 routes |
| `ipv6 network-instances` | IPv6 routes |
| `mpls ldp` | MPLS LDP state |
| `segment-routing` | SR state |

## gRPC Configuration

### Enable gRPC
```
grpc
 port 57400
 address-family dual
!
```

### gRPC with TLS
```
grpc
 port 57400
 address-family dual
 tls
  trustpoint GRPC-TRUSTPOINT
  mutual-auth
 !
!
```

### gRPC with Authentication
```
grpc
 port 57400
 address-family dual
!

username grpc-user
 group grpc-group
 secret <password>
!
```

## NetConf Configuration

### Enable NetConf
```
ssh server v2
ssh server netconf port 830
!
```

### NetConf with YANG
```
netconf-yang agent
 ssh
 !
!
```

## Zero Touch Provisioning (ZTP)

### ZTP Configuration
```
ztp
!
```

### ZTP Script (Python)
```python
#!/usr/bin/env python
import os

# ZTP Python script for IOS XR
def main():
    # Download configuration
    os.system('curl -o /tmp/config.cfg http://<server>/config.cfg')
    
    # Apply configuration
    os.system('configure replace /tmp/config.cfg')
    
    # Commit
    os.system('commit')
    
    # Disable ZTP after successful provisioning
    os.system('ztp disable')

if __name__ == '__main__':
    main()
```

### ZTP with DHCP Options
```
# DHCP Option 67 (Bootfile-Name)
option bootfile-name "ztp.py";

# DHCP Option 66 (TFTP Server)
option tftp-server-name "http://<server>/";
```

## Automation Tools

### EEM (Embedded Event Manager)

#### EEM Applet
```
event manager applet INTERFACE-DOWN
 event syslog pattern "Interface.*down"
 action 1.0 cli command "enable"
 action 2.0 cli command "show interfaces brief"
 action 3.0 syslog msg "Interface down detected"
!
```

### Python on Box

#### Execute Python Script
```
python
import cli

# Execute CLI command
output = cli.execute('show interfaces brief')
print(output)

# Configure interface
cli.configure('interface GigabitEthernet0/0/0/0')
cli.configure('description Updated by Python')
cli.configure('commit')
!
```

### Ansible Integration

#### Ansible Inventory
```yaml
[iosxr]
router1 ansible_host=10.0.0.1
router2 ansible_host=10.0.0.2

[iosxr:vars]
ansible_connection=network_cli
ansible_network_os=iosxr
ansible_user=admin
ansible_password=admin
ansible_become=yes
ansible_become_method=enable
```

#### Ansible Playbook Example
```yaml
---
- name: Configure BGP on IOS XR
  hosts: iosxr
  gather_facts: no
  tasks:
    - name: Configure BGP
      cisco.iosxr.iosxr_bgp:
        config:
          as_number: 65001
          bgp:
            router_id: 1.1.1.1
          neighbors:
            - neighbor_address: 10.0.0.2
              remote_as: 65002
        state: merged
```

## Telemetry Show Commands

```
show telemetry model-driven subscription     -- Subscription status
show telemetry model-driven destination      -- Destination status
show telemetry model-driven sensor-group     -- Sensor group status
show telemetry model-driven database         -- Telemetry database
show grpc                                    -- gRPC status
show netconf-yang                            -- NetConf status
show ztp                                   -- ZTP status
```

## Common Telemetry Scenarios

### Scenario 1: Full Telemetry Deployment
```
telemetry model-driven
 destination-group DGRP-COLLECTOR
  address-family ipv4 10.0.0.100 port 57500
   encoding self-describing-gpb
   protocol grpc
  !
 !
 sensor-group SGRP-INTERFACES
  sensor-path interfaces interface
 !
 sensor-group SGRP-BGP
  sensor-path bgp neighbors neighbor
 !
 sensor-group SGRP-CEF
  sensor-path cef forwarding
 !
 subscription SUB-ALL
  sensor-group-id SGRP-INTERFACES sample-interval 15000
  sensor-group-id SGRP-BGP sample-interval 30000
  sensor-group-id SGRP-CEF sample-interval 60000
  destination-id DGRP-COLLECTOR
 !
!

grpc
 port 57400
 address-family dual
!
```

### Scenario 2: On-Change BGP Monitoring
```
telemetry model-driven
 sensor-group SGRP-BGP-STATE
  sensor-path bgp neighbors neighbor state
 !
 destination-group DGRP-COLLECTOR
  address-family ipv4 10.0.0.100 port 57500
   encoding self-describing-gpb
   protocol grpc
  !
 !
 subscription SUB-BGP-ONCHANGE
  sensor-group-id SGRP-BGP-STATE sample-interval 0
  destination-id DGRP-COLLECTOR
 !
!
```
