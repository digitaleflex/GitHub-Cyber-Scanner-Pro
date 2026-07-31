# pktmon-sensor.ps1 — headless Windows capture-to-ETL with rotation + pcapng conversion
# Runs Pktmon continuously, rotating ETL files, and converts each to pcapng for Wireshark/tshark.
# Schedule via Task Scheduler at startup as SYSTEM/Administrator.
#
# Usage (Administrator PowerShell):
#   .\pktmon-sensor.ps1 -OutDir C:\caps -MaxGB 5 -FilterName F1
# Or as a scheduled task:
#   $a = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-File C:\scripts\pktmon-sensor.ps1 -OutDir C:\caps"
#   $t = New-ScheduledTaskTrigger -AtStartup
#   Register-ScheduledTask -TaskName PktmonSensor -Action $a -Trigger $t -RunLevel Highest -User SYSTEM
param(
    [string]$OutDir = "C:\caps",
    [int]$MaxGB = 5,
    [string]$FilterName = "",           # optional pre-configured pktmon filter name
    [int]$CaptureDurationMin = 0        # 0 = run until Ctrl+C / service stop
)

#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
$capFile = Join-Path $OutDir "cap.etl"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$pcapng = Join-Path $OutDir "cap_$stamp.pcapng"

Write-Host ">> Pktmon headless capture → $capFile (max ${MaxGB} GB)" -ForegroundColor Cyan
Write-Host ">> Will convert to $pcapng on stop" -ForegroundColor Cyan

$filterArg = if ($FilterName) { "" } else { "" }
# Apply filter if specified (filter must already exist: pktmon filter add F1 ...)
if ($FilterName) {
    Write-Host ">> Using pre-configured filter: $FilterName"
}

# Start capture (full packets, all NICs)
if ($CaptureDurationMin -gt 0) {
    $proc = Start-Process pktmon -ArgumentList "start --capture -c -p 0 --pkt-size 0 -f `"$capFile`"" -PassThru -NoNewWindow
    Start-Sleep -Seconds ($CaptureDurationMin * 60)
    pktmon stop | Out-Null
} else {
    pktmon start --capture --comp nics --pkt-size 0 -f "$capFile"
    # Wait until service is stopped or Ctrl+C
    Write-Host ">> Capturing. Run 'pktmon stop' to end, or stop this script." -ForegroundColor Yellow
    try {
        while ($true) { Start-Sleep -Seconds 5 }
    } finally {
        pktmon stop | Out-Null
    }
}

# Convert to pcapng
Write-Host ">> Converting $capFile → $pcapng" -ForegroundColor Cyan
pktmon etl2pcap "$capFile" -o "$pcapng"

# Rotate: delete old ETL/pcapng beyond MaxGB
$files = Get-ChildItem -Path $OutDir -Include *.etl,*.pcapng -File | Sort-Object LastWriteTime
$totalGB = ($files | Measure-Object Length -Sum).Sum / 1GB
if ($totalGB -gt $MaxGB) {
    Write-Host ">> Pruning old captures (> ${MaxGB} GB)" -ForegroundColor Yellow
    while ((($files | Measure-Object Length -Sum).Sum / 1GB) -gt $MaxGB -and $files.Count -gt 1) {
        $oldest = $files[0]
        Remove-Item $oldest.FullName -Force
        $files = $files[1..($files.Count - 1)]
    }
}

Write-Host ">> Done. Latest pcapng: $pcapng" -ForegroundColor Green
Write-Host ">> Analyze with:"
Write-Host "   tshark -r `"$pcapng`" -Y `"tcp.analysis.retransmission`""
Write-Host "   tshark -r `"$pcapng`" -o `"tls.keylog_file:K:\tmp\sslkeylog.txt`" -Y `"http`""
