# Design Document: SAST Security Audit Integration

## Goal
Implement a robust Static Application Security Testing (SAST) pipeline within the CyberScan Hub project using Trivy and Gitleaks, alongside existing Bandit and Semgrep scans.

## Architecture
The system follows a worker-based architecture where Celery tasks trigger the security analyzer.

### Components
1. **Dockerized Environment**: Container pre-loaded with all security binaries.
2. **SecurityAnalyzer (src/security_analyzer.py)**: Orchestrator for multiple scan engines.
3. **Database (src/database.py)**: PostgreSQL storage for audit results.
4. **Celery Task (src/tasks.py)**: Asynchronous execution of the audit.

## Data Flow
1. `task_security_audit` is triggered with a repository URL.
2. `SecurityAnalyzer` clones the repository into a temporary directory.
3. Multiple scans are executed:
    - **Bandit**: Python-specific vulnerabilities.
    - **Semgrep**: Generic code patterns.
    - **Trivy**: Vulnerabilities in dependencies and configuration.
    - **Gitleaks**: Secret detection in git history/files.
4. `SecurityAnalyzer` aggregates findings and determines a final `verdict`.
5. Results are saved to PostgreSQL.
6. Temporary directory is deleted.

## Tools Configuration
- **Trivy**: Running in filesystem mode (`trivy fs`).
- **Gitleaks**: Running in detect mode (`gitleaks detect`).

## Verdict Algorithm
- **CRITIQUE**: 
    - Findings by Gitleaks (any secret).
    - Findings by Trivy/Semgrep/Bandit with severity "CRITICAL".
- **SUSPECT**:
    - Findings with severity "HIGH".
- **SAIN**:
    - No CRITICAL or HIGH findings.

## Database Schema Update
Table `repositories` will be updated with:
- `verdict_securite` (VARCHAR(20))
- `rapport_audit` (JSONB)
