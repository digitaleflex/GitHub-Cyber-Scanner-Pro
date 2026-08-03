# CyberScan Pro — Stratégie Dataset & Positionnement (Recherche 2026)

> **Objectif** : Identifier les plus gros datasets du monde en cybersécurité, les APIs qui y donnent accès,
> et les plateformes qui centralisent la veille — pour hisser CyberScan Pro au sommet.

---

## 1. Les Plus Gros Datasets — Par Volume de Données

### 🌐 Internet Scanning (Catégorie reine — milliards d'enregistrements)

| API | Volume estimé | Données | API gratuite | Prix pro | Ce qu'on peut ingérer |
|---|---|---|---|---|---|
| **Onyphe** | **20B+ banners/mois**, 5000+ ports | Bannières, certs, DNS, WHOIS, vulns | ✅ Limitée (50 req/j) | €400/mo | Hosts exposés, services vulnérables |
| **Censys** | **100B+ certs, 10B+ services** | Hosts, certs, services, risques | ✅ Limitée (250/mois) | $300/mo+ | Certificats, software exposé |
| **Shodan** | **5B+ devices scannés** | Bannières, services, IoT, ICS | ✅ Limitée | $69/mo | Services exposés, CVE matching |
| **BinaryEdge** | ❌ **FERMÉ (Coalition, mars 2025)** | — | — | — | Plus disponible |
| **FOFA** | **4B+ assets (Chine)** | Bannières, services, certs | ✅ Limitée | Payant | Marché chinois, APT infrastructure |
| **ZoomEye** | **1.5B+ assets** | Bannières, services, vulns | ✅ Limitée | Payant | Marché asiatique |
| **Netlas.io** | **500M+ certs, hosts** | DNS, certs, services | ✅ 50 req/j | $250/mo | Alternative Censys émergente |
| **Criminal IP** | **4B+ assets** | IPs, domains, vulnérabilités | ✅ Limitée | $49/mo | Alternative Shodan avec scoring risque |
| **FullHunt** | **Millions d'assets** | Surface d'attaque, DNS, certs | ❌ Payant | $99/mo | Attack surface management |
| **LeakIX** | **Millions de leaks** | Databases exposées, configs cloud | ✅ Gratuit | Gratuit | Configs mal configurées |

### 📡 DNS / WHOIS / Domaines (Milliards)

| API | Volume | Données | API gratuite | Prix |
|---|---|---|---|---|
| **WhoisXML API** | **12B+ WHOIS records** (29 APIs) | WHOIS, DNS, IP, domaine, email, screenshot | ❌ Payant | $99/mo+ |
| **SecurityTrails** | **4B+ DNS records**, 1B+ domaines, 500M+ certs | Passive DNS, domaines, IPs, whois, subdomaines | ✅ 50 req/mois | $49/mo |
| **Farsight DNSDB** | **100B+ DNS observations** (absorbé par DomainTools 2022) | Passive DNS historique | ❌ Payant | $500+/mo |
| **DomainTools** | **WHOIS historique + DNS + certs** | WHOIS, DNS, reverse IP, domain monitoring | ❌ Payant | $300/mo+ |
| **PassiveTotal (RiskIQ/Microsoft)** | **Passive DNS + WHOIS + certs** | DNS passif, WHOIS, certificats, composants web | ❌ Payant | Via Microsoft E5 |

### 🦠 Malware / Threat Feeds (Millions à Milliards)

| API | Volume | Données | API gratuite | Prix |
|---|---|---|---|---|
| **VirusTotal** | **2B+ fichiers scannés**, 70+ antivirus | Fichiers, URLs, IPs, domaines, relations | ✅ 500 req/j (gratuit) | €100K+/an (Enterprise) |
| **abuse.ch** (URLhaus/MalwareBazaar/ThreatFox/FeodoTracker/SSL Blacklist) | **5M+ IOCs combinés** | URLs malware, hashes, IOCs, C2 IPs, certs SSL malveillants | ✅ **100% gratuit, illimité** | Gratuit |
| **ANY.RUN** | **Millions de sandbox runs** | Analyse interactive malware, réseau, processus | ✅ 1 VM/j | $99/mo |
| **Triage** | **Millions de sandbox runs** | Analyse automatisée malware | ✅ 1/j | €120/mo |
| **Hybrid Analysis** | **Millions de sandbox runs** | Falcon Sandbox + CrowdStrike intel | ✅ 2000/mois | Payant |
| **AlienVault OTX** | **20M+ pulses, 40M+ IOCs** | Pulses communautaires, IOCs, YARA, STIX | ✅ **100% gratuit, illimité** | Gratuit |
| **Malpedia** | **Bibliothèque malware curatée** | Yara rules, familles malware, TTPs | ✅ Gratuit | Gratuit |
| **VX Underground** | **35M+ échantillons malware** | Malware samples, source code, papers | ❌ Pas d'API | Gratuit (Discord/dons) |

### 🔑 Breach / Identity

| API | Volume | Données | API gratuite | Prix |
|---|---|---|---|---|
| **Have I Been Pwned** | **12B+ comptes compromis** | Emails, passwords, breaches | ✅ Limitée | $3.95/mo |
| **DeHashed** | **15B+ records** | Emails, usernames, passwords, IPs | ❌ Payant | $5.49/mo |
| **SpyCloud** | **Billions de creds + cookies de session** | Credentials, session cookies, PII | ❌ Payant | $15K/an+ |
| **Constella Intelligence** | **100B+ identity records** | Identités, deep/dark web | ❌ Payant | Enterprise |
| **LeakCheck** | **7B+ records** | Emails, passwords, combos | ✅ Limitée ($3/mo) | $3/mo |

### 🏴 Dark Web / Underground

| API | Volume | Données | API | Prix |
|---|---|---|---|---|
| **Intel 471** | **HUMINT exclusive** | Forums underground, marketplaces, acteurs | ❌ Payant | $75K+/an |
| **Flashpoint** | **Deep + dark web** | Forums, carding, chats, ransomware blogs | ❌ Payant | $75K+/an |
| **Cybersixgill** | **Deep + dark web automatisé** | Forums, IMs, C2, phishing kits | ❌ Payant | $50K+/an |
| **SOCRadar** | **Dark web + surface + Telegram** | Creds, forums, ransomware, supply chain | 🔶 Freemium | $10K+/an |
| **Cyble** | **Dark web + surface + code repos** | Ransomware, creds, brand monitoring | 🔶 Freemium | $30K+/an |
| **DarkOwl** | **Dark web search engine** | Indexe Tor, I2P, forums, marketplaces | ❌ Payant | Enterprise |

---

## 2. Les Plateformes qui Centralisent Tout (One-Stop Shop)

### Tier 1 — Leaders Enterprise ($50K-500K/an)

| Plateforme | Données ingérées | Point fort | Prix |
|---|---|---|---|
| **Recorded Future** | 1M+ sources : web ouvert, dark web, feeds techniques, code repos, paste sites, réseaux sociaux | Intelligence Graph propriétaire, IA de corrélation, couverture 360° | $50K-500K/an |
| **Anomali ThreatStream** | "Largest curated threat intel repository" — centaines de feeds commerciaux et communautaires | Agentic SOC Platform (TIP + SIEM + SOAR + XDR unifiés), MCP support | $100K-500K/an |
| **Mandiant (Google)** | IR frontline + VirusTotal + Google Safe Browsing + Chronicle | Attribution d'acteurs (600+ groupes), données de breaches réelles exclusives | $75K-500K/an |
| **CrowdStrike Falcon** | Trillions d'events/jour des endpoints + OSINT + dark web | Seul TIP qui nourrit directement l'EDR en temps réel (closed-loop) | $50K-1M/an |
| **Microsoft Defender TI** | 1B+ devices Windows, Office 365, Azure + RiskIQ (DNS/certs/web) | Intégration native avec tout l'écosystème Microsoft (Sentinel, Copilot, XDR) | Inclus E5 / $15/jour standalone |
| **ThreatConnect** | Feeds internes, OSINT, commerciaux, ISAC | Meilleur SOAR intégré, Risk Quantification, acquisition Dataminr | $30K-300K/an |

### Tier 2 — Open Source / Gratuit (Notre espace)

| Plateforme | Données | Point fort | Prix |
|---|---|---|---|
| **MISP** | Feeds communautaires, abuse.ch, OTX, STIX/TAXII, custom | Standard de facto du partage, galaxy/taxonomy framework, 1000+ instances | **Gratuit** (AGPL) |
| **OpenCTI** | Connecteurs 100+ sources : MISP, OTX, MITRE, CVE, VT, URLhaus, etc. | STIX 2.1 natif, graph visualization, architecture moderne (G2 Leader) | **Gratuit** (Apache 2.0) |
| **Yeti** | MITRE ATT&CK, abuse.ch, URLhaus, DFIQ, Sigma/YARA | Pont CTI ↔ DFIR, forensic artifacts, chasse aux menaces | **Gratuit** |
| **CyberScan Pro** | GitHub (224 queries), 300K+ CVEs, 46K exploits, Neo4j graph, 22 modèles HF, abuse.ch, OTX, OpenCVE, EPSS, urlscan.io | **Seul à combiner GitHub scanning + IA gratuite + knowledge graph** | **Gratuit** (MIT) |

### Tier 3 — Mid-Market / Spécialisé ($10K-100K/an)

| Plateforme | Spécialité | Prix |
|---|---|---|
| **SOCRadar** | Dark web + Attack Surface + Brand protection en une plateforme | $10K-100K/an |
| **Pulsedive** | **Meilleur rapport qualité/prix** — $29/mo pour du threat intel pro | $29/mo-500/mo |
| **Intel 471** | HUMINT underground exclusive — infiltration de forums criminels | $75K-250K/an |
| **Flashpoint** | Cyber + physique + fraude en une plateforme, VulnDB propriétaire | $75K-300K/an |
| **Cybersixgill** | Automatisation dark web, CVE exploitation pre-NVD (10-30j d'avance) | $50K-200K/an |
| **Constella Intelligence** | 100B+ identity records — la plus grosse base d'identités compromises | Enterprise |
| **Digital Shadows (ReliaQuest)** | Digital Risk Protection — marque, execs, cloud buckets exposés | $50K-200K/an |

---

## 3. Ce que CyberScan Pro devrait ingérer en priorité

### 🔥 Tier 1 — Gratuit, massif, immédiat (déjà fait ✅ ou à faire)

| Source | Volume | Action |
|---|---|---|
| ✅ abuse.ch (5 APIs) | 5M+ IOCs | Déjà intégré |
| ✅ AlienVault OTX | 40M+ IOCs, 20M+ pulses | Déjà intégré |
| ✅ OpenCVE | 200K+ CVEs temps réel | Déjà intégré |
| ✅ FIRST EPSS | 200K+ scores | Déjà intégré |
| ✅ urlscan.io | Millions scans publics | Déjà intégré |
| ⬜ **VirusTotal API** | 2B+ fichiers, 70+ AV engines | À intégrer (500 req/j gratuites) |
| ⬜ **SecurityTrails** | 4B+ DNS records, 1B+ domaines, 500M+ certs | À intégrer (50 req/mois gratuites, $49/mo pro) |
| ⬜ **Have I Been Pwned** | 12B+ comptes compromis | À intégrer ($3.95/mo) |
| ⬜ **Malpedia** | Yara rules + familles malware | À intégrer (gratuit, API REST) |
| ⬜ **Shodan API** | 5B+ devices | À intégrer (gratuit 50 req, $69/mo pro) |

### 🔶 Tier 2 — Payant, haute valeur

| Source | Volume | Coût estimé |
|---|---|---|
| **Censys** | 100B+ certs, 10B+ services | $300/mo+ |
| **Onyphe** | 20B banners/mois | €400/mo |
| **GreyNoise** | Billions d'events/jour | $500/mo+ |
| **ANY.RUN** | Sandbox interactive | $99/mo |
| **Pulsedive** | Threat intel + enrichment | $29/mo |
| **DeHashed** | 15B+ breach records | $5.49/mo |

### 💎 Tier 3 — Premium (quand on a du budget)

| Source | Volume | Valeur |
|---|---|---|
| **Intel 471 HUMINT** | Exclusif underground | Attribution APT |
| **Flashpoint** | Dark web + VulnDB | Vulnérabilités inédites |
| **SpyCloud** | Session cookies recapturés | Prévention takeovers |
| **Recorded Future feed** | Intelligence Graph | Corrélation IA |

---

## 4. Positionnement Final

```
                            CHER ($$$)
                               │
    Recorded Future ●          │          ● Mandiant
    CrowdStrike    ●          │          ● Anomali
    Flashpoint     ●          │          ● Microsoft
                               │
    ──────────────────────────┼──────────────────────
                               │
    SOCRadar ●                │          ● CyberScan Pro 🏠
    Pulsedive ●               │          ● MISP
    Shodan    ●               │          ● OpenCTI
    Censys    ●               │          ● OTX
                               │
                            GRATUIT
                               │
                   PEU DE DONNÉES ──────── BEAUCOUP DE DONNÉES
```

**CyberScan Pro** est le **seul** à offrir gratuitement :
- GitHub scanner (224 queries × daily)
- 22 modèles HuggingFace
- Knowledge Graph Neo4j
- STIX 2.1 export natif
- Pipeline d'ingestion 9 sources
- UI moderne (glass-morphism + DataTable + Drawer + Cockpit)
- MCP Server pour agents IA

**Pour atteindre le sommet** : ajouter VirusTotal + SecurityTrails + Shodan (tous ont des tiers gratuits/liftés) et on couvre **80% des données CTI mondiales gratuitement**.
