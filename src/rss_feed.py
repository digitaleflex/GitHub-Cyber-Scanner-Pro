import logging
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

RSS_FEEDS = {
    "CERT-FR": "https://www.cert.ssi.gouv.fr/feed/",
    "CERT-FR Alerts": "https://www.cert.ssi.gouv.fr/feed/alerte/",
}

CATEGORY_KEYWORDS = {
    "ransomware": ["ransomware", "rançongiciel", "lockbit", "clop", "blackcat", "alphv"],
    "malware": ["malware", "malveillant", "trojan", "botnet", "stealer", "infostealer"],
    "vulnerability": ["cve", "vulnérabilité", "vulnerability", "zero-day", "0-day", "exploit"],
    "phishing": ["phishing", "hameçonnage", "social-engineering"],
    "apt": ["apt", "advanced persistent threat", "espionnage", "cyberespionage"],
    "data-breach": ["brèche", "data breach", "fuite", "leak", "exfiltration"],
    "critical": ["critique", "urgent", "warning", "alerte"],
}

def categorize_article(title: str, summary: str) -> str:
    text = (title + " " + summary).lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "general"

def fetch_rss_feed(url: str) -> list[dict]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CyberScan-Pro/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        items = []
        for item in root.iter("{http://www.w3.org/2005/Atom}entry"):
            title = item.findtext("{http://www.w3.org/2005/Atom}title", "")
            link_el = item.find("{http://www.w3.org/2005/Atom}link")
            link = link_el.get("href", "") if link_el is not None else ""
            summary = item.findtext("{http://www.w3.org/2005/Atom}summary", "")
            published = item.findtext("{http://www.w3.org/2005/Atom}published", "")
            updated = item.findtext("{http://www.w3.org/2005/Atom}updated", "")
            items.append({
                "title": title.strip(),
                "link": link.strip(),
                "summary": summary.strip(),
                "published": published.strip() or updated.strip(),
                "source": url,
            })
        for item in root.iter("item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            desc = item.findtext("description", "")
            pub_date = item.findtext("pubDate", "")
            items.append({
                "title": title.strip(),
                "link": link.strip(),
                "summary": desc.strip(),
                "published": pub_date.strip(),
                "source": url,
            })
        return items
    except Exception as e:
        logging.error(f"❌ Erreur fetch RSS {url}: {e}")
        return []


def fetch_all_feeds() -> list[dict]:
    all_items = []
    seen_links = set()
    for source_name, feed_url in RSS_FEEDS.items():
        logging.info(f"📡 Récupération flux RSS: {source_name}")
        items = fetch_rss_feed(feed_url)
        for item in items:
            item["source_name"] = source_name
            item["category"] = categorize_article(item["title"], item["summary"])
            dedup_key = item["link"] or item["title"]
            if dedup_key not in seen_links:
                seen_links.add(dedup_key)
                all_items.append(item)
        logging.info(f"   → {len(items)} articles de {source_name}")
    all_items.sort(key=lambda x: x.get("published", ""), reverse=True)
    return all_items
