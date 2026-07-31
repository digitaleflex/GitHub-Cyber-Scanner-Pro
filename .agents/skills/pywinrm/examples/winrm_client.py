#!/usr/bin/env python3
"""
PyWinRM Universal Client
A comprehensive Windows remote management client supporting multiple operations.

Usage:
    uv run winrm_client.py <host> <username> <password> <action> [options]

Actions:
    exec <command>          - Execute PowerShell command
    cmd <command>           - Execute CMD command
    info                    - Get system information
    services [status]       - List services (optional: Running, Stopped)
    processes [sort]        - List processes (optional: CPU, Memory)
    events <log> [count]    - Get event log entries
    files <path>            - List directory contents
    read <path>             - Read file content
    disk                    - Get disk usage
    network                 - Get network configuration
    updates                 - Check for Windows updates
    reboot-check            - Check pending reboot status

Examples:
    uv run winrm_client.py 192.168.1.100 Administrator P@ssw0rd exec "Get-Process"
    uv run winrm_client.py 192.168.1.100 Administrator P@ssw0rd services Running
    uv run winrm_client.py 192.168.1.100 Administrator P@ssw0rd events System 10
"""

import sys
import json
import argparse
import winrm
from typing import Optional, Dict, Any


class WinRMClient:
    """Universal WinRM client for Windows remote management."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 5985,
        use_https: bool = False,
        transport: str = "basic",
    ):
        """Initialize WinRM connection."""
        protocol = "https" if use_https else "http"
        port = port if port else (5986 if use_https else 5985)

        self.session = winrm.Session(
            f"{protocol}://{host}:{port}/wsman",
            auth=(username, password),
            transport=transport,
            server_cert_validation="ignore" if use_https else None,
        )
        self.host = host

    def execute_ps(self, command: str) -> Dict[str, Any]:
        """Execute PowerShell command."""
        result = self.session.run_ps(command)
        return {
            "status_code": result.status_code,
            "stdout": result.std_out.decode("utf-8", errors="replace"),
            "stderr": result.std_err.decode("utf-8", errors="replace"),
        }

    def execute_cmd(self, command: str) -> Dict[str, Any]:
        """Execute CMD command."""
        result = self.session.run_cmd(command)
        return {
            "status_code": result.status_code,
            "stdout": result.std_out.decode("utf-8", errors="replace"),
            "stderr": result.std_err.decode("utf-8", errors="replace"),
        }

    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        ps_script = """
        $os = Get-WmiObject Win32_OperatingSystem
        $cs = Get-WmiObject Win32_ComputerSystem
        $proc = Get-WmiObject Win32_Processor | Select-Object -First 1
        
        @{
            ComputerName = $env:COMPUTERNAME
            Domain = $cs.Domain
            Manufacturer = $cs.Manufacturer
            Model = $cs.Model
            OS = $os.Caption
            Version = $os.Version
            BuildNumber = $os.BuildNumber
            Architecture = $os.OSArchitecture
            InstallDate = $os.InstallDate
            LastBootTime = $os.LastBootUpTime
            TotalMemoryGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 2)
            ProcessorName = $proc.Name
            ProcessorCores = $proc.NumberOfCores
            ProcessorLogical = $proc.NumberOfLogicalProcessors
            SystemDrive = $env:SystemDrive
            WindowsDirectory = $env:windir
            TimeZone = (Get-TimeZone).DisplayName
            CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
        } | ConvertTo-Json -Depth 2
        """
        result = self.execute_ps(ps_script)
        if result["status_code"] == 0:
            return json.loads(result["stdout"])
        raise Exception(result["stderr"])

    def get_services(self, status: Optional[str] = None) -> list:
        """Get Windows services."""
        filter_clause = f"| Where-Object {{$_.Status -eq '{status}'}}" if status else ""
        ps_script = f"""
        Get-Service {filter_clause} | 
        Select-Object Name, DisplayName, Status, StartType |
        ConvertTo-Json -Depth 2
        """
        result = self.execute_ps(ps_script)
        if result["status_code"] == 0:
            data = json.loads(result["stdout"])
            return data if isinstance(data, list) else [data]
        raise Exception(result["stderr"])

    def get_processes(self, sort_by: str = "CPU", top: int = 20) -> list:
        """Get top processes."""
        sort_prop = "CPU" if sort_by.upper() == "CPU" else "WorkingSet64"
        ps_script = f"""
        Get-Process | Sort-Object {sort_prop} -Descending | 
        Select-Object -First {top} Id, ProcessName,
            @{{Name='CPU_Sec';Expression={{[math]::Round($_.CPU, 2)}}}},
            @{{Name='MemoryMB';Expression={{[math]::Round($_.WorkingSet64 / 1MB, 2)}}}},
            @{{Name='Threads';Expression={{$_.Threads.Count}}}} |
        ConvertTo-Json -Depth 2
        """
        result = self.execute_ps(ps_script)
        if result["status_code"] == 0:
            data = json.loads(result["stdout"])
            return data if isinstance(data, list) else [data]
        raise Exception(result["stderr"])

    def get_event_logs(self, log_name: str, count: int = 50) -> list:
        """Get event log entries."""
        ps_script = f"""
        Get-EventLog -LogName {log_name} -Newest {count} |
        Select-Object TimeGenerated, EntryType, Source, EventID, Message |
        ConvertTo-Json -Depth 2
        """
        result = self.execute_ps(ps_script)
        if result["status_code"] == 0 and result["stdout"].strip():
            data = json.loads(result["stdout"])
            return data if isinstance(data, list) else [data]
        return []

    def list_directory(self, path: str) -> list:
        """List directory contents."""
        ps_script = f'''
        Get-ChildItem -Path "{path}" -ErrorAction Stop |
        Select-Object Name,
            @{{Name='Type';Expression={{if($_.PSIsContainer){{'Directory'}}else{{'File'}}}}}},
            @{{Name='Size';Expression={{$_.Length}}}},
            LastWriteTime |
        ConvertTo-Json -Depth 2
        '''
        result = self.execute_ps(ps_script)
        if result["status_code"] == 0:
            data = json.loads(result["stdout"])
            return data if isinstance(data, list) else [data]
        raise Exception(result["stderr"])

    def read_file(self, path: str) -> str:
        """Read file content."""
        ps_script = f'Get-Content -Path "{path}" -Raw'
        result = self.execute_ps(ps_script)
        if result["status_code"] == 0:
            return result["stdout"]
        raise Exception(result["stderr"])

    def get_disk_usage(self) -> list:
        """Get disk usage information."""
        ps_script = """
        Get-WmiObject Win32_LogicalDisk -Filter "DriveType=3" |
        Select-Object DeviceID,
            @{Name='SizeGB';Expression={[math]::Round($_.Size / 1GB, 2)}},
            @{Name='FreeGB';Expression={[math]::Round($_.FreeSpace / 1GB, 2)}},
            @{Name='UsedGB';Expression={[math]::Round(($_.Size - $_.FreeSpace) / 1GB, 2)}},
            @{Name='PercentFree';Expression={[math]::Round($_.FreeSpace / $_.Size * 100, 1)}} |
        ConvertTo-Json -Depth 2
        """
        result = self.execute_ps(ps_script)
        if result["status_code"] == 0:
            data = json.loads(result["stdout"])
            return data if isinstance(data, list) else [data]
        raise Exception(result["stderr"])

    def get_network_config(self) -> list:
        """Get network configuration."""
        ps_script = """
        Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | ForEach-Object {
            $adapter = $_
            $ip = Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue
            $gateway = Get-NetIPConfiguration -InterfaceIndex $adapter.ifIndex -ErrorAction SilentlyContinue
            @{
                Name = $adapter.Name
                Description = $adapter.InterfaceDescription
                MacAddress = $adapter.MacAddress
                LinkSpeed = $adapter.LinkSpeed
                IPv4Address = $ip.IPAddress
                SubnetMask = $ip.PrefixLength
                DefaultGateway = $gateway.IPv4DefaultGateway.NextHop
                DNSServers = ($gateway.DNSServer.ServerAddresses -join ", ")
            }
        } | ConvertTo-Json -Depth 2
        """
        result = self.execute_ps(ps_script)
        if result["status_code"] == 0 and result["stdout"].strip():
            data = json.loads(result["stdout"])
            return data if isinstance(data, list) else [data]
        return []

    def check_updates(self) -> Dict[str, Any]:
        """Check for available Windows updates."""
        ps_script = """
        $session = New-Object -ComObject Microsoft.Update.Session
        $searcher = $session.CreateUpdateSearcher()
        $results = $searcher.Search("IsInstalled=0")
        
        @{
            UpdatesAvailable = $results.Updates.Count
            Updates = $results.Updates | ForEach-Object {
                @{
                    Title = $_.Title
                    KBArticleIDs = ($_.KBArticleIDs -join ",")
                    IsMandatory = $_.IsMandatory
                    SizeMB = [math]::Round($_.MaxDownloadSize / 1MB, 2)
                }
            }
        } | ConvertTo-Json -Depth 3
        """
        result = self.execute_ps(ps_script)
        if result["status_code"] == 0:
            return json.loads(result["stdout"])
        raise Exception(result["stderr"])

    def check_pending_reboot(self) -> Dict[str, Any]:
        """Check if system has pending reboot."""
        ps_script = """
        $pending = $false
        $reasons = @()
        
        if (Test-Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update\\RebootRequired") {
            $pending = $true
            $reasons += "Windows Update"
        }
        
        if (Test-Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Component Based Servicing\\RebootPending") {
            $pending = $true
            $reasons += "Component Based Servicing"
        }
        
        $pfro = Get-ItemProperty "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Session Manager" -Name PendingFileRenameOperations -EA SilentlyContinue
        if ($pfro) {
            $pending = $true
            $reasons += "Pending File Rename"
        }
        
        @{
            PendingReboot = $pending
            Reasons = $reasons
            CheckedAt = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        } | ConvertTo-Json
        """
        result = self.execute_ps(ps_script)
        if result["status_code"] == 0:
            return json.loads(result["stdout"])
        raise Exception(result["stderr"])


def main():
    parser = argparse.ArgumentParser(
        description="PyWinRM Universal Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("host", help="Target Windows host")
    parser.add_argument("username", help="Username for authentication")
    parser.add_argument("password", help="Password for authentication")
    parser.add_argument("action", help="Action to perform")
    parser.add_argument("args", nargs="*", help="Additional arguments")
    parser.add_argument("--port", type=int, default=5985, help="WinRM port")
    parser.add_argument("--https", action="store_true", help="Use HTTPS")
    parser.add_argument(
        "--transport",
        default="basic",
        choices=["basic", "ntlm", "kerberos", "credssp"],
        help="Authentication transport",
    )

    args = parser.parse_args()

    try:
        client = WinRMClient(
            args.host,
            args.username,
            args.password,
            port=args.port,
            use_https=args.https,
            transport=args.transport,
        )

        action = args.action.lower()

        if action == "exec":
            command = " ".join(args.args) if args.args else "Get-Date"
            result = client.execute_ps(command)
            print(result["stdout"])
            if result["stderr"]:
                print(f"STDERR: {result['stderr']}", file=sys.stderr)

        elif action == "cmd":
            command = " ".join(args.args) if args.args else "hostname"
            result = client.execute_cmd(command)
            print(result["stdout"])

        elif action == "info":
            info = client.get_system_info()
            print(json.dumps(info, indent=2))

        elif action == "services":
            status = args.args[0] if args.args else None
            services = client.get_services(status)
            print(json.dumps(services, indent=2))

        elif action == "processes":
            sort_by = args.args[0] if args.args else "CPU"
            processes = client.get_processes(sort_by)
            print(json.dumps(processes, indent=2))

        elif action == "events":
            log_name = args.args[0] if args.args else "System"
            count = int(args.args[1]) if len(args.args) > 1 else 20
            events = client.get_event_logs(log_name, count)
            print(json.dumps(events, indent=2))

        elif action == "files":
            path = args.args[0] if args.args else "C:\\"
            files = client.list_directory(path)
            print(json.dumps(files, indent=2))

        elif action == "read":
            if not args.args:
                print("Error: File path required", file=sys.stderr)
                sys.exit(1)
            content = client.read_file(args.args[0])
            print(content)

        elif action == "disk":
            disks = client.get_disk_usage()
            print(json.dumps(disks, indent=2))

        elif action == "network":
            network = client.get_network_config()
            print(json.dumps(network, indent=2))

        elif action == "updates":
            updates = client.check_updates()
            print(json.dumps(updates, indent=2))

        elif action == "reboot-check":
            reboot = client.check_pending_reboot()
            print(json.dumps(reboot, indent=2))

        else:
            print(f"Unknown action: {action}", file=sys.stderr)
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
