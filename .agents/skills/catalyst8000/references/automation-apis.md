# Automation and APIs Reference

## DevNet Resources

### Key Repositories
| Repository | URL | Description |
|------------|-----|-------------|
| **terraform-provider-sdwan** | https://github.com/CiscoDevNet/terraform-provider-sdwan | Terraform provider for SD-WAN |
| **catalystwan** | https://github.com/CiscoDevNet/catalystwan | Python SDK for Catalyst WAN |
| **sastre** | https://github.com/CiscoDevNet/sastre | SD-WAN automation toolset |
| **sdwan-devops** | https://github.com/CiscoDevNet/sdwan-devops | SD-WAN DevOps tools |
| **sdwan-ansible-code** | https://github.com/CiscoDevNet/sdwan-ansible-code | Ansible playbooks for SD-WAN |
| **catalyst-sdwan-mcp-community** | https://github.com/CiscoDevNet/catalyst-sdwan-mcp-community | MCP server for vManage |
| **wan-automation-examples** | https://github.com/CiscoDevNet/wan-automation-examples | Python and Terraform examples |

## vManage REST API

### Authentication
```python
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VMANAGE_IP = "10.10.20.100"
USERNAME = "admin"
PASSWORD = "C1sco12345"

base_url = f"https://{VMANAGE_IP}/dataservice"

# Login
login_url = f"{base_url}/j_security_check"
login_data = {
    "j_username": USERNAME,
    "j_password": PASSWORD
}

session = requests.Session()
session.verify = False
response = session.post(login_url, data=login_data)

if "j_security_check" in response.text:
    print("Login failed")
else:
    print("Login successful")
```

### Get Devices
```python
# Get all devices
devices_url = f"{base_url}/device"
response = session.get(devices_url)
devices = response.json()["data"]

for device in devices:
    print(f"{device['host-name']}: {device['device-type']} - {device['reachability']}")
```

### Get Templates
```python
# Get device templates
templates_url = f"{base_url}/template/device"
response = session.get(templates_url)
templates = response.json()["data"]

for template in templates:
    print(f"{template['templateName']}: {template['deviceType']}")
```

### Get Policies
```python
# Get policy definitions
policies_url = f"{base_url}/template/policy/definition"
response = session.get(policies_url)
policies = response.json()["data"]

for policy in policies:
    print(f"{policy['name']}: {policy['type']}")
```

### Get BFD Sessions
```python
# Get BFD sessions from specific device
device_id = "edge1-uuid"
bfd_url = f"{base_url}/device/{device_id}/bfd/sessions"
response = session.get(bfd_url)
bfd_sessions = response.json()["data"]

for session in bfd_sessions:
    print(f"{session['system-ip']}: {session['state']}")
```

## Python SDK (catalystwan)

### Installation
```bash
pip install catalystwan
```

### Basic Usage
```python
from catalystwan.session import create_session
from catalystwan.api.device_inventory_api import DeviceInventoryAPI
from catalystwan.api.template_api import TemplatesAPI

# Create session
session = create_session(
    url="https://10.10.20.100",
    username="admin",
    password="C1sco12345"
)

# Get devices
device_inventory = DeviceInventoryAPI(session)
devices = device_inventory.get()
for device in devices:
    print(f"{device.hostname}: {device.device_type}")

# Get templates
templates_api = TemplatesAPI(session)
templates = templates_api.get_device_templates()
for template in templates:
    print(f"{template.template_name}: {template.device_type}")
```

### Deploy Template
```python
from catalystwan.api.template_api import TemplatesAPI

templates_api = TemplatesAPI(session)

# Get template
template = templates_api.get_device_template_by_name("Branch-Template")

# Deploy to device
deployment = templates_api.attach_device_template(
    template_id=template.id,
    devices=["edge1-uuid", "edge2-uuid"]
)

# Monitor deployment
process_id = deployment.process_id
status = templates_api.get_template_attachment_status(process_id)
print(f"Deployment status: {status}")
```

## Terraform Provider

### Installation
```bash
terraform init
```

### Provider Configuration
```hcl
terraform {
  required_providers {
    sdwan = {
      source  = "CiscoDevNet/sdwan"
      version = ">= 0.1.0"
    }
  }
}

provider "sdwan" {
  url      = "https://10.10.20.100"
  username = "admin"
  password = "C1sco12345"
}
```

### Create Feature Template
```hcl
resource "sdwan_system_feature_template" "system_template" {
  name        = "System-Template"
  description = "System configuration template"
  device_type = "c8000v"

  system_ip         = "1.1.1.1"
  site_id           = 100
  organization_name = "MyOrg"
}
```

### Create Device Template
```hcl
resource "sdwan_device_template" "branch_template" {
  name        = "Branch-Template"
  description = "Branch device template"
  device_type = "c8000v"

  feature_template_ids = [
    sdwan_system_feature_template.system_template.id,
    sdwan_vpn_feature_template.vpn0_template.id,
    sdwan_vpn_feature_template.vpn1_template.id,
  ]
}
```

### Attach Template to Device
```hcl
resource "sdwan_device_template_attachment" "branch_attachment" {
  device_template_id = sdwan_device_template.branch_template.id
  devices {
    device_id = "edge1-uuid"
    variables = {
      system_ip = "1.1.1.1"
      site_id   = "100"
    }
  }
}
```

## Sastre (SD-WAN Automation Toolset)

### Installation
```bash
pip install cisco-sdwan
```

### Configuration
```bash
# Create config file
cat > sdwan.conf << EOF
[vmanage]
host = 10.10.20.100
port = 443
user = admin
password = C1sco12345
EOF
```

### Common Commands
```bash
# Export all templates
sastre export templates

# Export all policies
sastre export policies

# Export all devices
sastre export devices

# Import templates
sastre import templates

# Import policies
sastre import policies

# Build device config
sastre build device edge1

# Deploy configuration
sastre deploy device edge1
```

## Ansible

### Inventory
```yaml
[vmanage]
vmanage ansible_host=10.10.20.100

[c8000v]
edge1 ansible_host=10.10.20.110
edge2 ansible_host=10.10.20.120
```

### Playbook Example
```yaml
---
- name: Configure Catalyst 8000v
  hosts: c8000v
  gather_facts: no
  tasks:
    - name: Configure system
      cisco.iosxr.iosxr_config:
        lines:
          - sdwan
          -  system
          -   system-ip {{ system_ip }}
          -   site-id {{ site_id }}
          -   org-name MyOrg
          -   controller-group default
          -   vbond 10.10.20.102 port 12346
          -  !
          - !
      vars:
        system_ip: "{{ hostvars[inventory_hostname]['system_ip'] }}"
        site_id: "{{ hostvars[inventory_hostname]['site_id'] }}"
```

## MCP Server (AI Assistant Integration)

### Overview
The catalyst-sdwan-mcp-community repository provides a Model Context Protocol (MCP) server for vManage, allowing AI assistants to query and manage SD-WAN fabric through vManage REST API.

### Setup
```bash
git clone https://github.com/CiscoDevNet/catalyst-sdwan-mcp-community.git
cd catalyst-sdwan-mcp-community
pip install -r requirements.txt
```

### Configuration
```json
{
  "vmanage": {
    "host": "10.10.20.100",
    "username": "admin",
    "password": "C1sco12345"
  }
}
```

### Available Tools
- Get device inventory
- Get device status
- Get BFD sessions
- Get OMP routes
- Get tunnel status
- Get application statistics
- Get policy status
- Deploy templates

## Best Practices

1. **Use catalystwan SDK** for Python automation
2. **Use Terraform** for infrastructure-as-code
3. **Use Sastre** for template/policy management
4. **Use Ansible** for device configuration
5. **Use MCP server** for AI assistant integration
6. **Test automation** in DevNet sandbox before production
7. **Version control** all automation scripts
8. **Use CI/CD** for automation deployment
9. **Document automation workflows** for team
10. **Monitor API rate limits** on vManage
