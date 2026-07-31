# Project-Specific Scanning Profiles

Language and framework-specific scanning commands and troubleshooting.

## Node.js / TypeScript Project

```bash
# Layer 1: Secrets
gitleaks detect --source . --no-git

# Layer 2: Patterns (JS/TS focused)
semgrep --config p/javascript --config p/owasp-top-ten --config p/secrets \
  --exclude "node_modules,dist,.next,build" .

# Layer 3: Dependencies
trivy fs --scanners vuln --skip-dirs node_modules .

# Layer 4: CodeQL (if needed for deep analysis)
codeql database create /tmp/codeql-db --language=javascript --overwrite .
codeql database analyze /tmp/codeql-db codeql/javascript-queries:Security \
  --format=sarif-latest --output=codeql.sarif

# Layer 5: Full sweep
horusec start -p . --disable-docker -i "node_modules,dist,.next,build" -t 300
```

### Common Node.js Findings

| Finding | Tool | Fix |
|---|---|---|
| Prototype pollution | Semgrep | Update affected packages, use `Object.create(null)` |
| Path traversal in `express.static` | Semgrep | Validate path with `path.resolve` and `startsWith` |
| XSS via `innerHTML` | Semgrep | Use `textContent` or DOMPurify |
| Prototype pollution in lodash | Trivy | `npm update lodash` |
| ReDoS in validator | Trivy | Update validator package |

---

## Python Project

```bash
# Layer 1: Secrets
gitleaks detect --source . --no-git

# Layer 2: Patterns + Bandit-style rules
semgrep --config p/python --config p/security-audit --config p/secrets \
  --exclude "venv,.venv,__pycache__,dist,egg-info" .

# Layer 3: Dependencies
trivy fs --scanners vuln .

# Layer 4: CodeQL
codeql database create /tmp/codeql-db --language=python --overwrite .
codeql database analyze /tmp/codeql-db codeql/python-queries:Security \
  --format=sarif-latest --output=codeql.sarif

# Layer 5: Full sweep
horusec start -p . --disable-docker -i "venv,.venv,__pycache__,dist" -t 300
```

### Common Python Findings

| Finding | Tool | Fix |
|---|---|---|
| SQL injection via f-strings | Semgrep | Use parameterized queries |
| `eval()` with dynamic input | Semgrep/CodeQL | Replace with `ast.literal_eval()` |
| Hardcoded passwords | Gitleaks | Use environment variables |
| Pickle deserialization | Semgrep | Use `json` or `msgpack` |
| Flask debug mode | Semgrep | Set `debug=False` in production |

---

## Go Project

```bash
# Layer 1: Secrets
gitleaks detect --source . --no-git

# Layer 2: Patterns + Go-specific
semgrep --config p/go --config p/security-audit \
  --exclude "vendor" .

# Layer 3: Dependencies
trivy fs --scanners vuln .

# Layer 4: CodeQL
codeql database create /tmp/codeql-db --language=go --overwrite .
codeql database analyze /tmp/codeql-db codeql/go-queries:Security \
  --format=sarif-latest --output=codeql.sarif

# Layer 5: Full sweep
horusec start -p . --disable-docker -i "vendor" -t 300
```

---

## Docker / Container Project

```bash
# Layer 1: Secrets
gitleaks detect --source . --no-git

# Layer 2: Dockerfile misconfigs
trivy config --severity HIGH,CRITICAL .

# Layer 3: Base image vulnerabilities
trivy image --severity HIGH,CRITICAL myapp:latest

# Layer 4: IaC (K8s, Terraform)
trivy fs --scanners misconfig .

# Layer 5: Full scan
trivy fs --scanners vuln,secret,misconfig .
```

### Common Container Findings

| Finding | Tool | Fix |
|---|---|---|
| Running as root | Trivy | Add `USER appuser` to Dockerfile |
| No health check | Trivy | Add `HEALTHCHECK` instruction |
| Large attack surface | Trivy | Use `distroless` or `alpine` base images |
| Hardcoded secrets in ENV | Gitleaks | Use Docker secrets or runtime env vars |
| Outdated base image | Trivy | `docker pull` to update, or pin specific digest |

---

## Multi-Language Monorepo

```bash
# Layer 1: Secrets
gitleaks detect --source . --no-git

# Layer 2: All patterns (auto-detects languages)
semgrep --config auto --exclude "node_modules,vendor,.git,dist,build" .

# Layer 3: All dependencies + IaC
trivy fs --scanners vuln,secret,misconfig .

# Layer 4: Horusec full sweep (catches what others miss)
horusec start -p . --disable-docker -t 600
```

For CodeQL, create separate databases per language and analyze each:

```bash
# Detect languages in project
LANGS=$(codeql resolve languages | cut -f1)

# Create and analyze database for each language
for lang in javascript python go; do
  codeql database create /tmp/codeql-db-$lang --language=$lang --overwrite .
  codeql database analyze /tmp/codeql-db-$lang \
    codeql/${lang}-queries:Security \
    --format=sarif-latest \
    --output=codeql-$lang.sarif
done
```

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Semgrep too slow | Scanning huge directories | `--exclude "node_modules,vendor,build,dist,.git"` |
| Semgrep too many findings | `--config auto` is broad | Use specific rule sets: `p/security-audit` |
| Gitleaks false positives | Test fixtures look like real keys | Add `.gitleaks.toml` allowlist |
| Trivy can't find lockfile | No lockfile committed | Generate: `npm install --package-lock-only` / `pip freeze > requirements.txt` |
| CodeQL database creation fails | Build fails or missing deps | Install build dependencies, run from project root |
| CodeQL out of memory | Large codebase | Add `--threads=2` and increase JVM heap: `_JAVA_OPTIONS=-Xmx8G` |
| Horusec Docker errors | Docker not running or not installed | Use `--disable-docker` flag (stand-alone mode) |
| Horusec timeout | Large project | Increase `-t` value (default 600s) |
| Tool not found | Not on PATH | Add install location to PATH in `~/.zshrc` |
| Trivy DB download slow | First run downloads vulnerability DB | Re-run — DB is cached locally after first download |