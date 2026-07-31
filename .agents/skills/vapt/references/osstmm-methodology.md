# OSSTMM-Based Assessment Methodology

Open Source Security Testing Methodology Manual (OSSTMM) structured assessment procedures organized by channel. Each channel includes testing steps, tool commands, verification procedures, and step-by-step remediation guidance.

## OSSTMM Channels

| Channel | Scope | Primary Tools |
|---------|-------|---------------|
| **Human** | Social engineering, physical security | Manual, Python scripts |
| **Physical** | Facilities, access controls, CCTV | Manual, site survey |
| **Network** | Routers, switches, firewalls, VPNs | NetExec, Secator, nmap |
| **Communications** | Protocols, wireless, VoIP | Secator, NetExec, Python |
| **Wireless** | WiFi, Bluetooth, IoT radios | aircrack-ng, bettercap |

## Assessment Types and Scope

### Blackbox (Zero Knowledge)

**Objective**: Simulate external attacker with no insider knowledge.

1. **Passive Recon Only** (no direct interaction with target)
   - WHOIS/DNS enumeration: `secator x subfinder target.com -raw`
   - Certificate transparency: `curl -s "https://crt.sh/?q=%25.target.com&output=json" | jq '.[].name_value'`
   - Search engine dorking: Google, Shodan, Censys
   - Public code repos: GitHub, GitLab search for leaked secrets
   - Social media: LinkedIn employee enumeration
   - Document metadata: PDF/Office file metadata extraction

2. **Active Recon** (direct interaction begins)
   - Port scanning: `secator x naabu target.com -p-`
   - Service identification: `secator x nmap target.com -sV -sC`
   - Web probing: `secator x httpx target.com -td -asn -cdn`

3. **Vulnerability Discovery**
   - Automated: `secator x nuclei target.com -tags cve -severity critical,high`
   - Manual testing per OWASP WSTG (see owasp-testing-guide.md)

### Greybox (Partial Knowledge)

**Objective**: Test with limited insider knowledge (e.g., standard user account).

1. **Validate Provided Information**
   ```bash
   # Verify credentials work
   nxc smb target -u provided_user -p 'provided_pass'
   nxc ssh target -u provided_user -p 'provided_pass'
   ```

2. **Enumerate Within Privilege Boundaries**
   ```bash
   nxc ldap target -u provided_user -p 'provided_pass' --users
   nxc smb target -u provided_user -p 'provided_pass' --shares
   ```

3. **Privilege Escalation Attempts**
   - Test horizontal escalation to other standard users
   - Test vertical escalation to admin/root
   - Test access to unauthorized resources

### Whitebox (Full Knowledge)

**Objective**: Comprehensive assessment with complete access.

1. **Source Code Review**
   - Static analysis: `secator x grype /path/to/code`
   - Secret scanning: `trufflehog filesystem /path/to/code`
   - Dependency audit: `pip-audit`, `npm audit`, `yarn audit`

2. **Configuration Review**
   ```bash
   # Review hardening compliance
   nxc smb target -u admin -p 'pass' --pass-pol
   ```

3. **Focused Exploit Testing**
   - Test every input point identified in code review
   - Verify access controls match documented requirements
   - Test authentication/authorization boundaries

---

## Network Channel Assessment

### Step 1: Host Discovery

```bash
# ICMP sweep
secator x fping 10.0.0.0/24

# ARP discovery (local segment)
nmap -sn -PR 10.0.0.0/24

# CIDR expansion
secator x mapcidr 10.0.0.0/16
```

### Step 2: Port Scanning

```bash
# TCP full scan
secator x naabu target.com -p- -rate 1000 -json

# UDP top ports
secator x nmap target.com -sU --top-ports 100 -json

# Service version detection
secator x nmap target.com -sV -sC -p 22,80,443,445,3389,8080 -json
```

### Step 3: Service Enumeration by Protocol

#### SMB (Port 445)
```bash
# Null session enumeration
nxc smb 10.0.0.0/24 -u '' -p ''
nxc smb target -u '' -p '' --shares
nxc smb target -u '' -p '' --sessions
nxc smb target -u '' -p '' --users

# Authenticated enumeration
nxc smb target -u admin -p 'P@ssw0rd' --shares
nxc smb target -u admin -p 'P@ssw0rd' --pass-pol
nxc smb target -u admin -p 'P@ssw0rd' --groups
nxc smb target -u admin -p 'P@ssw0rd' --local-groups

# Vulnerability scanning
nxc smb target -u '' -p '' -M enum_vulnerability
nxc smb target -u '' -p '' -M ms17-010
```

**Remediation — SMB Hardening (Step-by-Step)**:
1. Disable SMBv1: `Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force`
2. Require SMB signing: `Set-SmbServerConfiguration -RequireSecuritySignature $true -Force`
3. Block port 445 at perimeter firewall
4. Disable null sessions: Set `RestrictNullSessAccess=1` in registry
5. Verify: `nxc smb target -u '' -p '' --shares` should return ACCESS_DENIED
6. Verify: `nmap --script smb-protocols target` should show SMBv3 only

#### LDAP (Port 389/636)
```bash
# Anonymous bind enumeration
nxc ldap target -u '' -p '' --users
nxc ldap target -u '' -p '' --groups
nxc ldap target -u '' -p '' --asreproast asreproast.txt

# Authenticated enumeration
nxc ldap target -u admin -p 'P@ss' --users
nxc ldap target -u admin -p 'P@ss' --groups
nxc ldap target -u admin -p 'P@ss' --kerberoasting kerberoast.txt
nxc ldap target -u admin -p 'P@ss' --find-delegation
nxc ldap target -u admin -p 'P@ss' --gmsa
nxc ldap target -u admin -p 'P@ss' --check-ldap-signing
```

**Remediation — LDAP Hardening (Step-by-Step)**:
1. Enable LDAP signing: Group Policy → Computer Config → Windows Settings → Security → Local Policies → Security Options → "LDAP client signing requirements" → Set to "Require signing"
2. Enable Channel Binding: Set `LdapEnforceChannelBinding=1` in registry
3. Disable anonymous LDAP queries: Set `RestrictAnonymous=1` or `RestrictAnonymousSam=1`
4. Implement LDAPS (port 636) with valid certificates
5. Monitor: `nxc ldap target -u '' -p '' --users` should fail with anonymous bind denied
6. Verify: `nxc ldap target -u admin -p 'P@ss' --check-ldap-signing` shows signing required

#### SSH (Port 22)
```bash
nxc ssh target -u root -p 'password' --ssh-key /path/to/key
nxc ssh target -u root -p 'password' -x "id"
```

**Remediation — SSH Hardening (Step-by-Step)**:
1. Disable password auth: Set `PasswordAuthentication no` in `/etc/ssh/sshd_config`
2. Disable root login: Set `PermitRootLogin no`
3. Require key-based auth: Set `PubkeyAuthentication yes`
4. Set key algorithm: `KexAlgorithms curve25519-sha256` and `HostKeyAlgorithms ssh-ed25519`
5. Set MACs: `MACs hmac-sha2-512-etm@openssh.com`
6. Restart: `systemctl restart sshd`
7. Verify: `nxc ssh target -u root -p 'anypassword'` should fail with auth error

#### WinRM (Port 5985/5986)
```bash
nxc winrm target -u admin -p 'P@ssw0rd' -x "whoami"
nxc winrm target -u admin -p 'P@ssw0rd' -x "systeminfo"
```

**Remediation — WinRM Hardening (Step-by-Step)**:
1. Restrict WinRM listeners: `winrm set winrm/config/service '@{AllowUnencrypted="false"}'`
2. Require HTTPS: Configure WinRM with server certificate
3. Limit access: `winrm set winrm/config/service '@{MaxConnections=5"}'`
4. Restrict to specific IPs: Configure `AllowedSources` in firewall
5. Verify: `nxc winrm target -u '' -p ''` should fail; only authorized users connect

#### MSSQL (Port 1433)
```bash
nxc mssql target -u sa -p 'P@ssw0rd' --enum
nxc mssql target -u sa -p 'P@ssw0rd' -x "xp_cmdshell 'whoami'"
```

**Remediation — MSSQL Hardening (Step-by-Step)**:
1. Disable `xp_cmdshell`: `EXEC sp_configure 'xp_cmdshell', 0; RECONFIGURE;`
2. Disable `clr enabled`: `EXEC sp_configure 'clr enabled', 0; RECONFIGURE;`
3. Remove default `sa` account or rename: `ALTER LOGIN sa DISABLE;`
4. Enforce Windows Authentication mode
5. Apply principle of least privilege to database roles
6. Verify: `nxc mssql target -u sa -p 'oldpass'` should fail; xp_cmdshell disabled

#### RDP (Port 3389)
```bash
nxc rdp target -u admin -p 'P@ssw0rd'
nxc rdp target --screenshot  # Requires NLA disabled
```

**Remediation — RDP Hardening (Step-by-Step)**:
1. Enable Network Level Authentication (NLA): System Properties → Remote → "Allow connections only from computers running Remote Desktop with NLA"
2. Configure TLS: Set `SecurityLayer=2` and `MinEncryptionLevel=3` in registry
3. Restrict access via firewall to specific IP ranges
4. Change default port (optional): Update `PortNumber` in `HKLM\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp`
5. Verify: `nxc rdp target --nla` should require NLA and succeed only with valid credentials

#### FTP (Port 21)
```bash
nxc ftp target -u anonymous -p ''
nxc ftp target -u admin -p 'P@ssw0rd'
```

**Remediation — FTP Hardening (Step-by-Step)**:
1. Disable anonymous access in FTP server config
2. Use SFTP (SSH) or FTPS (TLS) instead of plain FTP
3. Restrict user access to specific directories (chroot)
4. Set upload/download permissions explicitly
5. Verify: `nxc ftp target -u anonymous -p ''` should return ACCESS_DENIED

#### NFS (Port 2049)
```bash
nxc nfs target --enum
nxc nfs target --share /export/home --download sensitive.txt
```

**Remediation — NFS Hardening (Step-by-Step)**:
1. Restrict exports to specific IPs: `/export/home 10.0.0.5(rw,sync,no_root_squash)` → `/export/home 10.0.0.5(rw,sync,root_squash,sec=krb5)`
2. Enable `root_squash` (never use `no_root_squash`)
3. Use `sec=krb5` or `sec=krb5p` for Kerberos authentication
4. Set `fsid=0` only on root exports
5. Verify: `nxc nfs target --enum` shows restricted exports only

### Step 4: Network Device Assessment

#### Cisco/Switches
```bash
# SNMP enumeration
nmap -sU -p 161 --script snmp-brute target
nmap -sU -p 161 --script snmp-info target

# SSH/Telnet access
nxc ssh switch_ip -u admin -p 'cisco'
```

**Remediation — Network Device Hardening (Step-by-Step)**:
1. Disable Telnet: `no line vty 0 4; transport input ssh`
2. Enable SSH v2 only: `ip ssh version 2`
3. Set strong enable secret: `enable secret <strong-password>`
4. Configure SNMPv3 only: `snmp-server group SECURE v3 priv`
5. Apply ACLs: `access-list 10 permit 10.0.0.0 0.0.0.255; line vty 0 4; access-class 10 in`
6. Enable logging: `logging host <syslog-server>`
7. Verify: `nxc ssh switch -u admin -p 'newpass'` works; Telnet blocked

#### Firewalls
```bash
# Identify firewall type
secator x nmap target -sV -p 80,443,8443,22,222

# Test ACL rules
python3 -c "
import socket
for port in [22,80,443,3389,445,1433,3306,5432,8080,8443]:
    s = socket.socket()
    s.settimeout(2)
    try:
        s.connect(('target', port))
        print(f'Port {port}: OPEN')
    except:
        print(f'Port {port}: FILTERED/CLOSED')
    s.close()
"
```

**Remediation — Firewall Hardening (Step-by-Step)**:
1. Implement default-deny policy: Block all ingress, allow only explicit rules
2. Remove any `any-any` rules
3. Log all denied traffic
4. Review and remove unused rules quarterly
5. Enable geo-blocking where applicable
6. Verify: Only documented service ports respond; all others filtered

---

## Communications Channel Assessment

### Protocol Testing Matrix

| Protocol | Ports | Tests | Tools |
|----------|-------|-------|-------|
| DNS | 53 | Zone transfer, DNS cache poisoning, DNSSEC | Secator (dnsx), dig |
| SMTP | 25/587 | Open relay, user enumeration, STARTTLS | NetExec, Python |
| POP3/IMAP | 110/995/143/993 | Cleartext auth, certificate validation | NetExec, OpenSSL |
| SNMP | 161/162 | Community strings, MIB data leakage | nmap NSE, onesixtyone |
| NTP | 123 | Monlist amplification, time shift attacks | nmap NSE, Python |
| LDAP | 389/636 | Anonymous bind, signing, channel binding | NetExec |
| Kerberos | 88 | ASREPRoast, Kerberoast, pass-the-ticket | NetExec, impacket |
| SIP | 5060 | Registration hijack, eavesdropping | sipsak, Python |

### DNS Testing
```bash
# Zone transfer attempt
dig @target_dns axfr target.com

# DNSSEC validation
dig @target_dns +dnssec target.com A

# Subdomain enumeration
secator x subfinder target.com | secator x dnsx -a -cname -txt
```

**Remediation — DNS Hardening (Step-by-Step)**:
1. Disable zone transfers to untrusted IPs: In BIND, use `allow-transfer { trusted-servers; };`
2. Enable DNSSEC: `dnssec-signzone` the zone files
3. Restrict recursive queries: `allow-recursion { internal-nets; };`
4. Implement Response Rate Limiting (RRL): `rate-limit { responses-per-second 10; }`
5. Use DNS-over-TLS (DoT) or DNS-over-HTTPS (DoH) for clients
6. Verify: `dig @target_dns axfr target.com` should return `TRANSFER FAILED`

### SMTP Testing
```bash
# Open relay test
python3 -c "
import smtplib
s = smtplib.SMTP('target', 25)
s.ehlo()
# Test if STARTTLS is supported
s.starttls()
# Test open relay
try:
    s.sendmail('test@external.com', 'victim@external.com', 'Subject: Test\r\nTest')
    print('OPEN RELAY DETECTED')
except Exception as e:
    print(f'Relay denied: {e}')
"

# User enumeration (VRFY/RCPT TO)
nxc smtp target -u '' -p ''  # If NetExec supports it
```

**Remediation — SMTP Hardening (Step-by-Step)**:
1. Disable open relay: Configure `mynetworks` to trusted IPs only (Postfix: `mynetworks = 127.0.0.0/8`)
2. Require authentication: `smtpd_recipient_restrictions = permit_sasl_authenticated, reject_unauth_destination`
3. Enable STARTTLS: Configure SSL/TLS certificates
4. Disable VRFY/EXPN commands: Postfix `disable_vrfy_command = yes`
5. Rate limit: Postfix `smtpd_client_message_rate_limit = 100`
6. Verify: Python relay test returns `Relay access denied`

---

## Wireless Channel Assessment

### WiFi Testing
```bash
# Interface setup
airmon-ng start wlan0

# Discovery
airodump-ng wlan0mon -w capture

# WPA handshake capture
airodump-ng wlan0mon --bssid <AP_MAC> -c <channel> -w handshake

# Deauth test (verify client resilience)
aireplay-ng -0 5 -a <AP_MAC> wlan0mon

# WPS testing
reaver -i wlan0mon -b <AP_MAC> -vv
```

**Remediation — WiFi Hardening (Step-by-Step)**:
1. Use WPA3 or WPA2-Enterprise (RADIUS) — never WPA2-PSK for enterprise
2. Disable WPS: Access point admin → Wireless → WPS → Disable
3. Use 802.1X authentication with RADIUS server
4. Segment WiFi: Separate SSIDs for corporate, guest, IoT
5. Monitor for rogue APs: Deploy WIDS/WIPS
6. Verify: `airodump-ng` shows WPA3 authentication; WPS disabled

---

## Verification Checklist (Per Finding)

For every finding, confirm using this checklist before reporting:

1. [ ] Finding reproduced independently with 2+ methods
2. [ ] Raw tool output captured (with timestamps)
3. [ ] Screenshots taken (with timestamp and URL/IP visible)
4. [ ] Impact demonstrated (not just theoretical)
5. [ ] Scope confirmation (target is within authorized scope)
6. [ ] Remediation steps documented with exact commands
7. [ ] Remediation verification steps documented
8. [ ] CVSS score calculated and justified
9. [ ] Risk rating assigned per OSSTMM RAV methodology