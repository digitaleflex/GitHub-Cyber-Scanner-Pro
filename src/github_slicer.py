"""GitHub Slicer — contourne la limite 1000 resultats via tranches stars × langues × dates."""
import logging
import random
import time

import requests

# Configuration du slicing
STAR_RANGES = [
    (5000, None, "5000+"),
    (1000, 5000, "1000-5000"),
    (500, 1000, "500-1000"),
    (100, 500, "100-500"),
    (50, 100, "50-100"),
    (10, 50, "10-50"),
    (3, 10, "3-10"),
    (0, 3, "0-3"),
]

# Sous-tranches pour les ranges qui retournent > 1000 resultats
DATE_RANGES = [
    ("2026-01-01", None, "2026"),
    ("2025-01-01", "2025-12-31", "2025"),
    ("2024-01-01", "2024-12-31", "2024"),
    ("2023-01-01", "2023-12-31", "2023"),
    ("2022-01-01", "2022-12-31", "2022"),
    ("2020-01-01", "2021-12-31", "2020-2021"),
    (None, "2019-12-31", "<2020"),
]

LANGUAGES = [
    "Python", "Go", "Rust", "JavaScript", "TypeScript", "Java", "C", "C++",
    "Ruby", "Shell", "PowerShell", "PHP", "C#", "Lua", "Kotlin", "Swift",
    "R", "Perl", "HCL", "YAML",
]

SECURITY_KEYWORDS = [
    "security", "pentest", "exploit", "vulnerability", "malware",
    "ransomware", "phishing", "forensic", "reverse-engineering",
    "threat-intelligence", "red-team", "blue-team", "osint",
    "hacking", "bug-bounty", "fuzzer", "scanner", "detection",
    "c2", "payload", "backdoor", "rootkit", "keylogger",
    "incident-response", "dfir", "threat-hunting", "hardening",
    "ssl", "tls", "waf", "firewall", "ids", "ips",
    "privacy", "anonymity", "encryption", "cryptography",
    "owasp", "cve", "mitre", "sigma", "yara", "splunk",
    "adversary", "emulation", "deception", "honeypot", "sandbox",
    "obfuscation", "evasion", "persistence", "lateral-movement",
    "credential", "kerberos", "ldap", "dns", "smb",
    "reconnaissance", "enumeration", "brute-force", "password",
    "token", "jwt", "oauth", "saml", "openid",
    "xss", "sqli", "csrf", "ssrf", "rce", "lfi", "rfi",
    "deserialization", "injection", "traversal", "spoofing",
    "misconfiguration", "exposure", "disclosure", "leak",
    "container-security", "kubernetes", "docker-security",
    "cloud-security", "aws-security", "azure-security", "gcp-security",
    "supply-chain", "sbom", "dependency", "package-security",
    "binary-analysis", "static-analysis", "dynamic-analysis",
    "memory-corruption", "buffer-overflow", "use-after-free",
    "iot-security", "mobile-security", "android-security", "ios-security",
]

HEADERS = {"Accept": "application/vnd.github.v3+json",
           "User-Agent": "Mozilla/5.0 (compatible; CyberScan-Pro/2.3)"}


def generate_queries() -> list[dict]:
    """Genere les queries de slicing: large d'abord, puis raffine."""
    queries = []

    # Phase 1: Balayage large (langue × keywords, sans filtre stars)
    for lang in LANGUAGES[:15]:
        for kw in SECURITY_KEYWORDS[:3]:  # 3 keywords par langue
            queries.append({"query": f"{kw} language:{lang}", "type": "broad"})
            if len(queries) >= 50:
                return queries[:50]

    # Phase 2: Stars × langues (plus specifique)
    for min_s, max_s, _label in STAR_RANGES[:4]:  # Top 4 ranges
        for lang in LANGUAGES[:8]:
            q = f"security language:{lang} stars:{min_s}..{max_s or ''}"
            queries.append({"query": q, "type": "stars_lang"})
            if len(queries) >= 100:
                return queries[:100]

    return queries[:100]
    return queries[:200]


def search_slice(query: str, token: str, per_page: int = 100) -> list[dict]:
    """Execute une requete slice et retourne les repos trouves."""
    headers = dict(HEADERS)
    headers["Authorization"] = f"token {token}"
    try:
        r = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "sort": "stars", "order": "desc", "per_page": per_page},
            headers=headers, timeout=20,
        )
        if r.status_code == 200:
            items = r.json().get("items", [])
            repos = []
            for item in items:
                repos.append({
                    "id": item["id"],
                    "full_name": item["full_name"],
                    "description": item.get("description") or "",
                    "html_url": item["html_url"],
                    "stargazers_count": item["stargazers_count"],
                    "language": item.get("language") or "",
                    "updated_at": item.get("updated_at", ""),
                    "created_at": item.get("created_at", ""),
                })
            return repos
        elif r.status_code in (403, 429):
            logging.warning(f"Slicer rate-limited on: {query[:60]}")
        else:
            logging.debug(f"Slicer {r.status_code}: {query[:60]}")
    except Exception as e:
        logging.warning(f"Slicer error: {e}")
    return []


def run_slicing_scan(tokens: list[str], max_queries: int = 20, per_page: int = 100) -> dict:
    """Execute le slicing scan. Retourne les stats."""
    from src import database

    if not tokens:
        return {"error": "Aucun token disponible", "discovered": 0}

    queries = generate_queries()
    queries = queries[:max_queries]

    total_saved = 0
    total_repos = 0
    for i, q in enumerate(queries):
        token = random.choice(tokens)
        saved = 0
        repos = search_slice(q["query"], token, per_page)
        if repos:
            total_repos += len(repos)
            try:
                saved = database.save_repositories(repos)
                total_saved += saved
            except Exception:
                pass
            if saved:
                logging.info(f"🧩 Slice {i+1}/{len(queries)}: +{saved} | {q['query'][:70]}")
        time.sleep(0.5)

    return {
        "queries_executed": len(queries),
        "repos_found": total_repos,
        "repos_saved": total_saved,
        "sample_queries": [q["query"] for q in queries[:5]],
    }
