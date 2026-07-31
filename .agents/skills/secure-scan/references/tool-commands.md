# Tool Commands Reference

Complete command reference for all five security scanning tools.

## Semgrep — Fast Pattern-Matching SAST

### Basic Scans

```bash
# Auto-detect best rules for the project
semgrep --config auto /path/to/project

# Specific rule sets
semgrep --config p/security-audit /path/to/project    # Security audit
semgrep --config p/owasp-top-ten /path/to/project     # OWASP Top 10
semgrep --config p/default /path/to/project           # Default rules
semgrep --config p/ci /path/to/project                 # CI-appropriate
semgrep --config p/secrets /path/to/project            # Secret detection

# Language-specific rules
semgrep --config p/javascript /path/to/project
semgrep --config p/python /path/to/project
semgrep --config p/go /path/to/project
semgrep --config p/java /path/to/project

# Combine multiple rule sets
semgrep --config p/security-audit --config p/owasp-top-ten /path/to/project

# Custom rules (YAML)
semgrep --config /path/to/custom-rules.yml /path/to/project
```

### Output Formats

```bash
semgrep --config auto --json /path/to/project          # JSON
semgrep --config auto --sarif /path/to/project         # SARIF (for GitHub)
semgrep --config auto --junit-xml /path/to/project     # JUnit XML
```

### Filtering & CI

```bash
# Exclude paths
semgrep --config auto --exclude "node_modules,vendor,.git,dist,build" /path/to/project

# CI mode — exit with error on findings
semgrep --config auto --error /path/to-project

# Severity filter
semgrep --config auto --severity ERROR --severity WARNING /path/to/project
```

---

## Gitleaks — Secret Detection

### Basic Scans

```bash
# Scan git repository (checks git history too)
gitleaks detect --source /path/to/project

# Scan directory without git
gitleaks detect --source /path/to/project --no-git

# Verbose output
gitleaks detect --source /path/to/project -v
```

### Output Formats

```bash
gitleaks detect --source /path/to/project --report-format json --report-path leaks.json
gitleaks detect --source /path/to/project --report-format sarif --report-path leaks.sarif
```

### Configuration

```bash
# Custom config (allowlists, custom patterns)
gitleaks detect --source /path/to/project --config /path/to/.gitleaks.toml

# Pre-commit hook mode — only check staged changes
gitleaks protect --source /path/to/project --staged

# Exit code: 1 = leaks found, 0 = clean
gitleaks detect --source /path/to/project --exit-code 1
```

---

## Trivy — All-in-One Scanner

### Filesystem Scans

```bash
# Full filesystem scan (code + dependencies + secrets + misconfigs)
trivy fs /path/to/project

# Specific scanners only
trivy fs --scanners vuln /path/to/project              # Dependency CVEs only
trivy fs --scanners secret /path/to/project            # Secrets only
trivy fs --scanners misconfig /path/to/project          # IaC misconfigs only
trivy fs --scanners vuln,secret,misconfig /path/to/project

# Severity filtering
trivy fs --severity HIGH,CRITICAL /path/to/project
```

### Output Formats

```bash
trivy fs --format json /path/to/project                 # JSON
trivy fs --format sarif /path/to/project                # SARIF
trivy fs --format table /path/to/project                # Table (default)
trivy fs --format spdx-json /path/to/project            # SPDX SBOM
```

### Container & K8s Scans

```bash
# Docker image scan
trivy image myapp:latest
trivy image --severity HIGH,CRITICAL myapp:latest
trivy image --ignore-unfixed myapp:latest               # Only show fixable vulns

# Kubernetes scan
trivy k8s --namespace default all

# Code-specific scanning (newer Trivy versions)
trivy code /path/to/project                            # SAST via Trivy
```

### Configuration

```bash
# Skip directories
trivy fs --skip-dirs node_modules,vendor /path/to/project

# Ignore file (suppress known false positives)
trivy fs --ignorefile .trivyignore /path/to/project
```

---

## CodeQL — Deep Semantic Analysis

### Database Creation (Required First Step)

```bash
# Create database for specific language
codeql database create /tmp/my-db --language=python /path/to/project
codeql database create /tmp/my-db --language=javascript /path/to/project
codeql database create /tmp/my-db --language=go /path/to/project
codeql database create /tmp/my-db --language=java /path/to/project
codeql database create /tmp/my-db --language=cpp /path/to/project
codeql database create /tmp/my-db --language=ruby /path/to/project
codeql database create /tmp/my-db --language=swift /path/to/project

# Overwrite existing database (for re-analysis)
codeql database create /tmp/my-db --language=python --overwrite /path/to/project
```

### Analysis

```bash
# Default security analysis
codeql database analyze /tmp/my-db --format=sarif-latest --output=results.sarif

# Language-specific security queries
codeql database analyze /tmp/my-db codeql/python-queries:Security --format=sarif-latest --output=results.sarif
codeql database analyze /tmp/my-db codeql/javascript-queries:Security --format=sarif-latest --output=results.sarif
codeql database analyze /tmp/my-db codeql/go-queries:Security --format=sarif-latest --output=results.sarif
codeql database analyze /tmp/my-db codeql/java-queries:Security --format=sarif-latest --output=results.sarif

# CSV output
codeql database analyze /tmp/my-db --format=csv --output=results.csv

# Parallelized analysis for large projects
codeql database analyze /tmp/my-db --threads=4 --format=sarif-latest --output=results.sarif
```

### Utilities

```bash
# List supported languages
codeql resolve languages

# List available query packs
codeql resolve packs

# Clean up database
codeql database cleanup /tmp/my-db
```

---

## Horusec — Multi-Engine Orchestrator

### Basic Scans

```bash
# Full scan — runs all 15+ engines
horusec start -p /path/to/project

# With timeout (default 600 seconds)
horusec start -p /path/to/project -t 300

# Stand-alone mode (no Docker required — uses bundled binaries)
horusec start -p /path/to/project --disable-docker
```

### Configuration

```bash
# Disable specific engines (useful when already ran separately)
horusec start -p /path/to/project --disable="SemgrepDocker,GitleaksDocker,TrivyDocker"

# Output formats
horusec start -p /path/to/project -o json               # JSON
horusec start -p /path/to/project -o sarif                # SARIF

# Ignore specific paths
horusec start -p /path/to/project -i "node_modules,vendor,.git,dist"

# Informational severity only (don't fail on warnings)
horusec start -p /path/to/project --information-severity

# Force retry on failed tools
horusec start -p /path/to/project --force-retry
```

---

## Tool Comparison Summary

| Dimension | Semgrep | Gitleaks | Trivy | CodeQL | Horusec |
|---|---|---|---|---|---|
| Speed | ⚡⚡⚡ | ⚡⚡⚡ | ⚡⚡ | 🐢 | 🐢 |
| Depth | Medium | Shallow | Medium | Deep | Broad |
| Code vulnerabilities | ✅✅✅ | — | ✅ | ✅✅✅ | ✅✅ |
| Secret detection | ✅ | ✅✅✅ | ✅✅ | — | ✅✅ |
| Dependency CVEs | ✅ (Pro) | — | ✅✅✅ | — | ✅✅ |
| Container scanning | — | — | ✅✅✅ | — | — |
| IaC misconfigs | — | — | ✅✅✅ | — | ✅ |
| Taint analysis | Limited | — | — | ✅✅✅ | ✅ (via engines) |
| Custom rules | ✅✅✅ | ✅✅ | ✅ | ✅✅ | ✅ |
| CI/CD ready | ✅✅✅ | ✅✅✅ | ✅✅✅ | ✅✅ | ✅✅ |
| Needs build | No | No | No | Yes | No |
| Needs Docker | No | No | No | No | Optional |
| Languages | 40+ | Any | 30+ | 15+ | 18+ |
| License | LGPL 2.1 | MIT | Apache 2.0 | MIT | Apache 2.0 |