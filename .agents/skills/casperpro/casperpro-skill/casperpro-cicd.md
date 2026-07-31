# CasperPro CI/CD Integration Module

Enterprise security testing automation for CI/CD pipelines. Integrates with GitHub Actions, GitLab CI, Jenkins, and standalone automation.

## Overview

This module provides:
- Pipeline-ready security scanning configurations
- Automated vulnerability detection with fail/pass thresholds
- Integration with DAST tools (nuclei, sqlmap, ffuf)
- JSON/SARIF output for security dashboards
- Slack/Teams notifications for findings

---

## GitHub Actions Integration

### Complete Security Workflow

```yaml
# .github/workflows/security-scan.yml
name: CasperPro Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

env:
  TARGET_URL: ${{ secrets.TARGET_URL }}
  AUTH_TOKEN: ${{ secrets.AUTH_TOKEN }}

jobs:
  security-scan:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"
      
      - name: Install dependencies
        run: |
          uv tool install mitmproxy
          uv add httpx playwright aiohttp
          uv run playwright install chromium
          
          # Install security tools
          go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
          go install -v github.com/ffuf/ffuf/v2@latest
      
      - name: API Discovery
        run: |
          curl -s "$TARGET_URL/api" -o /tmp/api_response.json
          ffuf -u "$TARGET_URL/FUZZ" \
            -w wordlists/api-endpoints.txt \
            -o /tmp/endpoints.json \
            -of json \
            -mc 200,201,301,302,401,403
      
      - name: Nuclei Scan
        run: |
          nuclei -u "$TARGET_URL" \
            -t cves/ -t exposures/ -t vulnerabilities/ \
            -severity critical,high,medium \
            -o /tmp/nuclei-results.txt \
            -json-export /tmp/nuclei-results.json \
            -sarif-export /tmp/nuclei-results.sarif
      
      - name: IDOR Testing
        run: |
          uv run python scripts/idor_scanner.py \
            --target "$TARGET_URL" \
            --token "$AUTH_TOKEN" \
            --output /tmp/idor-results.json
      
      - name: Authentication Tests
        run: |
          uv run python scripts/auth_tester.py \
            --target "$TARGET_URL" \
            --output /tmp/auth-results.json
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: /tmp/nuclei-results.sarif
      
      - name: Check for Critical Findings
        run: |
          CRITICAL=$(jq '[.[] | select(.info.severity=="critical")] | length' /tmp/nuclei-results.json)
          HIGH=$(jq '[.[] | select(.info.severity=="high")] | length' /tmp/nuclei-results.json)
          
          echo "Critical: $CRITICAL, High: $HIGH"
          
          if [ "$CRITICAL" -gt 0 ]; then
            echo "::error::Found $CRITICAL critical vulnerabilities!"
            exit 1
          fi
          
          if [ "$HIGH" -gt 5 ]; then
            echo "::warning::Found $HIGH high severity vulnerabilities"
          fi
      
      - name: Upload Artifacts
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: security-results
          path: /tmp/*-results.*
```

### Reusable Action

```yaml
# .github/actions/casperpro-scan/action.yml
name: CasperPro Security Scan
description: Run CasperPro security tests

inputs:
  target_url:
    description: Target URL to scan
    required: true
  auth_token:
    description: Authentication token
    required: false
  severity_threshold:
    description: Minimum severity to report (critical, high, medium, low)
    default: medium
  fail_on_critical:
    description: Fail build on critical findings
    default: 'true'

outputs:
  findings_count:
    description: Total findings count
  critical_count:
    description: Critical findings count

runs:
  using: composite
  steps:
    - name: Setup Tools
      shell: bash
      run: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        uv tool install mitmproxy
        go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
    
    - name: Run Scan
      shell: bash
      run: |
        nuclei -u "${{ inputs.target_url }}" \
          -severity ${{ inputs.severity_threshold }},high,critical \
          -json-export /tmp/results.json
        
        CRITICAL=$(jq '[.[] | select(.info.severity=="critical")] | length' /tmp/results.json)
        echo "critical_count=$CRITICAL" >> $GITHUB_OUTPUT
        
        if [ "${{ inputs.fail_on_critical }}" = "true" ] && [ "$CRITICAL" -gt 0 ]; then
          exit 1
        fi
```

---

## GitLab CI Integration

### Security Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - security
  - deploy

variables:
  TARGET_URL: ${CI_ENVIRONMENT_URL}

security-scan:
  stage: security
  image: python:3.12-slim
  
  before_script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - export PATH="$HOME/.local/bin:$PATH"
    - uv tool install mitmproxy
    - uv add httpx playwright
    
    # Install nuclei
    - apt-get update && apt-get install -y wget
    - wget -q https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip
    - unzip nuclei_linux_amd64.zip && mv nuclei /usr/local/bin/
  
  script:
    - |
      nuclei -u "$TARGET_URL" \
        -t cves/ -t exposures/ \
        -severity critical,high \
        -json-export nuclei-results.json \
        -sarif-export gl-sast-report.json
    
    - |
      uv run python - <<'EOF'
      import json
      import sys
      
      with open('nuclei-results.json') as f:
          results = json.load(f)
      
      critical = [r for r in results if r.get('info', {}).get('severity') == 'critical']
      if critical:
          print(f"Found {len(critical)} critical vulnerabilities!")
          sys.exit(1)
      EOF
  
  artifacts:
    reports:
      sast: gl-sast-report.json
    paths:
      - nuclei-results.json
    expire_in: 1 week
  
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_MERGE_REQUEST_ID

dast-scan:
  stage: security
  image: python:3.12-slim
  
  script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - export PATH="$HOME/.local/bin:$PATH"
    - uv add httpx aiohttp
    
    - |
      uv run python - <<'EOF'
      import httpx
      import asyncio
      import json
      
      async def test_idor(base_url, endpoints):
          results = []
          async with httpx.AsyncClient() as client:
              for endpoint in endpoints:
                  for i in range(1, 20):
                      try:
                          resp = await client.get(f"{base_url}{endpoint}/{i}")
                          if resp.status_code == 200:
                              results.append({
                                  "type": "IDOR",
                                  "endpoint": f"{endpoint}/{i}",
                                  "severity": "high"
                              })
                      except:
                          pass
          return results
      
      results = asyncio.run(test_idor("$TARGET_URL", ["/api/users", "/api/orders"]))
      
      with open('dast-results.json', 'w') as f:
          json.dump(results, f, indent=2)
      
      if results:
          print(f"Found {len(results)} potential IDOR vulnerabilities")
      EOF
  
  artifacts:
    paths:
      - dast-results.json
    expire_in: 1 week
```

---

## Jenkins Pipeline

### Jenkinsfile

```groovy
pipeline {
    agent any
    
    environment {
        TARGET_URL = credentials('target-url')
        AUTH_TOKEN = credentials('auth-token')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                    curl -LsSf https://astral.sh/uv/install.sh | sh
                    export PATH="$HOME/.local/bin:$PATH"
                    uv tool install mitmproxy
                    uv add httpx playwright aiohttp
                    
                    # Install nuclei
                    wget -q https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip
                    unzip -o nuclei_linux_amd64.zip
                    chmod +x nuclei
                '''
            }
        }
        
        stage('Discovery') {
            steps {
                sh '''
                    export PATH="$HOME/.local/bin:$PATH"
                    
                    # Endpoint discovery
                    ./ffuf -u "${TARGET_URL}/FUZZ" \
                        -w wordlists/api-endpoints.txt \
                        -o endpoints.json \
                        -of json \
                        -mc 200,201,301,302,401,403
                '''
            }
        }
        
        stage('Vulnerability Scan') {
            parallel {
                stage('Nuclei') {
                    steps {
                        sh '''
                            ./nuclei -u "${TARGET_URL}" \
                                -t cves/ -t exposures/ \
                                -severity critical,high,medium \
                                -json-export nuclei-results.json
                        '''
                    }
                }
                
                stage('IDOR Test') {
                    steps {
                        sh '''
                            export PATH="$HOME/.local/bin:$PATH"
                            uv run python scripts/idor_scanner.py \
                                --target "${TARGET_URL}" \
                                --token "${AUTH_TOKEN}" \
                                --output idor-results.json
                        '''
                    }
                }
                
                stage('Auth Test') {
                    steps {
                        sh '''
                            export PATH="$HOME/.local/bin:$PATH"
                            uv run python scripts/auth_tester.py \
                                --target "${TARGET_URL}" \
                                --output auth-results.json
                        '''
                    }
                }
            }
        }
        
        stage('Analysis') {
            steps {
                script {
                    def results = readJSON file: 'nuclei-results.json'
                    def critical = results.findAll { it.info?.severity == 'critical' }
                    def high = results.findAll { it.info?.severity == 'high' }
                    
                    echo "Critical: ${critical.size()}, High: ${high.size()}"
                    
                    if (critical.size() > 0) {
                        error "Found ${critical.size()} critical vulnerabilities!"
                    }
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: '*-results.json', fingerprint: true
            
            // Publish to security dashboard
            publishHTML(target: [
                reportDir: '.',
                reportFiles: 'security-report.html',
                reportName: 'Security Report'
            ])
        }
        
        failure {
            slackSend(
                channel: '#security-alerts',
                color: 'danger',
                message: "Security scan failed for ${env.JOB_NAME} - ${env.BUILD_URL}"
            )
        }
    }
}
```

---

## Standalone Automation Script

### Full Pipeline Script

```python
#!/usr/bin/env python3
"""
CasperPro Automated Security Pipeline
Run with: uv run casperpro_pipeline.py --target https://api.example.com
"""

import argparse
import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx


class CasperProPipeline:
    def __init__(self, target: str, token: str = None, output_dir: str = "./results"):
        self.target = target.rstrip("/")
        self.token = token
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = {"target": target, "timestamp": datetime.now().isoformat(), "findings": []}
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    async def run_discovery(self) -> list[str]:
        """Discover API endpoints"""
        print("[*] Running endpoint discovery...")
        endpoints = []

        # Common API paths
        paths = ["/api", "/api/v1", "/api/v2", "/graphql", "/rest", "/swagger.json", "/openapi.json"]

        async with httpx.AsyncClient(headers=self.headers, timeout=10) as client:
            for path in paths:
                try:
                    resp = await client.get(f"{self.target}{path}")
                    if resp.status_code < 500:
                        endpoints.append(path)
                        print(f"  [+] Found: {path} ({resp.status_code})")
                except Exception:
                    pass

        return endpoints

    async def run_idor_scan(self, endpoints: list[str]) -> list[dict]:
        """Test for IDOR vulnerabilities"""
        print("[*] Running IDOR scan...")
        findings = []

        async with httpx.AsyncClient(headers=self.headers, timeout=10) as client:
            for endpoint in endpoints:
                for i in range(1, 20):
                    try:
                        url = f"{self.target}{endpoint}/{i}"
                        resp = await client.get(url)
                        if resp.status_code == 200 and len(resp.content) > 50:
                            finding = {
                                "type": "IDOR",
                                "severity": "high",
                                "url": url,
                                "status_code": resp.status_code,
                            }
                            findings.append(finding)
                            print(f"  [!] Potential IDOR: {url}")
                    except Exception:
                        pass

        return findings

    async def run_auth_tests(self) -> list[dict]:
        """Test authentication mechanisms"""
        print("[*] Running authentication tests...")
        findings = []

        tests = [
            {"name": "No auth header", "headers": {}},
            {"name": "Empty bearer", "headers": {"Authorization": "Bearer "}},
            {"name": "Invalid token", "headers": {"Authorization": "Bearer invalid"}},
            {"name": "None algorithm JWT", "headers": {"Authorization": "Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxMjM0NTY3ODkwIn0."}},
        ]

        async with httpx.AsyncClient(timeout=10) as client:
            for test in tests:
                try:
                    resp = await client.get(f"{self.target}/api/users/me", headers=test["headers"])
                    if resp.status_code == 200:
                        finding = {
                            "type": "AUTH_BYPASS",
                            "severity": "critical",
                            "test": test["name"],
                            "url": f"{self.target}/api/users/me",
                        }
                        findings.append(finding)
                        print(f"  [!] Auth bypass: {test['name']}")
                except Exception:
                    pass

        return findings

    def run_nuclei(self) -> list[dict]:
        """Run nuclei scanner"""
        print("[*] Running nuclei scan...")
        output_file = self.output_dir / "nuclei-results.json"

        try:
            subprocess.run(
                [
                    "nuclei",
                    "-u", self.target,
                    "-t", "cves/",
                    "-t", "exposures/",
                    "-severity", "critical,high,medium",
                    "-json-export", str(output_file),
                    "-silent",
                ],
                capture_output=True,
                timeout=300,
            )

            if output_file.exists():
                with open(output_file) as f:
                    return json.load(f)
        except FileNotFoundError:
            print("  [!] nuclei not found, skipping...")
        except Exception as e:
            print(f"  [!] nuclei error: {e}")

        return []

    async def run_injection_tests(self) -> list[dict]:
        """Test for injection vulnerabilities"""
        print("[*] Running injection tests...")
        findings = []

        payloads = {
            "sqli": ["'", "1 OR 1=1", "1' OR '1'='1", "1; DROP TABLE--"],
            "xss": ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>"],
            "ssrf": ["http://127.0.0.1", "http://localhost", "http://169.254.169.254"],
        }

        async with httpx.AsyncClient(headers=self.headers, timeout=10) as client:
            for vuln_type, tests in payloads.items():
                for payload in tests:
                    try:
                        resp = await client.get(f"{self.target}/api/search", params={"q": payload})
                        
                        # Check for SQL errors
                        if vuln_type == "sqli" and any(
                            err in resp.text.lower()
                            for err in ["sql", "syntax", "mysql", "postgresql", "oracle"]
                        ):
                            findings.append({
                                "type": "SQL_INJECTION",
                                "severity": "critical",
                                "payload": payload,
                                "url": str(resp.url),
                            })
                            print(f"  [!] SQLi detected: {payload}")
                        
                        # Check for XSS reflection
                        if vuln_type == "xss" and payload in resp.text:
                            findings.append({
                                "type": "XSS",
                                "severity": "high",
                                "payload": payload,
                                "url": str(resp.url),
                            })
                            print(f"  [!] XSS reflection: {payload}")
                            
                    except Exception:
                        pass

        return findings

    async def run_pipeline(self) -> dict[str, Any]:
        """Execute full security pipeline"""
        print(f"\n{'='*60}")
        print(f"CasperPro Security Pipeline")
        print(f"Target: {self.target}")
        print(f"{'='*60}\n")

        # Discovery
        endpoints = await self.run_discovery()

        # Parallel security tests
        idor_task = asyncio.create_task(self.run_idor_scan(endpoints))
        auth_task = asyncio.create_task(self.run_auth_tests())
        injection_task = asyncio.create_task(self.run_injection_tests())

        # Run nuclei in background
        nuclei_results = self.run_nuclei()

        # Gather async results
        idor_results, auth_results, injection_results = await asyncio.gather(
            idor_task, auth_task, injection_task
        )

        # Combine all findings
        all_findings = idor_results + auth_results + injection_results
        
        for result in nuclei_results:
            all_findings.append({
                "type": "NUCLEI",
                "severity": result.get("info", {}).get("severity", "unknown"),
                "name": result.get("info", {}).get("name", "Unknown"),
                "url": result.get("matched-at", ""),
            })

        self.results["findings"] = all_findings
        self.results["summary"] = {
            "total": len(all_findings),
            "critical": len([f for f in all_findings if f.get("severity") == "critical"]),
            "high": len([f for f in all_findings if f.get("severity") == "high"]),
            "medium": len([f for f in all_findings if f.get("severity") == "medium"]),
        }

        # Save results
        output_file = self.output_dir / "pipeline-results.json"
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        # Print summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Total findings: {self.results['summary']['total']}")
        print(f"  Critical: {self.results['summary']['critical']}")
        print(f"  High: {self.results['summary']['high']}")
        print(f"  Medium: {self.results['summary']['medium']}")
        print(f"\nResults saved to: {output_file}")

        return self.results


def main():
    parser = argparse.ArgumentParser(description="CasperPro Security Pipeline")
    parser.add_argument("--target", "-t", required=True, help="Target URL")
    parser.add_argument("--token", help="Auth token")
    parser.add_argument("--output", "-o", default="./results", help="Output directory")
    parser.add_argument("--fail-on-critical", action="store_true", help="Exit 1 on critical findings")
    args = parser.parse_args()

    pipeline = CasperProPipeline(args.target, args.token, args.output)
    results = asyncio.run(pipeline.run_pipeline())

    if args.fail_on_critical and results["summary"]["critical"] > 0:
        print(f"\n[!] FAILED: Found {results['summary']['critical']} critical vulnerabilities")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Usage

```bash
# Install dependencies
uv add httpx

# Run pipeline
uv run casperpro_pipeline.py --target https://api.example.com --token "$TOKEN"

# Fail on critical (for CI)
uv run casperpro_pipeline.py --target https://api.example.com --fail-on-critical
```

---

## Notifications

### Slack Webhook

```python
#!/usr/bin/env python3
"""Send security results to Slack - run with: uv run notify_slack.py"""

import json
import httpx
import sys

def send_slack_notification(webhook_url: str, results_file: str):
    with open(results_file) as f:
        results = json.load(f)
    
    summary = results.get("summary", {})
    color = "danger" if summary.get("critical", 0) > 0 else "warning" if summary.get("high", 0) > 0 else "good"
    
    payload = {
        "attachments": [{
            "color": color,
            "title": "CasperPro Security Scan Results",
            "fields": [
                {"title": "Target", "value": results.get("target", "Unknown"), "short": True},
                {"title": "Total Findings", "value": str(summary.get("total", 0)), "short": True},
                {"title": "Critical", "value": str(summary.get("critical", 0)), "short": True},
                {"title": "High", "value": str(summary.get("high", 0)), "short": True},
            ],
            "footer": f"Scan completed at {results.get('timestamp', 'Unknown')}"
        }]
    }
    
    resp = httpx.post(webhook_url, json=payload)
    print(f"Notification sent: {resp.status_code}")

if __name__ == "__main__":
    send_slack_notification(sys.argv[1], sys.argv[2])
```

### Teams Webhook

```bash
# Send to Microsoft Teams
curl -X POST "$TEAMS_WEBHOOK" \
  -H "Content-Type: application/json" \
  -d '{
    "@type": "MessageCard",
    "themeColor": "FF0000",
    "title": "CasperPro Security Alert",
    "text": "Found 3 critical vulnerabilities in production API",
    "sections": [{
      "facts": [
        {"name": "Target", "value": "https://api.example.com"},
        {"name": "Critical", "value": "3"},
        {"name": "High", "value": "7"}
      ]
    }]
  }'
```

---

## Docker Integration

### Dockerfile

```dockerfile
FROM python:3.12-slim

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl wget unzip jq \
    && rm -rf /var/lib/apt/lists/*

# Install nuclei
RUN wget -q https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip \
    && unzip nuclei_linux_amd64.zip \
    && mv nuclei /usr/local/bin/ \
    && rm nuclei_linux_amd64.zip

# Install Python dependencies
RUN uv add httpx playwright aiohttp

# Install Playwright browsers
RUN uv run playwright install chromium --with-deps

WORKDIR /app
COPY scripts/ ./scripts/

ENTRYPOINT ["uv", "run", "python", "scripts/casperpro_pipeline.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  casperpro:
    build: .
    environment:
      - TARGET_URL=${TARGET_URL}
      - AUTH_TOKEN=${AUTH_TOKEN}
    volumes:
      - ./results:/app/results
    command: ["--target", "${TARGET_URL}", "--fail-on-critical"]
```

---

## Output Formats

### SARIF (for GitHub/GitLab)

```python
def convert_to_sarif(results: dict) -> dict:
    """Convert CasperPro results to SARIF format"""
    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "CasperPro",
                    "version": "2.3",
                    "informationUri": "https://github.com/your-org/casperpro"
                }
            },
            "results": []
        }]
    }
    
    severity_map = {"critical": "error", "high": "warning", "medium": "note", "low": "note"}
    
    for finding in results.get("findings", []):
        sarif["runs"][0]["results"].append({
            "ruleId": finding.get("type", "UNKNOWN"),
            "level": severity_map.get(finding.get("severity", "medium"), "note"),
            "message": {"text": f"{finding.get('type')}: {finding.get('url', 'Unknown')}"},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": finding.get("url", "")}
                }
            }]
        })
    
    return sarif
```

---

## Best Practices

1. **Never store secrets in code** - Use CI/CD secrets management
2. **Rate limit scans** - Add delays to avoid overwhelming targets
3. **Scope validation** - Only scan authorized targets
4. **Result retention** - Archive results for compliance
5. **Fail fast** - Exit early on critical findings in CI

---

**Related Modules:**
- **casperpro-automation.md** - Python automation framework
- **casperpro-reporting.md** - Report generation and CVSS scoring
- **casperpro-tools-integration.md** - Tool configuration
