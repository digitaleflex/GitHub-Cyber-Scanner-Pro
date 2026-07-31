# Telemetry and Monitoring Reference

## vManage Monitoring

### Dashboard Views
- **Network Summary**: Fabric health, device status, tunnel count
- **Alarms**: Active alarms, severity, acknowledgment
- **Events**: System events, audit trail
- **Applications**: Application recognition, statistics, SLA
- **Devices**: Per-device health, resources, interfaces

### Alarm Management
```
Alarm Severities:
  - Critical: Immediate action required
  - Major: Significant impact
  - Medium: Moderate impact
  - Minor: Low impact
  - Info: Informational
```

### Alarm Show Commands
```
show sdwan system status              -- System status
show sdwan control connections        -- Control connections
show sdwan bfd sessions               -- BFD sessions
show sdwan omp peers                  -- OMP peers
show sdwan omp routes                 -- OMP routes
```

## Streaming Telemetry

### Telemetry Configuration
```
sdwan
 telemetry
  server vmanage
   source-interface GigabitEthernet1
   port 57400
  !
 !
!
```

### Telemetry Data Types
| Data Type | Description | Interval |
|-----------|-------------|----------|
| **BFD** | BFD session status | 5 seconds |
| **OMP** | OMP routes and TLOCs | 5 seconds |
| **Interface** | Interface statistics | 5 seconds |
| **System** | CPU, memory, disk | 60 seconds |
| **Application** | Application statistics | 5 seconds |
| **Tunnel** | Tunnel SLA and status | 5 seconds |

### Telemetry Show Commands
```
show sdwan telemetry status           -- Telemetry status
show sdwan telemetry server           -- Telemetry server config
show sdwan telemetry subscription     -- Active subscriptions
```

## SNMP Configuration

### SNMP Configuration
```
snmp-server community public RO
snmp-server community private RW
snmp-server host 10.10.20.50 version 2c public
snmp-server location "Branch Office"
snmp-server contact "admin@company.com"
```

### SNMP Traps
```
snmp-server enable traps sdwan
snmp-server enable traps bfd
snmp-server enable traps ospf
snmp-server enable traps bgp
```

## Syslog Configuration

### Syslog Configuration
```
logging host 10.10.20.60
logging trap informational
logging source-interface GigabitEthernet1
logging facility local7
```

### Syslog Show Commands
```
show logging                          -- System logs
show logging | include SDWAN          -- SD-WAN logs
show logging | include BFD            -- BFD logs
show logging | include OMP            -- OMP logs
```

## NetFlow Configuration

### NetFlow Configuration
```
flow exporter NETFLOW-EXPORTER
 destination 10.10.20.70
 source GigabitEthernet1
 transport udp 2055
!

flow monitor NETFLOW-MONITOR
 exporter NETFLOW-EXPORTER
 record netflow-original
!

interface GigabitEthernet1
 ip flow monitor NETFLOW-MONITOR input
 ip flow monitor NETFLOW-MONITOR output
!
```

## Monitoring Best Practices

1. **Configure SNMP** for external monitoring systems
2. **Enable syslog** for centralized logging
3. **Configure NetFlow** for traffic analysis
4. **Monitor vManage alarms** regularly
5. **Set up alert notifications** for critical events
6. **Monitor BFD sessions** for tunnel health
7. **Monitor OMP peers** for control plane health
8. **Monitor application statistics** for SLA compliance
9. **Use streaming telemetry** for real-time monitoring
10. **Test monitoring** in DevNet sandbox before production
