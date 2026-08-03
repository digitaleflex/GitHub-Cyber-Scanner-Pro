"""Dorking engine — decouverte de repos et outils via GitHub Code Search + sources externes."""
import logging
import os
import random
import time

import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ── GitHub Code Search ────────────────────────────────────────────────────
# Les dorks cherchent dans le CODE des repos (pas juste les descriptions)
CODE_DORKS = [
    # Outils red team
    ("red team tool", "Red team tools"),
    ("adversary simulation", "Adversary simulation frameworks"),
    ("C2 framework", "Command & Control frameworks"),
    ("lateral movement script", "Lateral movement tools"),
    ("privilege escalation poc", "Privilege escalation PoCs"),
    ("kerberoasting tool", "Kerberos attack tools"),
    ("dll sideloading", "DLL sideloading techniques"),
    ("bypass amsi", "AMSI bypass tools"),
    ("bypass defender", "Windows Defender bypass"),
    ("EDR evasion", "EDR evasion techniques"),
    # Outils blue team
    ("detection rule sigma", "Sigma detection rules"),
    ("incident response automation", "IR automation tools"),
    ("threat hunting query", "Threat hunting queries"),
    ("yara rule malware", "YARA rules for malware"),
    ("forensic artifact parser", "Forensic tools"),
    ("log analysis siem", "SIEM log analysis tools"),
    ("network detection signature", "Network detection tools"),
    # Outils exploit/PoC
    ("CVE proof of concept", "CVE PoC exploits"),
    ("vulnerability scanner", "Vulnerability scanners"),
    ("fuzzer security", "Security fuzzers"),
    ("reverse engineering tool", "RE tools"),
    # Offensive/Red Team
    ("phishing toolkit", "Phishing toolkits"),
    ("payload generator", "Payload generators"),
    ("implant beacon", "Implant/beacon tools"),
    ("osint reconnaissance", "OSINT recon tools"),
]


def github_code_search(query: str, token: str, per_page: int = 20) -> list[dict]:
    """Recherche dans le code source GitHub. Retourne les repos trouves."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }
    try:
        r = requests.get(
            "https://api.github.com/search/code",
            params={"q": query, "per_page": per_page},
            headers=headers,
            timeout=20,
        )
        if r.status_code == 200:
            items = r.json().get("items", [])
            repos = {}
            for item in items:
                repo_full = item["repository"]["full_name"]
                if repo_full not in repos:
                    repos[repo_full] = {
                        "id": item["repository"]["id"],
                        "full_name": repo_full,
                        "description": item["repository"].get("description") or "",
                        "html_url": item["repository"]["html_url"],
                        "stargazers_count": item["repository"].get("stargazers_count", 0),
                        "language": item["repository"].get("language") or "",
                        "updated_at": item["repository"].get("updated_at", ""),
                        "created_at": item["repository"].get("created_at", ""),
                    }
            return list(repos.values())
    except Exception as e:
        logging.warning(f"GitHub code search '{query}': {e}")
    return []


def run_dorking_scan(tokens: list[str], limit: int = 10) -> int:
    """Execute les dorks GitHub Code Search. Retourne le nb de nouveaux repos."""
    from src import database

    if not tokens:
        logging.warning("Aucun token pour le dorking")
        return 0

    found = 0
    # Limiter a N dorks aleatoires pour eviter de saturer
    dorks = random.sample(CODE_DORKS, min(limit, len(CODE_DORKS)))

    for query, category in dorks:
        token = random.choice(tokens)
        repos = github_code_search(query, token, per_page=15)
        if repos:
            try:
                saved = database.save_repositories(repos)
                if saved:
                    logging.info(f"🔍 Dork '{category}': {saved} nouveau(x)")
                found += saved
            except Exception:
                pass
        time.sleep(0.8)  # rate-limit GitHub code search (10 req/min per token)

    logging.info(f"🔍 Dorking: {found} repos decouverts via code search")
    return found


# ── Exploit-DB CSV ────────────────────────────────────────────────────────

EXPLOITDB_URL = "https://gitlab.com/exploit-database/exploitdb/-/raw/main/files_exploits.csv"


def import_exploitdb() -> int:
    """Telecharge et importe le CSV Exploit-DB comme mots-cles. Retourne nb ajoutes."""
    import csv
    from io import StringIO
    from src import database

    try:
        r = requests.get(EXPLOITDB_URL, timeout=60)
        if r.status_code != 200:
            logging.warning(f"Exploit-DB: HTTP {r.status_code}")
            return 0

        reader = csv.DictReader(StringIO(r.text))
        keywords = []
        seen = set()
        for row in reader:
            desc = (row.get("description") or "")[:80]
            platform = (row.get("platform") or "")[:30]
            term = f"{desc}".lower().strip()
            if len(term) < 4 or term in seen:
                continue
            seen.add(term)
            keywords.append({
                "term": term,
                "category_guess": "exploit",
                "score": 0.70,
                "sources": 1,
                "source_samples": f"Exploit-DB: {platform}",
            })

        if keywords:
            saved = database.save_discovered_keywords(keywords)
            logging.info(f"💣 Exploit-DB: {saved} mots-cles importes ({len(keywords)} tries)")
            return saved
    except Exception as e:
        logging.error(f"Erreur Exploit-DB: {e}")
    return 0
