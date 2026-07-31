# vManage Configuration Reference

## vManage Overview

### Key Functions
- **Network Management**: Single pane of glass for SD-WAN fabric
- **Configuration Templates**: Feature and device templates
- **Policy Management**: Centralized, localized, and app-aware policies
- **Monitoring**: Real-time fabric monitoring and troubleshooting
- **Software Management**: Image distribution and upgrades

### Access
```
URL: https://<vmanage-ip>
Username: admin
Password: <configured-password>
```

## Template Configuration

### Feature Templates

#### System Template
```json
{
  "templateName": "System-Template",
  "templateDescription": "System configuration template",
  "deviceType": "c8000v",
  "configType": "template",
  "factoryDefault": false,
  "policyId": "",
  "featureTemplateUidRange": [],
  "generalTemplates": [
    {
      "templateId": "system-template-id",
      "templateType": "system"
    }
  ]
}
```

#### VPN Template
```json
{
  "templateName": "VPN-0-Template",
  "templateDescription": "Transport VPN template",
  "deviceType": "c8000v",
  "configType": "template",
  "templateId": "vpn-template-id",
  "templateType": "vpn"
}
```

#### Interface Template
```json
{
  "templateName": "GE-Interface-Template",
  "templateDescription": "GigabitEthernet interface template",
  "deviceType": "c8000v",
  "configType": "template",
  "templateId": "interface-template-id",
  "templateType": "vpn- interface"
}
```

### Device Templates

#### Create Device Template
1. Navigate to **Configuration > Templates**
2. Click **Add Template > Device**
3. Select device type (c8000v)
4. Add feature templates
5. Save and attach to devices

#### Attach Template to Device
1. Select device template
2. Click **Attach to Devices**
3. Select target devices
4. Configure template variables
5. Click **Configure**

## Policy Configuration

### Centralized Policies

#### Data Policy (Application-Aware Routing)
```
Policy Type: Data
Policy Name: App-Aware-Policy
Sequence:
  1. Match: Application = Office365
     Action: Set SLA-Class = Voice
             Forward-Class = 1
  2. Match: Application = WebEx
     Action: Set SLA-Class = Realtime
             Forward-Class = 2
  3. Match: Any
     Action: Forward-Class = 0
```

#### Control Policy
```
Policy Type: Control
Policy Name: Route-Filter-Policy
Sequence:
  1. Match: Route = 10.0.0.0/8
     Action: Accept
  2. Match: Any
     Action: Reject
```

### Localized Policies

#### ACL Policy
```
Policy Type: ACL
Policy Name: Branch-ACL
Sequence:
  1. Match: Source = 192.168.1.0/24
            Destination = Any
            Protocol = TCP
            Port = 80,443
     Action: Accept
  2. Match: Any
     Action: Reject
```

## Monitoring

### Dashboard Views
- **Network Summary**: Fabric health, device status, tunnel count
- **Alarms**: Active alarms, severity, acknowledgment
- **Events**: System events, audit trail
- **Troubleshooting**: Packet capture, flow analysis, path trace

### Device Monitoring
```
show sdwan system status              -- Device status
show sdwan control connections        -- Control connections
show sdwan bfd sessions               -- BFD sessions
show sdwan omp peers                  -- OMP peers
show sdwan omp routes                 -- OMP routes
```

### Application Monitoring
- **Application Recognition**: DPI-based app identification
- **Application Statistics**: Per-app traffic, performance
- **Application SLA**: Latency, loss, jitter per app
- **Application Policies**: Policy hit counts, effectiveness

## Software Management

### Image Upload
1. Navigate to **Administration > Device > Software**
2. Click **Upload Image**
3. Select image file
4. Upload to vManage

### Image Distribution
1. Select target devices
2. Choose software version
3. Schedule upgrade
4. Monitor progress

### Device Activation
1. Navigate to **Configuration > Devices**
2. Select devices
3. Click **Activate**
4. Monitor activation status

## vManage API

### Authentication
```bash
curl -k -X POST "https://<vmanage-ip>/j_security_check" \
  -d "j_username=admin" \
  -d "j_password=<password>" \
  -c cookies.txt
```

### Get Devices
```bash
curl -k -X GET "https://<vmanage-ip>/dataservice/device" \
  -b cookies.txt
```

### Get Templates
```bash
curl -k -X GET "https://<vmanage-ip>/dataservice/template/device" \
  -b cookies.txt
```

### Get Policies
```bash
curl -k -X GET "https://<vmanage-ip>/dataservice/template/policy/definition" \
  -b cookies.txt
```

## Best Practices

1. **Use feature templates** for consistent configuration
2. **Validate templates** before attaching to devices
3. **Use device templates** to bundle feature templates
4. **Test policies** in vManage before pushing to fabric
5. **Monitor alarms** regularly
6. **Use maintenance windows** for software upgrades
7. **Document all changes** with comments
8. **Backup vManage** configuration regularly
9. **Use role-based access** for multi-admin environments
10. **Test in DevNet sandbox** before production
