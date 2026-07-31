"""OSINT Enricher — telecharge des datasets open source pour enrichir la base de connaissances."""
import csv
import json
import logging
import os
import time
from io import StringIO

import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# ── Sources OSINT ────────────────────────────────────────────────────────

SOURCES = {
    # CISA Known Exploited Vulnerabilities (CSV)
    "cisa_kev": {
        "url": "https://www.cisa.gov/sites/default/files/csv/known_exploited_vulnerabilities.csv",
        "type": "csv",
        "file": "cisa_kev.csv",
    },
    # GTFOBins (Living Off the Land binaries - JSON)
    "gtfobins": {
        "url": "https://gtfobins.github.io/gtfobins.json",
        "type": "json",
        "file": "gtfobins.json",
    },
    # LOLBAS (Windows LOLBins - CSV via raw GitHub)
    "lolbas": {
        "url": "https://raw.githubusercontent.com/LOLBAS-Project/LOLBAS-Project.github.io/master/_data/lolbas.json",
        "type": "json",
        "file": "lolbas.json",
    },
    # Open Source Security Software (OWASP curated list - GitHub API)
    "owasp_oss": {
        "url": "https://api.github.com/search/repositories?q=topic:security+topic:owasp+stars:>50&sort=stars&per_page=50",
        "type": "github_search",
        "file": "owasp_oss.json",
    },
}

# ── Awesome Lists (via GitHub API) ────────────────────────────────────────

AWESOME_QUERIES = [
    "awesome-security stars:>10",
    "awesome-pentest stars:>10",
    "awesome-hacking stars:>10",
    "awesome-malware-analysis stars:>10",
    "awesome-threat-intelligence stars:>10",
    "awesome-exploit-development stars:>10",
    "awesome-reverse-engineering stars:>10",
    "awesome-forensics stars:>10",
    "awesome-osint stars:>10",
    "awesome-bug-bounty stars:>10",
]

# ── Sigma Rules ──────────────────────────────────────────────────────────

SIGMA_RULES_URL = "https://api.github.com/repos/SigmaHQ/sigma/contents/rules"


def import_sigma_rules(tokens: list[str]) -> int:
    """Telecharge et importe les titres de regles Sigma comme mots-cles. Retourne nb."""
    import random
    try:
        import yaml as _yaml
    except ImportError:
        logging.warning("PyYAML non installe, Sigma rules ignorees")
        return 0
    from src import database

    if not tokens:
        return 0

    token = random.choice(tokens)
    headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"token {token}"}
    keywords = []
    seen = set()

    # Recursive fetch of rule directories
    def fetch_dir(url: str, depth: int = 0):
        if depth > 2:
            return
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code != 200:
                return
            for item in r.json():
                if item["type"] == "dir" and depth < 1:
                    fetch_dir(item["url"], depth + 1)
                elif item["type"] == "file" and item["name"].endswith(".yml"):
                    fetch_rule(item["download_url"])
            time.sleep(0.3)
        except Exception:
            pass

    def fetch_rule(url: str):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                return
            rule = _yaml.safe_load(r.text)
            if not rule:
                return
            title = str(rule.get("title", "")).lower().strip()
            tags = rule.get("tags", [])
            level = rule.get("level", "")
            # Extract meaningful terms from title
            for word in title.replace(",", " ").replace("-", " ").split():
                word = word.strip()
                if len(word) > 4 and word not in seen and word not in _STOPWORDS:
                    seen.add(word)
                    keywords.append({
                        "term": word.lower(),
                        "category_guess": "sigma_detection",
                        "score": 0.70,
                        "sources": 1,
                        "source_samples": f"Sigma rule: {title[:80]}",
                    })
        except Exception:
            pass

    fetch_dir(SIGMA_RULES_URL)

    if keywords:
        try:
            saved = database.save_discovered_keywords(keywords)
            logging.info(f"📏 Sigma: {saved} mots-cles extraits de regles de detection")
            return saved
        except Exception as e:
            logging.error(f"Sigma import: {e}")
    return 0


_STOPWORDS = {
    "about", "above", "after", "again", "against", "being", "below", "between",
    "could", "doing", "during", "every", "first", "found", "given", "going",
    "having", "hello", "might", "month", "never", "other", "place", "quite",
    "rather", "right", "shall", "since", "still", "their", "there", "these",
    "thing", "think", "those", "under", "until", "using", "value", "where",
    "which", "while", "world", "would", "write", "years", "could", "event",
}


def download_source(name: str, config: dict) -> str | None:
    """Telecharge une source OSINT. Retourne le chemin du fichier ou None."""
    path = os.path.join(DATA_DIR, config["file"])
    try:
        r = requests.get(config["url"], timeout=30, headers={"User-Agent": "CyberScan-Pro/2.3"})
        if r.status_code != 200:
            logging.warning(f"OSINT {name}: HTTP {r.status_code}")
            return None
        with open(path, "w", encoding="utf-8") as f:
            f.write(r.text)
        logging.info(f"📥 OSINT {name}: telecharge ({len(r.text)} octets)")
        return path
    except Exception as e:
        logging.error(f"OSINT {name}: {e}")
        return None


def import_cisa_kev(path: str) -> int:
    """Importe les CVE du catalogue CISA KEV. Retourne le nb enrichi."""
    from src import database

    try:
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        conn = database.get_db_connection()
        cursor = conn.cursor()
        updated = 0
        for row in rows:
            cve_id = row.get("cveID", "").strip()
            if not cve_id:
                continue
            cursor.execute(
                """UPDATE cve_entries
                   SET weaknesses = CASE WHEN weaknesses IS NULL THEN %s
                       WHEN weaknesses NOT LIKE %s THEN weaknesses || '; CISA_KEV'
                       ELSE weaknesses END
                   WHERE cve_id = %s""",
                ("CISA_KEV: " + (row.get("vulnerabilityName", "")[:120]),
                 "%CISA_KEV%", cve_id),
            )
            if cursor.rowcount:
                updated += 1
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"🔴 CISA KEV: {updated}/{len(rows)} CVEs enrichies (exploitees activement)")
        return updated
    except Exception as e:
        logging.error(f"Erreur import CISA KEV: {e}")
        return 0


def import_gtfobins(path: str) -> int:
    """Importe les techniques GTFOBins/LOLBAS comme mots-cles. Retourne le nb."""
    from src import database

    try:
        with open(path) as f:
            data = json.load(f)

        keywords = []
        entries = data if isinstance(data, list) else data.get("functions", [])
        # GTFOBins format: list of {name, functions: [{description, code, ...}]}
        for entry in entries:
            name = entry.get("binary") or entry.get("Name") or entry.get("name", "")
            if not name:
                continue
            keywords.append({
                "term": f"lolbin-{name.lower()}",
                "category_guess": "lolbin",
                "score": 0.85,
                "sources": 1,
                "source_samples": f"GTFOBins/LOLBAS dataset",
            })

        if keywords:
            saved = database.save_discovered_keywords(keywords)
            logging.info(f"🔧 GTFOBins/LOLBAS: {saved} techniques importees")
            return saved
    except Exception as e:
        logging.error(f"Erreur import GTFOBins: {e}")
    return 0


def import_awesome_lists(tokens: list[str]) -> int:
    """Decouvre des repos depuis les Awesome Lists de securite. Retourne le nb."""
    import random
    from src import database

    found = 0
    for query in AWESOME_QUERIES:
        token = random.choice(tokens) if tokens else None
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"
        try:
            r = requests.get(
                f"https://api.github.com/search/repositories?q={query}&sort=stars&per_page=10",
                headers=headers, timeout=15,
            )
            if r.status_code != 200:
                continue
            repos = r.json().get("items", [])
            for repo in repos:
                items = [{
                    "full_name": repo["full_name"],
                    "stars": repo["stargazers_count"],
                    "description": repo.get("description") or "",
                    "html_url": repo["html_url"],
                    "language": repo.get("language") or "",
                    "updated_at": repo.get("updated_at", ""),
                    "created_at": repo.get("created_at", ""),
                }]
                try:
                    saved = database.save_repositories(items)
                    found += saved
                except Exception:
                    pass
            time.sleep(0.5)  # rate-limit amical
        except Exception as e:
            logging.warning(f"Awesome list '{query}': {e}")
            continue
    logging.info(f"📚 Awesome Lists: {found} nouveaux repos decouverts")
    return found


def run_osint_enrichment(limit: int = 5) -> dict:
    """Execute l'enrichissement OSINT complet. Retourne un resume."""
    import src.github_client as gc

    tokens = gc._available_tokens() if gc.TOKENS else []
    results = {}

    # Download & import sources
    for name, config in SOURCES.items():
        try:
            path = download_source(name, config)
            if not path:
                results[name] = 0
                continue
            if name == "cisa_kev":
                results[name] = import_cisa_kev(path)
            elif name in ("gtfobins", "lolbas"):
                results[name] = import_gtfobins(path)
            else:
                results[name] = 1  # just downloaded
        except Exception as e:
            logging.error(f"OSINT {name}: {e}")
            results[name] = 0

    # Awesome lists discovery
    if tokens:
        results["awesome_lists"] = import_awesome_lists(tokens)
        results["sigma_rules"] = import_sigma_rules(tokens)
    else:
        results["awesome_lists"] = 0
        results["sigma_rules"] = 0

    return results
