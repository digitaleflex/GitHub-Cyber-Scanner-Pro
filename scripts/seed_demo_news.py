"""
Seed de demonstration : insere des actualites cyber realistes dans cyber_news,
puis lance l'enrichissement (extraction CVE/IOC/ATT&CK) et affiche les
incidents corrélés via get_incidents().

Usage :
    python3 scripts/seed_demo_news.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

from src import database
import src.news_enricher as news_enricher


DEMO_NEWS = [
    {
        "title": "CERT-FR alerte sur l'exploitation active de CVE-2026-1234 dans Microsoft Exchange",
        "link": "https://www.cert.ssi.gouv.fr/actus/CVE-2026-1234-exchange/",
        "summary": "Une campagne cible les serveurs Exchange avec le CVE-2026-1234. IOC observe : 185.220.101.45 et le domaine evil-exchange.example.com. Technique MITRE ATT&CK T1190 (Exploit Public-Facing Application).",
        "source_name": "CERT-FR", "category": "alert", "country": "FR",
        "published": "2026-07-18 09:00:00",
    },
    {
        "title": "Critical: CVE-2026-1234 exploited in the wild against Exchange servers",
        "link": "https://www.cisa.gov/news-events/cve-2026-1234-exchange",
        "summary": "CISA adds CVE-2026-1234 to its Known Exploited Vulnerabilities catalog. Affects Microsoft Exchange. Also impacts Ivanti products. SHA256: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
        "source_name": "CISA", "category": "alert", "country": "US",
        "published": "2026-07-18 11:30:00",
    },
    {
        "title": "Ivanti零day également touché par CVE-2026-1234, confirme le vendeur",
        "link": "https://forums.ivanti.com/s/article/CVE-2026-1234",
        "summary": "Ivanti confirme que CVE-2026-1234 impacte ses appliances. Mitigation disponible. T1190 observe.",
        "source_name": "Ivanti Security", "category": "vendor", "country": "US",
        "published": "2026-07-18 14:00:00",
    },
    {
        "title": "Ransomware LockBit vise le secteur hospitalier francais",
        "link": "https://www.zataz.com/lockbit-hopitaux-fr-2026",
        "summary": "Plusieurs etablissements de sante francais sont touchees par LockBit. IOC : 45.155.205.233 et le hash md5 44d88612fea8a8f36de82e1278abb02f.",
        "source_name": "ZATAZ", "category": "threat", "country": "FR",
        "published": "2026-07-17 20:00:00",
    },
    {
        "title": "Phishing campaign abuses Google Chrome zero-day CVE-2026-7777",
        "link": "https://www.bleepingcomputer.com/news/chrome-cve-2026-7777/",
        "summary": "Des attaquants exploitent CVE-2026-7777 dans Chrome pour voler des cookies. Domaine de commande : phish-chrome.example.net. Technique T1566 (Phishing).",
        "source_name": "BleepingComputer", "category": "threat", "country": "US",
        "published": "2026-07-16 10:00:00",
    },
    {
        "title": "Chrome 128 patched CVE-2026-7777 — update now",
        "link": "https://chromereleases.googleblog.com/2026/07/stable-channel-update.html",
        "summary": "Google publie un correctif pour CVE-2026-7777 affectant Chrome sur Windows, Linux et Android.",
        "source_name": "Google", "category": "patch", "country": "US",
        "published": "2026-07-16 16:00:00",
    },
    {
        "title": "ANSSI publie un avis sur les vulnérabilités Fortinet",
        "link": "https://www.cert.ssi.gouv.fr/avis/CERTFR-2026-AVI-0421/",
        "summary": "Fortinet corrige plusieurs failles dont une critique. Aucun CVE public mentionne. Produit : FortiGate.",
        "source_name": "CERT-FR", "category": "advisory", "country": "FR",
        "published": "2026-07-15 09:00:00",
    },
    {
        "title": "APT29 utilise des techniques de persistence sur Active Directory",
        "link": "https://www.microsoft.com/en-us/security/blog/apt29-ad-2026",
        "summary": "Microsoft decrit l'usage de T1078 (Valid Accounts) et T1098 par APT29 contre Active Directory.",
        "source_name": "Microsoft", "category": "threat", "country": "US",
        "published": "2026-07-14 12:00:00",
    },
    {
        "title": "Nouvelle vague de ransomwares cible les PME via RDP",
        "link": "https://www.silicon.fr/ransomware-pme-rdp-2026",
        "summary": "Des attaques par force brute RDP touchent des PME francaises. IOC : 193.43.72.11.",
        "source_name": "Silicon.fr", "category": "threat", "country": "FR",
        "published": "2026-07-13 08:00:00",
    },
    {
        "title": "CVE-2026-9999 critique dans Apache Struts permet l'execution de code",
        "link": "https://lists.apache.org/thread/struts-cve-2026-9999",
        "summary": "Apache Struts est affecte par CVE-2026-9999 (RCE). Recommandation de mise a jour immediate. T1190 observe.",
        "source_name": "Apache", "category": "advisory", "country": "US",
        "published": "2026-07-12 15:00:00",
    },
    {
        "title": "Struts RCE CVE-2026-9999 actively exploited, warns CERT-EU",
        "link": "https://cert.europa.eu/alerts/struts-cve-2026-9999",
        "summary": "CERT-EU warns that CVE-2026-9999 in Apache Struts is exploited in the EU. Mitigation recommended.",
        "source_name": "CERT-EU", "category": "alert", "country": "EU",
        "published": "2026-07-12 18:00:00",
    },
    {
        "title": "Campagne de phishing cible les utilisateurs Office 365 en France",
        "link": "https://www.lexpress.fr/phishing-o365-2026",
        "summary": "Une campagne de phishing vise les comptes Office 365. Domaine : o365-secure.example.org. Technique T1566.",
        "source_name": "L'Express", "category": "threat", "country": "FR",
        "published": "2026-07-11 09:00:00",
    },
]


def main():
    print("=" * 60)
    print("SEED DEMO — insertion des actualites de demonstration")
    print("=" * 60)

    saved = database.save_cyber_news(DEMO_NEWS)
    print(f"[+] {saved} article(s) insere(s) dans cyber_news")

    enriched = database.enrich_unenriched_news(limit=500)
    print(f"[+] {enriched} article(s) enrichi(s) en entites (CVE/IOC/ATT&CK)")

    print("\n" + "=" * 60)
    print("INCIDENTS CORRELES (/api/news/incidents)")
    print("=" * 60)
    incidents = database.get_incidents(limit=50)
    if not incidents:
        print("Aucun incident (verifiez la connexion DB).")
        return

    for inc in incidents:
        print(f"\n● [{inc['num_sources']} source(s)] {inc['title']}")
        if inc["cves"]:
            print(f"    CVE   : {', '.join(inc['cves'])}")
        if inc["products"]:
            print(f"    PROD  : {', '.join(inc['products'])}")
        if inc["domains"]:
            print(f"    DOM   : {', '.join(inc['domains'])}")
        if inc["hashes"]:
            print(f"    HASH  : {len(inc['hashes'])} valeur(s)")
        print(f"    PAYS  : {', '.join(inc['countries']) or '-'}")
        print(f"    SRC   : {', '.join(inc['sources'])}")
        for n in inc["news"][1:]:
            print(f"      └─ {n['source_name']}: {n['title'][:60]}")


if __name__ == "__main__":
    main()
