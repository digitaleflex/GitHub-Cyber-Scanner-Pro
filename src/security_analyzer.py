import json
import logging
import os
import shutil
import subprocess # nosec B404
import tempfile

from git import Repo

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class SecurityAnalyzer:
    def __init__(self, work_dir=None):
        self.work_dir = work_dir if work_dir else tempfile.gettempdir()

    def clone_repo(self, repo_url, target_path):
        """Clone le dépôt avec une profondeur de 1 (sans historique)."""
        try:
            logging.info(f"📂 Clonage éphémère de {repo_url} vers {target_path}...")
            Repo.clone_from(repo_url, target_path, depth=1)
            return True
        except Exception as e:
            logging.error(f"❌ Erreur lors du clonage : {e}")
            return False

    def run_bandit(self, path):
        """Exécute Bandit sur le code Python."""
        try:
            logging.info(f"🛡️ Exécution de Bandit sur {path}...")
            # On cherche les fichiers .py pour voir si ça vaut le coup
            py_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(path) for f in filenames if f.endswith('.py')]
            if not py_files:
                return {"status": "skipped", "reason": "No Python files found"}

            cmd = ["bandit", "-r", path, "-f", "json", "-q"]
            result = subprocess.run(cmd, capture_output=True, text=True) # nosec B603

            # Bandit retourne 1 si des vulnérabilités sont trouvées, on ignore le code de retour
            try:
                data = json.loads(result.stdout)
                return {
                    "status": "success",
                    "results": data.get("results", []),
                    "metrics": data.get("metrics", {})
                }
            except:
                return {"status": "error", "reason": "Failed to parse Bandit output"}
        except Exception as e:
            logging.error(f"❌ Erreur Bandit : {e}")
            return {"status": "error", "reason": str(e)}

    def run_semgrep(self, path):
        """Exécute Semgrep avec les règles de sécurité par défaut."""
        try:
            logging.info(f"🛡️ Exécution de Semgrep sur {path}...")
            cmd = ["semgrep", "--config=auto", "--json", path, "--quiet"]
            result = subprocess.run(cmd, capture_output=True, text=True) # nosec B603

            try:
                data = json.loads(result.stdout)
                return {
                    "status": "success",
                    "results": data.get("results", [])
                }
            except:
                return {"status": "error", "reason": "Failed to parse Semgrep output"}
        except Exception as e:
            logging.error(f"❌ Erreur Semgrep : {e}")
            return {"status": "error", "reason": str(e)}

    def analyze_repository(self, repo_url):
        """Workflow complet d'analyse SAST."""
        temp_path = os.path.join(self.work_dir, f"scan_{os.urandom(4).hex()}")

        try:
            if not self.clone_repo(repo_url, temp_path):
                return {"verdict": "ERROR", "reason": "Cloning failed"}

            bandit_res = self.run_bandit(temp_path)
            semgrep_res = self.run_semgrep(temp_path)

            # Calcul du verdict
            critical_count = 0
            high_count = 0

            # Analyse Bandit
            if bandit_res.get("status") == "success":
                for issue in bandit_res["results"]:
                    if issue["issue_severity"] == "HIGH": high_count += 1

            # Analyse Semgrep
            if semgrep_res.get("status") == "success":
                for issue in semgrep_res["results"]:
                    extra = issue.get("extra", {})
                    severity = extra.get("severity", "")
                    if severity == "ERROR": critical_count += 1
                    elif severity == "WARNING": high_count += 1

            if critical_count > 0:
                verdict = "CRITIQUE"
            elif high_count > 0:
                verdict = "SUSPECT"
            else:
                verdict = "SAIN"

            return {
                "verdict": verdict,
                "stats": {
                    "critical": critical_count,
                    "high": high_count
                },
                "bandit": bandit_res,
                "semgrep": semgrep_res
            }

        finally:
            if os.path.exists(temp_path):
                # Sous Windows, les fichiers .git sont souvent en lecture seule
                def onerror(func, path, exc_info):
                    import stat
                    if not os.access(path, os.W_OK):
                        os.chmod(path, stat.S_IWUSR)
                        func(path)
                    else:
                        raise
                shutil.rmtree(temp_path, onerror=onerror)
                logging.info(f"🧹 Nettoyage du dossier temporaire {temp_path}")

if __name__ == "__main__":
    analyzer = SecurityAnalyzer()
    # Test sur un petit repo
    # res = analyzer.analyze_repository("https://github.com/test/repo")
    # print(json.dumps(res, indent=2))
