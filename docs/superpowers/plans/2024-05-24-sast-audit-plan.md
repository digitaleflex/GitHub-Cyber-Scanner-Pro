# SAST Security Audit Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a comprehensive SAST security audit (Trivy + Gitleaks) with automated verdict calculation and persistence.

**Architecture:** Enhancement of the `SecurityAnalyzer` class to support multi-engine scanning and deep result aggregation, integrated into a Celery task.

**Tech Stack:** Python, Docker, Trivy, Gitleaks, Celery, PostgreSQL.

---

### Task 1: Update Dockerfile with Security Binaries

**Files:**
- Modify: `Dockerfile`

- [ ] **Step 1: Add Trivy and Gitleaks installation steps**

```dockerfile
# (Inside Dockerfile, after installing system dependencies)
# Installer Trivy
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Installer Gitleaks
RUN curl -L https://github.com/gitleaks/gitleaks/releases/download/v8.18.2/gitleaks_8.18.2_linux_x64.tar.gz -o gitleaks.tar.gz \
    && tar -xzf gitleaks.tar.gz gitleaks \
    && mv gitleaks /usr/local/bin/ \
    && rm gitleaks.tar.gz
```

- [ ] **Step 2: Build the image (dry run/simulated)**
Since I'm in a CLI environment, I won't actually build the image, but I verify the Dockerfile syntax.

### Task 2: Database Schema and Functionality

**Files:**
- Modify: `src/database.py`

- [ ] **Step 1: Add new columns to `init_db` migration**

```python
    try:
        cursor.execute("ALTER TABLE repositories ADD COLUMN IF NOT EXISTS verdict_securite VARCHAR(20) DEFAULT 'NON_AUDITE';")
        cursor.execute("ALTER TABLE repositories ADD COLUMN IF NOT EXISTS rapport_audit JSONB;")
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.warning(f"⚠️ Erreur migration colonnes SAST repositories : {e}")
```

- [ ] **Step 2: Implement `save_security_audit`**

```python
def save_security_audit(repo_id, verdict, raw_report_json):
    """Enregistre le résultat de l'audit SAST dans PostgreSQL."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE repositories SET verdict_securite = %s, rapport_audit = %s WHERE id = %s",
            (verdict, psycopg2.extras.Json(raw_report_json), repo_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"❌ Erreur save_security_audit: {e}")
        return False
```

### Task 3: Refactor SecurityAnalyzer

**Files:**
- Modify: `src/security_analyzer.py`

- [ ] **Step 1: Implement `run_trivy`**

```python
    def run_trivy(self, path):
        """Exécute Trivy sur le système de fichiers."""
        try:
            logging.info(f"🛡️ Exécution de Trivy sur {path}...")
            cmd = ["trivy", "fs", "--format", "json", "--quiet", path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            try:
                data = json.loads(result.stdout)
                return {
                    "status": "success",
                    "results": data.get("Results", [])
                }
            except:
                return {"status": "error", "reason": "Failed to parse Trivy output"}
        except Exception as e:
            logging.error(f"❌ Erreur Trivy : {e}")
            return {"status": "error", "reason": str(e)}
```

- [ ] **Step 2: Implement `run_gitleaks`**

```python
    def run_gitleaks(self, path):
        """Exécute Gitleaks pour détecter des secrets."""
        try:
            logging.info(f"🛡️ Exécution de Gitleaks sur {path}...")
            # On utilise un fichier temporaire pour le rapport car Gitleaks ne sort pas le JSON directement sur stdout facilement avec toutes les versions
            report_file = os.path.join(self.work_dir, f"gitleaks_{os.urandom(4).hex()}.json")
            cmd = ["gitleaks", "detect", "--source", path, "--format", "json", "--report-path", report_file]
            
            # Gitleaks retourne 1 si des secrets sont trouvés, on ignore le exit code
            subprocess.run(cmd, capture_output=True)
            
            if os.path.exists(report_file):
                with open(report_file, 'r') as f:
                    data = json.load(f)
                os.remove(report_file)
                return {
                    "status": "success",
                    "findings": data
                }
            return {"status": "success", "findings": []}
        except Exception as e:
            logging.error(f"❌ Erreur Gitleaks : {e}")
            return {"status": "error", "reason": str(e)}
```

- [ ] **Step 3: Update `analyze_repository` with new engines and improved verdict**

```python
    def analyze_repository(self, repo_url):
        """Workflow complet d'analyse SAST avec multi-moteurs."""
        temp_path = os.path.join(self.work_dir, f"scan_{os.urandom(4).hex()}")

        try:
            if not self.clone_repo(repo_url, temp_path):
                return {"verdict": "ERROR", "reason": "Cloning failed"}

            bandit_res = self.run_bandit(temp_path)
            semgrep_res = self.run_semgrep(temp_path)
            trivy_res = self.run_trivy(temp_path)
            gitleaks_res = self.run_gitleaks(temp_path)

            # Calcul du verdict
            critical_count = 0
            high_count = 0
            secrets_count = 0

            # Gitleaks
            if gitleaks_res.get("status") == "success":
                secrets_count = len(gitleaks_res.get("findings", []))

            # Bandit
            if bandit_res.get("status") == "success":
                for issue in bandit_res["results"]:
                    if issue["issue_severity"] == "HIGH": high_count += 1

            # Semgrep
            if semgrep_res.get("status") == "success":
                for issue in semgrep_res["results"]:
                    extra = issue.get("extra", {})
                    severity = extra.get("severity", "")
                    if severity == "ERROR": critical_count += 1
                    elif severity == "WARNING": high_count += 1

            # Trivy
            if trivy_res.get("status") == "success":
                for target in trivy_res.get("results", []):
                    for vuln in target.get("Vulnerabilities", []):
                        sev = vuln.get("Severity", "")
                        if sev == "CRITICAL": critical_count += 1
                        elif sev == "HIGH": high_count += 1

            if secrets_count > 0 or critical_count > 0:
                verdict = "CRITIQUE"
            elif high_count > 0:
                verdict = "SUSPECT"
            else:
                verdict = "SAIN"

            return {
                "verdict": verdict,
                "stats": {
                    "critical": critical_count,
                    "high": high_count,
                    "secrets": secrets_count
                },
                "bandit": bandit_res,
                "semgrep": semgrep_res,
                "trivy": trivy_res,
                "gitleaks": gitleaks_res
            }
```

### Task 4: Celery Task Wiring

**Files:**
- Modify: `src/tasks.py`

- [ ] **Step 1: Import SecurityAnalyzer and add `task_security_audit`**

```python
from security_analyzer import SecurityAnalyzer

@app.task(name="task_security_audit")
def task_security_audit(repo_url, repo_id):
    """Effectue un audit de sécurité complet et sauvegarde le résultat."""
    logging.info(f"🛡️ [Celery] Début de l'audit sécurité pour {repo_id}")
    try:
        analyzer = SecurityAnalyzer()
        report = analyzer.analyze_repository(repo_url)
        
        # Sauvegarder en base
        database.save_security_audit(repo_id, report["verdict"], report)
        
        return f"✅ Audit terminé pour {repo_id} : Verdict {report['verdict']}"
    except Exception as e:
        logging.error(f"❌ Erreur audit sécurité pour {repo_id}: {e}")
        return str(e)
```

### Task 5: Verification

- [ ] **Step 1: Check Python syntax of all modified files**
Run: `python -m py_compile src/*.py`
Expected: No errors.
