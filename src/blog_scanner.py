"""Blog Intelligence — surveille 50+ blogs securite via RSS/Atom, resume IA."""
import logging
import os
import re
import time
from datetime import datetime, timezone
from xml.etree import ElementTree

import requests

GROQ_KEY = os.getenv("GROQ_API_KEY", "")
HF_KEY = os.getenv("HF_API_KEY", "")

BLOGS = [
    # Google / Microsoft
    ("Google Security", "https://security.googleblog.com/feeds/posts/default"),
    ("Microsoft Security", "https://www.microsoft.com/en-us/security/blog/feed/"),
    # Cisco / Palo Alto
    ("Cisco Talos", "https://blog.talosintelligence.com/feed/"),
    ("Unit42 (Palo Alto)", "https://unit42.paloaltonetworks.com/feed/"),
    # EDR / Threat Intel
    ("CrowdStrike", "https://www.crowdstrike.com/blog/feed/"),
    ("Mandiant", "https://www.mandiant.com/resources/blog/rss.xml"),
    # Offsec / Consulting
    ("PortSwigger", "https://portswigger.net/research/rss"),
    ("NCC Group", "https://research.nccgroup.com/feed/"),
    ("BishopFox", "https://bishopfox.com/blog/rss.xml"),
    ("Trail of Bits", "https://blog.trailofbits.com/feed/"),
    # Cloud
    ("AWS Security", "https://aws.amazon.com/blogs/security/feed/"),
    ("Cloudflare", "https://blog.cloudflare.com/rss/"),
    # Vendors
    ("Snyk", "https://snyk.io/blog/feed/"),
    ("Aqua Security", "https://blog.aquasec.com/rss.xml"),
    ("Wiz", "https://www.wiz.io/feed/rss.xml"),
    ("Datadog Security", "https://www.datadoghq.com/blog/feed/"),
    # GitHub / GitLab
    ("GitHub Security Lab", "https://github.blog/category/security/feed/"),
    ("GitLab Security", "https://about.gitlab.com/blog/categories/security/feed/"),
    # CERT / Gouv
    ("CERT-FR", "https://www.cert.ssi.gouv.fr/feed/"),
    ("CISA", "https://www.cisa.gov/cybersecurity-advisories/feed"),
    # Communities
    ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
    ("BleepingComputer", "https://www.bleepingcomputer.com/feed/"),
    ("Schneier on Security", "https://www.schneier.com/feed/"),
    ("Krebs on Security", "https://krebsonsecurity.com/feed/"),
    # Project Discovery
    ("ProjectDiscovery Blog", "https://blog.projectdiscovery.io/feed/"),
    # Elastic
    ("Elastic Security", "https://www.elastic.co/security-labs/rss"),
    # SentinelOne
    ("SentinelOne", "https://www.sentinelone.com/blog/feed/"),
    # Rapid7
    ("Rapid7", "https://www.rapid7.com/blog/rss/"),
    # Sophos
    ("Sophos Naked Security", "https://nakedsecurity.sophos.com/feed/"),
    # Trend Micro
    ("Trend Micro", "https://www.trendmicro.com/en_us/research.html"),
]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CyberScan-Pro/2.3)"}


def fetch_feed(url: str) -> list[dict]:
    """Parse un flux RSS/Atom et retourne les articles."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return []
        root = ElementTree.fromstring(r.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        items = []
        for entry in root.findall(".//item") or root.findall(".//atom:entry", ns) or root.findall(".//entry"):
            title = (entry.findtext("title") or "").strip()
            link = ""
            for tag in ["link", "{http://www.w3.org/2005/Atom}link"]:
                el = entry.find(tag)
                if el is not None:
                    link = el.get("href") or el.text or ""
                    break
            if not link:
                link = entry.findtext("link") or ""
            desc = (entry.findtext("description") or entry.findtext("summary") or entry.findtext("{http://www.w3.org/2005/Atom}summary") or "")
            pub = entry.findtext("pubDate") or entry.findtext("published") or entry.findtext("{http://www.w3.org/2005/Atom}published") or ""
            if title and link:
                items.append({"title": title[:300], "link": link[:500], "description": _clean_html(desc)[:500], "published": pub})
        return items[:3]  # top 3 par source
    except Exception as e:
        logging.debug(f"Blog feed {url}: {e}")
        return []


def _clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _summarize(text: str, max_len: int = 100) -> str:
    """Resume via Groq ou HF (bart-large-cnn)."""
    if not text:
        return ""
    if GROQ_KEY:
        try:
            import src.llm_router as llm
            prompt = f"Resume cet article en 1 phrase (francais, max 100 chars):\n\n{text[:1500]}"
            result = llm.llm_complete(prompt, max_tokens=100, temperature=0.3)
            return result.strip()[:max_len]
        except Exception:
            pass
    if HF_KEY:
        try:
            import src.hf_client as hf
            return hf.summarize(text, max_len=max_len)[:max_len]
        except Exception:
            pass
    return text[:max_len] + "..." if len(text) > max_len else text


def scan_all(limit_per_source: int = 3) -> int:
    """Scanne tous les blogs et sauvegarde les articles en DB. Retourne nb sauvegardes."""
    from src import database

    conn = database.get_db_connection()
    cursor = conn.cursor()
    # Creer la table si elle n'existe pas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blog_posts (
            id SERIAL PRIMARY KEY,
            title VARCHAR(500),
            link VARCHAR(1000) UNIQUE,
            source_name VARCHAR(100),
            summary TEXT,
            published TIMESTAMP,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    saved = 0
    for name, url in BLOGS:
        items = fetch_feed(url)
        for item in items:
            summary = _summarize(item["description"])
            try:
                cursor.execute("""
                    INSERT INTO blog_posts (title, link, source_name, summary, published)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (link) DO NOTHING
                """, (item["title"][:500], item["link"][:1000], name, summary, item.get("published")))
                if cursor.rowcount:
                    saved += 1
            except Exception:
                pass
        if items:
            logging.info(f"📰 Blog {name}: {len(items)} articles")
        time.sleep(0.3)  # rate-limit amical
    conn.commit()
    cursor.close()
    conn.close()
    logging.info(f"📰 Blog scan: {saved} nouveaux articles sauvegardes")
    return saved


def get_posts(limit: int = 20, source: str = None) -> list[dict]:
    """Recupere les derniers articles de blog."""
    from src.database import get_db_connection
    from psycopg2.extras import RealDictCursor

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    if source:
        cursor.execute(
            "SELECT * FROM blog_posts WHERE source_name = %s ORDER BY COALESCE(published, discovered_at) DESC LIMIT %s",
            (source, limit),
        )
    else:
        cursor.execute(
            "SELECT * FROM blog_posts ORDER BY COALESCE(published, discovered_at) DESC LIMIT %s",
            (limit,),
        )
    rows = [dict(r) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows


def get_sources() -> list[dict]:
    """Retourne les sources de blog disponibles avec leur nombre d'articles."""
    from src.database import get_db_connection

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT source_name, count(*) as cnt FROM blog_posts
        GROUP BY source_name ORDER BY cnt DESC
    """)
    rows = [{"source": r[0], "count": r[1]} for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows


def extract_entities(text: str) -> dict:
    """Extrait les entites d'un article: CVE, GitHub URLs, IOCs, outils."""
    cves = list(set(re.findall(r'CVE-\d{4}-\d{4,7}', text, re.IGNORECASE)))
    gh_urls = list(set(re.findall(r'https?://github\.com/[\w.-]+/[\w.-]+', text)))
    ips = list(set(re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)))[:5]
    domains = list(set(re.findall(r'\b(?:[\w-]+\.)+[\w-]{2,}\b', text)))[:10]
    # Filtrer les faux positifs
    domains = [d for d in domains if d not in ('com', 'org', 'net', 'www', 'blog') and '.' in d and len(d) > 5][:5]
    return {
        "cves": cves[:5],
        "github_urls": gh_urls[:5],
        "ips": ips,
        "domains": domains,
    }
