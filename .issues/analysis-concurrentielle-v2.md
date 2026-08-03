# Analyse Concurrentielle — CyberScan Pro v3.1 vs Géants CTI

> **Mise à jour post-refonte UI** — Dashboard, DataTable, Drawer, Chip, Skeleton, Hotkeys, Cockpit Admin, AI Lab dédié  
> Légende : 🟢 Supérieur &nbsp; 🟡 Comparable &nbsp; 🔴 Inférieur

---

## 1. CyberScan Pro vs Recorded Future (Leader CTI Enterprise — ~$500M ARR)

| Dimension | CyberScan Pro 🏠 | Recorded Future 🏢 | Écart |
|---|---|---|---|
| **Prix** | 🟢 **Gratuit MIT** | 🔴 $50K-$500K/an | 🟢 +100 |
| **GitHub Scanner** | 🟢 **224 requêtes, slicer, dorking, anti-noise** | 🔴 Aucun | 🟢 Unique |
| **CVE + Exploit Correlation** | 🟢 **Knowledge Graph CVE↔Exploit↔Outil** | 🟡 CVE enrichies mais pas de lien outil | 🟢 Supérieur |
| **AI embarquée** | 🟢 Groq Llama 3.3 + 22 modèles HF gratuits | 🟢 **NLP propriétaire (Insikt)** | 🟡 Comparable |
| **Dark Web** | 🔴 **Aucun** | 🟢 **Leader mondial** | 🔴 Énorme écart |
| **APT Tracking** | 🔴 Aucun | 🟢 **Actor profiles, TTP, campaigns** | 🔴 Énorme écart |
| **IOC Feeds** | 🔴 Basique | 🟢 **Rich feeds, STIX, TAXII** | 🔴 Énorme écart |
| **SIEM Integration** | 🔴 Aucune | 🟢 **Splunk, QRadar, Sentinel, 50+** | 🔴 Énorme écart |
| **Dashboard** | 🟢 **Cockpit moderne, glass-morphism, live** | 🟢 Dashboard enterprise | 🟡 Comparable |
| **UX** | 🟢 Hotkeys, Drawer, DataTable, Skeleton | 🟢 Professionnel | 🟡 Comparable |
| **API** | 🟡 REST basique | 🟢 **API mature, SDKs, docs** | 🔴 Écart |
| **OSINT** | 🟡 7 outils, pipeline IA 12 modèles | 🟢 **Équipe dédiée d'analystes** | 🔴 Écart |
| **Rapports** | 🟡 Markdown + HTML | 🟢 **PDFs professionnels, branding** | 🔴 Écart |
| **Support** | 🔴 **Communauté uniquement** | 🟢 **24/7, dedicated analysts** | 🔴 Énorme écart |
| **Déploiement** | 🟢 **Docker auto-hébergé** | ☁️ SaaS uniquement | 🟢 Liberté |

**Verdict** : Imbattable sur le **rapport qualité/prix** (gratuit vs $50K+) et sur **GitHub + AI**. Recorded Future est inégalable sur **Dark Web, APT, intégrations SIEM et support**. Two different leagues — CyberScan est le seul à faire du **GitHub Threat Intel gratuitement avec IA**.

---

## 2. CyberScan Pro vs VirusTotal (Google — Référence malware/URL scanning)

| Dimension | CyberScan Pro 🏠 | VirusTotal 🏢 | Écart |
|---|---|---|---|
| **GitHub Scanner** | 🟢 **Unique** | 🔴 Aucun | 🟢 Unique |
| **File/URL scanning** | 🔴 **Aucun** | 🟢 **70+ antivirus engines** | 🔴 Énorme écart |
| **AI Analysis** | 🟢 **Verdict IA, 22 modèles HF, CVE analysis** | 🔴 Pas d'IA custom | 🟢 Supérieur |
| **CVE Management** | 🟢 **300K+ CVEs, KEV, exploit correlation** | 🟡 Basique (via NVD) | 🟢 Supérieur |
| **Knowledge Graph** | 🟢 **Neo4j CVE↔Exploit↔Outil** | 🟢 **Relation graph (VT Graph)** | 🟡 Comparable |
| **API** | 🟡 REST basique | 🟢 **API mature, 500+ req/day free** | 🔴 Écart |
| **Communauté** | 🔴 Petite | 🟢 **Massive, Google-backed** | 🔴 Énorme écart |
| **UI/UX** | 🟢 **Glass-morphism, DataTable, Drawer, Skeleton** | 🟢 SPA Polymer, chips, drawer | 🟡 Comparable |
| **IOC Enrichment** | 🟡 abuse.ch basique | 🟢 **Passive DNS, WHOIS, certificates** | 🔴 Écart |
| **Déploiement** | 🟢 **Docker auto-hébergé** | ☁️ SaaS uniquement | 🟢 Liberté |

**Verdict** : VirusTotal est **irremplaçable pour le scan de fichiers/URLs**. CyberScan est **irremplaçable pour la découverte de nouveaux outils GitHub et l'IA embarquée**. Complémentaires plutôt que concurrents directs.

---

## 3. CyberScan Pro vs Shodan (Référence Internet scanning — ~$100M)

| Dimension | CyberScan Pro 🏠 | Shodan 🏢 | Écart |
|---|---|---|---|
| **GitHub Scanner** | 🟢 **Unique** | 🔴 Aucun | 🟢 Unique |
| **Internet Scanning** | 🔴 **Aucun** | 🟢 **Leader mondial, tout l'Internet** | 🔴 Énorme écart |
| **IoT/ICS Discovery** | 🔴 Aucun | 🟢 **Excellence** | 🔴 Énorme écart |
| **CVE + Tools** | 🟢 **Corrélation complète** | 🟡 CVE tagging basique | 🟢 Supérieur |
| **Search UX** | 🟡 3 modes (classic/IA/sémantique) | 🟢 **Query language, facettes, hotkeys** | 🟡 Comparable |
| **AI** | 🟢 **22 modèles, verdict, analyse** | 🔴 Aucun | 🟢 Supérieur |
| **API** | 🟡 Basique | 🟢 **API mature, streaming, banners** | 🔴 Écart |
| **Prix** | 🟢 **Gratuit** | 🟡 Freemium ($69/m pro) | 🟢 Meilleur |
| **Dashboard** | 🟢 **Glass cockpit, live, workflows** | 🟡 Monitor (produit séparé) | 🟢 Supérieur |

**Verdict** : Shodan domine l'Internet scanning. CyberScan domine GitHub + AI. Deux outils pour deux usages radicalement différents — un SOC a besoin des deux.

---

## 4. CyberScan Pro vs MISP (Open Source CTI — Référence threat sharing)

| Dimension | CyberScan Pro 🏠 | MISP 🏢 | Écart |
|---|---|---|---|
| **GitHub Scanner** | 🟢 **Unique** | 🔴 Aucun | 🟢 Unique |
| **STIX/TAXII** | 🔴 **Absent** | 🟢 **STIX 1.x/2.x, TAXII server** | 🔴 Énorme écart |
| **Threat Sharing** | 🔴 Aucun | 🟢 **Communautés, sharing groups** | 🔴 Énorme écart |
| **IOC Management** | 🔴 Basique | 🟢 **Galaxies, clusters, correlation** | 🔴 Énorme écart |
| **AI embarquée** | 🟢 **22 modèles, Groq, pipeline** | 🔴 Aucun | 🟢 Supérieur |
| **UI/UX** | 🟢 **Moderne, DataTable, Drawer** | 🔴 Vieillissante, lourde | 🟢 Supérieur |
| **Déploiement** | 🟢 **Docker simple** | 🟢 Docker, VM,裸机 | 🟡 Comparable |
| **MCP Server** | 🟢 **SSE, tools, queries** | 🔴 Aucun | 🟢 Unique |
| **Communauté** | 🔴 Petite | 🟢 **Massive, NATO, EU, CERTs** | 🔴 Énorme écart |

**Verdict** : MISP est le standard **de facto** pour le partage de threat intel. CyberScan est 10x plus moderne en UI et 100x plus riche en IA. Le **mariage des deux** (CyberScan qui alimente MISP en IOCs) serait idéal.

---

## 5. CyberScan Pro vs SpiderFoot (OSINT Automation)

| Dimension | CyberScan Pro 🏠 | SpiderFoot 🏢 | Écart |
|---|---|---|---|
| **GitHub Scanner** | 🟢 **Unique, 224 queries** | 🔴 Aucun | 🟢 Unique |
| **OSINT Modules** | 🟡 7 outils + pipeline IA | 🟢 **200+ modules** | 🔴 Écart |
| **AI Pipeline** | 🟢 **12 modèles IA chaînés** | 🔴 Aucun | 🟢 Supérieur |
| **CVE Management** | 🟢 **300K+ avec correlation** | 🔴 Aucun | 🟢 Supérieur |
| **Knowledge Graph** | 🟢 **Neo4j CVE↔Tool** | 🟢 **Graph de relations** | 🟡 Comparable |
| **UI** | 🟢 **Moderne, multi-pages** | 🟡 Scan-based, web basique | 🟢 Supérieur |
| **Déploiement** | 🟢 **Docker** | 🟢 Python/Docker | 🟡 Comparable |
| **Prix** | 🟢 **100% gratuit** | 🟡 HX payant (enterprise) | 🟢 Meilleur |

**Verdict** : SpiderFoot a plus de modules OSINT. CyberScan a **l'IA, GitHub, et une UI moderne**. CyberScan gagne sur la partie CTI, SpiderFoot sur la partie pure reconnaissance.

---

## 6. Comparaison Globale — Matrice de Positionnement

```
                    ┌─────────────────────────────────────────────┐
                    │           FORCE DE L'IA EMBARQUÉE           │
                    │                                             │
    IA forte        │  CyberScan Pro 🟢                           │
                    │  (Groq + 22 HF + pipeline)                  │
                    │                                             │
                    │                   Recorded Future 🟡        │
                    │                   (NLP propriétaire)        │
                    │                                             │
                    │  VirusTotal 🔴    Shodan 🔴    MISP 🔴      │
                    │  SpiderFoot 🔴    Censys 🔴                 │
    IA faible       │                                             │
                    └─────────────────────────────────────────────┘
                    Faible ◄──── INTÉGRATIONS SIEM ────► Forte
```

```
                    ┌─────────────────────────────────────────────┐
                    │        GITHUB / DEV TOOLS COVERAGE          │
                    │                                             │
    GitHub natif    │  CyberScan Pro 🟢                           │
                    │  (224 queries, slicer, dorking)             │
                    │                                             │
                    │                   TOUS LES AUTRES 🔴        │
                    │                   (Aucun ne scanne GitHub)  │
                    │                                             │
    Aucun GitHub    │                                             │
                    └─────────────────────────────────────────────┘
```

```
                    ┌─────────────────────────────────────────────┐
                    │        RAPPORT QUALITÉ / PRIX               │
                    │                                             │
    Gratuit         │  CyberScan Pro 🟢  MISP 🟢                 │
                    │                                             │
                    │  SpiderFoot 🟡    OTX 🟡                   │
                    │                                             │
    Payant          │  Shodan 🟡        VirusTotal 🟡             │
                    │  Censys 🟡                                  │
                    │  Recorded Future 🔴    ThreatConnect 🔴     │
    Très cher       │  Anomali 🔴          Intel471 🔴           │
                    └─────────────────────────────────────────────┘
```

---

## Synthèse Finale

### 🟢 Où CyberScan est **leader incontesté** (personne ne fait ça)

1. **GitHub Cyber Scanner** — 224 requêtes, slicer temporel, dorking, anti-noise — **0 concurrent**
2. **AI Verdict automatisé gratuit** — Personne n'audite des repos open source avec LLM + HF
3. **Knowledge Graph CVE↔Exploit↔Outil** — Unique, même Recorded Future ne le fait pas
4. **22 modèles HuggingFace en self-hosted gratuit** — Aucune plateforme CTI
5. **MCP Server pour agents IA** — Aucun concurrent
6. **Glass-morphism + DataTable + Drawer** — UI plus moderne que MISP, SpiderFoot, OTX
7. **100% gratuit, MIT, Docker** — Recorded Future facture $100K pour moins d'IA

### 🟡 Où CyberScan est **compétitif mais pas leader**

- **CVE management** — Bon volume mais pas de STIX/TAXII (MISP est leader)
- **OSINT** — 7 outils + pipeline IA, mais SpiderFoot a 200+ modules
- **Search UX** — 3 modes, mais Shodan a un query language plus puissant
- **Graph** — Fonctionnel, mais Maltego a 60+ transforms

### 🔴 Où les géants nous **écrasent** (gap critique à combler)

| Gap | Leader | Urgence |
|---|---|---|
| **Dark Web intel** | Recorded Future | Moyen terme |
| **APT tracking** | Recorded Future, Intel471 | Moyen terme |
| **IOC Feeds temps réel** | MISP, OTX | **Court terme** |
| **STIX/TAXII export** | MISP | **Court terme** |
| **SIEM Integration** | Recorded Future | Moyen terme |
| **File/URL scanning** | VirusTotal | Long terme |
| **Internet scanning** | Shodan | Long terme |
| **OSINT modules** | SpiderFoot (200+) | Moyen terme |
| **Communauté** | MISP, OTX | Long terme |
| **API mature + SDK** | VirusTotal, Shodan | Moyen terme |
| **Support enterprise** | Recorded Future | Hors scope |

---

## Positionnement unique

> **CyberScan Pro est la SEULE plateforme CTI qui combine GitHub scanning, IA gratuite (Groq + 22 modèles HF), knowledge graph, et OSINT pipeline — le tout en open source et auto-hébergeable.**

Les géants (Recorded Future, VirusTotal, Shodan) sont meilleurs sur leurs niches respectives (Dark Web, malware scanning, Internet scanning), mais **aucun ne fait ce que CyberScan fait sur le croisement GitHub + IA + CVE**.

Le gap le plus urgent à combler pour être crédible face à un SOC : **STIX/TAXII export + IOC feed automatisé**.
