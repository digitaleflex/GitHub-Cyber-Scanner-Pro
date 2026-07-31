---
name: secure-scan
description: Comprehensive secure code analysis and vulnerability review using Semgrep, Gitleaks, Trivy, CodeQL, and Horusec in a layered defense approach. Covers secret detection, pattern-based SAST, dependency CVEs, IaC misconfigs, container scanning, deep taint analysis, and multi-engine sweeps. Use when performing security scans, vulnerability assessments, code security reviews, secret detection, dependency audits, or CI/CD security gate setup.
---

# Secure Code Analysis & Review

Five-tool layered security scanning: Semgrep (patterns), Gitleaks (secrets), Trivy (deps/IaC/containers), CodeQL (taint analysis), Horusec (multi-engine sweep).

## Layered Defense Model

```
Layer 1: SECRETS      → Gitleaks (API keys, passwords, tokens)
Layer 2: PATTERNS     → Semgrep (known vulnerability patterns)
Layer 3: DEPENDENCIES → Trivy SCA (CVEs in libraries)
Layer 4: MISCONFIGS   → Trivy IaC (Terraform, K8s, Docker)
Layer 5: CONTAINERS   → Trivy Image (base image vulns)
Layer 6: DATA FLOW    → CodeQL (taint analysis, attack chains)
Layer 7: FULL SWEEP   → Horusec (15+ engines, maximum coverage)
```

## Tool Roles

| Tool | Speed | Depth | Best For |
|---|---|---|---|
| **Semgrep** | ⚡ Seconds | Medium | Code-level vulns, custom rules, CI/CD gates |
| **Gitleaks** | ⚡ Seconds | Shallow | Hardcoded keys, tokens, passwords |
| **Trivy** | ⚡ Sec–Min | Medium | Dependency CVEs, container misconfigs, IaC drift |
| **CodeQL** | 🐢 Minutes | Deep | Taint chains, data flow, complex attack paths |
| **Horusec** | 🐢 Minutes | Broad | Maximum coverage, runs 15+ scanners at once |

## Quick Start

### Full Security Scan (All Layers)

```bash
# End-to-end orchestrated scan with results aggregation
bash scripts/secure-scan.sh /path/to/project

# Quick scan — fast layers only (secrets + patterns + deps)
bash scripts/secure-scan.sh /path/to/project --layers quick

# CI gate — fail on any HIGH/CRITICAL finding
bash scripts/secure-scan.sh /path/to/project --ci --severity high,critical

# Specific layers
bash scripts/secure-scan.sh /path/to/project --layers secrets,patterns,deps

# JSON output for downstream processing
bash scripts/secure-scan.sh /path/to/project --format json --output results.json
```

### Individual Tool Quick Commands

```bash
# Secrets (always scan first)
gitleaks detect --source /path/to/project -v

# Patterns (fast, catches common vulns)
semgrep --config auto --exclude "node_modules,vendor,.git,dist,build" /path/to/project

# Dependencies + IaC + Secrets
trivy fs --scanners vuln,secret,misconfig /path/to/project

# Deep analysis (slowest, catches data flow)
codeql database create /tmp/codeql-db --language=javascript --overwrite /path/to/project
codeql database analyze /tmp/codeql-db --format=sarif-latest --output=results.sarif

# Full sweep (all engines)
horusec start -p /path/to/project --disable-docker -t 600
```

## Decision Matrix

| Scenario | Primary Tool | Secondary | Why |
|---|---|---|---|
| Quick PR check (<30s) | Semgrep + Gitleaks | — | Fastest, catches most common issues |
| Pre-merge security gate | Semgrep + Gitleaks + Trivy | — | Patterns, secrets, dependencies |
| Full security audit | All 5 tools | — | Maximum coverage |
| Hardcoded secrets | Gitleaks | Trivy `--scanners secret` | Purpose-built for this |
| Dependency CVEs | Trivy | — | Best SCA coverage |
| Container security | Trivy image | — | Purpose-built for images |
| IaC misconfigs | Trivy `--scanners misconfig` | — | Best Terraform/K8s/Docker |
| Deep taint analysis | CodeQL | — | Only tool tracking data flow across functions |
| Maximum coverage | Horusec | — | Runs 15+ engines |
| Monorepo 5+ languages | Semgrep + Trivy + Horusec | — | Broad language coverage |

## Scanning Workflow

Always scan in this order — secrets first because leaked credentials require immediate rotation:

```
1. Gitleaks    → If secrets found: STOP, rotate credentials, then continue
2. Semgrep     → Fix ERROR-severity findings before merge
3. Trivy       → Update HIGH/CRITICAL dependency CVEs
4. CodeQL      → Run on PRs touching security-sensitive code (auth, input handling)
5. Horusec     → Weekly full sweep to catch what others miss
```

### Per-Project Profiles

| Project Type | Layers | Commands |
|---|---|---|
| **Node.js/TS** | secrets → patterns → deps | `gitleaks detect --source . --no-git` → `semgrep --config p/javascript --config p/owasp-top-ten --exclude "node_modules,dist" .` → `trivy fs --scanners vuln --skip-dirs node_modules .` |
| **Python** | secrets → patterns → deps → deep | `gitleaks detect --source . --no-git` → `semgrep --config p/python --config p/security-audit --exclude "venv,.venv,__pycache__" .` → `trivy fs --scanners vuln .` → CodeQL python-queries:Security |
| **Go** | secrets → patterns → deps → deep | `gitleaks detect --source . --no-git` → `semgrep --config p/go --config p/security-audit --exclude "vendor" .` → `trivy fs --scanners vuln .` → CodeQL go-queries:Security |
| **Docker/Container** | secrets → IaC → image | `gitleaks detect --source . --no-git` → `trivy config --severity HIGH,CRITICAL .` → `trivy image --severity HIGH,CRITICAL myapp:latest` |
| **Monorepo** | secrets → all patterns → all deps → full sweep | `gitleaks detect --source . --no-git` → `semgrep --config auto --exclude "node_modules,vendor,.git" .` → `trivy fs --scanners vuln,secret,misconfig .` → `horusec start -p . --disable-docker` |

## Severity Actions

| Severity | Action |
|---|---|
| **CRITICAL** | Fix immediately, block deployment |
| **HIGH** | Fix before next release |
| **MEDIUM** | Fix within sprint, add to backlog |
| **LOW** | Fix when convenient |
| **INFO** | Review, no action required |

## Safety Rules

1. **NEVER commit real API keys, passwords, or tokens** — even in test files
2. **Rotate any credential found by Gitleaks** — do not just delete from code
3. **Do not suppress findings without justification** — document why in comments or config
4. **Run scans BEFORE merging to main** — not after
5. **Do not skip CodeQL because it's slow** — it catches what Semgrep misses (taint chains)
6. **Review all CRITICAL/HIGH findings** — do not auto-dismiss
7. **Keep rule configs in version control** — `.gitleaks.toml`, custom Semgrep YAML, `.trivyignore`
8. **Run secret detection on git history** — not just current code
9. **Never expose scan results publicly** — they contain vulnerability details attackers can use

## False Positive Suppression

```bash
# Semgrep — inline suppression
# nosemgrep: <rule-id>

# Gitleaks — .gitleaks.toml allowlist
# [[allowlist]]
# paths = ['''tests/test_keys.py''']

# Trivy — .trivyignore
# CVE-2024-XXXX # reason for acceptance

# CodeQL — inline suppression
# codeql[python/clear-text-logging] — suppressed: test fixture

# Horusec — .horusec-config.json
# "horusecCliFalsePositiveHashes": ["<hash>"]
```

## References

- [references/tool-commands.md](references/tool-commands.md) — Complete command reference for all 5 tools (Semgrep, Gitleaks, Trivy, CodeQL, Horusec)
- [references/ci-cd-integration.md](references/ci-cd-integration.md) — GitHub Actions, GitLab CI, and pre-commit hook configurations
- [references/custom-rules.md](references/custom-rules.md) — Custom Semgrep rules, Gitleaks config, and Trivy ignore files
- [references/interpretation-guide.md](references/interpretation-guide.md) — Results aggregation, severity interpretation, and report generation
- [references/project-profiles.md](references/project-profiles.md) — Language-specific scanning profiles and troubleshooting