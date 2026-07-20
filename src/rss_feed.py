import json
import logging
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ATOM_NS = "{http://www.w3.org/2005/Atom}"
DC_NS = "{http://purl.org/dc/elements/1.1/}"
CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"

# Fichier de suivi de sante des flux (succes/echecs, anti-bot detecte).
HEALTH_FILE = Path("data/rss_health.json")
# Nombre d'echecs consecutifs avant de desactiver automatiquement un flux.
MAX_CONSECUTIVE_FAILURES = 5
# Code HTTP consideres comme "anti-bot / bloque" (flux inutilisable sans contournement).
BOT_BLOCK_CODES = {401, 403, 429}


@dataclass
class FeedSource:
    name: str
    url: str
    lang: str
    category: str
    country: str = ""


# Flux tech / cyber (FR + EN) valides et verifies. Chaque source porte sa langue et sa categorie.
RSS_FEEDS: list[FeedSource] = [
    # ---------- FR · Autorités / CERT / ANSSI ----------
    FeedSource("CERT-FR", "https://www.cert.ssi.gouv.fr/feed/", "fr", "cert"),
    FeedSource("CERT-FR Alertes", "https://www.cert.ssi.gouv.fr/alerte/feed/", "fr", "cert"),
    FeedSource("CERT-FR Avis", "https://www.cert.ssi.gouv.fr/avis/feed/", "fr", "vulnerability"),
    FeedSource("ANSSI Actualités", "https://cyber.gouv.fr/feed/", "fr", "general"),
    FeedSource("CNIL", "https://www.cnil.fr/fr/rss.xml", "fr", "privacy"),
    FeedSource("ZATAZ", "https://www.zataz.com/feed/", "fr", "general"),
    FeedSource("IT-Connect", "https://www.it-connect.fr/feed/", "fr", "general"),
    FeedSource("Le Big Data", "https://www.lebigdata.fr/feed/", "fr", "general"),
    FeedSource("Developpement Logiciel (LMI)", "https://www.lemondeinformatique.fr/developpement-logiciel/rss/rubrique.aspx", "fr", "dev"),
    FeedSource("SSTIC", "https://www.sstic.org/feeds/all/", "fr", "research"),

    # ---------- EN · CERT / Gov / Vuln ----------
    FeedSource("CISA Advisories", "https://www.cisa.gov/cybersecurity-advisories/all.xml", "en", "cert"),
    FeedSource("CISA ICS Advisories", "https://www.cisa.gov/cybersecurity-advisories/ics-advisories.xml", "en", "vulnerability"),
    FeedSource("CISA News", "https://www.cisa.gov/news.xml", "en", "cert"),
    FeedSource("CISA Blog", "https://www.cisa.gov/blog.xml", "en", "general"),
    FeedSource("US-CERT NCAS", "https://us-cert.cisa.gov/ncas/all.xml", "en", "cert"),
    FeedSource("CERT-EU Threat Intel", "https://cert.europa.eu/publications/threat-intelligence-rss", "en", "apt"),
    FeedSource("CERT-EU Advisories", "https://cert.europa.eu/publications/security-advisories-rss", "en", "cert"),
    FeedSource("NCSC UK", "https://www.ncsc.gov.uk/api/1/services/v1/all-rss-feed.xml", "en", "cert"),
    FeedSource("ENISA News", "https://www.enisa.europa.eu/news/feed", "en", "cert"),
    FeedSource("JPCERT", "https://www.jpcert.or.jp/english/rss/jpcert-en.rdf", "en", "cert"),
    FeedSource("JPCERT Blog", "https://blogs.jpcert.or.jp/en/atom.xml", "en", "research"),
    FeedSource("ACSC Australia", "https://www.cyber.gov.au/about-us/news/rss", "en", "cert"),
    FeedSource("CERT.at", "https://cert.at/cert-at.en.blog.rss_2.0.xml", "en", "cert"),
    FeedSource("CERT-BE News", "https://ccb.belgium.be/news.xml", "en", "cert"),
    FeedSource("CERT-BE Advisories", "https://ccb.belgium.be/advisories.xml", "en", "cert"),
    FeedSource("Canadian Centre for Cyber Security", "https://cyber.gc.ca/webservice/en/rss/alerts", "en", "cert"),
    FeedSource("BSI CERT-Bund", "https://www.bsi.bund.de/SiteGlobals/Functions/RSSFeed/rsssec/rsssec.xml", "en", "cert"),
    FeedSource("NCSC-NL", "https://ncsc.nl/rss/feeds/news.xml", "en", "cert"),
    FeedSource("CERT-SE", "https://www.cert.se/feed/atom", "en", "apt"),
    FeedSource("MITRE CVE", "https://cve.mitre.org/data/downloads/allitems.xml", "en", "vulnerability"),
    FeedSource("CVEfeed Latest", "https://cvefeed.io/rssfeed/latest.xml", "en", "vulnerability"),
    FeedSource("Google Project Zero", "https://googleprojectzero.blogspot.com/feeds/posts/default?alt=rss", "en", "vulnerability"),
    FeedSource("Microsoft MSRC", "https://api.msrc.microsoft.com/update-guide/rss", "en", "vulnerability"),
    FeedSource("Palo Alto PSIRT", "https://security.paloaltonetworks.com/rss.xml", "en", "vulnerability"),
    FeedSource("Cisco PSIRT", "https://tools.cisco.com/security/center/psirtrss20/CiscoSecurityAdvisoryListRss20.xml", "en", "vulnerability"),
    FeedSource("ZDI Published", "https://www.zerodayinitiative.com/rss/published/", "en", "vulnerability"),
    FeedSource("FortiGuard PSIRT", "https://www.fortiguard.com/rss/ir.xml", "en", "vulnerability"),

    # ---------- EN · Médias / News ----------
    FeedSource("The Hacker News", "https://feeds.feedburner.com/TheHackersNews", "en", "general"),
    FeedSource("Krebs on Security", "https://krebsonsecurity.com/feed/", "en", "general"),
    FeedSource("BleepingComputer", "https://www.bleepingcomputer.com/feed/", "en", "general"),
    FeedSource("BleepingComputer Forum", "https://www.bleepingcomputer.com/forum45.xml", "en", "general"),
    FeedSource("SANS ISC", "https://isc.sans.edu/rssfeed_full.xml", "en", "general"),
    FeedSource("Dark Reading", "https://www.darkreading.com/rss.xml", "en", "general"),
    FeedSource("SecurityWeek", "https://feeds.feedburner.com/securityweek", "en", "general"),
    FeedSource("CyberScoop", "https://www.cyberscoop.com/feed", "en", "general"),
    FeedSource("The Record", "https://therecord.media/feed/", "en", "general"),
    FeedSource("The Register - Security", "https://www.theregister.com/security/headlines.atom", "en", "general"),
    FeedSource("Ars Technica - Security", "https://arstechnica.com/security/feed/", "en", "general"),
    FeedSource("TechCrunch - Security", "https://techcrunch.com/category/security/feed/", "en", "general"),
    FeedSource("Hacker News", "https://news.ycombinator.com/rss", "en", "general"),
    FeedSource("Slashdot - Security", "https://rss.slashdot.org/Slashdot/slashdotSecurity", "en", "general"),
    FeedSource("Help Net Security", "https://www.helpnetsecurity.com/feed/", "en", "general"),
    FeedSource("Security Affairs", "https://securityaffairs.com/feed", "en", "general"),
    FeedSource("Heise Security", "https://www.heise.de/security/rss/news-atom.xml", "en", "general"),
    FeedSource("Threatpost", "https://threatpost.com/feed/", "en", "general"),
    FeedSource("Risky Business", "https://risky.biz/rss.xml", "en", "general"),

    # ---------- EN · Threat Intel / APT / Vendor ----------
    FeedSource("Mandiant", "https://www.mandiant.com/resources/blog/rss.xml", "en", "apt"),
    FeedSource("CrowdStrike", "https://www.crowdstrike.com/blog/feed/", "en", "apt"),
    FeedSource("Cisco Talos", "https://feeds.feedburner.com/feedburner/Talos", "en", "apt"),
    FeedSource("Proofpoint Threat Insight", "https://www.proofpoint.com/us/threat-insight-blog.xml", "en", "phishing"),
    FeedSource("Securelist (Kaspersky)", "https://securelist.com/feed/", "en", "apt"),
    FeedSource("WeLiveSecurity (ESET)", "https://www.welivesecurity.com/en/rss/feed/", "en", "malware"),
    FeedSource("SentinelOne", "https://www.sentinelone.com/feed/", "en", "apt"),
    FeedSource("Elastic Security Labs", "https://www.elastic.co/security-labs/rss/feed.xml", "en", "apt"),
    FeedSource("Rapid7 Blog", "https://blog.rapid7.com/rss/", "en", "vulnerability"),
    FeedSource("Check Point Research", "https://research.checkpoint.com/feed/", "en", "apt"),
    FeedSource("Google TAG", "https://blog.google/threat-analysis-group/rss/", "en", "apt"),
    FeedSource("Google Cloud Threat Intel", "https://www.googlecloudpresscorner.com/GoogleCloudSecurity/rss.xml", "en", "apt"),

    # ---------- EN · Malware / Ransomware / Phishing ----------
    FeedSource("Malwarebytes Labs", "https://blog.malwarebytes.com/feed/", "en", "malware"),
    FeedSource("Malware-Traffic-Analysis", "https://www.malware-traffic-analysis.net/blog-entries.rss", "en", "malware"),
    FeedSource("Spamhaus", "https://www.spamhaus.org/rss.xml", "en", "phishing"),
    FeedSource("PhishTank", "https://www.phishtank.com/phishtank.xml", "en", "phishing"),
    FeedSource("Ransomware.news", "https://ransomware.news/feed/", "en", "ransomware"),
    FeedSource("Exploit-DB", "https://www.exploit-db.com/rss.xml", "en", "exploit"),

    # ---------- EN · Research / Papers ----------
    FeedSource("Schneier on Security", "https://www.schneier.com/feed/atom/", "en", "research"),
    FeedSource("Troy Hunt", "https://www.troyhunt.com/rss/", "en", "data-breach"),
    FeedSource("Have I Been Pwned", "https://haveibeenpwned.com/feed", "en", "data-breach"),
    FeedSource("Google Online Security", "https://feeds.feedburner.com/GoogleOnlineSecurityBlog", "en", "general"),
    FeedSource("Cloudflare Blog", "https://blog.cloudflare.com/rss/", "en", "general"),
    FeedSource("NIST Cybersecurity", "https://www.nist.gov/cybersecurity/cybersecurity-rss.xml", "en", "research"),
    FeedSource("arXiv cs.CR", "https://rss.arxiv.org/rss/cs.CR", "en", "research"),
    FeedSource("Trail of Bits", "https://blog.trailofbits.com/feed/", "en", "research"),
    FeedSource("USENIX", "https://www.usenix.org/feed", "en", "research"),

    # ---------- EN · Pentest / Tools / CTF ----------
    FeedSource("OWASP", "https://owasp.org/www-news/feed/", "en", "pentest"),
    FeedSource("PortSwigger", "https://portswigger.net/blog/rss", "en", "pentest"),
    FeedSource("HackerOne", "https://www.hackerone.com/feed", "en", "pentest"),
    FeedSource("Bugcrowd", "https://www.bugcrowd.com/feed/", "en", "pentest"),
    FeedSource("Hackaday", "https://hackaday.com/blog/feed/", "en", "general"),
    FeedSource("Pentest-Tools", "https://pentest-tools.com/blog/feed/", "en", "tools"),
    FeedSource("CTFtime", "https://ctftime.org/feed/", "en", "ctf"),

    # ---------- EN · Dev / Open Source Security ----------
    FeedSource("GitHub Blog - Security", "https://github.blog/security/feed/", "en", "dev"),
    FeedSource("GitHub Changelog", "https://github.blog/changelog/feed/", "en", "dev"),
    FeedSource("OpenSSF", "https://www.openssf.org/feed/", "en", "dev"),
    FeedSource("Linux Security", "https://linuxsecurity.com/feed", "en", "dev"),
    FeedSource("Snyk Blog", "https://snyk.io/blog/feed/", "en", "dev"),
    FeedSource("Aqua Security", "https://www.aquasec.com/feed/", "en", "dev"),
    FeedSource("Sysdig Blog", "https://sysdig.com/blog/feed/", "en", "dev"),
    FeedSource("Wiz Blog", "https://www.wiz.io/blog/rss", "en", "dev"),
    FeedSource("Qualys Blog", "https://blog.qualys.com/feed", "en", "dev"),

    # ---------- EN · Privacy / Legal ----------
    FeedSource("EFF", "https://www.eff.org/rss/updates.xml", "en", "privacy"),
    FeedSource("Privacy International", "https://privacyinternational.org/rss.xml", "en", "privacy"),
    FeedSource("EPIC", "https://www.epic.org/alerts/atom.xml", "en", "privacy"),

    # ---------- EN · Reddit communities ----------
    FeedSource("Reddit r/netsec", "https://www.reddit.com/r/netsec/.rss", "en", "general"),
    FeedSource("Reddit r/cybersecurity", "https://www.reddit.com/r/cybersecurity/.rss", "en", "general"),
    FeedSource("Reddit r/ReverseEngineering", "https://www.reddit.com/r/ReverseEngineering/.rss", "en", "research"),
    FeedSource("Reddit r/OSINT", "https://www.reddit.com/r/OSINT/.rss", "en", "osint"),
    FeedSource("Reddit r/privacytoolsIO", "https://www.reddit.com/r/privacytoolsIO/.rss", "en", "privacy"),

    # ---------- EN · ICS / OT / IoT ----------
    FeedSource("Nozomi Networks", "https://www.nozominetworks.com/blog/feed", "en", "vulnerability"),
    FeedSource("Dragos", "https://www.dragos.com/blog/feed/", "en", "apt"),
]


CATEGORY_KEYWORDS = {
    "ransomware": ["ransomware", "rançongiciel", "lockbit", "clop", "blackcat", "alphv"],
    "malware": ["malware", "malveillant", "trojan", "botnet", "stealer", "infostealer"],
    "vulnerability": ["cve", "vulnérabilité", "vulnerability", "zero-day", "0-day", "exploit", "patch"],
    "phishing": ["phishing", "hameçonnage", "social-engineering", "spam"],
    "apt": ["apt", "advanced persistent threat", "espionnage", "cyberespionage", "threat actor"],
    "data-breach": ["brèche", "data breach", "fuite", "leak", "exfiltration", "pwned"],
    "critical": ["critique", "urgent", "warning", "alerte", "critical"],
}


def categorize_article(title: str, summary: str) -> str:
    text = (title + " " + summary).lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return "general"


def _text(el, *paths):
    for p in paths:
        v = el.findtext(p)
        if v and v.strip():
            return v.strip()
    return ""


def _link(el):
    # RSS 2.0 <link>text</link>
    v = el.findtext("link")
    if v and v.strip():
        return v.strip()
    # Atom <link href="..."/>
    for link in el.iter(ATOM_NS + "link"):
        rel = link.get("rel")
        if rel is None or rel == "alternate":
            return (link.get("href") or "").strip()
    return ""


def fetch_rss_feed(source: FeedSource, timeout: int = 15) -> tuple[list[dict], bool, Optional[str]]:
    """Retourne (articles, succes, raison_erreur)."""
    try:
        req = urllib.request.Request(
            source.url, headers={"User-Agent": "CyberScan-Pro/2.0 (+https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        items = []

        # Atom
        for entry in root.iter(ATOM_NS + "entry"):
            title = _text(entry, ATOM_NS + "title")
            link = _link(entry)
            summary = _text(entry, ATOM_NS + "summary", ATOM_NS + "content", CONTENT_NS + "encoded")
            published = _text(entry, ATOM_NS + "published", ATOM_NS + "updated", DC_NS + "date")
            if title and link:
                items.append({
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "published": published,
                    "source": source.url,
                })

        # RSS 2.0 / RDF
        for item in root.iter("item"):
            title = _text(item, "title")
            link = _link(item)
            desc = _text(item, "description", CONTENT_NS + "encoded")
            pub_date = _text(item, "pubDate", DC_NS + "date")
            if title and link:
                items.append({
                    "title": title,
                    "link": link,
                    "summary": desc,
                    "published": pub_date,
                    "source": source.url,
                })

        if not items:
            # XML valide mais aucun item => flux vide ou format inconnu.
            return [], True, "no_items"
        return items, True, None
    except urllib.error.HTTPError as e:
        reason = f"http_{e.code}"
        if e.code in BOT_BLOCK_CODES:
            reason = f"bot_block_{e.code}"
        return [], False, reason
    except Exception as e:
        return [], False, type(e).__name__


def _load_health() -> dict:
    if HEALTH_FILE.exists():
        try:
            return json.loads(HEALTH_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_health(health: dict) -> None:
    try:
        HEALTH_FILE.parent.mkdir(parents=True, exist_ok=True)
        HEALTH_FILE.write_text(json.dumps(health, indent=2, default=str))
    except Exception as e:
        logging.error(f"❌ Erreur sauvegarde health RSS: {e}")


def get_health() -> dict:
    return _load_health()


def get_healthy_feeds() -> list[FeedSource]:
    """Retourne les flux actifs (hors morts/anti-bot repetes)."""
    health = _load_health()
    return [
        s for s in RSS_FEEDS
        if (health.get(s.url) or {}).get("disabled") is not True
    ]


def count_usable_feeds() -> dict:
    """Compte les flux fiables (sains) vs morts/bloques."""
    health = _load_health()
    usable, dead, blocked = [], [], []
    for s in RSS_FEEDS:
        h = health.get(s.url) or {}
        if h.get("disabled"):
            (blocked if h.get("reason", "").startswith("bot_block") else dead).append(s.name)
        else:
            usable.append(s.name)
    return {
        "total": len(RSS_FEEDS),
        "usable": len(usable),
        "dead": dead,
        "blocked_antibot": blocked,
    }


def _process_source(source: FeedSource, health: dict) -> list[dict]:
    """Fetches a single RSS source, updates health, returns articles."""
    h = health.get(source.url, {"failures": 0, "successes": 0, "disabled": False})
    if h.get("disabled"):
        return []
    items, ok, reason = fetch_rss_feed(source)
    if ok:
        h["failures"] = 0
        h["successes"] = h.get("successes", 0) + 1
        h["disabled"] = False
        h["reason"] = None
        h["last_ok"] = time.time()
    else:
        h["failures"] = h.get("failures", 0) + 1
        h["reason"] = reason
        h["last_error"] = time.time()
        if h["failures"] >= MAX_CONSECUTIVE_FAILURES:
            h["disabled"] = True
            if reason and reason.startswith("bot_block"):
                logging.warning(f"🚫 Flux anti-bot desactive (auto): {source.name}")
            else:
                logging.warning(f"🚫 Flux mort desactive (auto): {source.name} -> {reason}")
    health[source.url] = h

    for item in items:
        item["source_name"] = source.name
        item["lang"] = source.lang
        item["country"] = source.country
        item["category"] = categorize_article(item["title"], item["summary"]) or source.category
    if items:
        logging.info(f"   → {len(items)} articles de {source.name}")
    return items

def fetch_all_feeds(max_workers: int = 10) -> list[dict]:
    health = _load_health()
    sources = [s for s in RSS_FEEDS if not health.get(s.url, {}).get("disabled")]
    all_items = []
    seen_links = set()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_process_source, s, health): s for s in sources}
        for future in as_completed(futures):
            try:
                items = future.result(timeout=20)
                all_items.extend(items)
            except Exception as e:
                src = futures[future]
                logging.warning(f"❌ Erreur sur {src.name}: {e}")

    _save_health(health)
    # Deduplicate by link
    deduped = []
    for item in all_items:
        dedup_key = item.get("link") or item.get("title", "")
        if dedup_key not in seen_links:
            seen_links.add(dedup_key)
            deduped.append(item)
    deduped.sort(key=lambda x: x.get("published", ""), reverse=True)
    logging.info(f"📰 Total: {len(deduped)} articles depuis {len(sources)} sources")
    return deduped


# ---------------------------------------------------------------------------
# Flux RSS publics de tous les CERT/gouvernements gouvernementaux du monde.
# Source de reference : pulsedive/certrss (liste communautaire verifiee de
# CERT officiels publiant des flux RSS publics). Les flux morts/anti-bot sont
# auto-exclus par le systeme de sante (fetch_all_feeds).
# ---------------------------------------------------------------------------
WORLD_GOV_CERT_FEEDS: list[FeedSource] = [
    FeedSource("DZ-CERT (Algeria)", "http://www.cerist.dz/index.php/en/?format=feed&type=rss", "en", "cert", "DZ"),
    FeedSource("AusCERT (Australia)", "https://portal.auscert.org.au/rss/bulletins/", "en", "cert", "AU"),
    FeedSource("CERT.at (Austria)", "https://cert.at/cert-at.en.blog.rss_2.0.xml", "en", "cert", "AT"),
    FeedSource("CERT.BE News (Belgium)", "https://ccb.belgium.be/news.xml", "en", "cert", "BE"),
    FeedSource("CERT.BE Advisories (Belgium)", "https://ccb.belgium.be/advisories.xml", "en", "cert", "BE"),
    FeedSource("CERT.br (Brazil)", "https://www.cert.br/rss/certbr-rss.xml", "pt", "cert", "BR"),
    FeedSource("Canadian CCCS Alerts (Canada)", "https://cyber.gc.ca/webservice/en/rss/alerts", "en", "cert", "CA"),
    FeedSource("Canadian CCSC News (Canada)", "https://cyber.gc.ca/webservice/en/rss/news", "en", "cert", "CA"),
    FeedSource("CERT.hr (Croatia)", "https://www.cert.hr/feed/", "hr", "cert", "HR"),
    FeedSource("NUKIB (Czechia)", "https://nukib.gov.cz/rss.xml", "cs", "cert", "CZ"),
    FeedSource("DKCERT (Denmark)", "https://www.cert.dk/news/rss", "da", "cert", "DK"),
    FeedSource("EG-CERT (Egypt)", "https://www.egcert.eg/feed/", "en", "cert", "EG"),
    FeedSource("CERT-EE (Estonia)", "https://www.ria.ee/et/news-feed/all/feed", "et", "cert", "EE"),
    FeedSource("CERT-EU Threat Intel (EU)", "https://cert.europa.eu/publications/threat-intelligence-rss", "en", "apt", "EU"),
    FeedSource("CERT-EU Advisories (EU)", "https://cert.europa.eu/publications/security-advisories-rss", "en", "cert", "EU"),
    FeedSource("NCSC-FI (Finland)", "https://www.kyberturvallisuuskeskus.fi/feed/rss/en", "en", "cert", "FI"),
    FeedSource("NCSC-FI Vulns (Finland)", "https://www.kyberturvallisuuskeskus.fi/sites/default/files/rss/vulns.xml", "en", "vulnerability", "FI"),
    FeedSource("CERT-FR (France)", "https://www.cert.ssi.gouv.fr/feed/", "fr", "cert", "FR"),
    FeedSource("GovCERT.HK (Hong Kong)", "https://www.govcert.gov.hk/en/rss_security_alerts.xml", "en", "cert", "HK"),
    FeedSource("HKCERT (Hong Kong)", "https://www.hkcert.org/getrss/security-bulletin", "en", "cert", "HK"),
    FeedSource("NCSC Hungary", "https://nki.gov.hu/figyelmeztetesek/riasztas/feed/", "hu", "cert", "HU"),
    FeedSource("CERT-IL (Israel)", "https://www.gov.il/he/api/PublicationApi/rss/4bcc13f5-fed6-4b8c-b8ee-7bf4a6bc81c8", "he", "cert", "IL"),
    FeedSource("CSIRT Italia (Italy)", "https://www.acn.gov.it/portale/feedrss/-/journal/rss/20119/723192", "it", "cert", "IT"),
    FeedSource("JPCERT (Japan)", "https://www.jpcert.or.jp/english/rss/jpcert-en.rdf", "en", "cert", "JP"),
    FeedSource("JPCERT Blog (Japan)", "https://blogs.jpcert.or.jp/en/atom.xml", "en", "research", "JP"),
    FeedSource("CERT.LV (Latvia)", "https://cert.lv/en/feed/rss/all", "en", "cert", "LV"),
    FeedSource("NISSA (Libya)", "https://nissa.gov.ly/feed/", "ar", "cert", "LY"),
    FeedSource("NCSC NL News (Netherlands)", "https://feeds.ncsc.nl/nieuws.rss", "nl", "cert", "NL"),
    FeedSource("NCSC NL Advisories (Netherlands)", "https://advisories.ncsc.nl/rss/advisories", "nl", "cert", "NL"),
    FeedSource("NSM NCSC (Norway)", "https://nsm.no/fagomrader/digital-sikkerhet/nasjonalt-cybersikkerhetssenter/varsler-fra-ncsc/rss/", "no", "cert", "NO"),
    FeedSource("CERT.PL (Poland)", "https://cert.pl/en/rss.xml", "en", "cert", "PL"),
    FeedSource("CNCS Portugal", "https://www.cncs.gov.pt/docs/noticias/feed-rss/index.xml", "pt", "cert", "PT"),
    FeedSource("CERT.RO (Romania)", "https://dnsc.ro/feed", "ro", "cert", "RO"),
    FeedSource("SK-CERT (Slovakia)", "https://www.sk-cert.sk/index.html%3Ffeed=rss", "sk", "cert", "SK"),
    FeedSource("SI-CERT (Slovenia)", "https://www.cert.si/en/category/news/feed/", "en", "cert", "SI"),
    FeedSource("CCN-CERT (Spain)", "https://www.ccn-cert.cni.es/en/communication-events/articles-and-reports.rss", "en", "cert", "ES"),
    FeedSource("INCIBE-CERT (Spain)", "https://www.incibe.es/en/incibe-cert/alerta-temprana/avisos/feed", "en", "cert", "ES"),
    FeedSource("CERT-SE (Sweden)", "https://www.cert.se/feed.rss", "sv", "cert", "SE"),
    FeedSource("Swiss GovCERT (Switzerland)", "https://www.newsd.admin.ch/newsd/feeds/rss?lang=en&org-nr=1101", "en", "cert", "CH"),
    FeedSource("UK NCSC (United Kingdom)", "https://www.ncsc.gov.uk/api/1/services/v1/all-rss-feed.xml", "en", "cert", "GB"),
    FeedSource("CERT-UA (Ukraine)", "https://cert.gov.ua/api/articles/rss", "uk", "apt", "UA"),
    FeedSource("ASD ACSC (Australia)", "https://www.cyber.gov.au/rss/alerts", "en", "cert", "AU"),
    FeedSource("CISA NCAS (USA)", "https://www.cisa.gov/uscert/ncas/all.xml", "en", "cert", "US"),
    FeedSource("SingCERT (Singapore)", "https://www.csa.gov.sg/Content/RSS-Feed", "en", "cert", "SG"),
]


# Etendre la liste principale avec les CERT mondiaux (sans doublons d'URL).
_EXISTING_URLS = {s.url for s in RSS_FEEDS}
RSS_FEEDS = RSS_FEEDS + [
    s for s in WORLD_GOV_CERT_FEEDS if s.url not in _EXISTING_URLS
]
