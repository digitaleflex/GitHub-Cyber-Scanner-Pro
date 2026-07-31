# DevNet Sandbox Reference

## Available Sandboxes

### Always-On Sandboxes

#### IOS XE on Cat8kv AlwaysOn
- **URL**: https://devnetsandbox.cisco.com
- **Category**: Networking
- **Description**: Pre-configured Catalyst 8000v environment
- **Access**: Always available, no reservation needed
- **Use Cases**:
  - Cat8000v CLI testing
  - IOS XE SD-WAN features
  - Basic configuration validation
  - API testing

#### SD-WAN 20.10 AlwaysOn
- **URL**: https://devnetsandbox.cisco.com
- **Category**: Networking
- **Description**: Full SD-WAN fabric with vManage, vSmart, vBond, and 4 edge routers
- **Access**: Always available, no reservation needed
- **Use Cases**:
  - Full SD-WAN fabric testing
  - vManage API testing
  - Policy configuration
  - Automation testing

### Reservable Sandboxes

#### IOS XE on Cat8kv
- **URL**: https://devnetsandbox.cisco.com
- **Category**: Networking
- **Description**: Dedicated Cat8000v environment
- **Access**: Requires reservation
- **Duration**: Up to 10 days
- **Use Cases**:
  - Dedicated Cat8000v testing
  - Custom configuration
  - Feature validation

#### SD-WAN 20.10
- **URL**: https://devnetsandbox.cisco.com
- **Category**: Networking
- **Description**: Full SD-WAN lab with vManage, vSmart, vBond, and edge routers
- **Access**: Requires reservation
- **Duration**: Up to 10 days
- **Use Cases**:
  - Full SD-WAN deployment testing
  - Custom fabric configuration
  - Policy development
  - Automation development

## Always-On Sandbox Details

### SD-WAN 20.10 AlwaysOn Topology
```
┌─────────────────────────────────────────────┐
│  vManage: 10.10.20.100                      │
│  vSmart:  10.10.20.101                      │
│  vBond:   10.10.20.102                      │
│                                              │
│  edge1:   10.10.20.110 (Cat8000v)           │
│  edge2:   10.10.20.120 (Cat8000v)           │
│  edge3:   10.10.20.130 (Cat8000v)           │
│  edge4:   10.10.20.140 (Cat8000v)           │
└─────────────────────────────────────────────┘
```

### Access Credentials
```
vManage:
  URL: https://sandbox-sdwan.cisco.com
  Username: admin
  Password: C1sco12345

Edge Routers:
  SSH: admin@10.10.20.110-140
  Username: admin
  Password: C1sco12345
```

## Testing Workflows

### API Testing
```bash
# Test vManage API
curl -k -X POST "https://sandbox-sdwan.cisco.com/j_security_check" \
  -d "j_username=admin" \
  -d "j_password=C1sco12345" \
  -c cookies.txt

# Get devices
curl -k -X GET "https://sandbox-sdwan.cisco.com/dataservice/device" \
  -b cookies.txt
```

### Python SDK Testing
```python
from catalystwan.session import create_session

session = create_session(
    url="https://sandbox-sdwan.cisco.com",
    username="admin",
    password="C1sco12345"
)

# Get devices
devices = session.api.device_inventory.get()
for device in devices:
    print(f"{device.hostname}: {device.device_type}")
```

### Terraform Testing
```hcl
provider "sdwan" {
  url      = "https://sandbox-sdwan.cisco.com"
  username = "admin"
  password = "C1sco12345"
}
```

### Sastre Testing
```bash
# Configure Sastre for sandbox
cat > sdwan.conf << EOF
[vmanage]
host = sandbox-sdwan.cisco.com
port = 443
user = admin
password = C1sco12345
EOF

# Export templates
sastre export templates

# Export policies
sastre export policies
```

## Sandbox Best Practices

1. **Use Always-On sandboxes** for quick testing
2. **Reserve dedicated sandboxes** for extended testing
3. **Test automation scripts** in sandbox before production
4. **Use sandbox for API development** and validation
5. **Test policy changes** in sandbox before production
6. **Document sandbox configurations** for reproducibility
7. **Reset sandbox** if configuration gets corrupted
8. **Use sandbox for training** and learning
9. **Test failover scenarios** in sandbox
10. **Validate DevNet code samples** in sandbox

## DevNet Learning Labs

### Relevant Learning Labs
- **Introduction to Cisco SD-WAN**
- **Cisco SD-WAN Programmability**
- **Cisco SD-WAN vManage API**
- **Cisco SD-WAN Automation with Python**
- **Cisco SD-WAN Terraform Provider**

### Learning Lab Resources
- **URL**: https://developer.cisco.com/learning/
- **Format**: Interactive, hands-on labs
- **Duration**: 1-4 hours per lab
- **Prerequisites**: Basic networking knowledge

## Code Exchange Resources

### Relevant Code Samples
- **sdwan-devops**: SD-WAN DevOps tools
- **catalystwan**: Python SDK examples
- **terraform-provider-sdwan**: Terraform examples
- **sdwan-ansible-code**: Ansible playbooks
- **sastre**: Automation toolset

### Code Exchange URL
- **URL**: https://developer.cisco.com/codeexchange/
- **Search**: "sdwan" or "catalyst"
- **Languages**: Python, Go, Terraform, Ansible
