# windows.ps1 — agentless Windows asset collector (WinRM/PowerShell).
# Emits ONE normalized JSON document to stdout (consumed by inventory:upsert).
# Run remotely over WinRM: powershell -NoProfile -File windows.ps1
# Read-only: this script only reads system state.

$ErrorActionPreference = 'SilentlyContinue'

function ToGB($bytes) { if ($bytes) { [math]::Round($bytes / 1GB, 2) } else { $null } }

$os   = Get-CimInstance Win32_OperatingSystem | Select-Object -First 1
$cs   = Get-CimInstance Win32_ComputerSystem | Select-Object -First 1
$cpu  = Get-CimInstance Win32_Processor | Select-Object -First 1
$bios = Get-CimInstance Win32_BIOS | Select-Object -First 1

$disks = @(Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
  @{
    device    = $_.DeviceID
    sizeGb    = ToGB $_.Size
    freeGb    = ToGB $_.FreeSpace
    fsType    = $_.FileSystem
  }
})

$nics = @(Get-NetAdapter | ForEach-Object {
  @{
    name        = $_.Name
    description = $_.InterfaceDescription
    mac         = $_.MacAddress
    linkSpeed   = $_.LinkSpeed
    status      = "$($_.Status)"
  }
})

$listeners = @(Get-NetTCPConnection -State Listen | ForEach-Object {
  @{ port = $_.LocalPort; pid = $_.OwningProcess }
} | Sort-Object -Property port -Unique)

$services = @(Get-Service | ForEach-Object {
  @{ name = $_.Name; status = "$($_.Status)"; startType = "$($_.StartType)" }
})

$software = @(
  Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
                   'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*' |
    Where-Object { $_.DisplayName } |
    ForEach-Object { @{ name = $_.DisplayName; version = $_.DisplayVersion } }
)

$hostname = $env:COMPUTERNAME
$fqdn = ([System.Net.Dns]::GetHostByName($hostname).HostName)

$asset = @{
  key    = "host:$hostname"
  type   = 'windows'
  name   = $hostname
  fqdn   = $fqdn
  mgmtIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '169.*' -and $_.IPAddress -ne '127.0.0.1' } | Select-Object -First 1).IPAddress
  source = 'winrm'
  attrs  = @{
    os             = $os.Caption
    version        = $os.Version
    build          = $os.BuildNumber
    manufacturer   = $cs.Manufacturer
    model          = $cs.Model
    serial         = $bios.SerialNumber
    cpu            = $cpu.Name
    cpuCores       = $cpu.NumberOfCores
    memGb          = ToGB $cs.TotalPhysicalMemory
    disks          = $disks
    nics           = $nics
    services       = $services
    listeningPorts = $listeners
    packages       = $software
  }
}

$asset | ConvertTo-Json -Depth 6 -Compress
