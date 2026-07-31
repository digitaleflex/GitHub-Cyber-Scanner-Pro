"""Multi-engine Dorking Engine — Google/Bing/DDG dorks pour OSINT professionnel."""
import logging
import re
import time
from urllib.parse import quote

import requests

import src.proxy as proxy

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr,en;q=0.9",
}

# ── Moteurs de recherche ────────────────────────────────────────────────

SEARCH_ENGINES = {
    "duckduckgo": {
        "url": "https://html.duckduckgo.com/html/",
        "params": {"q": None},
        "type": "html",
    },
    "duckduckgo_lite": {
        "url": "https://lite.duckduckgo.com/lite/",
        "params": {"q": None},
        "type": "html",
    },
    "bing": {
        "url": "https://www.bing.com/search",
        "params": {"q": None, "count": "20"},
        "type": "html",
    },
}


def _search(engine: str, query: str, max_results: int = 20) -> list[dict]:
    """Recherche sur un moteur et extrait les liens."""
    cfg = SEARCH_ENGINES.get(engine)
    if not cfg:
        return []
    try:
        session = proxy.get_session()
        r = session.get(
            cfg["url"],
            params={**cfg["params"], "q": query},
            headers=HEADERS, timeout=15,
        )
        if r.status_code != 200:
            return []

        urls = re.findall(r'<a[^>]*href="(https?://[^"]+)"', r.text)
        results = []
        seen = set()
        for url in urls:
            # Filtrer les URLs internes
            skip = ["duckduckgo", "bing.com", "microsoft.com/bing", "google", "youtube.com/watch", "accounts.google"]
            if any(s in url for s in skip) or url in seen:
                continue
            seen.add(url)
            results.append({"url": url, "engine": engine})
            if len(results) >= max_results:
                break
        return results
    except Exception as e:
        logging.warning(f"Dork {engine}: {e}")
        return []


# ── Dorks OSINT ──────────────────────────────────────────────────────────

def person_dorks(name: str, location: str = "") -> list[dict]:
    """Genere les dorks pour une recherche de personne."""
    dorks = []

    # Base
    dorks.append(("Identite exacte", f'"{name}" {location}'))
    if location:
        dorks.append(("Localisation precise", f'"{name}" "{location}"'))

    # Documents
    for ext in ["pdf", "docx", "xlsx", "ppt", "csv"]:
        dorks.append((f"Document {ext}", f'"{name}" filetype:{ext}'))

    # Reseaux sociaux / CV
    dorks.append(("LinkedIn/CV", f'"{name}" site:linkedin.com/in/'))
    dorks.append(("CV/Portfolio", f'"{name}" (CV OR resume OR portfolio)'))
    dorks.append(("GitHub/Bio", f'"{name}" site:github.com'))
    dorks.append(("Twitter/X", f'"{name}" site:x.com OR site:twitter.com'))

    # Adresse / contact
    dorks.append(("Contact/Adresse", f'"{name}" (email OR "@gmail" OR "@hotmail" OR phone OR tel OR address OR rue OR avenue)'))
    dorks.append(("Numero telephone", f'"{name}" (tel OR "+32" OR "04")'))

    # Entreprise
    dorks.append(("Entreprise/KBO", f'"{name}" (sprl OR bv OR sarl OR company OR enterprise)'))

    # Pastebin / leaks
    dorks.append(("Pastebin", f'"{name}" site:pastebin.com'))

    return dorks


def run_osint_dorks(name: str, location: str = "", engines: list[str] = None) -> dict:
    """Execute les dorks OSINT sur plusieurs moteurs. Retourne les resultats agreges."""
    if engines is None:
        engines = ["duckduckgo", "duckduckgo_lite"]

    dorks = person_dorks(name, location)
    report = {
        "target": {"name": name, "location": location},
        "dorks_executed": len(dorks),
        "engines_used": engines,
        "findings": {},
        "summary": "",
    }

    all_urls = {}
    for label, query in dorks:
        found_for_dork = []
        for engine in engines:
            results = _search(engine, query, max_results=8)
            for r in results:
                url = r["url"]
                if url not in all_urls:
                    all_urls[url] = {"url": url, "found_via": {"dork": label, "engine": engine}}
                found_for_dork.append(url)
            time.sleep(0.5)  # rate-limit
        if found_for_dork:
            report["findings"][label] = found_for_dork[:5]

    # Categoriser les resultats
    categories = {"documents": [], "social": [], "contact": [], "other": []}
    for url, info in all_urls.items():
        url_lower = url.lower()
        if any(ext in url_lower for ext in [".pdf", ".doc", ".xls", ".csv", ".ppt"]):
            categories["documents"].append(info)
        elif any(s in url_lower for s in ["linkedin", "github", "twitter", "x.com", "facebook", "instagram"]):
            categories["social"].append(info)
        elif any(s in url_lower for s in ["email", "phone", "tel", "address", "contact"]):
            categories["contact"].append(info)
        else:
            categories["other"].append(info)

    report["categories"] = {k: len(v) for k, v in categories.items()}
    report["total_urls"] = len(all_urls)
    report["top_findings"] = {k: v[:10] for k, v in categories.items()}
    report["summary"] = (
        f"{len(all_urls)} URLs trouvees via {len(dorks)} dorks sur {len(engines)} moteurs. "
        f"Docs: {categories['documents'].__len__()}, Social: {categories['social'].__len__()}, "
        f"Contact: {categories['contact'].__len__()}"
    )

    return report


# ── Extraction d'infos depuis les URLs trouvees ──────────────────────────

def extract_info_from_urls(urls: list[str]) -> list[dict]:
    """Telecharge et extrait les infos cles des URLs trouvees."""
    findings = []
    for url in urls[:10]:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
            text = r.text[:5000]

            # Extraire emails
            emails = list(set(re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)))[:3]

            # Extraire telephones
            phones = list(set(re.findall(r'(?:\+32|\+33|\+1|\+44|\+49)?\s*\d[\d\s.]{6,15}', text)))[:3]

            # Extraire adresses (pattern simple)
            addresses = list(set(re.findall(r'\d{1,4}\s+(?:rue|avenue|boulevard|chaussee|place|route)\s+[\w\s]+', text, re.IGNORECASE)))[:3]

            if emails or phones or addresses:
                findings.append({
                    "url": url,
                    "emails": emails,
                    "phones": phones,
                    "addresses": addresses,
                })
        except Exception:
            pass
        time.sleep(0.3)

    return findings


# ── Search Engine fallback (SearX public instances) ─────────────────────

SEARX_INSTANCES = [
    "https://searx.be/search",
    "https://search.sapti.me/search",
    "https://searx.tiekoetter.com/search",
]


def searx_search(query: str) -> list[dict]:
    """Recherche via une instance SearX publique (meta-moteur)."""
    for instance in SEARX_INSTANCES:
        try:
            r = requests.get(
                instance,
                params={"q": query, "format": "json", "language": "fr"},
                headers=HEADERS, timeout=10,
            )
            if r.status_code == 200:
                results = r.json().get("results", [])
                return [{"url": r.get("url"), "title": r.get("title", ""), "engine": "searx"} for r in results[:15]]
        except Exception:
            continue
    return []
