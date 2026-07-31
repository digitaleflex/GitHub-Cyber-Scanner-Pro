---
description: Enterprise-grade Windows remote management skill using PyWinRM for connecting to any Windows server with WinRM enabled. Provides advanced system administration, monitoring, Active Directory management, and automation capabilities.
name: pywinrm
---

# PyWinRM: Windows Remote Management Skill

> **Enterprise Windows Remote Administration**  
> Connect to and manage Windows servers remotely using Python's PyWinRM library for WinRM protocol access.

## What I Do

I am a comprehensive Windows remote management skill that provides full access to Windows servers through WinRM (Windows Remote Management). I enable:

- **Remote Command Execution**: Execute PowerShell, CMD, and batch commands on remote Windows servers
- **System Monitoring**: CPU, memory, disk, network, and process monitoring
- **Service Management**: Start, stop, restart, and configure Windows services
- **Active Directory**: User, group, computer, and OU management
- **Event Log Analysis**: Query and analyze Windows event logs
- **Registry Operations**: Read, write, and modify registry keys
- **File Operations**: Copy, move, delete files; read/write content remotely
- **Software Management**: Install, update, remove applications via WinRM
- **Scheduled Tasks**: Create, modify, and manage Windows scheduled tasks
- **Performance Monitoring**: Real-time performance counter collection
- **Security Auditing**: Security policy analysis and compliance checking

## When to Use Me

Use this skill when you need to:

- Execute commands on remote Windows servers without RDP
- Perform bulk operations across multiple Windows machines
- Automate Windows system administration tasks
- Monitor Windows server health and performance
- Manage Active Directory objects remotely
- Deploy software or configurations to Windows servers
- Collect logs and diagnostics from Windows systems
- Audit security configurations on Windows machines

## Prerequisites

### Python Environment

```bash
# Install pywinrm with all extras using uv
uv pip install pywinrm[credssp,kerberos]

# Or create a virtual environment
uv venv winrm-env
source winrm-env/bin/activate  # Unix
# winrm-env\Scripts\activate   # Windows
uv pip install pywinrm requests-ntlm requests-credssp
```

### Windows Server Requirements

The target Windows server must have WinRM enabled:

```powershell
# On target Windows server (run as Administrator)
Enable-PSRemoting -Force
winrm quickconfig -q
winrm set winrm/config/service '@{AllowUnencrypted="true"}'
winrm set winrm/config/service/auth '@{Basic="true"}'

# For HTTPS (recommended for production)
$cert = New-SelfSignedCertificate -DnsName "server.domain.com" -CertStoreLocation Cert:\LocalMachine\My
winrm create winrm/config/Listener?Address=*+Transport=HTTPS "@{Hostname=`"server.domain.com`";CertificateThumbprint=`"$($cert.Thumbprint)`"}"

# Open firewall
New-NetFirewallRule -Name "WinRM-HTTP" -DisplayName "WinRM HTTP" -Enabled True -Direction Inbound -Protocol TCP -LocalPort 5985 -Action Allow
New-NetFirewallRule -Name "WinRM-HTTPS" -DisplayName "WinRM HTTPS" -Enabled True -Direction Inbound -Protocol TCP -LocalPort 5986 -Action Allow
```

## Connection Configuration

### Known Windows Servers

| Server | IP | Username | Password | Port |
|--------|-----|----------|----------|------|
| AWS Windows 1 | 44.197.31.152 | Administrator | &@RSp14muPii*SdILEISHr&BqEu6;j2t | 5985 |
| AWS Windows 2 | 52.3.242.251 | Administrator | hcDfrOjKrvK9&;;CH1N.BxH@)AglPN2Dw | 5985 |
| 21CTL Windows | 80.248.0.66 | Administrator | data_21ctl@123 | 5985 |
| 21CTL Windows | 80.248.0.66 | superagent | @@Igbosere186@@ | 5985 |

### Connection Methods

```python
# Basic Auth (HTTP)
from winrm.protocol import Protocol

p = Protocol(
    endpoint='http://IP_ADDRESS:5985/wsman',
    transport='basic',
    username='Administrator',
    password='PASSWORD'
)

# NTLM Auth (Recommended for domains)
from winrm import Session

session = Session(
    'IP_ADDRESS',
    auth=('DOMAIN\\username', 'password'),
    transport='ntlm'
)

# HTTPS with certificate verification disabled (testing)
session = Session(
    'IP_ADDRESS',
    auth=('Administrator', 'password'),
    transport='basic',
    server_cert_validation='ignore'
)

# CredSSP (for double-hop scenarios)
session = Session(
    'IP_ADDRESS',
    auth=('Administrator', 'password'),
    transport='credssp',
    server_cert_validation='ignore'
)
```

## Core Operations

### 1. Execute PowerShell Commands

```python
#!/usr/bin/env python3
"""Execute PowerShell commands on remote Windows server."""
import winrm

def execute_powershell(host, username, password, command, port=5985):
    """Execute PowerShell command and return output."""
    session = winrm.Session(
        f'http://{host}:{port}/wsman',
        auth=(username, password),
        transport='basic'
    )
    
    # Encode command for PowerShell
    ps_script = f'''
    $ErrorActionPreference = "Stop"
    try {{
        {command}
    }} catch {{
        Write-Error $_.Exception.Message
        exit 1
    }}
    '''
    
    result = session.run_ps(ps_script)
    
    return {
        'status_code': result.status_code,
        'stdout': result.std_out.decode('utf-8', errors='replace'),
        'stderr': result.std_err.decode('utf-8', errors='replace')
    }

# Example usage
if __name__ == '__main__':
    result = execute_powershell(
        host='44.197.31.152',
        username='Administrator',
        password='YOUR_PASSWORD',
        command='Get-ComputerInfo | Select-Object CsName, WindowsVersion, OsArchitecture'
    )
    print(result['stdout'])
```

### 2. Execute CMD Commands

```python
#!/usr/bin/env python3
"""Execute CMD commands on remote Windows server."""
import winrm

def execute_cmd(host, username, password, command, port=5985):
    """Execute CMD command and return output."""
    session = winrm.Session(
        f'http://{host}:{port}/wsman',
        auth=(username, password),
        transport='basic'
    )
    
    result = session.run_cmd(command)
    
    return {
        'status_code': result.status_code,
        'stdout': result.std_out.decode('utf-8', errors='replace'),
        'stderr': result.std_err.decode('utf-8', errors='replace')
    }

# Example
result = execute_cmd('server', 'user', 'pass', 'systeminfo')
print(result['stdout'])
```

### 3. System Information Collection

```python
#!/usr/bin/env python3
"""Collect comprehensive system information from Windows server."""
import winrm
import json

def get_system_info(host, username, password, port=5985):
    """Collect system information."""
    session = winrm.Session(
        f'http://{host}:{port}/wsman',
        auth=(username, password),
        transport='basic'
    )
    
    ps_script = '''
    $info = @{
        ComputerName = $env:COMPUTERNAME
        Domain = (Get-WmiObject Win32_ComputerSystem).Domain
        OS = (Get-WmiObject Win32_OperatingSystem).Caption
        Version = (Get-WmiObject Win32_OperatingSystem).Version
        Architecture = (Get-WmiObject Win32_OperatingSystem).OSArchitecture
        LastBootTime = (Get-WmiObject Win32_OperatingSystem).LastBootUpTime
        TotalMemoryGB = [math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
        Processors = (Get-WmiObject Win32_Processor | Measure-Object).Count
        ProcessorName = (Get-WmiObject Win32_Processor | Select-Object -First 1).Name
        IPAddresses = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -ne '127.0.0.1'}).IPAddress
    }
    $info | ConvertTo-Json -Depth 3
    '''
    
    result = session.run_ps(ps_script)
    if result.status_code == 0:
        return json.loads(result.std_out.decode('utf-8'))
    else:
        raise Exception(result.std_err.decode('utf-8'))

# Example
info = get_system_info('server', 'user', 'pass')
print(json.dumps(info, indent=2))
```

### 4. Performance Monitoring

```python
#!/usr/bin/env python3
"""Monitor Windows server performance metrics."""
import winrm
import json

def get_performance_metrics(host, username, password, port=5985):
    """Get current performance metrics."""
    session = winrm.Session(
        f'http://{host}:{port}/wsman',
        auth=(username, password),
        transport='basic'
    )
    
    ps_script = '''
    $metrics = @{
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        CPU = @{
            UsagePercent = [math]::Round((Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue, 2)
        }
        Memory = @{
            TotalGB = [math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
            AvailableGB = [math]::Round((Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue / 1024, 2)
            UsagePercent = [math]::Round(100 - ((Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue / ((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1MB) * 100), 2)
        }
        Disk = Get-WmiObject Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
            @{
                Drive = $_.DeviceID
                SizeGB = [math]::Round($_.Size / 1GB, 2)
                FreeGB = [math]::Round($_.FreeSpace / 1GB, 2)
                UsagePercent = [math]::Round(100 - ($_.FreeSpace / $_.Size * 100), 2)
            }
        }
        Network = Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | ForEach-Object {
            $stats = Get-NetAdapterStatistics -Name $_.Name
            @{
                Name = $_.Name
                LinkSpeedMbps = [math]::Round($_.LinkSpeed / 1000000, 0)
                BytesSent = $stats.SentBytes
                BytesReceived = $stats.ReceivedBytes
            }
        }
    }
    $metrics | ConvertTo-Json -Depth 4
    '''
    
    result = session.run_ps(ps_script)
    if result.status_code == 0:
        return json.loads(result.std_out.decode('utf-8'))
    else:
        raise Exception(result.std_err.decode('utf-8'))

# Example
metrics = get_performance_metrics('server', 'user', 'pass')
print(json.dumps(metrics, indent=2))
```

### 5. Service Management

```python
#!/usr/bin/env python3
"""Manage Windows services remotely."""
import winrm
import json

class ServiceManager:
    def __init__(self, host, username, password, port=5985):
        self.session = winrm.Session(
            f'http://{host}:{port}/wsman',
            auth=(username, password),
            transport='basic'
        )
    
    def list_services(self, filter_status=None):
        """List all services, optionally filtered by status."""
        filter_clause = ""
        if filter_status:
            filter_clause = f"| Where-Object {{$_.Status -eq '{filter_status}'}}"
        
        ps_script = f'''
        Get-Service {filter_clause} | Select-Object Name, DisplayName, Status, StartType | 
        ConvertTo-Json -Depth 2
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def get_service(self, name):
        """Get details for a specific service."""
        ps_script = f'''
        $svc = Get-Service -Name "{name}" -ErrorAction SilentlyContinue
        if ($svc) {{
            $wmi = Get-WmiObject Win32_Service -Filter "Name='{name}'"
            @{{
                Name = $svc.Name
                DisplayName = $svc.DisplayName
                Status = $svc.Status.ToString()
                StartType = $svc.StartType.ToString()
                Path = $wmi.PathName
                Account = $wmi.StartName
                PID = $wmi.ProcessId
            }} | ConvertTo-Json
        }} else {{
            Write-Error "Service not found"
        }}
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def start_service(self, name):
        """Start a service."""
        ps_script = f'Start-Service -Name "{name}" -PassThru | Select-Object Name, Status | ConvertTo-Json'
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def stop_service(self, name):
        """Stop a service."""
        ps_script = f'Stop-Service -Name "{name}" -Force -PassThru | Select-Object Name, Status | ConvertTo-Json'
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def restart_service(self, name):
        """Restart a service."""
        ps_script = f'Restart-Service -Name "{name}" -PassThru | Select-Object Name, Status | ConvertTo-Json'
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def set_startup_type(self, name, startup_type):
        """Set service startup type (Automatic, Manual, Disabled)."""
        ps_script = f'Set-Service -Name "{name}" -StartupType {startup_type} -PassThru | Select-Object Name, StartType | ConvertTo-Json'
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))

# Example usage
mgr = ServiceManager('server', 'user', 'pass')
print(mgr.list_services('Running'))
print(mgr.get_service('Spooler'))
```

### 6. Event Log Analysis

```python
#!/usr/bin/env python3
"""Query and analyze Windows event logs."""
import winrm
import json

def get_event_logs(host, username, password, log_name='System', 
                   entry_type=None, newest=50, port=5985):
    """Query Windows event logs."""
    session = winrm.Session(
        f'http://{host}:{port}/wsman',
        auth=(username, password),
        transport='basic'
    )
    
    filter_clause = ""
    if entry_type:
        filter_clause = f"-EntryType {entry_type}"
    
    ps_script = f'''
    Get-EventLog -LogName {log_name} {filter_clause} -Newest {newest} | 
    Select-Object TimeGenerated, EntryType, Source, EventID, Message |
    ConvertTo-Json -Depth 2
    '''
    
    result = session.run_ps(ps_script)
    if result.status_code == 0:
        return json.loads(result.std_out.decode('utf-8'))
    else:
        raise Exception(result.std_err.decode('utf-8'))

def get_security_events(host, username, password, hours=24, port=5985):
    """Get security events from the last N hours."""
    session = winrm.Session(
        f'http://{host}:{port}/wsman',
        auth=(username, password),
        transport='basic'
    )
    
    ps_script = f'''
    $startTime = (Get-Date).AddHours(-{hours})
    Get-WinEvent -FilterHashtable @{{
        LogName = 'Security'
        StartTime = $startTime
    }} -MaxEvents 100 -ErrorAction SilentlyContinue | 
    Select-Object TimeCreated, Id, LevelDisplayName, Message |
    ConvertTo-Json -Depth 2
    '''
    
    result = session.run_ps(ps_script)
    if result.status_code == 0 and result.std_out:
        return json.loads(result.std_out.decode('utf-8'))
    return []

# Example
events = get_event_logs('server', 'user', 'pass', 'Application', 'Error', 10)
print(json.dumps(events, indent=2))
```

### 7. Process Management

```python
#!/usr/bin/env python3
"""Manage Windows processes remotely."""
import winrm
import json

class ProcessManager:
    def __init__(self, host, username, password, port=5985):
        self.session = winrm.Session(
            f'http://{host}:{port}/wsman',
            auth=(username, password),
            transport='basic'
        )
    
    def list_processes(self, sort_by='CPU', top=20):
        """List top processes by CPU or Memory usage."""
        sort_prop = 'CPU' if sort_by == 'CPU' else 'WorkingSet64'
        
        ps_script = f'''
        Get-Process | Sort-Object {sort_prop} -Descending | Select-Object -First {top} |
        Select-Object Id, ProcessName, 
            @{{Name='CPU_Seconds';Expression={{[math]::Round($_.CPU, 2)}}}},
            @{{Name='MemoryMB';Expression={{[math]::Round($_.WorkingSet64 / 1MB, 2)}}}},
            @{{Name='Threads';Expression={{$_.Threads.Count}}}},
            Path |
        ConvertTo-Json -Depth 2
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def get_process(self, name_or_id):
        """Get details for a specific process."""
        if str(name_or_id).isdigit():
            filter_clause = f"-Id {name_or_id}"
        else:
            filter_clause = f"-Name '{name_or_id}'"
        
        ps_script = f'''
        Get-Process {filter_clause} -ErrorAction SilentlyContinue | 
        Select-Object Id, ProcessName, CPU, 
            @{{Name='MemoryMB';Expression={{[math]::Round($_.WorkingSet64 / 1MB, 2)}}}},
            StartTime, Path, MainWindowTitle |
        ConvertTo-Json
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def stop_process(self, name_or_id, force=False):
        """Stop a process by name or ID."""
        force_flag = "-Force" if force else ""
        if str(name_or_id).isdigit():
            ps_script = f'Stop-Process -Id {name_or_id} {force_flag} -PassThru | Select-Object Id, ProcessName, HasExited | ConvertTo-Json'
        else:
            ps_script = f'Stop-Process -Name "{name_or_id}" {force_flag} -PassThru | Select-Object Id, ProcessName, HasExited | ConvertTo-Json'
        
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def start_process(self, path, arguments=None):
        """Start a new process."""
        args = f"-ArgumentList '{arguments}'" if arguments else ""
        ps_script = f'''
        $proc = Start-Process -FilePath "{path}" {args} -PassThru
        @{{
            Id = $proc.Id
            ProcessName = $proc.ProcessName
            StartTime = $proc.StartTime
        }} | ConvertTo-Json
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))

# Example
pm = ProcessManager('server', 'user', 'pass')
print(pm.list_processes('Memory', 10))
```

### 8. File Operations

```python
#!/usr/bin/env python3
"""Remote file operations on Windows servers."""
import winrm
import json
import base64

class FileManager:
    def __init__(self, host, username, password, port=5985):
        self.session = winrm.Session(
            f'http://{host}:{port}/wsman',
            auth=(username, password),
            transport='basic'
        )
    
    def list_directory(self, path):
        """List directory contents."""
        ps_script = f'''
        Get-ChildItem -Path "{path}" -ErrorAction Stop | 
        Select-Object Name, 
            @{{Name='Type';Expression={{if($_.PSIsContainer){{'Directory'}}else{{'File'}}}}}},
            @{{Name='SizeBytes';Expression={{$_.Length}}}},
            LastWriteTime,
            Attributes |
        ConvertTo-Json -Depth 2
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def read_file(self, path, encoding='utf-8'):
        """Read file content."""
        ps_script = f'Get-Content -Path "{path}" -Raw -Encoding {encoding}'
        result = self.session.run_ps(ps_script)
        return result.std_out.decode('utf-8')
    
    def write_file(self, path, content, encoding='utf-8'):
        """Write content to file."""
        # Base64 encode to handle special characters
        encoded = base64.b64encode(content.encode('utf-8')).decode('ascii')
        ps_script = f'''
        $bytes = [Convert]::FromBase64String("{encoded}")
        $content = [System.Text.Encoding]::UTF8.GetString($bytes)
        Set-Content -Path "{path}" -Value $content -Encoding {encoding}
        "Success"
        '''
        result = self.session.run_ps(ps_script)
        return result.status_code == 0
    
    def copy_file(self, source, destination):
        """Copy file or directory."""
        ps_script = f'Copy-Item -Path "{source}" -Destination "{destination}" -Recurse -Force; "Success"'
        result = self.session.run_ps(ps_script)
        return result.status_code == 0
    
    def move_file(self, source, destination):
        """Move file or directory."""
        ps_script = f'Move-Item -Path "{source}" -Destination "{destination}" -Force; "Success"'
        result = self.session.run_ps(ps_script)
        return result.status_code == 0
    
    def delete_file(self, path, recurse=False):
        """Delete file or directory."""
        recurse_flag = "-Recurse" if recurse else ""
        ps_script = f'Remove-Item -Path "{path}" {recurse_flag} -Force; "Success"'
        result = self.session.run_ps(ps_script)
        return result.status_code == 0
    
    def file_exists(self, path):
        """Check if file or directory exists."""
        ps_script = f'Test-Path -Path "{path}"'
        result = self.session.run_ps(ps_script)
        return result.std_out.decode('utf-8').strip().lower() == 'true'
    
    def get_file_info(self, path):
        """Get detailed file information."""
        ps_script = f'''
        $item = Get-Item -Path "{path}" -ErrorAction Stop
        @{{
            FullName = $item.FullName
            Name = $item.Name
            Extension = $item.Extension
            IsDirectory = $item.PSIsContainer
            SizeBytes = $item.Length
            CreationTime = $item.CreationTime.ToString("yyyy-MM-dd HH:mm:ss")
            LastWriteTime = $item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            LastAccessTime = $item.LastAccessTime.ToString("yyyy-MM-dd HH:mm:ss")
            Attributes = $item.Attributes.ToString()
            Owner = (Get-Acl $item.FullName).Owner
        }} | ConvertTo-Json
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))

# Example
fm = FileManager('server', 'user', 'pass')
print(fm.list_directory('C:\\'))
print(fm.get_file_info('C:\\Windows\\System32\\drivers\\etc\\hosts'))
```

### 9. Registry Operations

```python
#!/usr/bin/env python3
"""Windows Registry operations via WinRM."""
import winrm
import json

class RegistryManager:
    def __init__(self, host, username, password, port=5985):
        self.session = winrm.Session(
            f'http://{host}:{port}/wsman',
            auth=(username, password),
            transport='basic'
        )
    
    def get_value(self, path, name):
        """Get a registry value."""
        ps_script = f'''
        $value = Get-ItemProperty -Path "{path}" -Name "{name}" -ErrorAction Stop
        @{{
            Path = "{path}"
            Name = "{name}"
            Value = $value."{name}"
            Type = (Get-Item -Path "{path}").GetValueKind("{name}").ToString()
        }} | ConvertTo-Json
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def set_value(self, path, name, value, value_type='String'):
        """Set a registry value."""
        ps_script = f'''
        if (-not (Test-Path "{path}")) {{
            New-Item -Path "{path}" -Force | Out-Null
        }}
        Set-ItemProperty -Path "{path}" -Name "{name}" -Value "{value}" -Type {value_type}
        "Success"
        '''
        result = self.session.run_ps(ps_script)
        return result.status_code == 0
    
    def delete_value(self, path, name):
        """Delete a registry value."""
        ps_script = f'Remove-ItemProperty -Path "{path}" -Name "{name}" -Force; "Success"'
        result = self.session.run_ps(ps_script)
        return result.status_code == 0
    
    def list_values(self, path):
        """List all values in a registry key."""
        ps_script = f'''
        Get-Item -Path "{path}" -ErrorAction Stop | 
        Select-Object -ExpandProperty Property | ForEach-Object {{
            $name = $_
            $item = Get-Item -Path "{path}"
            @{{
                Name = $name
                Value = $item.GetValue($name)
                Type = $item.GetValueKind($name).ToString()
            }}
        }} | ConvertTo-Json -Depth 2
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def list_subkeys(self, path):
        """List subkeys of a registry key."""
        ps_script = f'''
        Get-ChildItem -Path "{path}" -ErrorAction Stop | 
        Select-Object Name, PSChildName |
        ConvertTo-Json
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))

# Example
reg = RegistryManager('server', 'user', 'pass')
print(reg.list_values('HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion'))
```

### 10. Active Directory Management

```python
#!/usr/bin/env python3
"""Active Directory management via WinRM."""
import winrm
import json

class ADManager:
    def __init__(self, host, username, password, port=5985):
        self.session = winrm.Session(
            f'http://{host}:{port}/wsman',
            auth=(username, password),
            transport='basic'
        )
    
    def get_domain_info(self):
        """Get domain information."""
        ps_script = '''
        Import-Module ActiveDirectory
        $domain = Get-ADDomain
        @{
            Name = $domain.Name
            DNSRoot = $domain.DNSRoot
            Forest = $domain.Forest
            DomainMode = $domain.DomainMode.ToString()
            PDCEmulator = $domain.PDCEmulator
            InfrastructureMaster = $domain.InfrastructureMaster
        } | ConvertTo-Json
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def list_users(self, filter_str=None, properties=None):
        """List AD users."""
        props = properties or ['SamAccountName', 'DisplayName', 'EmailAddress', 'Enabled', 'LastLogonDate']
        props_str = ','.join(props)
        filter_clause = f"-Filter \"{filter_str}\"" if filter_str else ""
        
        ps_script = f'''
        Import-Module ActiveDirectory
        Get-ADUser {filter_clause} -Properties {props_str} | 
        Select-Object {props_str} |
        ConvertTo-Json -Depth 2
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def get_user(self, identity):
        """Get detailed user information."""
        ps_script = f'''
        Import-Module ActiveDirectory
        Get-ADUser -Identity "{identity}" -Properties * | 
        Select-Object SamAccountName, DisplayName, EmailAddress, 
            Department, Title, Manager, MemberOf, 
            Enabled, LockedOut, PasswordExpired, 
            LastLogonDate, Created, Modified |
        ConvertTo-Json -Depth 2
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def create_user(self, sam_account_name, name, password, ou, enabled=True):
        """Create a new AD user."""
        ps_script = f'''
        Import-Module ActiveDirectory
        $securePass = ConvertTo-SecureString "{password}" -AsPlainText -Force
        New-ADUser -SamAccountName "{sam_account_name}" -Name "{name}" `
            -AccountPassword $securePass -Enabled ${str(enabled).lower()} `
            -Path "{ou}" -PassThru | 
        Select-Object SamAccountName, Name, Enabled, DistinguishedName |
        ConvertTo-Json
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def disable_user(self, identity):
        """Disable an AD user."""
        ps_script = f'''
        Import-Module ActiveDirectory
        Disable-ADAccount -Identity "{identity}"
        Get-ADUser -Identity "{identity}" | Select-Object SamAccountName, Enabled | ConvertTo-Json
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def unlock_user(self, identity):
        """Unlock a locked AD user."""
        ps_script = f'''
        Import-Module ActiveDirectory
        Unlock-ADAccount -Identity "{identity}"
        Get-ADUser -Identity "{identity}" -Properties LockedOut | 
        Select-Object SamAccountName, LockedOut | ConvertTo-Json
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def reset_password(self, identity, new_password):
        """Reset user password."""
        ps_script = f'''
        Import-Module ActiveDirectory
        $securePass = ConvertTo-SecureString "{new_password}" -AsPlainText -Force
        Set-ADAccountPassword -Identity "{identity}" -NewPassword $securePass -Reset
        "Password reset successful"
        '''
        result = self.session.run_ps(ps_script)
        return result.status_code == 0
    
    def list_groups(self, filter_str=None):
        """List AD groups."""
        filter_clause = f"-Filter \"{filter_str}\"" if filter_str else ""
        ps_script = f'''
        Import-Module ActiveDirectory
        Get-ADGroup {filter_clause} -Properties Description, Members | 
        Select-Object Name, SamAccountName, GroupScope, GroupCategory, 
            Description, @{{Name='MemberCount';Expression={{$_.Members.Count}}}} |
        ConvertTo-Json -Depth 2
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def get_group_members(self, identity):
        """Get members of an AD group."""
        ps_script = f'''
        Import-Module ActiveDirectory
        Get-ADGroupMember -Identity "{identity}" | 
        Select-Object Name, SamAccountName, objectClass |
        ConvertTo-Json
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def add_group_member(self, group, member):
        """Add a member to an AD group."""
        ps_script = f'''
        Import-Module ActiveDirectory
        Add-ADGroupMember -Identity "{group}" -Members "{member}"
        "Member added successfully"
        '''
        result = self.session.run_ps(ps_script)
        return result.status_code == 0
    
    def remove_group_member(self, group, member):
        """Remove a member from an AD group."""
        ps_script = f'''
        Import-Module ActiveDirectory
        Remove-ADGroupMember -Identity "{group}" -Members "{member}" -Confirm:$false
        "Member removed successfully"
        '''
        result = self.session.run_ps(ps_script)
        return result.status_code == 0

# Example
ad = ADManager('domain-controller', 'admin', 'pass')
print(ad.list_users())
print(ad.get_user('jsmith'))
```

### 11. Scheduled Task Management

```python
#!/usr/bin/env python3
"""Manage Windows Scheduled Tasks via WinRM."""
import winrm
import json

class ScheduledTaskManager:
    def __init__(self, host, username, password, port=5985):
        self.session = winrm.Session(
            f'http://{host}:{port}/wsman',
            auth=(username, password),
            transport='basic'
        )
    
    def list_tasks(self, path='\\'):
        """List scheduled tasks."""
        ps_script = f'''
        Get-ScheduledTask -TaskPath "{path}*" | 
        Select-Object TaskName, TaskPath, State, 
            @{{Name='LastRunTime';Expression={{$_.LastRunTime}}}},
            @{{Name='NextRunTime';Expression={{$_.NextRunTime}}}} |
        ConvertTo-Json -Depth 2
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def get_task(self, name, path='\\'):
        """Get detailed task information."""
        ps_script = f'''
        $task = Get-ScheduledTask -TaskName "{name}" -TaskPath "{path}" -ErrorAction Stop
        $info = Get-ScheduledTaskInfo -TaskName "{name}" -TaskPath "{path}"
        @{{
            TaskName = $task.TaskName
            TaskPath = $task.TaskPath
            State = $task.State.ToString()
            Description = $task.Description
            Author = $task.Author
            Actions = $task.Actions | ForEach-Object {{
                @{{
                    Type = $_.CimClass.CimClassName
                    Execute = $_.Execute
                    Arguments = $_.Arguments
                    WorkingDirectory = $_.WorkingDirectory
                }}
            }}
            Triggers = $task.Triggers | ForEach-Object {{
                @{{
                    Type = $_.CimClass.CimClassName
                    Enabled = $_.Enabled
                }}
            }}
            LastRunTime = $info.LastRunTime
            LastTaskResult = $info.LastTaskResult
            NextRunTime = $info.NextRunTime
            NumberOfMissedRuns = $info.NumberOfMissedRuns
        }} | ConvertTo-Json -Depth 3
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def run_task(self, name, path='\\'):
        """Run a scheduled task immediately."""
        ps_script = f'''
        Start-ScheduledTask -TaskName "{name}" -TaskPath "{path}"
        Start-Sleep -Seconds 2
        $info = Get-ScheduledTaskInfo -TaskName "{name}" -TaskPath "{path}"
        @{{
            TaskName = "{name}"
            State = (Get-ScheduledTask -TaskName "{name}" -TaskPath "{path}").State.ToString()
            LastRunTime = $info.LastRunTime
        }} | ConvertTo-Json
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def stop_task(self, name, path='\\'):
        """Stop a running scheduled task."""
        ps_script = f'Stop-ScheduledTask -TaskName "{name}" -TaskPath "{path}"; "Stopped"'
        result = self.session.run_ps(ps_script)
        return result.status_code == 0
    
    def enable_task(self, name, path='\\'):
        """Enable a scheduled task."""
        ps_script = f'Enable-ScheduledTask -TaskName "{name}" -TaskPath "{path}" | Select-Object TaskName, State | ConvertTo-Json'
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def disable_task(self, name, path='\\'):
        """Disable a scheduled task."""
        ps_script = f'Disable-ScheduledTask -TaskName "{name}" -TaskPath "{path}" | Select-Object TaskName, State | ConvertTo-Json'
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def create_task(self, name, execute, arguments=None, trigger_type='Daily', 
                    time='09:00', description='', run_as='SYSTEM'):
        """Create a new scheduled task."""
        args_param = f'-Argument "{arguments}"' if arguments else ''
        
        ps_script = f'''
        $action = New-ScheduledTaskAction -Execute "{execute}" {args_param}
        $trigger = New-ScheduledTaskTrigger -{trigger_type} -At "{time}"
        $principal = New-ScheduledTaskPrincipal -UserId "{run_as}" -LogonType ServiceAccount -RunLevel Highest
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
        
        Register-ScheduledTask -TaskName "{name}" -Action $action -Trigger $trigger `
            -Principal $principal -Settings $settings -Description "{description}" |
        Select-Object TaskName, State | ConvertTo-Json
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def delete_task(self, name, path='\\'):
        """Delete a scheduled task."""
        ps_script = f'Unregister-ScheduledTask -TaskName "{name}" -TaskPath "{path}" -Confirm:$false; "Deleted"'
        result = self.session.run_ps(ps_script)
        return result.status_code == 0

# Example
stm = ScheduledTaskManager('server', 'user', 'pass')
print(stm.list_tasks())
```

### 12. Windows Update Management

```python
#!/usr/bin/env python3
"""Manage Windows Updates via WinRM."""
import winrm
import json

class WindowsUpdateManager:
    def __init__(self, host, username, password, port=5985):
        self.session = winrm.Session(
            f'http://{host}:{port}/wsman',
            auth=(username, password),
            transport='basic'
        )
    
    def get_update_history(self, count=20):
        """Get Windows Update history."""
        ps_script = f'''
        $session = New-Object -ComObject Microsoft.Update.Session
        $searcher = $session.CreateUpdateSearcher()
        $history = $searcher.QueryHistory(0, {count})
        $history | ForEach-Object {{
            @{{
                Title = $_.Title
                Date = $_.Date
                Operation = switch($_.Operation) {{
                    1 {{"Installation"}}
                    2 {{"Uninstallation"}}
                    3 {{"Other"}}
                }}
                ResultCode = switch($_.ResultCode) {{
                    0 {{"Not Started"}}
                    1 {{"In Progress"}}
                    2 {{"Succeeded"}}
                    3 {{"Succeeded With Errors"}}
                    4 {{"Failed"}}
                    5 {{"Aborted"}}
                }}
            }}
        }} | ConvertTo-Json -Depth 2
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def check_for_updates(self):
        """Check for available updates."""
        ps_script = '''
        $session = New-Object -ComObject Microsoft.Update.Session
        $searcher = $session.CreateUpdateSearcher()
        $results = $searcher.Search("IsInstalled=0")
        $results.Updates | ForEach-Object {
            @{
                Title = $_.Title
                Description = $_.Description
                KBArticleIDs = $_.KBArticleIDs -join ","
                IsMandatory = $_.IsMandatory
                IsDownloaded = $_.IsDownloaded
                MaxDownloadSize = $_.MaxDownloadSize
            }
        } | ConvertTo-Json -Depth 2
        '''
        result = self.session.run_ps(ps_script)
        if result.std_out:
            return json.loads(result.std_out.decode('utf-8'))
        return []
    
    def get_installed_updates(self):
        """Get list of installed updates."""
        ps_script = '''
        Get-HotFix | Select-Object HotFixID, Description, InstalledBy, InstalledOn |
        ConvertTo-Json
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def get_pending_reboot(self):
        """Check if system has pending reboot."""
        ps_script = '''
        $pendingReboot = $false
        $reasons = @()
        
        # Check Windows Update
        if (Test-Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update\\RebootRequired") {
            $pendingReboot = $true
            $reasons += "Windows Update"
        }
        
        # Check Component Based Servicing
        if (Test-Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Component Based Servicing\\RebootPending") {
            $pendingReboot = $true
            $reasons += "Component Based Servicing"
        }
        
        # Check PendingFileRenameOperations
        $pfro = Get-ItemProperty "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager" -Name PendingFileRenameOperations -EA SilentlyContinue
        if ($pfro) {
            $pendingReboot = $true
            $reasons += "Pending File Rename"
        }
        
        @{
            PendingReboot = $pendingReboot
            Reasons = $reasons
        } | ConvertTo-Json
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))

# Example
wum = WindowsUpdateManager('server', 'user', 'pass')
print(wum.get_installed_updates())
print(wum.get_pending_reboot())
```

### 13. Network Configuration

```python
#!/usr/bin/env python3
"""Network configuration and diagnostics via WinRM."""
import winrm
import json

class NetworkManager:
    def __init__(self, host, username, password, port=5985):
        self.session = winrm.Session(
            f'http://{host}:{port}/wsman',
            auth=(username, password),
            transport='basic'
        )
    
    def get_network_adapters(self):
        """Get network adapter information."""
        ps_script = '''
        Get-NetAdapter | Select-Object Name, InterfaceDescription, Status,
            MacAddress, LinkSpeed, 
            @{Name='IPv4';Expression={(Get-NetIPAddress -InterfaceIndex $_.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue).IPAddress}},
            @{Name='IPv6';Expression={(Get-NetIPAddress -InterfaceIndex $_.ifIndex -AddressFamily IPv6 -ErrorAction SilentlyContinue | Where-Object {$_.PrefixOrigin -ne 'WellKnown'}).IPAddress}} |
        ConvertTo-Json -Depth 2
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def get_ip_configuration(self):
        """Get detailed IP configuration."""
        ps_script = '''
        Get-NetIPConfiguration | ForEach-Object {
            @{
                InterfaceAlias = $_.InterfaceAlias
                InterfaceIndex = $_.InterfaceIndex
                IPv4Address = $_.IPv4Address.IPAddress
                IPv4DefaultGateway = $_.IPv4DefaultGateway.NextHop
                DNSServer = $_.DNSServer.ServerAddresses
            }
        } | ConvertTo-Json -Depth 2
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def get_tcp_connections(self, state=None):
        """Get TCP connections."""
        filter_clause = f"| Where-Object {{$_.State -eq '{state}'}}" if state else ""
        ps_script = f'''
        Get-NetTCPConnection {filter_clause} | 
        Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, 
            State, OwningProcess,
            @{{Name='ProcessName';Expression={{(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).ProcessName}}}} |
        ConvertTo-Json -Depth 2
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def get_listening_ports(self):
        """Get all listening ports."""
        return self.get_tcp_connections('Listen')
    
    def test_connection(self, target, port=None):
        """Test network connectivity."""
        port_param = f"-Port {port}" if port else ""
        ps_script = f'''
        $result = Test-NetConnection -ComputerName "{target}" {port_param}
        @{{
            ComputerName = $result.ComputerName
            RemoteAddress = $result.RemoteAddress.IPAddressToString
            PingSucceeded = $result.PingSucceeded
            TcpTestSucceeded = $result.TcpTestSucceeded
            RoundtripTime = $result.PingReplyDetails.RoundtripTime
        }} | ConvertTo-Json
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def get_firewall_rules(self, enabled_only=True):
        """Get firewall rules."""
        filter_clause = "| Where-Object {$_.Enabled -eq $true}" if enabled_only else ""
        ps_script = f'''
        Get-NetFirewallRule {filter_clause} | 
        Select-Object -First 50 Name, DisplayName, Enabled, Direction, Action, Profile |
        ConvertTo-Json -Depth 2
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def create_firewall_rule(self, name, direction, action, protocol, port, description=''):
        """Create a firewall rule."""
        ps_script = f'''
        New-NetFirewallRule -Name "{name}" -DisplayName "{name}" `
            -Direction {direction} -Action {action} `
            -Protocol {protocol} -LocalPort {port} `
            -Description "{description}" |
        Select-Object Name, Enabled, Direction, Action | ConvertTo-Json
        '''
        result = self.session.run_ps(ps_script)
        return json.loads(result.std_out.decode('utf-8'))
    
    def remove_firewall_rule(self, name):
        """Remove a firewall rule."""
        ps_script = f'Remove-NetFirewallRule -Name "{name}"; "Removed"'
        result = self.session.run_ps(ps_script)
        return result.status_code == 0

# Example
nm = NetworkManager('server', 'user', 'pass')
print(nm.get_network_adapters())
print(nm.get_listening_ports())
```

## Quick Reference Commands

### One-Liner Examples

```bash
# Execute PowerShell command
uv run python -c "
import winrm
s = winrm.Session('http://IP:5985/wsman', auth=('Administrator', 'PASS'), transport='basic')
r = s.run_ps('Get-ComputerInfo | Select-Object CsName, WindowsVersion')
print(r.std_out.decode())
"

# Get system info
uv run python -c "
import winrm, json
s = winrm.Session('http://IP:5985/wsman', auth=('Administrator', 'PASS'), transport='basic')
r = s.run_ps('Get-ComputerInfo | ConvertTo-Json')
print(json.dumps(json.loads(r.std_out.decode()), indent=2))
"

# List running services
uv run python -c "
import winrm
s = winrm.Session('http://IP:5985/wsman', auth=('Administrator', 'PASS'), transport='basic')
r = s.run_ps('Get-Service | Where-Object {\$_.Status -eq \"Running\"} | Select-Object Name, DisplayName')
print(r.std_out.decode())
"

# Check disk space
uv run python -c "
import winrm
s = winrm.Session('http://IP:5985/wsman', auth=('Administrator', 'PASS'), transport='basic')
r = s.run_ps('Get-WmiObject Win32_LogicalDisk | Select-Object DeviceID, @{n=\"SizeGB\";e={\$_.Size/1GB}}, @{n=\"FreeGB\";e={\$_.FreeSpace/1GB}}')
print(r.std_out.decode())
"
```

### Multi-Server Execution

```python
#!/usr/bin/env python3
"""Execute commands across multiple Windows servers."""
import winrm
from concurrent.futures import ThreadPoolExecutor, as_completed

SERVERS = [
    {'host': '44.197.31.152', 'user': 'Administrator', 'pass': 'PASS1'},
    {'host': '52.3.242.251', 'user': 'Administrator', 'pass': 'PASS2'},
    {'host': '80.248.0.66', 'user': 'Administrator', 'pass': 'PASS3'},
]

def execute_on_server(server, command):
    """Execute command on a single server."""
    try:
        session = winrm.Session(
            f"http://{server['host']}:5985/wsman",
            auth=(server['user'], server['pass']),
            transport='basic'
        )
        result = session.run_ps(command)
        return {
            'host': server['host'],
            'success': True,
            'output': result.std_out.decode('utf-8'),
            'error': result.std_err.decode('utf-8') if result.std_err else None
        }
    except Exception as e:
        return {
            'host': server['host'],
            'success': False,
            'error': str(e)
        }

def execute_parallel(servers, command, max_workers=5):
    """Execute command on multiple servers in parallel."""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(execute_on_server, s, command): s for s in servers}
        for future in as_completed(futures):
            results.append(future.result())
    return results

# Example: Get uptime from all servers
if __name__ == '__main__':
    command = '(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime | Select-Object Days, Hours, Minutes'
    results = execute_parallel(SERVERS, command)
    for r in results:
        print(f"\n=== {r['host']} ===")
        if r['success']:
            print(r['output'])
        else:
            print(f"ERROR: {r['error']}")
```

## Security Best Practices

### Credential Management

```python
# Use environment variables
import os
password = os.environ.get('WINRM_PASSWORD')

# Or use a secrets manager
from getpass import getpass
password = getpass("Enter password: ")
```

### HTTPS Configuration

```python
# Use HTTPS for production
session = winrm.Session(
    'https://server.domain.com:5986/wsman',
    auth=('Administrator', 'password'),
    transport='ntlm',
    server_cert_validation='validate',  # Use 'ignore' only for testing
    ca_trust_path='/path/to/ca-bundle.crt'
)
```

### Kerberos Authentication

```python
# For domain environments
session = winrm.Session(
    'server.domain.com',
    auth=('user@DOMAIN.COM', 'password'),
    transport='kerberos'
)
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Verify WinRM is enabled: `winrm quickconfig`
   - Check firewall: `netsh advfirewall firewall show rule name=all | find "5985"`
   - Test locally: `winrm id -r:http://localhost:5985`

2. **Authentication Failed**
   - Check credentials
   - Verify Basic auth is enabled: `winrm get winrm/config/service/auth`
   - For NTLM, use `DOMAIN\\username` format

3. **Access Denied**
   - User must be in Administrators group or WinRMRemoteWMIUsers__
   - Check UAC settings for remote connections

4. **Timeout Issues**
   ```python
   session = winrm.Session(
       'server',
       auth=('user', 'pass'),
       transport='basic',
       read_timeout_sec=60,
       operation_timeout_sec=30
   )
   ```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now WinRM operations will show detailed logs
```

## Version Information

**Version:** 1.0  
**Last Updated:** 2026-01-28  
**Compatibility:** OpenCode Agent Skills Framework  
**Stack:** Python + PyWinRM  
**Platforms:** Windows Server 2012+, Windows 10/11

---

*This skill provides comprehensive Windows remote management capabilities via WinRM. Always ensure proper authorization before connecting to remote systems. Use HTTPS and strong authentication in production environments.*
