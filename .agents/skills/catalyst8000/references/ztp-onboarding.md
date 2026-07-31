# Zero-Touch Provisioning and Onboarding Reference

## ZTP Overview

### What is ZTP?
- Zero-Touch Provisioning (ZTP) allows edge routers to automatically configure themselves
- Devices contact vBond orchestrator on first boot
- vBond authenticates device with vManage
- vManage pushes configuration templates
- No manual configuration required

### ZTP Process Flow
```
1. Device boots with factory default config
2. Device contacts vBond (via DHCP Option or DNS)
3. vBond authenticates device with vManage
4. vManage validates device serial number
5. vManage pushes configuration templates
6. Device applies configuration
7. Device establishes control connections
8. Device is fully operational
```

## ZTP Configuration

### DHCP Options
```
Option 43: vBond IP address
Option 15: Domain name
Option 6: DNS server
Option 67: Bootfile name (optional)
```

### DHCP Configuration Example
```
option sdwan-vbond code 43 = ip-address;
option sdwan-domain code 15 = text;

subnet 10.10.20.0 netmask 255.255.255.0 {
  option routers 10.10.20.1;
  option domain-name "sdwan.local";
  option sdwan-vbond 10.10.20.102;
  option sdwan-domain "MyOrg";
}
```

### DNS-Based ZTP
```
DNS Record:
  vbond.sdwan.local → 10.10.20.102

Device resolves vbond.sdwan.local
Contacts vBond at resolved IP
```

## Device Onboarding

### Onboarding via vManage

#### Step 1: Add Device to vManage
1. Navigate to **Configuration > Devices**
2. Click **Add Devices**
3. Enter device serial number
4. Select device model (c8000v)
5. Generate chassis token

#### Step 2: Generate Bootstrap Configuration
1. Select device
2. Click **Generate Bootstrap**
3. Configure:
   - System IP
   - Site ID
   - Organization name
   - vBond IP/port
   - vManage IP
4. Download bootstrap config

#### Step 3: Apply Bootstrap
```
# Via console/SSH during first boot
sdwan
 system
  system-ip 1.1.1.1
  site-id 100
  org-name MyOrg
  controller-group default
  vbond 10.10.20.102 port 12346
 !
!
```

#### Step 4: Verify Onboarding
```
show sdwan system status              -- System status
show sdwan control connections        -- Control connections
show sdwan control summary            -- Control summary
show sdwan omp peers                  -- OMP peers
```

### Onboarding via CLI

#### Manual Configuration
```
sdwan
 system
  system-ip 1.1.1.1
  site-id 100
  org-name MyOrg
  controller-group default
  vbond 10.10.20.102 port 12346
 !
 interface GigabitEthernet1
  ip address 10.10.20.110 255.255.255.0
  no shutdown
 !
 interface GigabitEthernet2
  tunnel-interface GigabitEthernet2
   encapsulation ipsec
   color internet
   carrier default
   allow-service all
  !
 !
!
```

## Certificate Management

### Certificate Types
| Certificate | Purpose | Issued By |
|-------------|---------|-----------|
| **Device Certificate** | Device authentication | vManage |
| **vSmart Certificate** | Controller authentication | vManage |
| **vBond Certificate** | Orchestrator authentication | vManage |
| **Root CA** | Trust anchor | Cisco or Custom |

### Certificate Installation
```
1. vManage generates device certificate
2. Certificate pushed to device during onboarding
3. Device uses certificate for DTLS/TLS authentication
4. Certificate validated by vSmart/vBond
```

### Certificate Show Commands
```
show sdwan certificate                  -- Device certificates
show sdwan certificate detail           -- Detailed certificate info
show sdwan control local-properties     -- Local certificate properties
```

## ZTP Troubleshooting

### Device Not Contacting vBond
```
1. Check DHCP configuration
2. Verify DNS resolution
3. Check network connectivity
4. Verify vBond is reachable
5. Check firewall rules
```

### Authentication Failure
```
1. Verify serial number in vManage
2. Check chassis token
3. Verify organization name
4. Check certificate status
5. Review vManage logs
```

### Configuration Not Applied
```
1. Check template attachment
2. Verify template variables
3. Check template validation
4. Review vManage logs
5. Check device status
```

### ZTP Show Commands
```
show sdwan system status                -- System status
show sdwan control connections          -- Control connections
show sdwan control summary              -- Control summary
show sdwan certificate                  -- Certificate status
show sdwan ztp status                   -- ZTP status (if available)
```

## ZTP Best Practices

1. **Use DHCP Option 43** for vBond discovery
2. **Configure DNS** as fallback for vBond discovery
3. **Pre-register devices** in vManage before deployment
4. **Use consistent org-name** across all devices
5. **Test ZTP process** in lab before production
6. **Document ZTP topology** for troubleshooting
7. **Monitor onboarding status** in vManage
8. **Use bootstrap configs** for remote deployments
9. **Verify certificate status** after onboarding
10. **Test in DevNet sandbox** before production
