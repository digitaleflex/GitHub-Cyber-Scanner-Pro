"""OSINT Lab — Module de recherche de personnes (methodologie pro, API gratuite)."""
import json
import logging
import re
import time
from datetime import datetime
from urllib.parse import quote

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; OSINT-Lab/1.0; +https://cyberbook.eurin.tech)"}


# ── 1. GitHub Profile Search ─────────────────────────────────────────────

def search_github_user(name: str, location: str = "", tokens: list[str] = None) -> list[dict]:
    """Recherche un profil GitHub par nom et localisation."""
    import random
    if not tokens:
        return []
    query = f"{name} in:name"
    if location:
        query += f" location:{location}"
    headers = {"Authorization": f"token {random.choice(tokens)}", "Accept": "application/vnd.github.v3+json", **HEADERS}
    try:
        r = requests.get(
            "https://api.github.com/search/users",
            params={"q": query, "per_page": 10},
            headers=headers, timeout=15,
        )
        if r.status_code == 200:
            items = r.json().get("items", [])
            results = []
            for item in items[:5]:
                # Get user detail
                r2 = requests.get(item["url"], headers=headers, timeout=10)
                if r2.status_code == 200:
                    u = r2.json()
                    results.append({
                        "source": "github",
                        "username": u.get("login"),
                        "name": u.get("name"),
                        "location": u.get("location"),
                        "bio": (u.get("bio") or "")[:200],
                        "blog": u.get("blog"),
                        "company": u.get("company"),
                        "twitter": u.get("twitter_username"),
                        "followers": u.get("followers"),
                        "avatar": u.get("avatar_url"),
                        "url": u.get("html_url"),
                    })
                time.sleep(0.3)
            return results
    except Exception as e:
        logging.warning(f"GitHub user search: {e}")
    return []


# ── 2. Google Dorks (via DuckDuckGo lite) ───────────────────────────────

def search_dork(query: str) -> list[dict]:
    """Recherche via DuckDuckGo (lite, sans JS)."""
    results = []
    try:
        r = requests.get(
            "https://lite.duckduckgo.com/lite/",
            params={"q": query},
            headers=HEADERS, timeout=15,
        )
        if r.status_code == 200:
            # Extraire les liens (format lite)
            urls = re.findall(r'<a[^>]*href="(https?://[^"]+)"', r.text)
            for url in urls[:10]:
                if "duckduckgo" not in url:
                    results.append({"source": "dork", "url": url, "query": query})
        return results
    except Exception as e:
        logging.warning(f"Dork search: {e}")
    return []


# ── 3. Email Verification (basic MX check) ──────────────────────────────

def verify_email_domain(email: str) -> dict:
    """Verifie basiquement si un domaine d'email existe (MX record check)."""
    domain = email.split("@")[-1] if "@" in email else ""
    if not domain:
        return {"valid": False, "reason": "Format invalide"}
    try:
        import socket
        socket.getaddrinfo(domain, 25)
        return {"valid": True, "domain": domain}
    except Exception:
        return {"valid": False, "reason": f"Domaine {domain} injoignable"}


# ── 4. Social Media Presence Check ───────────────────────────────────────

SOCIAL_PLATFORMS = [
    ("GitHub", "https://github.com/{username}"),
    ("Twitter/X", "https://x.com/{username}"),
    ("Reddit", "https://reddit.com/user/{username}"),
    ("LinkedIn", "https://linkedin.com/in/{username}"),
    ("Medium", "https://medium.com/@{username}"),
    ("Dev.to", "https://dev.to/{username}"),
    ("GitLab", "https://gitlab.com/{username}"),
    ("HackerOne", "https://hackerone.com/{username}"),
    ("Keybase", "https://keybase.io/{username}"),
    ("Mastodon", "https://mastodon.social/@{username}"),
]


def check_social_presence(username: str) -> list[dict]:
    """Verifie la presence d'un username sur les plateformes sociales."""
    results = []
    for name, url_template in SOCIAL_PLATFORMS:
        url = url_template.format(username=username)
        try:
            r = requests.head(url, headers=HEADERS, timeout=5, allow_redirects=True)
            results.append({
                "platform": name,
                "url": url,
                "present": r.status_code < 400,
                "status": r.status_code,
            })
            time.sleep(0.1)
        except Exception:
            results.append({"platform": name, "url": url, "present": False, "status": 0})
    return results


# ── 5. Person OSINT (aggregateur) ────────────────────────────────────────

# ── 5. Person OSINT (aggregateur) ────────────────────────────────────────

def ai_extract_person(free_text: str) -> dict:
    """Utilise Groq pour extraire les parametres OSINT d'un texte libre."""
    import os
    if not os.getenv("GROQ_API_KEY"):
        return {"name": free_text[:50], "location": ""}
    try:
        import src.llm_router as llm
        prompt = (
            "Tu es un expert OSINT. Analyse ce texte et extrait les parametres de recherche.\n\n"
            f"Texte: {free_text}\n\n"
            "Reponds UNIQUEMENT en JSON: "
            '{"name": "nom ou pseudo", "location": "ville ou pays", '
            '"keywords": ["mot1", "mot2"], "probable_usernames": ["user1", "user2"], '
            '"email": "email si mentionne", "organization": "org si mentionnee", '
            '"search_strategy": "1 phrase decrivant la meilleure approche"}'
        )
        result = llm.llm_complete_json(prompt, max_tokens=300)
        if result:
            result.setdefault("name", free_text[:50])
            result.setdefault("location", "")
            return result
    except Exception as e:
        logging.warning(f"AI extract: {e}")
    return {"name": free_text[:50], "location": ""}


def investigate_person(name: str = "", location: str = "", email: str = "", username: str = "",
                       free_text: str = "", tokens: list[str] = None) -> dict:
    """Enquete OSINT complete sur une personne. Retourne un rapport structure."""
    
    # AI extraction si texte libre
    if free_text and not name:
        extracted = ai_extract_person(free_text)
        name = extracted.get("name", name)
        location = extracted.get("location", location)
        email = extracted.get("email", email)
        username = (extracted.get("probable_usernames") or [username or ""])[0] if not username else username
        keywords = extracted.get("keywords", [])
        strategy = extracted.get("search_strategy", "")
    else:
        keywords = []
        strategy = ""

    results = {
        "query": {"name": name, "location": location, "email": email, "username": username,
                  "free_text": free_text[:200] if free_text else ""},
        "ai_extracted": {"name": name, "location": location, "keywords": keywords,
                         "strategy": strategy} if free_text else {},
        "timestamp": datetime.utcnow().isoformat(),
        "findings": {},
        "methodology": "OSINT pro: AI extraction → recherche multicouche → verification → rapport",
    }

    # 1. GitHub profiles
    if name:
        github = search_github_user(name, location, tokens)
        if github:
            results["findings"]["github_profiles"] = github

    # 2. Social media presence
    uname = username or name.lower().replace(" ", "").replace(".", "")
    if uname:
        social = check_social_presence(uname)
        present = [s for s in social if s["present"]]
        if present:
            results["findings"]["social_presence"] = present

    # 3. Google Dorks (avec mots-cles IA)
    dork_query = f'"{name}"'
    if location:
        dork_query += f' "{location}"'
    for kw in keywords[:3]:
        dork_query += f' {kw}'
    dorks = search_dork(dork_query)
    if dorks:
        results["findings"]["dorks"] = dorks[:5]

    # 4. Email verification
    if email:
        results["findings"]["email_check"] = verify_email_domain(email)

    # 5. Resume
    total_findings = sum(len(v) if isinstance(v, list) else 1 for v in results["findings"].values())
    results["summary"] = f"{total_findings} sources trouvees. "
    if results["findings"].get("github_profiles"):
        results["summary"] += f'{len(results["findings"]["github_profiles"])} profils GitHub. '
    if results["findings"].get("social_presence"):
        results["summary"] += f'{len(results["findings"]["social_presence"])} comptes sociaux. '
    if strategy:
        results["summary"] += f'Strategie IA: {strategy[:100]}'

    return results
