# Catalyst 8000 QoS and Security Reference

## QoS Configuration

### QoS Overview
- **Classification**: Match traffic based on DSCP, application, ACL
- **Marking**: Set DSCP/CoS values
- **Policing**: Rate limit traffic
- **Shaping**: Smooth traffic bursts
- **Queuing**: Priority queuing for critical traffic

### QoS Policy Configuration (vManage)

#### QoS Policy Structure
```
Policy Type: QoS
Name: Branch-QoS
Queues:
  Queue 1: Voice (Priority, 20%)
  Queue 2: Video (Bandwidth, 30%)
  Queue 3: Critical Data (Bandwidth, 30%)
  Queue 4: Best Effort (Bandwidth, 20%)
```

#### Traffic Classification
```
Policy Type: QoS
Sequence 10:
  Match: DSCP = EF
  Action: Queue = 1 (Priority)
Sequence 20:
  Match: DSCP = AF41
  Action: Queue = 2 (Bandwidth 30%)
Sequence 30:
  Match: DSCP = AF21
  Action: Queue = 3 (Bandwidth 30%)
Sequence 40:
  Match: Any
  Action: Queue = 4 (Bandwidth 20%)
```

### QoS Show Commands
```
show sdwan policy qos                   -- QoS policy status
show sdwan policy qos interface         -- Per-interface QoS
show policy-map interface               -- Policy map status
show class-map                          -- Class map definitions
```

## Zone-Based Firewall

### Overview
- Stateful firewall between zones
- Default deny between zones
- Configured via vManage templates

### Zone Configuration
```
Zone: Inside (LAN interfaces)
Zone: Outside (WAN interfaces)
Zone: Guest (Guest WiFi)

Policy: Inside → Outside = Allow
Policy: Outside → Inside = Deny (except established)
Policy: Guest → Outside = Allow (restricted)
Policy: Guest → Inside = Deny
```

### Firewall Policy (vManage)
```
Policy Type: Zone-Based Firewall
Name: Branch-Firewall
Zones:
  Inside → Outside: Allow All
  Outside → Inside: Allow Established
  Guest → Outside: Allow HTTP/HTTPS
  Guest → Inside: Deny All
```

### Firewall Show Commands
```
show zone-pair security                 -- Zone pair status
show policy-map type inspect            -- Firewall policy status
show ip inspect sessions                -- Active sessions
show ip inspect statistics              -- Firewall statistics
```

## Intrusion Prevention System (IPS)

### IPS Overview
- Signature-based threat detection
- Integrated into SD-WAN fabric
- Configured via vManage

### IPS Configuration
```
Policy Type: IPS
Name: Branch-IPS
Signatures: Enabled
Action: Drop + Log
Update: Automatic from Cisco
```

### IPS Show Commands
```
show ips signature                      -- IPS signatures
show ips statistics                     -- IPS statistics
show ips alerts                         -- IPS alerts
show ips status                         -- IPS status
```

## URL Filtering

### URL Filtering Overview
- Block/allow URLs based on categories
- Integrated with Cisco Umbrella
- Configured via vManage

### URL Filtering Configuration
```
Policy Type: URL Filtering
Name: Branch-URL-Filter
Categories:
  Block: Malware, Phishing, Adult
  Allow: Business, Education
  Monitor: Social Media
Action: Block + Log
```

### URL Filtering Show Commands
```
show url-filtering statistics           -- URL filtering stats
show url-filtering alerts               -- URL alerts
show url-filtering status               -- URL filtering status
```

## TLS Inspection

### TLS Inspection Overview
- Decrypt and inspect encrypted traffic
- Requires certificate deployment
- Configured via vManage

### TLS Inspection Configuration
```
Policy Type: TLS Inspection
Name: Branch-TLS-Inspect
Mode: Decrypt + Inspect
Certificate: vManage-signed CA
Exclusions: Banking, Healthcare
```

### TLS Inspection Show Commands
```
show tls-inspection statistics          -- TLS inspection stats
show tls-inspection status              -- TLS inspection status
show tls-inspection certificates        -- Certificate status
```

## Security Best Practices

1. **Enable zone-based firewall** on all edge routers
2. **Configure IPS** with automatic signature updates
3. **Enable URL filtering** for web security
4. **Use TLS inspection** for encrypted traffic visibility
5. **Monitor security alerts** regularly
6. **Test security policies** in lab before production
7. **Document security topology** for troubleshooting
8. **Use role-based access** for security management
9. **Test in DevNet sandbox** before production
10. **Keep signatures updated** regularly
