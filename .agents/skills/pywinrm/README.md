# PyWinRM Skill for OpenCode

Enterprise-grade Windows remote management using PyWinRM.

## Quick Start

```bash
# Install pywinrm
uv pip install pywinrm

# Test connection
uv run python -c "
import winrm
s = winrm.Session('http://SERVER:5985/wsman', auth=('Administrator', 'PASS'), transport='basic')
print(s.run_ps('hostname').std_out.decode())
"
```

## Files

- `SKILL.md` - Full skill documentation with 13 management modules
- `examples/winrm_client.py` - Universal CLI client
- `examples/server_monitor.py` - Multi-server health monitor

## Modules Included

1. PowerShell/CMD Execution
2. System Information Collection
3. Performance Monitoring
4. Service Management
5. Event Log Analysis
6. Process Management
7. File Operations
8. Registry Operations
9. Active Directory Management
10. Scheduled Task Management
11. Windows Update Management
12. Network Configuration
13. Multi-Server Parallel Execution

## Known Servers

| Server | IP | Port |
|--------|-----|------|
| AWS Windows 1 | 44.197.31.152 | 5985 |
| AWS Windows 2 | 52.3.242.251 | 5985 |
| 21CTL Windows | 80.248.0.66 | 5985 |

## Example Usage

```python
import winrm

session = winrm.Session(
    'http://44.197.31.152:5985/wsman',
    auth=('Administrator', 'PASSWORD'),
    transport='basic'
)

# Get system info
result = session.run_ps('Get-ComputerInfo | Select CsName, WindowsVersion | ConvertTo-Json')
print(result.std_out.decode())

# List services
result = session.run_ps('Get-Service | Where Status -eq Running | Select Name, DisplayName')
print(result.std_out.decode())
```

## Version

- Version: 1.0
- Updated: 2026-01-28
- Compatibility: OpenCode Skills Framework
