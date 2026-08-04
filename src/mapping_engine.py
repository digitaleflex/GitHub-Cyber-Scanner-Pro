"""Moteur de corrélation CTI : relie chaque CVE aux référentiels MITRE.

Remplit 4 tables de mapping (vides jusqu'ici) pour une vue 360 d'une CVE :
  - cve_attack_mapping   (CVE ↔ technique ATT&CK)        -> LLM (Groq) + seed NVD
  - cve_campaign_mapping (CVE ↔ campagne / APT)         -> transitif via STIX `uses`
  - cve_capec_mapping     (CVE ↔ CAPEC)                  -> par CWE (seed statique)
  - cve_iocs              (CVE ↔ IOC)                    -> heuristique acteur/malware

Approche :
  * ATT&CK : MITRE et NVD ne lient quasiment jamais les CVE aux techniques (~0 refs
    directes). On utilise donc un LLM (Groq) pour associer une CVE à des techniques,
    après pré-filtrage par recouvrement de tokens pour limiter les tokens/couts.
  * Campagne/APT : on charge le graphe STIX (relations `uses`) depuis le bundle local
    et on remonte technique -> intrusion-set / campaign.
  * IOC : on remonte technique -> acteur -> malware, puis on matche le malware contre
    les tags du ioc_feed (abuse.ch / ThreatFox). Confiance faible (heuristique).
"""
import json
import logging
import os
import re
import threading

import requests
from dotenv import load_dotenv

from src import database

load_dotenv()

STIX_PATH = os.getenv("DATA_DIR", "data") + "/mitre_attack_enterprise.json"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

_lock = threading.Lock()
_graph = None

# ── Seed CWE -> CAPEC (mapping statique, CAPEC data indisponible en ligne) ──
_CWE_TO_CAPEC = {
    "CWE-79": ("CAPEC-63", "XSS (Cross-Site Scripting)"),
    "CWE-89": ("CAPEC-66", "SQL Injection"),
    "CWE-78": ("CAPEC-88", "Command Injection"),
    "CWE-22": ("CAPEC-126", "Path Traversal"),
    "CWE-352": ("CAPEC-62", "Cross-Site Request Forgery"),
    "CWE-287": ("CAPEC-114", "Authentication Abuse"),
    "CWE-306": ("CAPEC-94", "Authentication Bypass by Alternate Path"),
    "CWE-327": ("CAPEC-97", "Cryptanalysis"),
    "CWE-502": ("CAPEC-586", "Deserialization of Untrusted Data"),
    "CWE-434": ("CAPEC-644", "File Upload to Web Server"),
    "CWE-918": ("CAPEC-664", "Server-Side Request Forgery"),
    "CWE-416": ("CAPEC-52", "Buffer Overflow via Argument Expansion"),
    "CWE-119": ("CAPEC-100", "Overflow Buffers"),
    "CWE-200": ("CAPEC-116", "Information Disclosure"),
    "CWE-94": ("CAPEC-242", "Code Injection"),
    "CWE-310": ("CAPEC-97", "Cryptanalysis"),
    "CWE-732": ("CAPEC-17", "Accessing/Modifying Critical State Variables"),
    "CWE-862": ("CAPEC-122", "Exploitation of Authorization"),
    "CWE-863": ("CAPEC-122", "Exploitation of Authorization"),
    "CWE-284": ("CAPEC-122", "Exploitation of Authorization"),
    "CWE-798": ("CAPEC-191", "Hardware Design Specifications are Weak"),
    "CWE-269": ("CAPEC-132", "Privilege Escalation"),
    "CWE-250": ("CAPEC-132", "Privilege Escalation"),
    "CWE-611": ("CAPEC-211", "XML External Entities Blowup"),
    "CWE-476": ("CAPEC-46", "Buffer Overflow via Parameter Expansion"),
    "CWE-125": ("CAPEC-100", "Overflow Buffers"),
    "CWE-400": ("CAPEC-130", "Resource Exhaustion"),
    "CWE-20": ("CAPEC-123", "Input Data Manipulation"),
    "CWE-74": ("CAPEC-242", "Code Injection"),
    "CWE-190": ("CAPEC-100", "Overflow Buffers"),
    "CWE-521": ("CAPEC-112", "Brute Force"),
    "CWE-307": ("CAPEC-112", "Brute Force"),
    "CWE-640": ("CAPEC-112", "Brute Force"),
    "CWE-83": ("CAPEC-63", "XSS"),
    "CWE-613": ("CAPEC-114", "Authentication Abuse"),
    "CWE-288": ("CAPEC-114", "Authentication Abuse"),
    "CWE-290": ("CAPEC-114", "Authentication Abuse"),
    "CWE-494": ("CAPEC-185", "Malicious Software Update"),
    "CWE-829": ("CAPEC-185", "Inclusion of Untrusted Code"),
}


def _load_graph():
    """Charge le bundle STIX en mémoire et construit les index de relations.

    Retourne un dict avec :
      tech_by_id, name_index [(tid, name_lower, tokens)],
      uses_src[src] = set(dst), obj_by_id[type,name]->id, obj_name[id]->name
    """
    global _graph
    if _graph:
        return _graph

    bundle = {"objects": []}
    if os.path.exists(STIX_PATH):
        with open(STIX_PATH, encoding="utf-8") as f:
            bundle = json.load(f)

    tech_by_id = {}
    name_index = []
    obj_by_id = {}
    uses_src = {}        # src_ref -> set(dst_ref)
    obj_name_to_db = {}  # (type, name_lower) -> db id (rempli après requête DB)

    STOP = set("the a an of to in on for and or with via using by from is are be as at".split())

    for o in bundle.get("objects", []):
        oid = o.get("id")
        otype = o.get("type")
        if oid:
            obj_by_id[oid] = o
        if otype == "attack-pattern":
            refs = o.get("external_references", []) or []
            tid = refs[0].get("external_id") if refs else None
            if not tid:
                continue
            name = o.get("name", "") or ""
            desc = o.get("description", "") or ""
            tech_by_id[tid] = {"name": name, "desc": desc}
            tokens = set(re.findall(r"[a-z0-9]{3,}", (name + " " + desc).lower())) - STOP
            name_index.append((tid, name.lower(), tokens))
        elif otype == "relationship" and o.get("relationship_type") == "uses":
            uses_src.setdefault(o.get("source_ref"), set()).add(o.get("target_ref"))

    _graph = {
        "tech_by_id": tech_by_id,
        "name_index": name_index,
        "uses_src": uses_src,
        "obj_by_id": obj_by_id,
    }
    return _graph


def _attack_ext_id(o):
    refs = o.get("external_references", []) or []
    return refs[0].get("external_id") if refs else None


# ── LLM ATT&CK ──────────────────────────────────────────────────────────────

def _candidate_techniques(description: str, limit: int = 25):
    g = _load_graph()
    desc_tokens = set(re.findall(r"[a-z0-9]{3,}", (description or "").lower()))
    STOP = set("the a an of to in on for and or with via using by from is are be as at this that".split())
    desc_tokens -= STOP
    scored = []
    for tid, _name_lower, tokens in g["name_index"]:
        overlap = len(desc_tokens & tokens)
        if overlap:
            scored.append((overlap, tid, g["tech_by_id"][tid]["name"]))
    scored.sort(reverse=True)
    return scored[:limit]


def _llm_attack(cve_id: str, description: str):
    """Demande au LLM les techniques ATT&CK pertinentes pour une CVE."""
    if not GROQ_API_KEY:
        return []
    cands = _candidate_techniques(description)
    if not cands:
        return []
    lines = "\n".join(f"- {tid}: {name}" for _, tid, name in cands)
    prompt = (
        "Tu es un expert MITRE ATT&CK. Voici des techniques candidates (id: nom) "
        "issues du recouvrement de mots-cles avec la description d'une CVE.\n\n"
        f"CVE: {cve_id}\nDescription: {description}\n\n"
        "Techniques candidates:\n" + lines + "\n\n"
        "Renvoie UNIQUEMENT un tableau JSON des IDs de techniques DIRECTEMENT "
        "et clairement liees a cette vulnerabilite (exploitation, vecteur ou impact). "
        "Si aucune ne convient, renvoie []. Exemple: [\"T1190\",\"T1133\"]"
    )
    try:
        r = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 200, "temperature": 0.1},
            timeout=25,
        )
        if r.status_code != 200:
            return []
        raw = r.json()["choices"][0]["message"]["content"].strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        ids = json.loads(raw)
        if not isinstance(ids, list):
            return []
        valid = set(_load_graph()["tech_by_id"].keys())
        return [i for i in ids if i in valid][:8]
    except Exception as e:
        logging.error(f"LLM ATT&CK {cve_id}: {e}")
        return []


def _seed_nvd_attack(cve_id: str, references_urls: str):
    """Extrait les IDs de techniques ATT&CK des refs NVD (ex. attack.mitre.org/T1190)."""
    if not references_urls:
        return []
    found = re.findall(r"attack\.mitre\.org/techniques/([A-Za-z0-9/.]+)", references_urls)
    g = _load_graph()
    valid = set(g["tech_by_id"].keys())
    out = []
    for f in found:
        # NVD utilise parfois un slash (T1574/001) ; le STIX utilise un point (T1574.001)
        tid = f.replace("/", ".").upper()
        if tid in valid:
            out.append(tid)
        elif tid.startswith("T") and tid[1:].isdigit():
            out.append(tid)  # technique principale sans sous-technique
    return list(dict.fromkeys(out))


# ── Persistance ─────────────────────────────────────────────────────────────

def _save_attack(cve_id, mappings):
    """mappings: list of (technique_id, confidence, source)."""
    if not mappings:
        return 0
    conn = database.get_db_connection()
    cur = conn.cursor()
    n = 0
    for tid, conf, _src in mappings:
        cur.execute(
            "INSERT INTO cve_attack_mapping (cve_id, technique_id, confidence) "
            "VALUES (%s, %s, %s) ON CONFLICT (cve_id, technique_id) DO UPDATE SET confidence = GREATEST(cve_attack_mapping.confidence, EXCLUDED.confidence)",
            (cve_id, tid, conf),
        )
        n += 1
    conn.commit()
    cur.close()
    conn.close()
    return n


def _campaign_ids_for_techniques(technique_ids):
    """Remonte technique -> intrusion-set / campaign via STIX `uses`."""
    g = _load_graph()
    uses_src = g["uses_src"]
    obj_by_id = g["obj_by_id"]
    sources = set()
    for tid in technique_ids:
        tref = None
        for oid, o in obj_by_id.items():
            if o.get("type") == "attack-pattern" and _attack_ext_id(o) == tid:
                tref = oid
                break
        if not tref:
            continue
        for src, dsts in uses_src.items():
            if tref in dsts:
                so = obj_by_id.get(src)
                if so and so.get("type") in ("intrusion-set", "campaign"):
                    sources.add((so["type"], so.get("name", "")))
    # resolver vers DB ids (campaigns). Les intrusion-set (APT) sont relies aux
    # campagnes via campaigns.threat_actor_id.
    conn = database.get_db_connection()
    cur = conn.cursor()
    out = []
    for otype, name in sources:
        if otype == "campaign":
            cur.execute("SELECT id FROM campaigns WHERE LOWER(name)=LOWER(%s) LIMIT 1", (name,))
            row = cur.fetchone()
            if row:
                out.append(row[0])
        else:  # intrusion-set -> campagnes de cet acteur
            cur.execute(
                "SELECT id FROM campaigns WHERE threat_actor_id = "
                "(SELECT id FROM apt_groups WHERE LOWER(name)=LOWER(%s))",
                (name,),
            )
            for (cid,) in cur.fetchall():
                out.append(cid)
    cur.close()
    conn.close()
    return list(dict.fromkeys(out))


def _save_campaigns(cve_id, campaign_ids):
    if not campaign_ids:
        return 0
    conn = database.get_db_connection()
    cur = conn.cursor()
    n = 0
    for db_id in campaign_ids:
        cur.execute(
            "INSERT INTO cve_campaign_mapping (cve_id, campaign_id) VALUES (%s, %s) "
            "ON CONFLICT (cve_id, campaign_id) DO NOTHING",
            (cve_id, db_id),
        )
        n += 1
    conn.commit()
    cur.close()
    conn.close()
    return n


def _save_capec(cve_id, cwe_list):
    if not cwe_list:
        return 0
    conn = database.get_db_connection()
    cur = conn.cursor()
    n = 0
    for cwe in cwe_list:
        cap = _CWE_TO_CAPEC.get(cwe)
        if not cap:
            continue
        capec_id, capec_name = cap
        cur.execute(
            "INSERT INTO capec_patterns (capec_id, name) VALUES (%s, %s) "
            "ON CONFLICT (capec_id) DO NOTHING",
            (capec_id, capec_name),
        )
        cur.execute(
            "INSERT INTO cve_capec_mapping (cve_id, capec_id) VALUES (%s, %s) "
            "ON CONFLICT (cve_id, capec_id) DO NOTHING",
            (cve_id, capec_id),
        )
        n += 1
    conn.commit()
    cur.close()
    conn.close()
    return n


def _save_iocs(cve_id, technique_ids):
    """Heuristique : technique -> acteur -> malware -> IOC (tags abuse.ch)."""
    g = _load_graph()
    uses_src = g["uses_src"]
    obj_by_id = g["obj_by_id"]
    # techniques -> acteurs
    actors = set()
    for tid in technique_ids:
        tref = None
        for oid, o in obj_by_id.items():
            if o.get("type") == "attack-pattern" and _attack_ext_id(o) == tid:
                tref = oid
                break
        if not tref:
            continue
        for src, dsts in uses_src.items():
            if tref in dsts:
                so = obj_by_id.get(src)
                if so and so.get("type") == "intrusion-set":
                    actors.add(src)
    # acteurs -> malware names
    malware_names = set()
    for a in actors:
        for dst in uses_src.get(a, set()):
            so = obj_by_id.get(dst)
            if so and so.get("type") == "malware":
                malware_names.add(so.get("name", "").lower())
    if not malware_names:
        return 0
    conn = database.get_db_connection()
    cur = conn.cursor()
    # Limite par CVE pour eviter l'explosion de correspondances heuristiques
    MAX_PER_CVE = 25
    inserted = set()
    n = 0
    for mname in malware_names:
        if len(mname) < 5:
            continue
        mlow = mname.lower()
        # match token exact sur tags (pas sous-chaine) pour limiter le bruit
        cur.execute(
            "SELECT id, tags, value FROM ioc_feed "
            "WHERE LOWER(tags) LIKE %s OR LOWER(value) LIKE %s LIMIT 200",
            (f"%{mlow}%", f"%{mlow}%"),
        )
        for ioc_id, tags, value in cur.fetchall():
            if ioc_id in inserted:
                continue
            haystack = f"{(tags or '')} {(value or '')}".lower()
            if re.search(r"(?:^|[^a-z0-9])" + re.escape(mlow) + r"(?:[^a-z0-9]|$)", haystack):
                cur.execute(
                    "INSERT INTO cve_iocs (cve_id, ioc_id, confidence) VALUES (%s, %s, 2) "
                    "ON CONFLICT (cve_id, ioc_id) DO NOTHING",
                    (cve_id, ioc_id),
                )
                inserted.add(ioc_id)
                n += 1
                if len(inserted) >= MAX_PER_CVE:
                    break
        if len(inserted) >= MAX_PER_CVE:
            break
    conn.commit()
    cur.close()
    conn.close()
    return n


# ── Orchestration ───────────────────────────────────────────────────────────

def map_cve(cve_id: str, description: str = "", references_urls: str = "", weaknesses: str = ""):
    """Mappe une CVE vers ATT&CK + campagne + CAPEC + IOC. Retourne stats."""
    # ATT&CK
    mappings = []
    for tid in _seed_nvd_attack(cve_id, references_urls):
        mappings.append((tid, 5, "nvd_ref"))
    for tid in _llm_attack(cve_id, description):
        mappings.append((tid, 4, "llm"))
    n_attack = _save_attack(cve_id, mappings)

    technique_ids = [m[0] for m in mappings]
    n_campaign = 0
    n_ioc = 0
    if technique_ids:
        sources = _campaign_ids_for_techniques(technique_ids)
        n_campaign = _save_campaigns(cve_id, sources)
        n_ioc = _save_iocs(cve_id, technique_ids)

    cwe_list = [w.strip() for w in (weaknesses or "").split(",") if w.strip().startswith("CWE")]
    n_capec = _save_capec(cve_id, cwe_list)

    return {"attack": n_attack, "campaign": n_campaign, "capec": n_capec, "ioc": n_ioc}


def run_mapping(batch_limit: int = 200, only_kev: bool = True):
    """Mappe un lot de CVE prioritaires (KEV + critiques). Retourne stats globales."""
    if not _lock.acquire(blocking=False):
        return {"error": "already_running"}
    stats = {"processed": 0, "attack": 0, "campaign": 0, "capec": 0, "ioc": 0}
    try:
        conn = database.get_db_connection()
        cur = conn.cursor()
        if only_kev:
            cur.execute(
                """SELECT c.cve_id, c.description, c.references_urls, c.weaknesses
                   FROM cve_entries c JOIN cve_kev k ON k.cve_id = c.cve_id
                   WHERE NOT EXISTS (SELECT 1 FROM cve_attack_mapping m WHERE m.cve_id = c.cve_id)
                   ORDER BY c.cvss_score DESC NULLS LAST LIMIT %s""",
                (batch_limit,),
            )
        else:
            cur.execute(
                """SELECT cve_id, description, references_urls, weaknesses
                   FROM cve_entries
                   WHERE (description IS NOT NULL AND description != '')
                     AND NOT EXISTS (SELECT 1 FROM cve_attack_mapping m WHERE m.cve_id = cve_entries.cve_id)
                   ORDER BY
                     CASE WHEN weaknesses ILIKE '%CISA_KEV%' THEN 0 ELSE 1 END,
                     cvss_score DESC NULLS LAST
                   LIMIT %s""",
                (batch_limit,),
            )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        for cve_id, desc, refs, weak in rows:
            r = map_cve(cve_id, desc or "", refs or "", weak or "")
            stats["processed"] += 1
            stats["attack"] += r["attack"]
            stats["campaign"] += r["campaign"]
            stats["capec"] += r["capec"]
            stats["ioc"] += r["ioc"]
            if stats["processed"] % 25 == 0:
                logging.info(f"🗺️ Mapping: {stats['processed']} CVE traitées (ATT&CK={stats['attack']})")
    except Exception as e:
        logging.error(f"❌ Erreur mapping: {e}")
        stats["error"] = str(e)
    finally:
        _lock.release()
    logging.info(f"✅ Mapping terminé: {stats}")
    return stats
