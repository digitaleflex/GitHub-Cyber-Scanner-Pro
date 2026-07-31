# Troubleshooting Reference

## Diagnostic Command Framework

### General Health Check
```
show sdwan system status              -- System status
show sdwan control connections        -- Control connections
show sdwan control summary            -- Control summary
show sdwan bfd sessions               -- BFD sessions
show sdwan omp peers                  -- OMP peers
show sdwan omp routes                 -- OMP routes
show sdwan ipsec local-sa             -- IPsec SAs
show sdwan tunnel sla                 -- Tunnel SLA
show sdwan policy from-vsmart         -- Policies from vSmart
```

### Control Plane Troubleshooting

#### Edge to vBond Issues
```
show sdwan control connections        -- Check vBond connection
show sdwan system status              -- Check system status
show sdwan certificate                -- Check certificates
ping <vbond-ip>                        -- Check connectivity
```

#### Edge to vSmart Issues
```
show sdwan omp peers                  -- Check OMP peers
show sdwan control connections        -- Check vSmart connections
show sdwan omp summary                -- Check OMP summary
ping <vsmart-ip>                       -- Check connectivity
```

#### OMP Route Issues
```
show sdwan omp routes                 -- Check OMP routes
show sdwan omp tlocs                  -- Check TLOCs
show sdwan omp peers                  -- Check peer status
show ip route omp                     -- Check routing table
```

### Data Plane Troubleshooting

#### BFD Session Issues
```
show sdwan bfd sessions               -- Check BFD sessions
show sdwan bfd summary                -- Check BFD summary
show sdwan bfd history                -- Check BFD history
debug sdwan bfd events                -- BFD debugging
```

#### IPsec Tunnel Issues
```
show sdwan ipsec local-sa             -- Check local SAs
show sdwan ipsec outbound-sa          -- Check outbound SAs
show sdwan ipsec connections          -- Check connections
debug sdwan ipsec events              -- IPsec debugging
```

#### Application-Aware Routing Issues
```
show sdwan policy from-vsmart         -- Check policies
show sdwan policy data-policy         -- Check data policy
show sdwan app-route statistics       -- Check app stats
show sdwan sla                        -- Check SLA status
```

### Policy Troubleshooting

#### Policy Not Applied
```
show sdwan policy from-vsmart         -- Check policies from vSmart
show sdwan policy access-list-associations  -- Check ACL associations
show sdwan policy data-policy         -- Check data policy status
show running-config sdwan             -- Check configuration
```

#### Application Not Recognized
```
show sdwan app-route statistics       -- Check app stats
show sdwan app-route stats application  -- Check per-app stats
show sdwan dpi statistics             -- Check DPI stats
```

### Common Issues and Solutions

#### Issue 1: Device Not Connecting to vBond
```
Symptoms:
  - show sdwan control connections shows vBond as down
  - Device not appearing in vManage

Troubleshooting:
  1. Check DHCP Option 43 or DNS for vBond discovery
  2. Verify vBond is reachable (ping)
  3. Check firewall rules for UDP 12346
  4. Verify device serial number in vManage
  5. Check certificate status
```

#### Issue 2: OMP Session Down
```
Symptoms:
  - show sdwan omp peers shows peer as down
  - Routes not being exchanged

Troubleshooting:
  1. Check control connections to vSmart
  2. Verify vSmart is reachable
  3. Check OMP configuration
  4. Verify certificates are valid
  5. Check vSmart logs
```

#### Issue 3: BFD Session Down
```
Symptoms:
  - show sdwan bfd sessions shows session as down
  - Tunnel not forwarding traffic

Troubleshooting:
  1. Check IPsec SAs (show sdwan ipsec local-sa)
  2. Verify transport interface is up
  3. Check BFD configuration
  4. Verify remote TLOC is reachable
  5. Check for MTU issues
```

#### Issue 4: Application Not Using Correct Transport
```
Symptoms:
  - Traffic not following expected path
  - SLA not being met

Troubleshooting:
  1. Check data policy (show sdwan policy from-vsmart)
  2. Verify SLA class configuration
  3. Check application recognition (show sdwan app-route stats)
  4. Verify transport SLA (show sdwan sla)
  5. Check policy hit counts
```

### Debug Commands
```
debug sdwan bfd events                -- BFD debugging
debug sdwan omp events                -- OMP debugging
debug sdwan ipsec events              -- IPsec debugging
debug sdwan control connections       -- Control connection debugging
debug sdwan dpi packets               -- DPI debugging
undebug all                           -- Disable all debugging
```

### Log Analysis
```
show logging                          -- System logs
show logging | include SDWAN          -- SD-WAN logs
show logging | include BFD            -- BFD logs
show logging | include OMP            -- OMP logs
show logging | include IPSEC          -- IPsec logs
show logging | include POLICY         -- Policy logs
```

## Troubleshooting Best Practices

1. **Start with show commands** before using debug
2. **Check control plane** before data plane
3. **Verify connectivity** before checking protocols
4. **Check certificates** for authentication issues
5. **Monitor BFD sessions** for tunnel health
6. **Use vManage troubleshooting** tools
7. **Document all findings** for future reference
8. **Test fixes** in lab before production
9. **Use DevNet sandbox** for reproduction
10. **Contact Cisco TAC** for complex issues
