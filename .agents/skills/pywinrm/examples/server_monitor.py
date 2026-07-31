#!/usr/bin/env python3
"""
Windows Server Health Monitor
Monitors multiple Windows servers and reports health status.

Usage:
    uv run server_monitor.py                    # Monitor all configured servers
    uv run server_monitor.py --output json      # Output as JSON
    uv run server_monitor.py --threshold 80     # Alert if any metric > 80%

Configuration:
    Set SERVERS list below or use environment variables.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

try:
    import winrm
except ImportError:
    print("Installing pywinrm...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "pywinrm"])
    import winrm

# Server configuration - modify or use environment variables
SERVERS = [
    {
        "name": "AWS-Win-1",
        "host": os.getenv("WINRM_HOST_1", "44.197.31.152"),
        "user": os.getenv("WINRM_USER_1", "Administrator"),
        "pass": os.getenv("WINRM_PASS_1", ""),
        "port": 5985,
    },
    {
        "name": "AWS-Win-2",
        "host": os.getenv("WINRM_HOST_2", "52.3.242.251"),
        "user": os.getenv("WINRM_USER_2", "Administrator"),
        "pass": os.getenv("WINRM_PASS_2", ""),
        "port": 5985,
    },
    {
        "name": "21CTL-Win",
        "host": os.getenv("WINRM_HOST_3", "80.248.0.66"),
        "user": os.getenv("WINRM_USER_3", "Administrator"),
        "pass": os.getenv("WINRM_PASS_3", ""),
        "port": 5985,
    },
]


def get_server_health(server: Dict[str, Any]) -> Dict[str, Any]:
    """Collect health metrics from a single server."""
    result = {
        "name": server["name"],
        "host": server["host"],
        "timestamp": datetime.now().isoformat(),
        "status": "unknown",
        "metrics": {},
        "alerts": [],
    }

    if not server.get("pass"):
        result["status"] = "skipped"
        result["error"] = "No password configured"
        return result

    try:
        session = winrm.Session(
            f"http://{server['host']}:{server['port']}/wsman",
            auth=(server["user"], server["pass"]),
            transport="basic",
            read_timeout_sec=30,
            operation_timeout_sec=20,
        )

        # Collect metrics with a single PowerShell script
        ps_script = """
        $ErrorActionPreference = "SilentlyContinue"
        
        # CPU
        $cpu = (Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 1).CounterSamples.CookedValue
        
        # Memory
        $os = Get-WmiObject Win32_OperatingSystem
        $totalMem = $os.TotalVisibleMemorySize / 1MB
        $freeMem = $os.FreePhysicalMemory / 1MB
        $usedMem = $totalMem - $freeMem
        $memPercent = ($usedMem / $totalMem) * 100
        
        # Disk
        $disks = Get-WmiObject Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
            @{
                Drive = $_.DeviceID
                SizeGB = [math]::Round($_.Size / 1GB, 2)
                FreeGB = [math]::Round($_.FreeSpace / 1GB, 2)
                UsedPercent = [math]::Round(100 - ($_.FreeSpace / $_.Size * 100), 1)
            }
        }
        
        # Uptime
        $bootTime = (Get-WmiObject Win32_OperatingSystem).LastBootUpTime
        $uptime = (Get-Date) - [Management.ManagementDateTimeConverter]::ToDateTime($bootTime)
        
        # Services
        $stoppedCritical = Get-Service | Where-Object {
            $_.StartType -eq 'Automatic' -and $_.Status -ne 'Running'
        } | Select-Object -First 5 Name, Status
        
        # Top processes by memory
        $topProcs = Get-Process | Sort-Object WorkingSet64 -Descending | 
            Select-Object -First 5 ProcessName, @{N='MemoryMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}
        
        # Pending reboot check
        $pendingReboot = (Test-Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update\\RebootRequired") -or
                        (Test-Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Component Based Servicing\\RebootPending")
        
        @{
            Hostname = $env:COMPUTERNAME
            CPU = [math]::Round($cpu, 1)
            Memory = @{
                TotalGB = [math]::Round($totalMem, 2)
                UsedGB = [math]::Round($usedMem, 2)
                UsedPercent = [math]::Round($memPercent, 1)
            }
            Disks = $disks
            Uptime = @{
                Days = $uptime.Days
                Hours = $uptime.Hours
                Minutes = $uptime.Minutes
                TotalHours = [math]::Round($uptime.TotalHours, 1)
            }
            StoppedAutoServices = $stoppedCritical
            TopProcessesByMemory = $topProcs
            PendingReboot = $pendingReboot
        } | ConvertTo-Json -Depth 4
        """

        ps_result = session.run_ps(ps_script)

        if ps_result.status_code == 0 and ps_result.std_out:
            metrics = json.loads(ps_result.std_out.decode("utf-8"))
            result["status"] = "healthy"
            result["metrics"] = metrics

            # Check for alert conditions
            if metrics.get("CPU", 0) > 90:
                result["alerts"].append(f"High CPU: {metrics['CPU']}%")
                result["status"] = "warning"

            if metrics.get("Memory", {}).get("UsedPercent", 0) > 90:
                result["alerts"].append(
                    f"High Memory: {metrics['Memory']['UsedPercent']}%"
                )
                result["status"] = "warning"

            for disk in metrics.get("Disks", []):
                if disk.get("UsedPercent", 0) > 90:
                    result["alerts"].append(
                        f"Low disk space on {disk['Drive']}: {disk['UsedPercent']}% used"
                    )
                    result["status"] = "warning"

            if metrics.get("PendingReboot"):
                result["alerts"].append("Pending reboot detected")

            if metrics.get("StoppedAutoServices"):
                for svc in metrics["StoppedAutoServices"]:
                    result["alerts"].append(
                        f"Auto-start service stopped: {svc['Name']}"
                    )
        else:
            result["status"] = "error"
            result["error"] = ps_result.std_err.decode("utf-8", errors="replace")

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def monitor_servers(servers: List[Dict], threshold: int = 80) -> List[Dict]:
    """Monitor multiple servers in parallel."""
    results = []

    with ThreadPoolExecutor(max_workers=min(len(servers), 5)) as executor:
        futures = {executor.submit(get_server_health, s): s for s in servers}
        for future in as_completed(futures):
            results.append(future.result())

    return results


def print_report(results: List[Dict], output_format: str = "text"):
    """Print monitoring report."""
    if output_format == "json":
        print(json.dumps(results, indent=2))
        return

    print("\n" + "=" * 70)
    print(
        f"  WINDOWS SERVER HEALTH REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    print("=" * 70)

    for r in results:
        status_icon = {
            "healthy": "[OK]",
            "warning": "[!!]",
            "error": "[XX]",
            "skipped": "[--]",
            "unknown": "[??]",
        }.get(r["status"], "[??]")

        print(f"\n{status_icon} {r['name']} ({r['host']})")
        print("-" * 50)

        if r["status"] == "error":
            print(f"  ERROR: {r.get('error', 'Unknown error')}")
            continue

        if r["status"] == "skipped":
            print(f"  SKIPPED: {r.get('error', 'No configuration')}")
            continue

        metrics = r.get("metrics", {})

        if metrics:
            print(f"  Hostname: {metrics.get('Hostname', 'N/A')}")
            print(f"  CPU:      {metrics.get('CPU', 'N/A')}%")

            mem = metrics.get("Memory", {})
            print(
                f"  Memory:   {mem.get('UsedGB', 'N/A'):.1f} / {mem.get('TotalGB', 'N/A'):.1f} GB ({mem.get('UsedPercent', 'N/A')}%)"
            )

            for disk in metrics.get("Disks", []):
                free_pct = 100 - disk.get("UsedPercent", 0)
                print(
                    f"  Disk {disk['Drive']}:  {disk.get('FreeGB', 'N/A'):.1f} GB free ({free_pct:.1f}% free)"
                )

            uptime = metrics.get("Uptime", {})
            print(
                f"  Uptime:   {uptime.get('Days', 0)} days, {uptime.get('Hours', 0)} hours"
            )

            if metrics.get("PendingReboot"):
                print("  Reboot:   PENDING")

        if r["alerts"]:
            print("\n  ALERTS:")
            for alert in r["alerts"]:
                print(f"    - {alert}")

    print("\n" + "=" * 70)

    # Summary
    healthy = sum(1 for r in results if r["status"] == "healthy")
    warning = sum(1 for r in results if r["status"] == "warning")
    error = sum(1 for r in results if r["status"] == "error")

    print(f"  Summary: {healthy} healthy, {warning} warning, {error} error")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Windows Server Health Monitor")
    parser.add_argument(
        "--output", choices=["text", "json"], default="text", help="Output format"
    )
    parser.add_argument(
        "--threshold", type=int, default=80, help="Alert threshold percentage"
    )
    parser.add_argument(
        "--servers", type=str, help="Comma-separated list of servers (host:user:pass)"
    )

    args = parser.parse_args()

    servers = SERVERS

    # Parse command-line servers if provided
    if args.servers:
        servers = []
        for i, server_str in enumerate(args.servers.split(",")):
            parts = server_str.strip().split(":")
            if len(parts) >= 3:
                servers.append(
                    {
                        "name": f"Server-{i + 1}",
                        "host": parts[0],
                        "user": parts[1],
                        "pass": parts[2],
                        "port": int(parts[3]) if len(parts) > 3 else 5985,
                    }
                )

    # Filter out servers without passwords
    active_servers = [s for s in servers if s.get("pass")]

    if not active_servers:
        print("No servers configured with passwords.")
        print(
            "Set environment variables WINRM_HOST_1, WINRM_USER_1, WINRM_PASS_1, etc."
        )
        print("Or use --servers 'host1:user1:pass1,host2:user2:pass2'")
        sys.exit(1)

    results = monitor_servers(active_servers, args.threshold)
    print_report(results, args.output)

    # Exit with error code if any servers are in error state
    if any(r["status"] == "error" for r in results):
        sys.exit(1)
    if any(r["status"] == "warning" for r in results):
        sys.exit(2)


if __name__ == "__main__":
    main()
