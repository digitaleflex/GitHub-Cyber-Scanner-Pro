# Custom Rules Reference

Custom rule configurations for Semgrep, Gitleaks, and Trivy.

## Semgrep Custom Rules

### Rule Structure

```yaml
rules:
  - id: rule-id
    patterns:
      - pattern: |
          $MATCH
      - pattern-not: |
          $EXCLUSION
    message: "Description of the finding"
    severity: ERROR  # ERROR, WARNING, INFO
    languages: [python, javascript, go]
```

### Security Audit Rules

```yaml
# custom-security-rules.yml
rules:
  # === PYTHON ===

  - id: hardcoded-database-password
    patterns:
      - pattern: |
          $DB = SQLAlchemy($URL)
      - pattern-regex: 'password=[^$][^&]+'
    message: "Hardcoded database password detected. Use environment variable."
    severity: ERROR
    languages: [python]

  - id: unsafe-eval
    patterns:
      - pattern: eval($INPUT)
      - pattern-not: eval("...")
    message: "Avoid eval() with dynamic input — code injection risk"
    severity: ERROR
    languages: [python, javascript]

  - id: unparameterized-sql
    patterns:
      - pattern: |
          cursor.execute(f"...")
    message: "Use parameterized queries to prevent SQL injection"
    severity: ERROR
    languages: [python]

  - id: debug-endpoint-in-prod
    patterns:
      - pattern: app.run(debug=True)
    message: "Debug mode enabled — disable in production"
    severity: WARNING
    languages: [python]

  # === JAVASCRIPT / TYPESCRIPT ===

  - id: missing-https
    patterns:
      - pattern: fetch("http://...")
    message: "Use HTTPS instead of HTTP for API calls"
    severity: WARNING
    languages: [javascript, typescript]

  - id: innerhtml-assignment
    patterns:
      - pattern: $EL.innerHTML = $INPUT
      - pattern-not: $EL.innerHTML = "<safe-string>"
    message: "innerHTML with dynamic content is an XSS risk — use textContent or DOMPurify"
    severity: ERROR
    languages: [javascript, typescript]

  - id: exec-sync
    patterns:
      - pattern: require('child_process').execSync($CMD)
    message: "execSync with dynamic input is a command injection risk"
    severity: ERROR
    languages: [javascript]

  # === GO ===

  - id: go-sql-concat
    patterns:
      - pattern: |
          fmt.Sprintf("SELECT ... WHERE ... = '%s'", $VAL)
    message: "Use parameterized queries instead of string concatenation for SQL"
    severity: ERROR
    languages: [go]

  - id: go-http-without-timeout
    patterns:
      - pattern: |
          http.Client{$X}
      - pattern-not: |
          http.Client{$X, Timeout: $T}
    message: "http.Client without timeout can hang indefinitely"
    severity: WARNING
    languages: [go]
```

### Using Custom Rules

```bash
# Single custom rule file
semgrep --config custom-security-rules.yml /path/to/project

# Mix custom with built-in
semgrep --config p/security-audit --config custom-security-rules.yml /path/to/project

# Test custom rules
semgrep --config custom-security-rules.yml --validate
```

---

## Gitleaks Custom Config

### Complete Configuration

```toml
# .gitleaks.toml

# Extend default rules
[extend]
useDefault = true

# Custom rules
[[rules]]
id = "neural-ai-api-key"
description = "Neural AI API Key"
regex = '''sk-nai-[a-zA-Z0-9]{32}'''
tags = ["key", "neural-ai"]

[[rules]]
id = "openrouter-key"
description = "OpenRouter API Key"
regex = '''sk-or-v1-[a-f0-9]{48}'''
tags = ["key", "openrouter"]

[[rules]]
id = "custom-bearer-token"
description = "Custom Bearer Token"
regex = '''Bearer [a-zA-Z0-9\-._~+/]+=*'''
tags = ["token", "bearer"]

[[rules]]
id = "internal-service-key"
description = "Internal Service Key"
regex = '''INT-[a-zA-Z0-9]{40}'''
tags = ["key", "internal"]

# Allowlist — suppress false positives
[[allowlist]]
regexes = [
    '''sk-nai-test-.*''',
    '''sk-or-v1-test-.*''',
    '''INT-test-.*'''
]
paths = [
    '''tests/.*''',
    '''fixtures/.*''',
    '''mocks/.*''',
    '''__mocks__/.*'''
]

# Commit-based allowlist (ignore specific commits)
[[allowlist]]
commits = [
    'abc123def456789012345678901234567890abcd',
]
```

### Using Custom Config

```bash
# Point to custom config
gitleaks detect --source . --config .gitleaks.toml

# Pre-commit with custom config
gitleaks protect --staged --config .gitleaks.toml
```

---

## Trivy Ignore File

### .trivyignore

```
# .trivyignore — accepted risks with justification
# Format: CVE-ID # Justification

# No fix available, internal network only
CVE-2024-1234

# Vendor confirmed false positive, tracking issue #5678
CVE-2024-5678

# Accepted: low severity, requires local access
CVE-2023-9012
```

### Trivy Config File

```yaml
# trivy.yaml — Trivy configuration
severity:
  - CRITICAL
  - HIGH

skip-dirs:
  - node_modules
  - vendor
  - .git
  - dist
  - build

 scanners:
  - vuln
  - secret
  - misconfig

format: table

# Vulnerability DB settings
db:
  skip-update: false
  repository: ghcr.io/aquasecurity/trivy-db

# Ignore specific CVEs
ignorefile: .trivyignore
```

### Using Trivy Config

```bash
# Auto-loads trivy.yaml from project root
trivy fs .

# Explicit config path
trivy fs --config /path/to/trivy.yaml .

# Generate SBOM
trivy fs --format spdx-json --output sbom.json .

# Scan specific Docker base images before building
trivy image node:20-alpine --severity HIGH,CRITICAL
trivy image python:3.12-slim --severity HIGH,CRITICAL
```