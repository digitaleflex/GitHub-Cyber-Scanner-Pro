# install-windows-service.ps1 — register rterm-backend as an at-logon scheduled task.
# Run in an elevated PowerShell:  powershell -ExecutionPolicy Bypass -File install-windows-service.ps1

$TaskName = "RTermBackend"
$DataDir  = "$env:LOCALAPPDATA\rterm-backend"
$Port     = 17888

# 1. ensure the package is installed
$gyb = Get-Command gybackend -ErrorAction SilentlyContinue
if (-not $gyb) {
  Write-Host "Installing rterm-backend globally..."
  npm install -g rterm-backend
  $gyb = Get-Command gybackend -ErrorAction SilentlyContinue
}
if (-not $gyb) { Write-Error "gybackend not found after install"; exit 1 }
Write-Host "gybackend: $($gyb.Source)"

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

# 2. resolve the shim to a real node + script (more reliable than the .cmd shim)
$node = (Get-Command node).Source
$script = Join-Path (Split-Path (npm root -g)) "rterm-backend\bin\gybackend.js"
if (-not (Test-Path $script)) { Write-Error "cannot find $script"; exit 1 }

$action = New-ScheduledTaskAction -Execute $node `
  -Argument "`"$script`"" `
  -WorkingDirectory $DataDir

$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -RestartCount 999 -RestartInterval (New-TimeSpan -Seconds 10) -ExecutionTimeLimit ([TimeSpan]::Zero)

$env_block = @"
set GYBACKEND_WS_ENABLE=1&& set GYBACKEND_WS_HOST=0.0.0.0&& set GYBACKEND_WS_PORT=$Port&& set GYBACKEND_DATA_DIR=$DataDir&&
"@

# Use a cmd wrapper to set env vars (Task Scheduler doesn't set them directly)
$wrapper = Join-Path $DataDir "start-rterm-backend.cmd"
@"
@echo off
$env_block
`"$node`" `"$script`"
"@ | Out-File -Encoding ascii $wrapper

$cmdAction = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$wrapper`"" -WorkingDirectory $DataDir

Register-ScheduledTask -TaskName $TaskName -Action $cmdAction -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Host "Registered scheduled task '$TaskName' (starts at logon)."
Write-Host "Start it now with:  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "Gateway will be at: ws://0.0.0.0:$Port"
