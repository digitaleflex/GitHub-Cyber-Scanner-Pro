"""
Enrichissement des actualites cyber : extraction d'entites (CVE, CWE, CPE, IOC, ATT&CK)
et regroupement en "incidents" unifies (plusieurs flux => un meme evenement).

Entites supportees :
  - CVE-YYYY-NNNN
  - CWE-XXXX
  - CPE (cpe:2.3:...)
  - IPs (IPv4)
  - Domaines
  - Hashes (md5/sha1/sha256)
  - URLs
  - Techniques MITRE ATT&CK (TXXXX / TXXXX.X) + nom/tactique associee
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)
CWE_RE = re.compile(r"CWE-\d{2,5}", re.IGNORECASE)
ATTACK_RE = re.compile(r"\bT\d{4}(?:\.\d{1,3})?\b")
CPE_RE = re.compile(r"cpe:2\.3:[a-z\*]:[a-z0-9_\-\.\*]+", re.IGNORECASE)
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
SHA256_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")
SHA1_RE = re.compile(r"\b[a-fA-F0-9]{40}\b")
MD5_RE = re.compile(r"\b[a-fA-F0-9]{32}\b")
URL_RE = re.compile(r"https?://[^\s<>\"'\]\)]+", re.IGNORECASE)
# Domaine simple (sans le protocol pour eviter les doublons d'URL)
DOMAIN_RE = re.compile(r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,24}\b", re.IGNORECASE)

# Mots-cles produits/logiciels pour le regroupement "meme produit"
PRODUCT_KEYWORDS = [
    "windows", "linux", "android", "ios", "chrome", "firefox", "safari", "edge",
    "exchange", "outlook", "sharepoint", "active directory", "citrix", "vmware",
    "fortinet", "palo alto", "cisco", "juniper", "wordpress", "drupal", "joomla",
    "apache", "nginx", "openssl", "openssh", "log4j", "spring", "java", "python",
    "php", "node", "rust", "go ", "kubernetes", "docker", "gitlab", "github",
    "Ivanti", "Cisco", "Microsoft", "Apple", "Google", "Oracle", "Adobe", "SAP",
    "SolarWinds", "Okta", "Atlassian", "Confluence", "Jira", "Zimbra", "Exim",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elastic", "Git", "OpenSSL",
    "Chrome", "Edge", "Explorer", "Outlook", "Exchange", "SharePoint", "Azure",
    "AWS", "GCP", "Cloudflare", "F5", "Palo Alto", "FortiGate", "Juniper",
]

# Mapping MITRE ATT&CK (extrait representatif des techniques les plus courantes)
ATTACK_TECHNIQUES: dict[str, dict] = {
    "T1190": {"name": "Exploit Public-Facing Application", "tactic": "Initial Access"},
    "T1566": {"name": "Phishing", "tactic": "Initial Access"},
    "T1078": {"name": "Valid Accounts", "tactic": "Defense Evasion / Persistence"},
    "T1098": {"name": "Account Manipulation", "tactic": "Persistence"},
    "T1059": {"name": "Command and Scripting Interpreter", "tactic": "Execution"},
    "T1055": {"name": "Process Injection", "tactic": "Defense Evasion"},
    "T1486": {"name": "Data Encrypted for Impact (Ransomware)", "tactic": "Impact"},
    "T1110": {"name": "Brute Force", "tactic": "Credential Access"},
    "T1071": {"name": "Application Layer Protocol", "tactic": "Command and Control"},
    "T1027": {"name": "Obfuscated Files or Information", "tactic": "Defense Evasion"},
    "T1133": {"name": "External Remote Services", "tactic": "Initial Access"},
    "T1505": {"name": "Server Software Component", "tactic": "Persistence"},
    "T1048": {"name": "Exfiltration Over Alternative Protocol", "tactic": "Exfiltration"},
}

# Mots-cles de severite dans le texte
KEV_KEYWORDS = ["known exploited", "kev", "actively exploited", "exploitation active",
                "zero-day", "0-day", "zero day", "exploited in the wild"]
CRITICAL_KEYWORDS = ["critical", "critique", "rce", "remote code execution",
                     "execution de code", "severe", "grave"]
HIGH_KEYWORDS = ["high", "eleve", "important"]


@dataclass
class NewsEntity:
    type: str  # cve | cwe | cpe | ip | domain | hash | url | attack
    value: str


@dataclass
class EnrichedNews:
    news_id: Optional[int]
    title: str
    link: str
    source_name: str
    country: str
    entities: list[NewsEntity] = field(default_factory=list)
    products: list[str] = field(default_factory=list)


def extract_entities(text: str) -> list[NewsEntity]:
    """Extrait les entités cyber depuis un texte (titre + resume + contenu)."""
    if not text:
        return []
    entities: list[NewsEntity] = []
    seen = set()

    def add(t: str, v: str):
        key = (t, v.lower())
        if key not in seen:
            seen.add(key)
            entities.append(NewsEntity(type=t, value=v))

    for m in CVE_RE.findall(text):
        add("cve", m.upper())
    for m in CWE_RE.findall(text):
        add("cwe", m.upper())
    for m in ATTACK_RE.findall(text):
        add("attack", m.upper())
    for m in CPE_RE.findall(text):
        add("cpe", m.lower())
    for m in SHA256_RE.findall(text):
        add("hash", m.lower())
    for m in SHA1_RE.findall(text):
        add("hash", m.lower())
    for m in MD5_RE.findall(text):
        add("hash", m.lower())
    # IP : exclure les versions (ex: 1.2.3.4.5) et les ranges simples
    for m in IP_RE.findall(text):
        parts = [int(p) for p in m.split(".") if p.isdigit()]
        if len(parts) == 4 and all(0 <= p <= 255 for p in parts):
            add("ip", m)
    for m in URL_RE.findall(text):
        add("url", m.rstrip(".,);]"))
    for m in DOMAIN_RE.findall(text):
        m = m.rstrip(".")
        if m.lower() not in ("www", "http", "https", "ftp") and "." in m:
            add("domain", m.lower())
    return entities


def extract_attack_details(text: str) -> list[dict]:
    """Retourne les techniques ATT&CK avec nom + tactique associee."""
    found = []
    seen = set()
    for m in ATTACK_RE.findall(text):
        t = m.upper()
        if t in seen:
            continue
        seen.add(t)
        meta = ATTACK_TECHNIQUES.get(t, {"name": "Unknown Technique", "tactic": "Unknown"})
        found.append({"technique": t, "name": meta["name"], "tactic": meta["tactic"]})
    return found


def extract_products(text: str) -> list[str]:
    """Detecte les noms de produits/logiciels connus pour le regroupement."""
    if not text:
        return []
    found = set()
    low = text.lower()
    for kw in PRODUCT_KEYWORDS:
        if kw.lower() in low:
            found.add(kw.strip())
    return sorted(found)


def enrich_news(news_id: Optional[int], title: str, summary: str, content: str = "", link: str = "", source_name: str = "", country: str = "") -> EnrichedNews:
    text = f"{title}\n{summary}\n{content}"
    entities = extract_entities(text)
    products = extract_products(text)
    return EnrichedNews(
        news_id=news_id,
        title=title,
        link=link,
        source_name=source_name,
        country=country,
        entities=entities,
        products=products,
    )


def _title_similarity(a: str, b: str) -> float:
    """Similarite normalisee entre deux titres (0..1)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def score_incident(inc: dict) -> int:
    """
    Calcule un score de severite 0..100 pour un incident.
    Signaux : CVE KEV, IOC (ip/domain/hash), multi-sources, multi-pays,
    mots-cles critiques, techniques ATT&CK d'impact.
    """
    score = 0
    text_blob = " ".join(
        f"{n.get('title','')} {n.get('summary','')} {n.get('content','')}"
        for n in inc["news"]
    ).lower()

    # CVE present
    if inc.get("cves"):
        score += 20
        if any(k in text_blob for k in KEV_KEYWORDS):
            score += 25  # CVE activement exploitée = fort signal
    # IOC
    if inc.get("domains") or inc.get("ips") or inc.get("hashes"):
        score += 15
    # Multi-sources (correlation)
    score += min(len(inc.get("sources", [])) * 8, 24)
    # Multi-pays
    score += min(len(inc.get("countries", [])) * 5, 15)
    # Mots-cles severite
    if any(k in text_blob for k in CRITICAL_KEYWORDS):
        score += 10
    elif any(k in text_blob for k in HIGH_KEYWORDS):
        score += 5
    # Techniques ATT&CK d'impact (ransomware etc.)
    tactics = {t.get("tactic", "") for t in inc.get("attack_details", [])}
    if any("Impact" in t or "Ransomware" in t for t in tactics):
        score += 10

    return min(score, 100)


def build_incidents(news_list: list[dict], title_sim_threshold: float = 0.62) -> list[dict]:
    """
    Regroupe une liste de news en incidents unifies.
    Deux news appartiennent au meme incident si elles partagent :
      - au moins 1 CVE identique, OU
      - au moins 2 produits identiques, OU
      - au moins 1 domaine/hash identique (fort signal), OU
      - titre tres similaire (fuzzy, > title_sim_threshold) + au moins 1 produit commun.
    Retourne une liste d'incidents tries par score de severite puis nb de sources.
    """
    groups: list[dict] = []
    cve_to_group: dict[str, int] = {}
    domain_to_group: dict[str, int] = {}
    hash_to_group: dict[str, int] = {}
    ip_to_group: dict[str, int] = {}

    def _products_key(products):
        return tuple(sorted(p.lower() for p in products))

    prod_to_groups: dict[tuple, list[int]] = defaultdict(list)

    for n in news_list:
        blob = f"{n.get('title','')}\n{n.get('summary','')}\n{n.get('content','')}"
        ents = extract_entities(blob)
        prods = extract_products(blob)
        attack_details = extract_attack_details(blob)
        cves = {e.value for e in ents if e.type == "cve"}
        domains = {e.value for e in ents if e.type == "domain"}
        hashes = {e.value for e in ents if e.type == "hash"}
        ips = {e.value for e in ents if e.type == "ip"}
        pkey = _products_key(prods)

        candidate_groups = set()
        for c in cves:
            if c in cve_to_group:
                candidate_groups.add(cve_to_group[c])
        for d in domains:
            if d in domain_to_group:
                candidate_groups.add(domain_to_group[d])
        for h in hashes:
            if h in hash_to_group:
                candidate_groups.add(hash_to_group[h])
        for ip in ips:
            if ip in ip_to_group:
                candidate_groups.add(ip_to_group[ip])
        for g in prod_to_groups.get(pkey, []):
            candidate_groups.add(g)

        # Fuzzy titre : compare aux titres deja vus
        for g in groups:
            if g.get("merged") or g["id"] in candidate_groups:
                continue
            g_prods = {p.lower() for p in g["products"]}
            shared_prod = g_prods & {p.lower() for p in prods}
            for gn in g["news"]:
                sim = _title_similarity(n.get("title", ""), gn.get("title", ""))
                if sim >= title_sim_threshold and shared_prod:
                    candidate_groups.add(g["id"])
                    break

        if candidate_groups:
            target = min(candidate_groups)
            for g in candidate_groups:
                if g != target:
                    groups[target]["news"].extend(groups[g]["news"])
                    groups[g]["merged"] = True
            g = groups[target]
        else:
            groups.append({
                "id": len(groups),
                "news": [],
                "cves": set(),
                "products": set(),
                "domains": set(),
                "hashes": set(),
                "ips": set(),
                "attack_details": [],
                "sources": set(),
                "countries": set(),
                "merged": False,
            })
            g = groups[-1]

        g["news"].append(n)
        g["cves"] |= cves
        g["products"] |= set(prods)
        g["domains"] |= domains
        g["hashes"] |= hashes
        g["ips"] |= ips
        g["attack_details"].extend(attack_details)
        g["sources"].add(n.get("source_name", "?"))
        if n.get("country"):
            g["countries"].add(n["country"])

        for c in cves:
            cve_to_group[c] = g["id"]
        for d in domains:
            domain_to_group[d] = g["id"]
        for h in hashes:
            hash_to_group[h] = g["id"]
        for ip in ips:
            ip_to_group[ip] = g["id"]
        if pkey:
            prod_to_groups[pkey].append(g["id"])

    # Nettoyage + formatage
    incidents = []
    for g in groups:
        if g.get("merged"):
            continue
        if len(g["news"]) == 0:
            continue
        g["news"].sort(key=lambda x: x.get("published") or "", reverse=True)
        primary = g["news"][0]
        # dedupe attack_details
        seen_t = set()
        attack_clean = []
        for a in g["attack_details"]:
            if a["technique"] not in seen_t:
                seen_t.add(a["technique"])
                attack_clean.append(a)
        inc = {
            "incident_id": g["id"],
            "title": primary.get("title", "Incident"),
            "cves": sorted(g["cves"]),
            "products": sorted(g["products"]),
            "domains": sorted(g["domains"]),
            "hashes": sorted(g["hashes"]),
            "ips": sorted(g["ips"]),
            "attack_details": attack_clean,
            "sources": sorted(g["sources"]),
            "countries": sorted(g["countries"]),
            "num_sources": len(g["news"]),
            "news": g["news"],
            "primary_link": primary.get("link", ""),
        }
        inc["severity_score"] = score_incident(inc)
        incidents.append(inc)
    # Tri : score de severite d'abord, puis nb de sources
    incidents.sort(key=lambda i: (i["severity_score"], i["num_sources"]), reverse=True)
    return incidents
