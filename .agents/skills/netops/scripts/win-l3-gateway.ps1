# win-l3-gateway.ps1 — Turn a Windows box into a single-NIC L3 gateway sensor
# Usage (as Administrator):
#   .\win-l3-gateway.ps1 -InterfaceAlias "Ethernet" -GatewayIP 10.0.0.1/24 [-NAT]
# Then point observed hosts' default gateway at 10.0.0.1 (DHCP option 3 or manual)
# and run RustNet/Pktmon/tshark on the interface to see both directions (hairpin).
#
# Caveat: invasive (changes host gateways). SPOF if the sensor dies (mitigate with VRRP/keepalived backup).
# A transparent Layer-2 bridge is NOT possible on Windows — this is the single-NIC inline alternative.
param(
    [Parameter(Mandatory=$true)][string]$InterfaceAlias,
    [Parameter(Mandatory=$true)][string]$GatewayIP,   # e.g. 10.0.0.1
    [int]$PrefixLength = 24,
    [switch]$NAT,
    [string]$NatSubnet = "10.0.0.0/24"
)

#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"

Write-Host ">> Enabling IP forwarding on $InterfaceAlias" -ForegroundColor Cyan
Set-NetIPInterface -InterfaceAlias $InterfaceAlias -Forwarding Enabled
Set-NetIPInterface -InterfaceAlias $InterfaceAlias -Ipv4Forwarding Enabled

# Enable forwarding globally (registry)
$reg = "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
Set-ItemProperty -Path $reg -Name "IPEnableRouter" -Value 1 -Type DWord

Write-Host ">> Assigning gateway IP $GatewayIP/$PrefixLength to $InterfaceAlias" -ForegroundColor Cyan
$existing = Get-NetIPAddress -InterfaceAlias $InterfaceAlias -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -eq $GatewayIP }
if (-not $existing) {
    New-NetIPAddress -InterfaceAlias $InterfaceAlias -IPAddress $GatewayIP -PrefixLength $PrefixLength | Out-Null
}

if ($NAT) {
    Write-Host ">> Enabling NAT for $NatSubnet (hairpin to upstream)" -ForegroundColor Cyan
    $existingNat = Get-NetNat -Name "SensorNAT" -ErrorAction SilentlyContinue
    if (-not $existingNat) {
        New-NetNat -Name "SensorNAT" -InternalIPInterfaceAddressPrefix $NatSubnet | Out-Null
    }
}

Write-Host ">> IP forwarding state:" -ForegroundColor Green
Get-NetIPInterface -InterfaceAlias $InterfaceAlias -AddressFamily IPv4 |
    Select-Object InterfaceAlias, Forwarding, ConnectionState

Write-Host ""
Write-Host ">> DONE. Now point observed hosts' default gateway at $GatewayIP" -ForegroundColor Green
Write-Host "   (DHCP option 3, or manual on each host)"
Write-Host ""
Write-Host ">> Capture both directions (hairpin) with:"
Write-Host "   rustnet -i `"$InterfaceAlias`"          # live TUI (Admin)"
Write-Host "   pktmon start --capture --comp nics -m real-time   # headless"
Write-Host "   tshark -i `"$InterfaceAlias`" -w cap.pcapng            # if Wireshark/Npcap installed"
