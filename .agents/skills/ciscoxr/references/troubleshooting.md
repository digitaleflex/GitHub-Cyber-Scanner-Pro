# IOS XR Troubleshooting Reference

## Diagnostic Command Framework

### General Health Check
```
show platform                          -- Hardware status
show processes cpu                     -- CPU utilization
show processes memory                  -- Memory usage
show logging                           -- System logs
show alarms                            -- Active alarms
show environment                       -- Environmental status
show inventory                         -- Hardware inventory
show redundancy                        -- RP redundancy status
show clock                           -- System clock
show ntp status                      -- NTP synchronization
```

### Interface Troubleshooting

#### Step 1: Check Interface Status
```
show interfaces brief                  -- Quick status check
show interfaces <name>                 -- Detailed interface info
show interfaces <name> counters        -- Traffic counters
show interfaces <name> errors          -- Error statistics
```

#### Step 2: Check Physical Layer
```
show controllers <interface>           -- Physical layer status
show controllers <interface> counters  -- Hardware counters
show controllers <interface> transceiver  -- Optical transceiver
show controllers <interface> transceiver detail  -- Detailed optical stats
```

#### Step 3: Check Layer 2/Layer 3
```
show lldp neighbors                    -- LLDP neighbor discovery
show cdp neighbors                     -- CDP neighbor discovery
show arp                               -- ARP table
show arp vrf <vrf>                     -- VRF ARP table
show ipv4 interface brief              -- IPv4 interface summary
show ipv6 interface brief              -- IPv6 interface summary
```

### Routing Troubleshooting

#### BGP Troubleshooting Flow
```
# Step 1: Check BGP neighbor status
show bgp summary                       -- Neighbor state (Estab = good)
show bgp neighbors                     -- Detailed neighbor info

# Step 2: Check BGP routes
show bgp                               -- BGP table
show bgp <prefix>                      -- Specific prefix
show bgp <neighbor> routes             -- Routes from neighbor
show bgp <neighbor> advertised-routes  -- Routes advertised to neighbor

# Step 3: Check RIB installation
show route bgp                         -- BGP routes in RIB
show route <prefix>                    -- Specific route
show cef <prefix>                      -- CEF forwarding entry

# Step 4: Debug (use with caution)
debug bgp                              -- BGP debugging
show log | include BGP                 -- BGP log messages
```

#### OSPF Troubleshooting Flow
```
# Step 1: Check OSPF neighbors
show ospf neighbor                     -- Neighbor state (FULL = good)
show ospf neighbor detail              -- Detailed neighbor info

# Step 2: Check OSPF database
show ospf database                     -- LSDB
show ospf database router              -- Router LSAs
show ospf database network             -- Network LSAs

# Step 3: Check OSPF routes
show route ospf                        -- OSPF routes in RIB
show ospf interface                    -- OSPF interfaces

# Step 4: Debug
debug ospf adj                         -- Adjacency debugging
show log | include OSPF                -- OSPF log messages
```

#### IS-IS Troubleshooting Flow
```
# Step 1: Check IS-IS neighbors
show isis neighbors                    -- Neighbor state (UP = good)
show isis neighbors detail             -- Detailed neighbor info

# Step 2: Check IS-IS database
show isis database                     -- LSDB
show isis database verbose             -- Detailed LSDB

# Step 3: Check IS-IS routes
show route isis                        -- IS-IS routes in RIB
show isis topology                     -- IS-IS topology
```

### MPLS Troubleshooting

#### LDP Troubleshooting
```
show mpls ldp neighbor                 -- LDP neighbors
show mpls ldp discovery                -- LDP discovery
show mpls ldp bindings                 -- Label bindings
show mpls forwarding                   -- MPLS forwarding table
show mpls forwarding labels <label>    -- Specific label
```

#### SR Troubleshooting
```
show segment-routing mpls state        -- SR-MPLS state
show segment-routing mpls lb           -- Label blocks
show segment-routing mpls mapping      -- SID mapping
show segment-routing traffic-eng policy  -- SR-TE policies
```

### VRF Troubleshooting
```
show vrf                               -- VRF list
show vrf <name> interface              -- VRF interfaces
show route vrf <name>                  -- VRF routing table
show cef vrf <name>                    -- VRF CEF table
ping vrf <name> <ip>                   -- Ping from VRF
traceroute vrf <name> <ip>             -- Traceroute from VRF
```

### BFD Troubleshooting
```
show bfd summary                       -- BFD summary
show bfd neighbors                     -- BFD neighbors
show bfd neighbors detail              -- Detailed BFD info
```

## Common Troubleshooting Scenarios

### Scenario 1: BGP Neighbor Not Coming Up
```
# Check neighbor state
show bgp summary | include <neighbor>

# Check TCP connectivity
ping <neighbor>
show tcp brief | include <neighbor>

# Check BGP configuration
show running-config router bgp | include <neighbor>

# Check for ACL blocking
show access-lists | include <neighbor>

# Check for route to neighbor
show route <neighbor>

# Check BGP log messages
show log | include BGP.*<neighbor>
```

### Scenario 2: Route Not in RIB
```
# Check BGP table
show bgp <prefix>

# Check RIB
show route <prefix>

# Check CEF
show cef <prefix>

# Check route policy
show route-policy <name>

# Check admin distance
show route <prefix> detail
```

### Scenario 3: Interface Down
```
# Check interface status
show interfaces <name>

# Check physical layer
show controllers <interface>

# Check for errors
show interfaces <name> errors

# Check transceiver
show controllers <interface> transceiver detail

# Check for configuration issues
show running-config interface <name>

# Check for shutdown
show interfaces <name> | include administratively
```

### Scenario 4: High CPU Utilization
```
# Check CPU usage
show processes cpu

# Check top processes
show processes cpu sorted

# Check memory usage
show processes memory

# Check for packet interrupts
show controllers <interface> counters

# Check for routing protocol issues
show bgp summary
show ospf neighbor
show isis neighbors
```

### Scenario 5: MPLS Label Not Assigned
```
# Check LDP neighbor
show mpls ldp neighbor

# Check LDP bindings
show mpls ldp bindings <prefix>

# Check MPLS forwarding
show mpls forwarding

# Check IGP routes
show route <prefix>

# Check LDP configuration
show running-config mpls ldp
```

## Debug Commands (Use with Caution)

```
debug bgp                              -- BGP debugging
debug ospf events                      -- OSPF event debugging
debug isis adj-packets                 -- IS-IS adjacency debugging
debug mpls ldp                         -- LDP debugging
debug bfd                              -- BFD debugging
debug ip packet                        -- IP packet debugging
undebug all                            -- Disable all debugging
```

## Log Analysis

### Show Logs
```
show logging                           -- System logs
show logging | include <pattern>       -- Filter logs
show logging last 100                  -- Last 100 log entries
show logging rate-limit                -- Rate-limited logs
```

### Common Log Patterns
```
%BGP-5-ADJCHANGE: neighbor <ip> Up     -- BGP neighbor up
%BGP-5-ADJCHANGE: neighbor <ip> Down   -- BGP neighbor down
%OSPF-5-ADJCHG: Process <pid>, Nbr <ip> on <intf> is FULL  -- OSPF adjacency up
%OSPF-5-ADJCHG: Process <pid>, Nbr <ip> on <intf> is DOWN  -- OSPF adjacency down
%ISIS-5-ADJCHANGE: Level <level> adjacency to <system> on <intf> is UP  -- IS-IS adjacency up
%LINEPROTO-5-UPDOWN: Line protocol on Interface <intf>, changed state to up  -- Interface up
%LINEPROTO-5-UPDOWN: Line protocol on Interface <intf>, changed state to down  -- Interface down
```

## Best Practices

1. **Always use `show` commands before `debug`**
2. **Use `terminal monitor`** to see logs on console
3. **Use `terminal length 0`** when scripting
4. **Document all troubleshooting steps**
5. **Use `commit confirmed`** for production changes
6. **Check logs first** before diving into protocol debugging
7. **Verify physical layer** before troubleshooting routing
8. **Use ping/traceroute** to verify connectivity
9. **Check CEF table** for forwarding issues
10. **Use `show route <prefix> detail`** for route selection info
