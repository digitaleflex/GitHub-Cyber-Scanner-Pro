# Interpretation Guide

How to interpret, aggregate, and act on security scan results from all five tools.

## Results Aggregation Script

After running all tools, use this Python script to aggregate results:

```bash
# Run from the project root after scanning
python3 << 'PYEOF'
import json, os

results_dir = "/tmp/security-scan-results"
summary = {
    "secrets": {"total": 0, "by_type": {}},
    "patterns": {"total": 0, "by_severity": {}},
    "dependencies": {"total": 0, "by_severity": {}},
    "misconfigs": {"total": 0, "by_type": {}},
    "deep_analysis": {"total": 0, "by_severity": {}},
    "full_sweep": {"total": 0, "by_severity": {}},
    "critical_actions": []
}

# Parse Gitleaks
try:
    with open(f"{results_dir}/gitleaks.json") as f:
        leaks = json.load(f)
    summary["secrets"]["total"] = len(leaks)
    for leak in leaks:
        rule = leak.get("RuleID", "unknown")
        summary["secrets"]["by_type"][rule] = summary["secrets"]["by_type"].get(rule, 0) + 1
    if leaks:
        summary["critical_actions"].append(f"ROTATE {len(leaks)} leaked credentials immediately")
except: pass

# Parse Semgrep
try:
    with open(f"{results_dir}/semgrep.json") as f:
        data = json.load(f)
    results = data.get("results", [])
    summary["patterns"]["total"] = len(results)
    for r in results:
        sev = r.get("extra", {}).get("severity", "INFO")
        summary["patterns"]["by_severity"][sev] = summary["patterns"]["by_severity"].get(sev, 0) + 1
except: pass

# Parse Trivy
try:
    with open(f"{results_dir}/trivy.json") as f:
        data = json.load(f)
    for r in data.get("results", []):
        for v in (r.get("vulnerabilities") or []):
            summary["dependencies"]["total"] += 1
            sev = v.get("severity", "UNKNOWN")
            summary["dependencies"]["by_severity"][sev] = summary["dependencies"]["by_severity"].get(sev, 0) + 1
        for m in (r.get("misconfigurations") or []):
            summary["misconfigs"]["total"] += 1
            mid = m.get("ID", "unknown")
            summary["misconfigs"]["by_type"][mid] = summary["misconfigs"]["by_type"].get(mid, 0) + 1
except: pass

# Parse CodeQL
try:
    with open(f"{results_dir}/codeql.sarif") as f:
        data = json.load(f)
    for run in data.get("runs", []):
        for r in run.get("results", []):
            summary["deep_analysis"]["total"] += 1
            sev = r.get("level", "note")
            summary["deep_analysis"]["by_severity"][sev] = summary["deep_analysis"]["by_severity"].get(sev, 0) + 1
except: pass

# Print report
print("=" * 60)
print("SECURITY SCAN REPORT")
print("=" * 60)
print(f"Secrets leaked:     {summary['secrets']['total']}")
print(f"Pattern findings:   {summary['patterns']['total']}")
print(f"Dependency CVEs:    {summary['dependencies']['total']}")
print(f"IaC misconfigs:    {summary['misconfigs']['total']}")
print(f"Deep analysis:      {summary['deep_analysis']['total']}")
print()

total = (summary['secrets']['total'] + summary['patterns']['total'] +
         summary['dependencies']['total'] + summary['misconfigs']['total'] +
         summary['deep_analysis']['total'])
print(f"TOTAL FINDINGS:     {total}")
print()

if summary['secrets']['total'] > 0:
    print("🔐 SECRET LEAKS (IMMEDIATE ACTION):")
    for rule, count in sorted(summary['secrets']['by_type'].items(), key=lambda x: -x[1]):
        print(f"   {rule}: {count}")
    print()

if summary['patterns']['total'] > 0:
    print("🔍 PATTERN FINDINGS (SEMGREP):")
    for sev in ['ERROR', 'WARNING', 'INFO']:
        if sev in summary['patterns']['by_severity']:
            print(f"   {sev}: {summary['patterns']['by_severity'][sev]}")
    print()

if summary['dependencies']['total'] > 0:
    print("📦 DEPENDENCY VULNERABILITIES (TRIVY):")
    for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        if sev in summary['dependencies']['by_severity']:
            print(f"   {sev}: {summary['dependencies']['by_severity'][sev]}")
    print()

if summary['critical_actions']:
    print("⚠️  CRITICAL ACTIONS:")
    for action in summary['critical_actions']:
        print(f"   → {action}")
    print()

# Risk score
risk_score = (summary['secrets']['total'] * 10 +
              summary['patterns'].get('by_severity', {}).get('ERROR', 0) * 5 +
              summary['dependencies'].get('by_severity', {}).get('CRITICAL', 0) * 8 +
              summary['dependencies'].get('by_severity', {}).get('HIGH', 0) * 3)
if risk_score > 50:
    risk_level = "🔴 CRITICAL"
elif risk_score > 20:
    risk_level = "🟠 HIGH"
elif risk_score > 5:
    risk_level = "🟡 MEDIUM"
else:
    risk_level = "🟢 LOW"

print(f"Risk Score: {risk_score} — {risk_level}")
print("=" * 60)
PYEOF
```

## Severity Interpretation

| Severity | Meaning | Action |
|---|---|---|
| **CRITICAL** | Exploitable right now, no authentication needed | Fix immediately, block deployment |
| **HIGH** | Exploitable with some effort or specific conditions | Fix before next release |
| **MEDIUM** | Potential vulnerability under certain conditions | Fix within sprint, add to backlog |
| **LOW** | Minor issue, defense-in-depth improvement | Fix when convenient |
| **INFO** | Informational, no direct security impact | Review, no action required |

## Fix Priority Workflow

After scanning, apply fixes in this priority order:

### P0 — IMMEDIATE (Secrets Found)

```bash
# If Gitleaks found secrets:
# 1. Identify each leaked credential type
# 2. Rotate the credential on the provider console
# 3. Remove from code and replace with env var or secret manager
# 4. If committed to git: use BFG or git-filter-repo to scrub history
# 5. Add .gitleaks.toml allowlist for any intentional test fixtures
```

### P1 — BEFORE MERGE (ERROR/HIGH Findings)

```bash
# Semgrep ERROR findings:
# - SQL injection → parameterized queries / ORM
# - XSS → output encoding / CSP headers
# - Auth bypass → add proper auth middleware
# - Path traversal → validate and sanitize file paths
# - Command injection → avoid shell execution, use safe APIs

# Trivy HIGH/CRITICAL CVEs:
# - Run 'npm audit fix' / 'pip audit --fix' / 'go fix'
# - If no fix available, consider alternative libraries
# - Add .trivyignore for accepted risks with justification
# - Set up Dependabot/Renovate for automated dependency updates
```

### P2 — WITHIN SPRINT (MEDIUM Findings)

```bash
# Review CodeQL taint analysis results
# Address Semgrep WARNING findings
# Update MEDIUM-severity dependency CVEs
```

### P3 — BACKLOG (LOW/INFO Findings)

```bash
# Review informational findings
# Address defense-in-depth improvements
# Update custom rules to reduce false positives
```

## Risk Score Calculation

```
Risk Score = (secrets_found × 10)
           + (semgrep_ERROR × 5)
           + (trivy_CRITICAL × 8)
           + (trivy_HIGH × 3)

🔴 CRITICAL  → Score > 50
🟠 HIGH      → Score 21–50
🟡 MEDIUM    → Score 6–20
🟢 LOW       → Score 0–5
```

## Output Format Cross-Reference

| Tool | JSON | SARIF | Table | Other |
|---|---|---|---|---|
| Semgrep | `--json` | `--sarif` | default | `--junit-xml` |
| Gitleaks | `--report-format json` | `--report-format sarif` | default (`-v`) | — |
| Trivy | `--format json` | `--format sarif` | `--format table` | `--format spdx-json` |
| CodeQL | — | `--format=sarif-latest` | — | `--format=csv` |
| Horusec | `-o json` | `-o sarif` | default | — |

All tools support JSON output for programmatic processing. SARIF is the standard format for GitHub integration.