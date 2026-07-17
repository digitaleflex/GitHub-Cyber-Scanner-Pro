import logging
import os
import re
import zipfile
from io import BytesIO
from typing import Iterable

import requests

logger = logging.getLogger(__name__)

MITRE_ATTACK_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
CAPEC_URL = "https://capec.mitre.org/data/xml/capec_latest.xml"
CWE_URL = "https://cwe.mitre.org/data/xml/cwec_latest.xml.zip"

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)


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
    # Skip terms that are mostly numbers or MITRE IDs
    if re.match(r'^t\d{4}(\.\d{3})?$', term):
        return None
    if re.match(r'^capec-\d+$', term):
        return None
    if re.match(r'^cwe-\d+$', term):
        return None
    return term


def _load_json(url: str, cache_name: str):
    cache_path = os.path.join(DATA_DIR, cache_name)
    try:
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000:
            import json
            with open(cache_path, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning("Impossible de lire le cache %s: %s", cache_name, e)

    logger.info("Téléchargement de %s", url)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    try:
        import json
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning("Impossible de mettre en cache %s: %s", cache_name, e)
    return data


def _load_text(url: str, cache_name: str) -> str:
    cache_path = os.path.join(DATA_DIR, cache_name)
    try:
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000:
            with open(cache_path, encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        logger.warning("Impossible de lire le cache %s: %s", cache_name, e)

    logger.info("Téléchargement de %s", url)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    text = resp.text
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        logger.warning("Impossible de mettre en cache %s: %s", cache_name, e)
    return text


def _load_zip_text(url: str, cache_name: str) -> str:
    cache_path = os.path.join(DATA_DIR, cache_name)
    try:
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000:
            with open(cache_path, encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        logger.warning("Impossible de lire le cache %s: %s", cache_name, e)

    logger.info("Téléchargement de %s", url)
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    with zipfile.ZipFile(BytesIO(resp.content)) as z:
        xml_files = [n for n in z.namelist() if n.endswith(".xml")]
        if not xml_files:
            raise ValueError(f"Aucun fichier XML trouvé dans {url}")
        text = z.read(xml_files[0]).decode("utf-8")
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception as e:
        logger.warning("Impossible de mettre en cache %s: %s", cache_name, e)
    return text


def parse_mitre_attack(data: dict) -> dict[str, list[str]]:
    """Extrait termes et catégories depuis MITRE ATT&CK Enterprise."""
    objects = data.get("objects", [])

    category_map = {
        "attack-pattern": "pentest",
        "course-of-action": "defense",
        "malware": "malware",
        "tool": "red-team",
        "intrusion-set": "red-team",
        "campaign": "red-team",
    }

    results: dict[str, set[str]] = {
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

    for obj in objects:
        obj_type = obj.get("type", "")
        cat = category_map.get(obj_type)
        if not cat:
            continue
        name = obj.get("name", "")
        if not name:
            continue

        # Only use the canonical name, skip aliases to keep quality high
        for term in _extract_terms(name, max_n=3, skip_unigrams=True):
            clean = _clean_term(term)
            if clean:
                results[cat].add(clean)

    return {cat: list(terms) for cat, terms in results.items()}


def parse_capec(xml_text: str) -> list[str]:
    """Extraction simple des noms CAPEC."""
    import xml.etree.ElementTree as ET
    terms = set()
    try:
        root = ET.fromstring(xml_text)
        for attack in root.iter("{http://capec.mitre.org/capec-3}Attack_Pattern"):
            name = attack.get("Name", "")
            for term in _extract_terms(name, max_n=3, skip_unigrams=True):
                clean = _clean_term(term)
                if clean:
                    terms.add(clean)
    except Exception as e:
        logger.error("Erreur parsing CAPEC: %s", e)
    return list(terms)


def parse_cwe(xml_text: str) -> list[str]:
    """Extraction simple des noms CWE."""
    import xml.etree.ElementTree as ET
    terms = set()
    try:
        root = ET.fromstring(xml_text)
        for weakness in root.iter("{http://cwe.mitre.org/cwe-6}Weakness"):
            name = weakness.get("Name", "")
            for term in _extract_terms(name, max_n=3, skip_unigrams=True):
                clean = _clean_term(term)
                if clean:
                    terms.add(clean)
    except Exception as e:
        logger.error("Erreur parsing CWE: %s", e)
    return list(terms)


def _deduplicate_terms(terms: Iterable[str]) -> list[str]:
    seen = set()
    out = []
    for t in terms:
        if t in seen:
            continue
        # Skip if term is a substring of an already kept longer term
        if any(t != s and t in s for s in seen):
            continue
        seen.add(t)
        out.append(t)
    return out


def build_ontology() -> dict[str, list[str]]:
    """Construit l'ontologie complète MITRE + CAPEC + CWE."""
    logger.info("Construction de l'ontologie cyber...")

    attack_data = _load_json(MITRE_ATTACK_URL, "mitre_attack_enterprise.json")
    mitre_terms = parse_mitre_attack(attack_data)

    capec_xml = _load_text(CAPEC_URL, "capec_latest.xml")
    capec_terms = parse_capec(capec_xml)

    cwe_xml = _load_zip_text(CWE_URL, "cwec_latest.xml")
    cwe_terms = parse_cwe(cwe_xml)

    # CAPEC et CWE vont majoritairement dans pentest/defense
    mitre_terms["pentest"].extend(capec_terms)
    mitre_terms["defense"].extend(cwe_terms)

    ontology = {}
    for cat, terms in mitre_terms.items():
        ontology[cat] = _deduplicate_terms(terms)

    total = sum(len(v) for v in ontology.values())
    logger.info("Ontologie construite: %d termes repartis sur %d categories", total, len(ontology))
    return ontology


def import_ontology_to_db() -> int:
    """Importe l'ontologie MITRE/CAPEC/CWE dans discovered_keywords (approved)."""
    from database import save_discovered_keywords, approve_keyword
    from nlp_processor import refresh_cyber_terms

    ontology = build_ontology()
    keywords = []
    for cat, terms in ontology.items():
        for term in terms:
            keywords.append({
                "term": term,
                "category_guess": cat,
                "score": 0.95,
                "sources": 1,
                "source_samples": "MITRE/CAPEC/CWE ontology",
            })

    # Insert or update as pending then approve
    saved = save_discovered_keywords(keywords)

    # Approve all terms from ontology
    approved = 0
    for kw in keywords:
        if approve_keyword(kw["term"], "approved", kw["category_guess"]):
            approved += 1

    refresh_cyber_terms()
    logger.info("Ontologie importee: %d termes approuves", approved)
    return approved


def enrich_categories() -> dict[str, list[str]]:
    """Retourne l'ontologie pour enrichir directement CYBER_CATEGORIES."""
    return build_ontology()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import_ontology_to_db()
