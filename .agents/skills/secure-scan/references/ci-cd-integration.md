# CI/CD Integration Reference

Security scanning configurations for GitHub Actions, GitLab CI, and pre-commit hooks.

## GitHub Actions — Full Security Scan

```yaml
name: Security Scan
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Weekly Monday 6 AM

jobs:
  secrets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: gitleaks/gitleaks-action@v2

  semgrep:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/owasp-top-ten
            p/secrets

  trivy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Trivy filesystem scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          scan-ref: .
          severity: CRITICAL,HIGH
          exit-code: 1

  codeql:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: javascript, python
      - uses: github/codeql-action/analyze@v3
```

### GitHub Actions — Lightweight PR Check (Fast)

```yaml
name: PR Security Check
on:
  pull_request:
    branches: [main]

jobs:
  quick-scan:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }

      - name: Gitleaks
        uses: gitleaks/gitleaks-action@v2

      - name: Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: p/security-audit p/secrets

      - name: Trivy FS
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          scan-ref: .
          severity: CRITICAL,HIGH
          exit-code: 1
```

---

## GitLab CI

```yaml
stages:
  - security

semgrep:
  stage: security
  image: returntocorp/semgrep:latest
  script:
    - semgrep --config auto --json --output semgrep-results.json .
  artifacts:
    paths: [semgrep-results.json]
    when: always

trivy-scan:
  stage: security
  image: aquasec/trivy:latest
  script:
    - trivy fs --severity HIGH,CRITICAL --exit-code 1 .
  allow_failure: false

gitleaks:
  stage: security
  image: zricethezav/gitleaks:latest
  script:
    - gitleaks detect --source . --exit-code 1
  allow_failure: false

trivy-image:
  stage: security
  image: aquasec/trivy:latest
  script:
    - trivy image --severity HIGH,CRITICAL --exit-code 1 $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main
```

---

## Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks

  - repo: https://github.com/returntocorp/semgrep
    rev: v1.157.0
    hooks:
      - id: semgrep
        args: ['--config', 'p/security-audit', '--config', 'p/secrets', '--error']
```

### Local Pre-commit (Without Remote Repos)

```yaml
# .pre-commit-config.yaml — local tools
repos:
  - repo: local
    hooks:
      - id: gitleaks
        name: gitleaks
        entry: gitleaks detect --source . --staged
        language: system
        pass_filenames: false

      - id: trivy-fs
        name: trivy filesystem
        entry: trivy fs --scanners vuln,secret --severity HIGH,CRITICAL --exit-code 1 .
        language: system
        pass_filenames: false

      - id: semgrep
        name: semgrep
        entry: semgrep --config p/security-audit --config p/secrets --error
        language: system
        types: [python, javascript, typescript, go, java]
```

---

## Suggested Scan Cadence

```
┌─────────────┬──────────────────────────────────────────────────────────────┐
│ DAILY       │ gitleaks protect --staged                                   │
│ (pre-commit)│ semgrep --config p/security-audit --error .                │
├─────────────┼──────────────────────────────────────────────────────────────┤
│ PER MERGE   │ gitleaks detect --source . --exit-code 1                   │
│ (CI/CD gate)│ semgrep --config auto --error --exclude "node_modules" .   │
│             │ trivy fs --severity HIGH,CRITICAL --exit-code 1 .          │
├─────────────┼──────────────────────────────────────────────────────────────┤
│ WEEKLY      │ gitleaks detect --source .                              │
│ (full audit)│ semgrep --config p/security-audit --config p/owasp-top-ten .│
│             │ trivy fs --scanners vuln,secret,misconfig .               │
│             │ codeql database create + analyze (primary language)        │
│             │ horusec start -p . --disable-docker -t 600                │
├─────────────┼──────────────────────────────────────────────────────────────┤
│ MONTHLY     │ All 5 tools + review custom rules + update configs        │
│ (deep review)│ semgrep --config auto --dry-run . (check for new rules)   │
│             │ trivy image --reset (update vulnerability DB)             │
│             │ codeql resolve packs (check for new query packs)           │
└─────────────┴──────────────────────────────────────────────────────────────┘
```