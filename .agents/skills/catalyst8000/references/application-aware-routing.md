# Application-Aware Routing Reference

## Overview

Application-Aware Routing (AAR) is the core SD-WAN feature that steers application traffic over the best transport based on SLA requirements.

### How AAR Works
```
Application Traffic → DPI Classification → SLA Check → Best Transport Selection → Forward
```

1. **DPI**: Deep Packet Inspection identifies applications
2. **SLA Check**: Measures latency, loss, jitter per transport
3. **Selection**: Chooses best transport meeting SLA
4. **Forward**: Sends traffic over selected transport

## SLA Classes

### SLA Class Definition
```json
{
  "name": "Voice-SLA",
  "latency": 150,
  "loss": 1,
  "jitter": 30
}
```

### Common SLA Classes
| SLA Class | Latency (ms) | Loss (%) | Jitter (ms) | Use Case |
|-----------|-------------|----------|-------------|----------|
| **Voice** | 150 | 1 | 30 | VoIP, WebEx |
| **Video** | 200 | 2 | 50 | Video streaming |
| **Critical-Data** | 250 | 3 | 100 | ERP, CRM |
| **Default** | 500 | 10 | 200 | Best effort |

### SLA Class Configuration (vManage)
```
Policy Type: SLA Class
Name: Voice-SLA
Latency: 150
Loss: 1
Jitter: 30
```

## Forwarding Classes

### Forwarding Class Definition
- Maps traffic to specific queues
- Used in QoS policies
- 8 forwarding classes (0-7)

### Common Forwarding Classes
| Class | Queue | Use Case |
|-------|-------|----------|
| **0** | Default | Best effort |
| **1** | High Priority | Voice |
| **2** | Medium-High | Video |
| **3** | Medium | Critical data |
| **4-7** | Lower | Bulk data |

## Data Policies

### Data Policy Structure
```
Policy Type: Data
Name: App-Aware-Routing
Default Action: Forward-Class 0

Sequences:
  10: Match Application = Office365
      Action: SLA-Class = Voice
              Forward-Class = 1
  20: Match Application = WebEx
      Action: SLA-Class = Voice
              Forward-Class = 1
  30: Match Application = YouTube
      Action: SLA-Class = Video
              Forward-Class = 2
  40: Match Any
      Action: Forward-Class = 0
```

### Data Policy Configuration (vManage)
1. Navigate to **Configuration > Policies**
2. Click **Add Policy > Data**
3. Add sequences with match/action
4. Apply to sites or device groups

### Match Criteria
| Match Type | Description |
|------------|-------------|
| **Application** | DPI-based app identification |
| **Source IP** | Source IP address/prefix |
| **Destination IP** | Destination IP address/prefix |
| **Protocol** | TCP, UDP, ICMP |
| **Source Port** | Source port number |
| **Destination Port** | Destination port number |
| **DSCP** | DSCP value |
| **VPN** | VPN ID |

### Action Types
| Action Type | Description |
|-------------|-------------|
| **Set SLA Class** | Assign SLA class for transport selection |
| **Set Forward Class** | Assign forwarding class for QoS |
| **Set DSCP** | Set DSCP value |
| **Set Next-Hop** | Set next-hop IP |
| **Set TLOC** | Set specific TLOC |
| **Drop** | Drop traffic |
| **Accept** | Accept traffic |

## Topology Rules

### Hub-and-Spoke
```
Policy Type: Control
Name: Hub-Spoke-Topology
Sequence:
  10: Match Site-ID = Spoke-Sites
      Action: Restrict to Hub-Sites
  20: Match Site-ID = Hub-Sites
      Action: Allow All
```

### Full Mesh
```
Policy Type: Control
Name: Full-Mesh
Sequence:
  10: Match Any
      Action: Allow All
```

### Regional Mesh
```
Policy Type: Control
Name: Regional-Mesh
Sequence:
  10: Match Region = North
      Action: Allow North Sites
  20: Match Region = South
      Action: Allow South Sites
```

## Application Recognition

### DPI-Based Recognition
- Uses Deep Packet Inspection
- Identifies 3000+ applications
- Updated regularly via vManage

### Custom Applications
```
Policy Type: Application List
Name: Custom-Apps
Applications:
  - Office365
  - WebEx
  - Salesforce
  - Custom-App-1
```

### Application Groups
```
Policy Type: Application Group
Name: Business-Critical
Applications:
  - Office365
  - WebEx
  - Salesforce
  - SAP
```

## AAR Show Commands

### Policy Status
```
show sdwan policy from-vsmart             -- Policies from vSmart
show sdwan policy access-list-associations -- ACL associations
show sdwan policy data-policy             -- Data policy status
```

### Application Statistics
```
show sdwan app-route sla-class            -- SLA class status
show sdwan app-route statistics           -- Application statistics
show sdwan app-route stats application    -- Per-app statistics
show sdwan app-route stats transport      -- Per-transport statistics
```

### SLA Status
```
show sdwan sla                            -- SLA status
show sdwan sla detail                     -- Detailed SLA info
show sdwan sla history                    -- SLA history
```

## AAR Troubleshooting

### Policy Not Applied
```
show sdwan policy from-vsmart             -- Check policies
show sdwan policy data-policy             -- Check data policy
show sdwan policy access-list-associations -- Check associations
show running-config sdwan                 -- Check configuration
```

### Application Not Recognized
```
show sdwan app-route statistics           -- Check app stats
show sdwan app-route stats application    -- Check per-app stats
show sdwan dpi statistics                 -- Check DPI stats
```

### SLA Not Met
```
show sdwan sla                            -- Check SLA status
show sdwan bfd sessions                   -- Check BFD sessions
show sdwan tunnel sla                     -- Check tunnel SLA
show sdwan app-route sla-class            -- Check SLA classes
```

## Common Scenarios

### Scenario 1: Voice Traffic over MPLS
```
Data Policy: Voice-Over-MPLS
Sequence 10:
  Match: Application = WebEx, Office365-Voice
  Action: SLA-Class = Voice
          Forward-Class = 1
```

### Scenario 2: Video Traffic over Internet
```
Data Policy: Video-Over-Internet
Sequence 10:
  Match: Application = YouTube, Netflix
  Action: SLA-Class = Video
          Forward-Class = 2
```

### Scenario 3: Critical Data with Fallback
```
Data Policy: Critical-Data-Fallback
Sequence 10:
  Match: Application = SAP, Oracle
  Action: SLA-Class = Critical-Data
          Forward-Class = 3
          Fallback: Best-Effort
```

## Best Practices

1. **Define SLA classes** based on application requirements
2. **Use DPI** for application identification
3. **Test policies** in vManage before pushing to fabric
4. **Monitor application statistics** regularly
5. **Use forwarding classes** for QoS integration
6. **Document policy topology** for troubleshooting
7. **Test failover scenarios** in lab before production
8. **Monitor SLA compliance** regularly
9. **Use application groups** for easier policy management
10. **Test in DevNet sandbox** before production
