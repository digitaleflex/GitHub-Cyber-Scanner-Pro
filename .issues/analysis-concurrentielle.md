# Analyse Concurrentielle — CyberScan Pro vs Plateformes CTI

> Légende : 🟢 Unique / Supérieur &nbsp; 🟡 Comparable &nbsp; 🔴 Inférieur / Absent

## 1. Plateformes CTI Généralistes (grand public / PME)

| Fonctionnalité | **CyberScan Pro** 🏠 | **AlienVault OTX** | **VirusTotal** | **AbuseIPDB** | **Pulsedive** | **SpiderFoot** |
|---|---|---|---|---|---|---|
| **GitHub Scanner automatisé** | 🟢 **224 requêtes, slicer, dorking, anti-noise** | 🔴 Aucun | 🔴 Aucun | 🔴 Aucun | 🔴 Aucun | 🔴 Aucun |
| **CVE Management (NVD)** | 🟡 Import 2002-2025, ~300K+ CVEs | 🟡 OTX pulses sur CVEs | ❌ Limité | ❌ Aucun | ❌ Limité | ❌ Aucun |
| **CISA KEV flagged** | 🟢 **Intégré natif** | ❌ Partiel | ❌ Aucun | ❌ Aucun | ❌ Non | ❌ Aucun |
| **Base Exploit-DB corrélée** | 🟢 **46K exploits corrélés CVEs** | ❌ Limité | ❌ Non | ❌ Aucun | ❌ Aucun | ❌ Aucun |
| **Knowledge Graph (Neo4j)** | 🟢 **CVE↔Exploit↔Outil↔MITRE** | ❌ Aucun | ❌ Aucun | ❌ Aucun | ❌ Aucun | ❌ Aucun |
| **OSINT Investigation IA** | 🟡 Pipeline 12 modèles, dorking | ❌ Aucun | ❌ Aucun | ❌ Aucun | ❌ Aucun | 🟡 Plugin-based |
| **AI Verdict (Sécurité)** | 🟢 **Groq Llama 3.3, audit auto** | ❌ Aucun | ❌ Aucun | ❌ Aucun | 🟡 Risk scoring basique | ❌ Aucun |
| **AI Digest quotidien** | 🟢 **Résumé IA des menaces** | 🟡 Pulses communautaires | ❌ Aucun | ❌ Aucun | 🟡 Threat feed | ❌ Aucun |
| **Threat Priority Score** | 🟢 **Score intelligent > CVSS seul** | ❌ CVSS uniquement | ❌ Aucun | ❌ Aucun | 🟡 Risque calculé | ❌ Aucun |
| **Recherche sémantique** | 🟢 **TF-IDF + Groq re-rank + cosine** | 🟡 Recherche texte | 🟡 Recherche texte | 🟡 Recherche IP | 🟡 Recherche texte | ❌ Basique |
| **Blog/News Monitoring** | 🟡 RSS Miniflux + extracteur entités | ❌ Aucun | ❌ Aucun | ❌ Aucun | ❌ Aucun | ❌ Aucun |
| **Modèles HF (22)** | 🟢 **QA, vuln-type, guard, embed** | ❌ Aucun | ❌ Aucun | ❌ Aucun | ❌ Aucun | ❌ Aucun |
| **MCP Server** | 🟢 **SSE, query tools, search** | ❌ Aucun | ❌ Aucun | ❌ Aucun | ❌ Aucun | ❌ Aucun |
| **API Publique** | 🟡 `/api/v1/repos` | 🟢 **API OTX mature** | 🟢 **API Enterprise** | 🟢 **API simple** | 🟢 **API gratuite** | ❌ Pas d'API |
| **UX / Interface** | 🟡 Glass-morphism moderne | 🔴 Vieillissante | 🟢 Très bonne | 🔴 Basique | 🟡 Correcte | 🔴 CLI / Web basique |
| **Déploiement** | 🟢 **Docker auto-hébergeable** | ☁️ SaaS only | ☁️ SaaS only | ☁️ SaaS only | ☁️ SaaS only | 🟢 **Open source local** |
| **Gratuit / Open Source** | 🟢 **100% MIT, tout gratuit** | 🟡 Freemium | 🟡 Freemium | 🟢 **Gratuit (limité)** | 🟡 Freemium | 🟢 **GPLv2** |
| **Communauté / Base installée** | 🔴 **Projet solo, petite** | 🟢 **Très large** | 🟢 **Massive** | 🟢 **Très large** | 🟡 Moyenne | 🟡 Moyenne |
| **IOC Feed automatisé** | 🔴 **Basique** | 🟢 **Pulses, rich feeds** | 🟢 **Intégrations SIEM** | 🟢 **API IP reputation** | 🟡 IOC feed | 🔴 Limité |
| **STIX/TAXII** | 🔴 **Absent** | 🟢 **STIX 2.0/2.1** | ❌ Non | ❌ Non | ❌ Non | ❌ Non |
| **Collaboration / Teams** | 🔴 **Aucune** | 🟢 **Pulses, sharing** | 🟢 **VT Enterprise** | ❌ Aucune | ❌ Aucune | ❌ Aucune |
| **Multi-tenant** | 🔴 **Aucun** | 🟢 **OTX Entreprise** | 🟢 **Oui** | ❌ Aucun | ❌ Aucun | ❌ Aucun |
| **Alerting** | 🔴 **Aucun (statique)** | 🟢 **Email alerting** | 🟢 **Webhooks** | ❌ Aucun | 🟡 Alertes | ❌ Aucun |
| **CI/CD Integration** | 🔴 **Aucune** | 🟢 **API + Plugins** | 🟢 **GitHub Actions** | 🟢 **API simple** | 🟡 API | ❌ Aucune |

**Verdict** : CyberScan gagne sur **tout ce qui touche à GitHub, l'IA embarquée, et le knowledge graph** — des atouts uniques. Mais il est **totalement dépassé sur l'IOC feed, les alertes temps réel, STIX et la maturité API/communauté**.

---

## 2. Plateformes CTI Enterprise (professionnel / Fortune 500)

| Fonctionnalité | **CyberScan Pro** 🏠 | **Recorded Future** | **ThreatConnect** | **Anomali** | **Intel471** |
|---|---|---|---|---|---|
| **Prix annuel** | 🟢 **Gratuit (MIT)** | 🔴 $50K-500K+ | 🔴 $30K-300K+ | 🔴 $40K-400K+ | 🔴 $60K-500K+ |
| **GitHub Scanner** | 🟢 **Unique** | 🔴 Aucun | 🔴 Aucun | 🔴 Aucun | 🔴 Aucun |
| **AI Resume/Insight** | 🟡 Groq open source | 🟢 **NLP propriétaire avancé** | 🟢 **Machine learning** | 🟢 **AI engine** | 🟡 AI basique |
| **Dark Web Intel** | 🔴 **Aucun** | 🟢 **Très poussé** | 🟢 **Bon** | 🟡 Partiel | 🟢 **Spécialiste** |
| **Actor tracking (APT)** | 🔴 **Aucun** | 🟢 **Excellent** | 🟢 **Bon** | 🟢 **Bon** | 🟢 **Excellent** |
| **Playbooks / SOAR** | 🔴 **Aucun** | 🟡 Plugin SOAR | 🟢 **Playbooks intégrés** | 🟢 **Intégration SOAR** | ❌ Aucun |
| **MITRE ATT&CK mapping** | 🟡 Enrichissement | 🟢 **Mapping avancé** | 🟢 **TTP mapping** | 🟢 **Mapping complet** | 🟡 Partiel |
| **Threat Hunting** | 🔴 **Aucun** | 🟢 **Hunting module** | 🟢 **Plateforme hunting** | 🟢 **Module hunting** | 🟡 Limité |
| **SIEM/SOAR Integration** | 🔴 **Aucune** | 🟢 **Splunk, QRadar, etc.** | 🟢 **100+ intégrations** | 🟢 **Large écosystème** | 🟡 Partiel |
| **24/7 Analyst Support** | 🔴 **Aucun** | 🟢 **Équipe dédiée** | 🟢 **Support** | 🟢 **Support** | 🟢 **Analystes** |
| **Rapports automatisés** | 🟡 Markdown + HTML | 🟢 **PDFs professionnels** | 🟢 **Dashboards** | 🟢 **Rapports PDF** | 🟢 **Raports** |

**Verdict** : Les géants dominent sur **dark web, APT tracking, playbooks SOAR et intégrations SIEM**. Mais à **0€**, CyberScan offre des capacités uniques qu'aucun d'eux n'a (GitHub scanner, 22 modèles HF, OSINT pipeline IA).

---

## 3. Plateformes Spécialisées

### A. OSINT / Recon

| Fonctionnalité | **CyberScan Pro** 🏠 | **Maltego** | **SpiderFoot HX** | **Shodan** | **Censys** |
|---|---|---|---|---|---|
| **GitHub recon** | 🟢 **Unique** | 🟡 Via transforms | 🟡 Via module | 🔴 Aucun | 🔴 Aucun |
| **Person OSINT** | 🟡 7 outils pipeline | 🟢 **60+ transforms** | 🟢 **200+ modules** | 🔴 Aucun | 🔴 Aucun |
| **Infrastructure mapping** | 🔴 **Aucun** | 🟢 **Excellent** | 🟡 Correct | 🟢 **Le meilleur** | 🟢 **Excellent** |
| **Graph visualization** | 🟡 Neo4j basique | 🟢 **Le meilleur** | 🟡 Correct | ❌ Non | ❌ Non |
| **Passive DNS** | 🔴 **Aucun** | 🟡 Via transforms | ❌ Non | 🟢 **Excellent** | 🟢 **Excellent** |
| **Certificate search** | 🔴 **Aucun** | ❌ Non | ❌ Non | 🟢 **Excellent** | 🟢 **Excellent** |
| **Prix** | 🟢 **Gratuit** | 🔴 €1000/an min | 🔴 HX payant | 🟡 Freemium ($69/m) | 🟡 Freemium |

**Verdict** : Shodan/Censys sont imbattables sur le réseau/certificats. Maltego domine sur les graphs. Mais CyberScan est le **seul à combiner OSINT + GitHub scanning + AI** de façon intégrée et gratuite.

### B. GitHub Security / DevSecTools

| Fonctionnalité | **CyberScan Pro** 🏠 | **GitHub Security** | **Snyk** | **SonarCloud** | **GitGuardian** |
|---|---|---|---|---|---|
| **Découverte de nouveaux outils** | 🟢 **Unique, 224 queries** | 🔴 Aucun | 🔴 Aucun | 🔴 Aucun | 🔴 Aucun |
| **Scanner secret/password** | 🔴 Aucun | 🟢 **Secret scanning** | 🟡 Basique | 🟡 Basique | 🟢 **Le meilleur** |
| **SAST** | 🟡 Bandit + Semgrep | 🟢 **CodeQL** | 🟢 **Snyk Code** | 🟢 **Excellent** | 🔴 Aucun |
| **SCA (deps)** | 🟡 Basique | 🟢 **Dependabot** | 🟢 **Le meilleur** | ❌ Non | ❌ Non |
| **AI audit automatisé** | 🟢 **Verdict IA + Vuln type** | ❌ Copilot (différent) | 🔴 Aucun | 🔴 Aucun | 🔴 Aucun |
| **Knowledge graph CVE-Exploit** | 🟢 **Unique** | 🔴 Aucun | 🔴 Aucun | 🔴 Aucun | 🔴 Aucun |

**Verdict** : Snyk et GitGuardian dominent sur la sécurisation de code existant (secret scanning, SCA). Mais **aucun ne fait de la découverte proactive de nouveaux outils cyber comme CyberScan**.

### C. CVE / Vulnérabilités

| Fonctionnalité | **CyberScan Pro** 🏠 | **NVD (officiel)** | **CVE Details** | **VulDB** | **FIRST/EPSS** |
|---|---|---|---|---|---|
| **CVE volume** | 🟡 ~300K (importable) | 🟢 **250K+ officiel** | 🟡 200K | 🟡 200K+ | 🔴 Aucun |
| **CISA KEV native** | 🟢 **Intégré** | ❌ Non | ❌ Non | ❌ Non | ❌ Non |
| **Exploit-DB corrélé** | 🟢 **46K exploits liés** | ❌ Non | 🟡 Pointe vers EDB | 🔴 Payant | ❌ Non |
| **Threat Priority scoring** | 🟢 **Score intelligent** | 🔴 CVSS uniquement | 🔴 CVSS uniquement | 🟡 VulDB score | 🟢 **EPSS score** |
| **AI CVE analysis** | 🟢 **Résumé IA, impact, reco** | ❌ Aucun | ❌ Aucun | ❌ Aucun | ❌ Aucun |
| **API** | 🟡 Basique | 🟢 **API NVD** | 🔴 Aucune | 🟡 API payante | 🟢 **API EPSS** |
| **Outils corrélés** | 🟢 **Outil↔CVE unique** | ❌ Non | ❌ Non | ❌ Non | ❌ Non |

**Verdict** : CyberScan est **imbattable sur le lien CVE↔Tool et l'analyse IA**. La NVD reste la source officielle, et EPSS est meilleur pour le scoring probabiliste pur. Position de force unique.

---

## Synthèse — Avantages Compétitifs de CyberScan Pro

### 🟢 Ce que CyberScan fait **mieux que tout le monde** (vraiment unique)

1. **GitHub Cyber Scanner 360°** — Aucune plateforme CTI ne scanne GitHub avec 224 requêtes + slicer temporel + dorking
2. **Corrélation CVE↔Exploit↔Outil** — Knowledge graph Neo4j unique liant vulnérabilités aux outils de détection/exploitation
3. **22 modèles HuggingFace intégrés** — QA, vuln-type, guard, classification, embeddings, tous accessibles gratuitement
4. **AI Verdict automatisé (Groq)** — Audit de sécurité de repos open source, aucun concurrent ne le fait
5. **OSINT Pipeline IA 12 modèles** — Extraction de personne → classification → GitHub → social → dorks → sécurité → rapport
6. **MCP Server** — Seule plateforme CTI avec un serveur Model Context Protocol pour agents IA
7. **100% gratuit, open source, auto-hébergeable** — Aucun coût, Docker Compose, MIT license
8. **AI Digest quotidien** — Résumé IA des menaces du jour avec insights actionnables

### 🟡 Ce que CyberScan fait **bien mais pas exceptionnel**

- **CVE management** — Bon volume mais pas de STIX/TAXII, pas de VulDB, pas d'EPSS
- **OSINT** — 7 outils intégrés mais SpiderFoot a 200+ modules
- **Blog scanning** — Fonctionnel mais pas de NLP avancé
- **SAST** — Bandit + Semgrep mais pas CodeQL ni SCA avancé
- **UI** — Moderne mais pas de dashboards dynamiques temps réel

### 🔴 Ce que les concurrents font **mieux** (lacunes critiques)

| Lacune | Qui fait mieux | Impact |
|---|---|---|
| **Dark Web intel** | Recorded Future, Intel471 | Critique pour APT |
| **IOC Feeds / Threat Feeds** | OTX, ThreatConnect | Essentiel SOC |
| **STIX/TAXII** | Tous les CTI enterprise | Interopérabilité |
| **Alerting temps réel** | OTX, VirusTotal | Réactivité |
| **Infrastructure scanning** | Shodan, Censys | Surface d'attaque |
| **Playbooks / SOAR** | ThreatConnect, Splunk | Automatisation réponse |
| **SIEM Integration** | Tous les enterprise | Déploiement en production |
| **Actor/APT tracking** | Recorded Future, Intel471 | Attribution |
| **Collaboration multi-équipe** | OTX, ThreatConnect | Usage SOC |
| **Certifications / Compliance** | Recorded Future, Anomali | Vente entreprise |

---

## Recommandations stratégiques

### Court terme (gains rapides)
1. **Ajouter STIX 2.1 export** → interopérabilité immédiate avec tout SIEM
2. **IOC feed automatisé** → extraire IOCs des CVEs + repos et les publier
3. **Webhook alerting** → notifier sur nouvelles CVEs critiques

### Moyen terme (différenciation)
4. **Intégrer abuse.ch / URLhaus / MalwareBazaar** → enrichir les IOCs
5. **Passive DNS via SecurityTrails API** → domaine/certificat intel
6. **MITRE ATT&CK mapping complet** → TTP par outil, pas juste mots-clés

### Long terme (ambition)
7. **Dark web mention scanning** → via Ahmia/Tor + NLP
8. **SOAR playbooks** → réponses automatisées aux alertes
9. **Multi-tenant** → usage SOC avec RBAC
