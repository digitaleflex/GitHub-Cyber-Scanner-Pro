import logging
import re
import os
from typing import Iterable

import requests

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)


MITRE_MOBILE_URL = "https://raw.githubusercontent.com/mitre/cti/master/mobile-attack/mobile-attack.json"
MITRE_ICS_URL = "https://raw.githubusercontent.com/mitre/cti/master/ics-attack/ics-attack.json"
OWASP_CS_INDEX_URL = "https://raw.githubusercontent.com/OWASP/CheatSheetSeries/master/IndexASVS.md"
OWASP_CS_LIST_URL = "https://api.github.com/repos/OWASP/CheatSheetSeries/contents/cheatsheets"
EXPLOITDB_CSV_URL = "https://raw.githubusercontent.com/offensive-security/exploitdb/master/files_exploits.csv"


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\- ]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _extract_terms(text: str, max_n: int = 3, skip_unigrams: bool = False) -> list[str]:
    text = _slugify(text)
    words = text.split()
    terms = []
    start_n = 2 if skip_unigrams else 1
    for n in range(start_n, max_n + 1):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i:i + n])
            if len(phrase) >= 3 and len(phrase) <= 80:
                terms.append(phrase)
    return terms


def _clean_term(term: str) -> str | None:
    term = term.strip()
    if not term or len(term) < 3 or len(term) > 80:
        return None
    if re.match(r'^t\d{4}(\.\d{3})?$', term):
        return None
    if re.match(r'^capec-\d+$', term):
        return None
    if re.match(r'^cwe-\d+$', term):
        return None
    return term


def _deduplicate_terms(terms: Iterable[str]) -> list[str]:
    seen = set()
    out = []
    for t in terms:
        if t in seen:
            continue
        if any(t != s and t in s for s in seen):
            continue
        seen.add(t)
        out.append(t)
    return out


def _load_text(url: str, cache_name: str) -> str:
    cache_path = os.path.join(DATA_DIR, cache_name)
    try:
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000:
            with open(cache_path, encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        logger.warning("Cache read error %s: %s", cache_name, e)
    logger.info("Downloading %s", url)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    text = resp.text
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        logger.warning("Cache write error %s: %s", cache_name, e)
    return text


def _load_json(url: str, cache_name: str):
    cache_path = os.path.join(DATA_DIR, cache_name)
    try:
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000:
            import json
            with open(cache_path, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning("Cache read error %s: %s", cache_name, e)
    logger.info("Downloading %s", url)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    try:
        import json
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning("Cache write error %s: %s", cache_name, e)
    return data


def _parse_mitre_json(data: dict, category: str) -> list[str]:
    objects = data.get("objects", [])
    category_map = {
        "attack-pattern": "pentest",
        "course-of-action": "defense",
        "malware": category,
        "tool": "red-team",
        "intrusion-set": "red-team",
        "campaign": "red-team",
    }
    terms = set()
    for obj in objects:
        obj_type = obj.get("type", "")
        cat = category_map.get(obj_type)
        if cat != category:
            continue
        name = obj.get("name", "")
        if not name:
            continue
        for term in _extract_terms(name, max_n=3, skip_unigrams=True):
            clean = _clean_term(term)
            if clean:
                terms.add(clean)
    return list(terms)


def parse_mitre_mobile() -> list[str]:
    data = _load_json(MITRE_MOBILE_URL, "mitre_attack_mobile.json")
    return _parse_mitre_json(data, "mobile")


def parse_mitre_ics() -> list[str]:
    data = _load_json(MITRE_ICS_URL, "mitre_attack_ics.json")
    terms = set()
    objects = data.get("objects", [])
    category_map = {
        "attack-pattern": "iot",
        "course-of-action": "defense",
        "malware": "malware",
        "tool": "red-team",
        "intrusion-set": "red-team",
        "campaign": "red-team",
    }
    for obj in objects:
        obj_type = obj.get("type", "")
        cat = category_map.get(obj_type)
        if not cat:
            continue
        name = obj.get("name", "")
        if not name:
            continue
        for term in _extract_terms(name, max_n=3, skip_unigrams=True):
            clean = _clean_term(term)
            if clean:
                terms.add(clean)
    return list(terms)


def fetch_owasp_cheatsheet_keywords() -> list[str]:
    try:
        resp = requests.get(OWASP_CS_LIST_URL, timeout=30)
        resp.raise_for_status()
        files = resp.json()
        terms = set()
        for f in files:
            name = f.get("name", "")
            if not name.endswith(".md"):
                continue
            name_no_ext = name[:-3]
            name_no_ext = name_no_ext.replace("-", " ").replace("_", " ")
            for t in _extract_terms(name_no_ext, max_n=3):
                clean = _clean_term(t)
                if clean:
                    terms.add(clean)
            try:
                content_resp = requests.get(f.get("download_url", ""), timeout=15)
                if content_resp.status_code == 200:
                    content_text = content_resp.text
                    headings = re.findall(r'^#{1,3}\s+(.+)', content_text, re.MULTILINE)
                    examples = re.findall(r'(?i)(?:example|attack|injection|xss|csrf|ssrf|rce|sqli|ldap|xxe|redirect)', content_text)
                    for h in headings:
                        for t in _extract_terms(h, max_n=3):
                            clean = _clean_term(t)
                            if clean:
                                terms.add(clean)
                    for ex in examples:
                        if len(ex) >= 3:
                            terms.add(ex.lower())
            except Exception:
                pass
        logger.info("OWASP CheatSheets: %d termes extraits", len(terms))
        return list(terms)
    except Exception as e:
        logger.error("Erreur OWASP CheatSheets: %s", e)
        return []


def fetch_exploitdb_keywords() -> list[str]:
    try:
        text = _load_text(EXPLOITDB_CSV_URL, "exploitdb.csv")
        lines = text.splitlines()
        terms = set()
        for i, line in enumerate(lines):
            if i == 0:
                continue
            parts = line.split(",")
            if len(parts) >= 4:
                title = parts[2].strip().strip('"')
                for t in _extract_terms(title, max_n=3, skip_unigrams=True):
                    clean = _clean_term(t)
                    if clean:
                        terms.add(clean)
        logger.info("Exploit-DB: %d termes extraits", len(terms))
        return list(terms)
    except Exception as e:
        logger.error("Erreur Exploit-DB: %s", e)
        return []


def extract_cve_keywords(limit: int = 30000) -> list[dict]:
    from database import get_db_connection
    from psycopg2.extras import RealDictCursor

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT description, weaknesses
        FROM cve_entries
        WHERE description IS NOT NULL AND description != ''
        ORDER BY cvss_score DESC NULLS LAST
        LIMIT %s
    """, (limit,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        logger.info("CVE extractor: aucune CVE trouvee")
        return []

    from collections import Counter

    doc_freq: Counter = Counter()
    term_freq: Counter = Counter()
    term_sources: dict[str, set[str]] = {}

    for row in rows:
        desc = row.get("description") or ""
        weaknesses = row.get("weaknesses") or ""

        tokens = re.sub(r'[^a-z0-9\- ]', ' ', desc.lower()).split()
        seen = set()
        for i in range(len(tokens)):
            for n in range(1, 4):
                if i + n <= len(tokens):
                    phrase = " ".join(tokens[i:i + n])
                    if len(phrase) >= 3 and len(phrase) <= 80:
                        term_freq[phrase] += 1
                        if phrase not in seen:
                            seen.add(phrase)
                            doc_freq[phrase] += 1
                            term_sources.setdefault(phrase, set()).add("cve")

        if weaknesses:
            for w in weaknesses.split(","):
                w = w.strip().lower()
                if len(w) >= 3:
                    term_freq[w] += 1
                    if w not in seen:
                        seen.add(w)
                        doc_freq[w] += 1
                        term_sources.setdefault(w, set()).add("cve-weakness")

    total_docs = len(rows)
    candidates = []
    import math
    for term, tf in term_freq.most_common(5000):
        df = doc_freq.get(term, 1)
        if df < 3 or df > total_docs * 0.3:
            continue
        if re.match(r'^[0-9\s\-]+$', term):
            continue
        if re.match(r'^cve-\d{4}', term):
            continue
        stop_words = {"the", "and", "for", "that", "this", "with", "from", "such", "which", "their", "them"}
        words = term.split()
        if all(w in stop_words for w in words):
            continue
        idf = math.log((total_docs + 1) / (df + 1)) + 1
        tf_weight = 1 + math.log1p(tf)
        score = tf_weight * idf

        security_hints = [
            "vuln", "cve", "exploit", "remote", "code", "execution", "buffer",
            "overflow", "injection", "xss", "csrf", "bypass", "privilege",
            "escalation", "denial", "service", "memory", "corruption",
            "authentication", "authorization", "encryption", "decrypt",
            "malware", "ransom", "trojan", "backdoor", "phishing",
            "information", "disclosure", "security", "vulnerability",
            "arbitrary", "heap", "stack", "integer", "overflow",
            "directory", "traversal", "command", "injection",
        ]
        if any(h in term for h in security_hints):
            score *= 1.3

        candidates.append({
            "term": term,
            "category_guess": "pentest",
            "score": round(score, 4),
            "sources": len(term_sources.get(term, set())),
            "source_samples": f"extracted from {df} CVEs",
        })

    candidates.sort(key=lambda x: -x["score"])
    logger.info("CVE extractor: %d candidats extraits de %d CVEs", len(candidates), len(rows))
    return candidates[:2000]


def build_combined_ontology() -> dict[str, list[str]]:
    ontology = {
        "pentest": set(),
        "defense": set(),
        "malware": set(),
        "red-team": set(),
        "osint": set(),
        "cloud": set(),
        "mobile": set(),
        "iot": set(),
        "crypto": set(),
    }

    mobile_terms = parse_mitre_mobile()
    ontology["mobile"].update(mobile_terms)
    logger.info("MITRE Mobile: %d termes", len(mobile_terms))

    ics_terms = parse_mitre_ics()
    ontology["iot"].update(ics_terms)
    logger.info("MITRE ICS: %d termes (categorie iot)", len(ics_terms))

    owasp_terms = fetch_owasp_cheatsheet_keywords()
    ontology["pentest"].update(owasp_terms)
    logger.info("OWASP CheatSheets: %d termes (categorie pentest)", len(owasp_terms))

    exploitdb_terms = fetch_exploitdb_keywords()
    ontology["pentest"].update(exploitdb_terms)
    logger.info("Exploit-DB: %d termes (categorie pentest)", len(exploitdb_terms))

    return {cat: list(terms) for cat, terms in ontology.items()}


def import_external_sources_to_db() -> dict:
    from database import save_discovered_keywords
    from nlp_processor import refresh_cyber_terms

    stats = {"cve": 0, "mitre_mobile_ics": 0, "owasp": 0, "exploitdb": 0, "total": 0}

    cve_terms = extract_cve_keywords(limit=30000)
    if cve_terms:
        saved = save_discovered_keywords(cve_terms)
        stats["cve"] = saved
        stats["total"] += saved

    ontology = build_combined_ontology()
    for cat, terms in ontology.items():
        if not terms:
            continue
        keywords = [
            {
                "term": t,
                "category_guess": cat,
                "score": 0.9,
                "sources": 1,
                "source_samples": "MITRE Mobile/ICS / OWASP / Exploit-DB",
            }
            for t in _deduplicate_terms(terms)
        ]
        saved = save_discovered_keywords(keywords)
        if cat == "mobile":
            stats["mitre_mobile_ics"] += saved
        elif cat == "iot":
            stats["mitre_mobile_ics"] += saved
        else:
            stats["owasp"] += saved
        stats["total"] += saved

    if stats["total"] > 0:
        try:
            from database import auto_approve_keywords
            approved = auto_approve_keywords(min_score=0.7, min_sources=2)
            stats["approved"] = approved
        except Exception:
            pass

    try:
        refresh_cyber_terms()
    except Exception:
        pass

    logger.info(
        "Import terminé: %d CVE, %d MITRE, %d OWASP/Exploit-DB, %d total",
        stats["cve"], stats["mitre_mobile_ics"], stats["owasp"], stats["total"],
    )
    return stats
