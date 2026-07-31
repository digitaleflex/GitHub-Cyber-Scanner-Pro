"""OSINT Pro — Enquete professionnelle: Email, Phone, WHOIS, Cross-reference, Rapport."""
import json
import logging
import re
import time
from datetime import datetime, timezone

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; OSINT-Pro/1.0)"}


# ── 1. EMAIL OSINT ──────────────────────────────────────────────────────

def check_email_breaches(email: str) -> dict:
    """Verifie si l'email apparait dans des breaches connues (HaveIBeenPwned API)."""
    try:
        r = requests.get(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
            headers={"hibp-api-key": "", "User-Agent": "CyberScan-Pro"},  # API gratuite sans cle
            timeout=10,
        )
        if r.status_code == 200:
            breaches = r.json()
            return {
                "found": True,
                "breaches": [{"name": b.get("Name"), "date": b.get("BreachDate"),
                              "data_classes": b.get("DataClasses", [])[:5]}
                            for b in breaches[:5]],
                "count": len(breaches),
            }
        elif r.status_code == 404:
            return {"found": False, "breaches": [], "note": "Aucune breach connue (base HIBP)"}
    except Exception as e:
        logging.warning(f"HIBP: {e}")
    return {"found": False, "error": "API indisponible"}


def search_pastebin(email: str) -> list[dict]:
    """Cherche l'email dans les pastebins publiques via Google Dorks."""
    dork = f'site:pastebin.com "{email}"'
    try:
        r = requests.get(
            "https://lite.duckduckgo.com/lite/",
            params={"q": dork},
            headers=HEADERS, timeout=10,
        )
        if r.status_code == 200:
            urls = re.findall(r'pastebin\.com/[a-zA-Z0-9]+', r.text)
            return [{"url": f"https://pastebin.com/{u}", "source": "pastebin"} for u in set(urls)[:5]]
    except Exception:
        pass
    return []


# ── 2. PHONE OSINT ──────────────────────────────────────────────────────

def analyze_phone(phone: str) -> dict:
    """Analyse basique d'un numero de telephone."""
    clean = re.sub(r'[^\d+]', '', phone)
    result = {"raw": phone, "clean": clean, "valid": len(clean) >= 7}

    # Country detection
    if clean.startswith("+32"):
        result["country"] = "Belgique"
        result["country_code"] = "+32"
    elif clean.startswith("+33"):
        result["country"] = "France"
        result["country_code"] = "+33"
    elif clean.startswith("+1"):
        result["country"] = "USA/Canada"
    elif clean.startswith("+44"):
        result["country"] = "UK"
    elif clean.startswith("+49"):
        result["country"] = "Allemagne"
    elif clean.startswith("+41"):
        result["country"] = "Suisse"

    # Numverify API (gratuit, 250 req/mois)
    try:
        r = requests.get(
            f"http://apilayer.net/api/validate",
            params={"access_key": "demo", "number": clean, "format": 1},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("valid"):
                result["carrier"] = data.get("carrier", "")
                result["line_type"] = data.get("line_type", "")
                result["location"] = data.get("location", "")
    except Exception:
        pass

    return result


# ── 3. DOMAIN / WHOIS ────────────────────────────────────────────────────

def lookup_domain(domain: str) -> dict:
    """WHOIS/RDAP lookup gratuit."""
    clean = domain.lower().replace("https://", "").replace("http://", "").split("/")[0]

    # RDAP lookup (gratuit, pas de rate limit)
    try:
        r = requests.get(f"https://rdap.org/domain/{clean}", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            entities = []
            for e in data.get("entities", []):
                vcard = e.get("vcardArray", [[], []])
                props = {p[0]: p[3] for p in vcard[1] if len(p) > 3} if len(vcard) > 1 else {}
                entities.append({
                    "role": e.get("roles", ["unknown"])[0],
                    "name": props.get("fn", ""),
                    "org": props.get("org", ""),
                    "email": props.get("email", ""),
                    "country": props.get("adr", [{}])[0].get("cc", "") if props.get("adr") else "",
                })
            return {
                "domain": clean,
                "status": [s.get("status") for s in data.get("status", [])],
                "nameservers": [n.get("ldhName") for n in data.get("nameservers", [])],
                "entities": entities,
                "registered": [e.get("eventDate") for e in data.get("events", []) if e.get("eventAction") == "registration"],
            }
    except Exception:
        pass

    return {"domain": clean, "error": "RDAP indisponible"}


# ── 4. CROSS-REFERENCE ──────────────────────────────────────────────────

def cross_reference(findings: dict) -> dict:
    """Correle automatiquement les trouvailles entre plateformes."""
    refs = {"matches": [], "insights": []}

    github = findings.get("github_profiles", [])
    social = findings.get("social_presence", [])

    # Meme username sur plusieurs plateformes
    if github and social:
        gh_usernames = {p.get("username", "").lower() for p in github}
        social_platforms = [s for s in social if s.get("present")]
        for s in social_platforms:
            plat_username = s.get("url", "").split("/")[-1].lower()
            if plat_username in gh_usernames:
                refs["matches"].append({
                    "type": "username_shared",
                    "username": plat_username,
                    "platforms": ["github"] + [s["platform"]],
                    "confidence": "eleve",
                })

    # Meme localisation
    locations = set()
    for p in github:
        loc = p.get("location", "")
        if loc:
            locations.add(loc.lower())
    if len(locations) == 1 and locations:
        refs["insights"].append(f"Localisation unique trouvee: {list(locations)[0]}")

    return refs


# ── 5. RAPPORT PRO ──────────────────────────────────────────────────────

def generate_report(target: dict, findings: dict, pipeline_results: dict = None) -> dict:
    """Genere un rapport OSINT professionnel."""
    report = {
        "report_id": f"OSINT-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target": target,
        "methodology": "OSINT Pro v2: collecte multi-source → verification croisee → analyse IA → rapport",
        "findings_summary": {},
        "findings_detail": findings,
        "cross_references": cross_reference(findings),
        "confidence_assessment": _assess_confidence(findings),
        "legal_notice": "Rapport genere a partir de sources publiques uniquement. Aucune donnee privee n'a ete accedee.",
    }

    # Resume
    gh = findings.get("github_profiles", [])
    social = [s for s in findings.get("social_presence", []) if s.get("present")]
    breaches = findings.get("email_breaches", {}).get("breaches", [])
    report["findings_summary"] = {
        "github_profiles": len(gh),
        "social_platforms": len(social),
        "breaches": len(breaches),
        "total_sources": len(gh) + len(social) + len(breaches),
    }

    return report


def _assess_confidence(findings: dict) -> dict:
    """Evalue le niveau de confiance des trouvailles."""
    score = 0
    details = []

    gh = findings.get("github_profiles", [])
    if gh:
        score += 30
        details.append("Profils GitHub trouves (+30)")
        # Nom + location match = confiance elevee
        for p in gh:
            if p.get("name") and p.get("location"):
                score += 10
                details.append("Nom + localisation confirmes (+10)")
                break

    social = [s for s in findings.get("social_presence", []) if s.get("present")]
    if len(social) >= 3:
        score += 20
        details.append(f"Presence sur {len(social)} plateformes (+20)")

    breaches = findings.get("email_breaches", {}).get("breaches", [])
    if breaches:
        score += 15
        details.append(f"{len(breaches)} breaches trouvees (+15)")

    if findings.get("domain_info", {}).get("entities"):
        score += 10
        details.append("WHOIS/RDAP disponible (+10)")

    return {
        "score": min(100, score),
        "level": "ELEVE" if score >= 70 else "MOYEN" if score >= 40 else "FAIBLE",
        "details": details,
    }
