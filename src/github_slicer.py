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
    (0, 10, "0-10"),
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
]

HEADERS = {"Accept": "application/vnd.github.v3+json",
           "User-Agent": "Mozilla/5.0 (compatible; CyberScan-Pro/2.3)"}


def generate_queries(max_per_star_range: int = 3) -> list[dict]:
    """Genere les queries de slicing: stars × langues × keywords."""
    queries = []
    for min_stars, max_stars, label in STAR_RANGES:
        if len(queries) >= 500:
            break
        for lang in LANGUAGES:
            if len(queries) >= 500:
                break
            # Top keywords first
            for kw in SECURITY_KEYWORDS[:max_per_star_range]:
                q = f"{kw} language:{lang}"
                if min_stars or max_stars:
                    q += f" stars:{min_stars}..{max_stars or ''}"
                queries.append({
                    "query": q,
                    "lang": lang,
                    "stars_range": label,
                    "keyword": kw,
                })
                if len(queries) >= 500:
                    break
    logging.info(f"🧩 GitHub Slicer: {len(queries)} requetes generees ({len(LANGUAGES)} langues × {len(STAR_RANGES)} tranches × keywords)")
    return queries


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
    # Limiter le nombre de queries par cycle (sinon 500+ requêtes)
    queries = random.sample(queries, min(max_queries, len(queries)))

    total_saved = 0
    total_repos = 0
    for i, q in enumerate(queries):
        token = random.choice(tokens)
        repos = search_slice(q["query"], token, per_page)
        if repos:
            total_repos += len(repos)
            try:
                saved = database.save_repositories(repos)
                total_saved += saved
            except Exception:
                pass
            if saved:
                logging.info(f"🧩 Slice {i+1}/{len(queries)}: +{saved} ({q['stars_range']} | {q['lang']} | {q['keyword'][:15]})")
        time.sleep(0.5)

    return {
        "queries_executed": len(queries),
        "repos_found": total_repos,
        "repos_saved": total_saved,
        "sample_queries": [q["query"] for q in queries[:5]],
    }
