import logging
import os
import time
from typing import Optional

import requests

import src.rss_feed as rss_feed
from src import database

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

MINIFLUX_URL = os.getenv("MINIFLUX_URL", "http://miniflux:8080").rstrip("/")
MINIFLUX_TOKEN = os.getenv("MINIFLUX_TOKEN", "")
MINIFLUX_ENABLED = os.getenv("MINIFLUX_ENABLED", "true").lower() == "true"

# Categories Miniflux ciblees par type de flux
CATEGORY_MAP = {
    "cert": "CERT / Gouv",
    "vulnerability": "Vulnérabilités",
    "apt": "Threat Intel",
    "malware": "Malware",
    "ransomware": "Malware",
    "phishing": "Phishing",
    "pentest": "Pentest / Red Team",
    "dev": "Dev / Open Source",
    "research": "Recherche",
    "privacy": "Privacy / Legal",
    "general": "Général",
    "tools": "Outils",
    "ctf": "CTF",
    "osint": "OSINT",
    "exploit": "Exploits",
    "data-breach": "Data Breach",
    "legal": "Privacy / Legal",
}


def _headers() -> dict:
    return {"X-Auth-Token": MINIFLUX_TOKEN, "Content-Type": "application/json"}


def _api(path: str, method: str = "GET", json_body: Optional[dict] = None) -> Optional[dict]:
    if not MINIFLUX_TOKEN:
        return None
    try:
        resp = requests.request(
            method, f"{MINIFLUX_URL}/v1/{path}", headers=_headers(),
            json=json_body, timeout=20,
        )
        if resp.status_code >= 400:
            logging.error(f"❌ Miniflux API {method} {path} -> {resp.status_code} {resp.text[:120]}")
            return None
        return resp.json() if resp.content else {}
    except Exception as e:
        logging.error(f"❌ Erreur Miniflux API {path}: {e}")
        return None


def ensure_categories() -> dict:
    """Retourne {nom_categorie: id}. Cree les categories manquantes."""
    cats = _api("categories") or []
    by_name = {c["title"]: c["id"] for c in cats}
    needed = set(CATEGORY_MAP.values())
    for name in needed:
        if name not in by_name:
            created = _api("categories", "POST", {"title": name})
            if created:
                by_name[name] = created["id"]
    return by_name


def sync_feeds() -> int:
    """Cree les flux de RSS_FEEDS dans Miniflux (idempotent). Retourne le nb de flux actifs."""
    if not MINIFLUX_ENABLED or not MINIFLUX_TOKEN:
        logging.warning("Miniflux desactive (MINIFLUX_ENABLED=false ou token manquant)")
        return 0
    by_name = ensure_categories()
    existing = _api("feeds") or []
    existing_urls = {f["feed_url"] for f in existing}

    created = 0
    for src in rss_feed.RSS_FEEDS:
        if src.url in existing_urls:
            continue
        cat = CATEGORY_MAP.get(src.category, "Général")
        cat_id = by_name.get(cat, next(iter(by_name.values())) if by_name else 1)
        res = _api("feeds", "POST", {
            "feed_url": src.url,
            "category_id": cat_id,
            "user_agent": "CyberScan-Pro/2.0",
            "crawler": True,
        })
        if res and "id" in res:
            created += 1
            logging.info(f"➕ Flux Miniflux ajoute: {src.name}")
    total = len(existing) + created
    logging.info(f"📡 Miniflux: {total} flux configures ({created} nouveaux)")
    return total


def pull_entries(limit_per_feed: int = 50, max_entries: int = 2000) -> int:
    """Recupere les entrees Miniflux et les sauvegarde dans cyber_news. Retourne le nb sauvegarde."""
    if not MINIFLUX_ENABLED or not MINIFLUX_TOKEN:
        return 0
    entries = _api(f"entries?limit={max_entries}&order=published_at&direction=desc")
    if not entries:
        return 0
    items = []
    for e in entries.get("entries", []):
        feed = e.get("feed", {}) or {}
        feed_title = feed.get("title", "unknown")
        # Devine la langue/categorie depuis le flux source connu
        src = next((s for s in rss_feed.RSS_FEEDS if s.url == feed.get("feed_url")), None)
        lang = src.lang if src else "en"
        country = src.country if src else ""
        category = rss_feed.categorize_article(e.get("title", ""), e.get("content", "")) or (src.category if src else "general")
        items.append({
            "title": e.get("title", "")[:500],
            "link": e.get("url", "")[:1000],
            "summary": (e.get("content") or e.get("author") or "")[:2000],
            "source_name": feed_title[:100],
            "category": category,
            "published": e.get("published_at", ""),
            "lang": lang,
            "country": country,
        })
    saved = database.save_cyber_news(items)
    logging.info(f"📰 {saved} article(s) RSS importes depuis Miniflux")
    return saved


def refresh_all_feeds() -> None:
    """Force le rafraichissement de tous les flux Miniflux."""
    _api("feeds/refresh", "PUT")


def run_bridge() -> dict:
    """Pipeline complet : sync + refresh + pull. Retourne un resume."""
    if not MINIFLUX_ENABLED:
        return {"enabled": False}
    start = time.time()
    nb_feeds = sync_feeds()
    refresh_all_feeds()
    # Laisse Miniflux le temps de fetcher
    time.sleep(3)
    saved = pull_entries()
    return {
        "enabled": True,
        "feeds": nb_feeds,
        "saved": saved,
        "duration_s": round(time.time() - start, 2),
    }


if __name__ == "__main__":
    print(run_bridge())
