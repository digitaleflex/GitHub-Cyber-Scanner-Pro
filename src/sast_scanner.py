import json
import logging
import os
import subprocess
import tempfile
import time
from pathlib import Path

from src import database

logger = logging.getLogger(__name__)

VERDICT_SAIN = "Sain"
VERDICT_SUSPECT = "Suspect"
VERDICT_CRITIQUE = "Critique"

SEMGREP_CUSTOM_RULES = """
rules:
  - id: obfuscated-code-detection
    pattern-either:
      - pattern: eval($X)
      - pattern: exec($X)
      - pattern: base64.b64decode($X)
      - pattern: base64_decode($X)
      - pattern: str_rot13($X)
      - pattern: "pack('H*', $X)"
      - pattern: chr($X) + chr($Y)
    message: Code obfuscation detected (eval/exec/base64)
    severity: WARNING
    languages:
      - python
      - php
      - javascript
      - ruby

  - id: suspicious-ip-hardcoded
    pattern-regex: (?:[0-9]{1,3}\\.){3}[0-9]{1,3}
    message: Hardcoded IP address found
    severity: WARNING
    languages:
      - python
      - javascript
      - ruby
      - go
      - rust
      - java

  - id: crypto-weakness
    pattern-either:
      - pattern: hashlib.md5($X)
      - pattern: hashlib.sha1($X)
      - pattern: Crypto.Cipher.DES.new(...)
      - pattern: cryptography.hazmat.primitives.ciphers.algorithms.DES(...)
    message: Weak cryptographic algorithm detected
    severity: WARNING
    languages:
      - python

  - id: command-injection
    pattern-either:
      - pattern: os.system($X)
      - pattern: subprocess.call($X, shell=True)
      - pattern: subprocess.Popen($X, shell=True)
      - pattern: exec("..." + $X)
    message: Potential command injection
    severity: ERROR
    languages:
      - python
      - javascript
      - php
      - ruby
"""


def _clone_repo(url: str, target_dir: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--single-branch", url, target_dir],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            logger.warning(
                "Clone failed for %s: %s", url, result.stderr.strip()[:200]
            )
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.warning("Clone timed out for %s", url)
        return False
    except FileNotFoundError:
        logger.error("git not found in PATH")
        return False


def _run_bandit(target_dir: str) -> list[dict]:
    try:
        result = subprocess.run(
            ["bandit", "-r", "-f", "json", target_dir, "-q"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode not in (0, 1):
            logger.warning("Bandit returned unexpected code %d", result.returncode)
            return []
        if not result.stdout.strip():
            return []
        data = json.loads(result.stdout)
        return data.get("results", [])
    except json.JSONDecodeError:
        logger.warning("Bandit output not valid JSON")
        return []
    except subprocess.TimeoutExpired:
        logger.warning("Bandit timed out")
        return []
    except FileNotFoundError:
        logger.warning("Bandit not installed")
        return []


def _run_semgrep(target_dir: str) -> list[dict]:
    try:
        rules_path = os.path.join(target_dir, ".semgrep_custom_rules.yaml")
        with open(rules_path, "w") as f:
            f.write(SEMGREP_CUSTOM_RULES)

        result = subprocess.run(
            [
                "semgrep",
                "--config=auto",
                f"--config={rules_path}",
                "--json",
                "--quiet",
                target_dir,
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode not in (0, 1):
            logger.debug("Semgrep returned code %d: %s", result.returncode, result.stderr[:200])
            return []
        if not result.stdout.strip():
            return []
        data = json.loads(result.stdout)
        return data.get("results", [])
    except json.JSONDecodeError:
        logger.warning("Semgrep output not valid JSON")
        return []
    except subprocess.TimeoutExpired:
        logger.warning("Semgrep timed out")
        return []
    except FileNotFoundError:
        logger.warning("Semgrep not installed")
        return []


def _determine_verdict(
    bandit_results: list[dict], semgrep_results: list[dict]
) -> tuple[str, str]:
    all_issues = []

    for r in bandit_results:
        severity = (r.get("issue_severity") or "LOW").upper()
        text = r.get("issue_text") or r.get("test_name") or "Bandit finding"
        all_issues.append({"tool": "bandit", "severity": severity, "text": text})

    for r in semgrep_results:
        severity = (r.get("extra") or {}).get("severity", "WARNING").upper()
        text = (r.get("extra") or {}).get("message") or r.get("check_id") or "Semgrep finding"
        all_issues.append({"tool": "semgrep", "severity": severity, "text": text})

    if not all_issues:
        return VERDICT_SAIN, ""

    has_critical = any(
        i["severity"] in ("ERROR", "CRITICAL", "HIGH") for i in all_issues
    )
    has_warning = any(
        i["severity"] in ("WARNING", "MEDIUM") for i in all_issues
    )

    details = json.dumps(all_issues, indent=2, ensure_ascii=False)

    if has_critical:
        return VERDICT_CRITIQUE, details
    if has_warning:
        return VERDICT_SUSPECT, details

    return VERDICT_SAIN, details


def run_sast_on_repo(repo_id: str, full_name: str, repo_url: str) -> None:
    logger.info("🔍 SAST scan for %s...", full_name)

    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp(prefix="sast_")
        clone_target = os.path.join(tmpdir, "repo")

        if not _clone_repo(repo_url, clone_target):
            database.update_repo_security_verdict(repo_id, VERDICT_SAIN, "Clone failed, skipped")
            return

        bandit_results = _run_bandit(clone_target)
        semgrep_results = _run_semgrep(clone_target)

        verdict, details = _determine_verdict(bandit_results, semgrep_results)
        database.update_repo_security_verdict(repo_id, verdict, details)

        if verdict != VERDICT_SAIN:
            logger.info(
                "  → Verdict: %s for %s (%d bandit + %d semgrep issues)",
                verdict, full_name, len(bandit_results), len(semgrep_results),
            )
        else:
            logger.info("  → Verdict: %s for %s", verdict, full_name)

    except Exception as e:
        logger.error("SAST error for %s: %s", full_name, e)
        database.update_repo_security_verdict(repo_id, VERDICT_SUSPECT, f"Error: {e}")
    finally:
        if tmpdir and os.path.exists(tmpdir):
            subprocess.run(["rm", "-rf", tmpdir], capture_output=True, timeout=30)


def process_unscanned_repos(limit: int = 20) -> int:
    repos = database.get_repos_without_sast(limit)
    if not repos:
        return 0

    logger.info("🔬 SAST analysis for %d repo(s)...", len(repos))
    count = 0
    for repo_id, full_name, repo_url in repos:
        run_sast_on_repo(repo_id, full_name, repo_url)
        count += 1
        time.sleep(2)

    return count
