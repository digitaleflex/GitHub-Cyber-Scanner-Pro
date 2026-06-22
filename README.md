# CyberBook Collector

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI/CD](https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro/actions/workflows/deploy.yml/badge.svg)](https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro/actions/workflows/deploy.yml)
[![CyberScan](https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro/actions/workflows/scan.yml/badge.svg)](https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro/actions/workflows/scan.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)

Outil simple pour decouvrir les nouveaux outils cybersecurite sur GitHub.

## Ce que fait l'outil

1. **Scanne GitHub** tous les 3 jours avec 13 requetes ciblees
2. **Filtre le bruit** (repos vides, forks, awesome-lists)
3. **Genere un rapport** (dashboard HTML + markdown + JSON)

## Installation rapide

```bash
git clone https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro.git
cd GitHub-Cyber-Scanner-Pro
pip install requests
```

## Configuration

### Option 1 : Token GitHub (recommande)

Sans token, l'API GitHub limite a 10 requetes/minute. Avec token : 30/minute.

1. Aller sur https://github.com/settings/tokens
2. Generer un token (Classic)
3. Permissions : `public_repo` uniquement
4. Creer le fichier `.env` :

```env
GITHUB_TOKENS=ghp_votre_token_ici
```

### Option 2 : Sans token

Le script marche sans token, mais sera plus lent (rate limit).

## Utilisation

### Lancer un scan

```bash
python scripts/scan.py
```

Resultat :
```
data/last_scan.json    → les repos trouves cette session
data/seen.json         → historique (deduplication)
```

### Generer le rapport

```bash
python scripts/report.py
```

Resultat :
```
reports/rapport_YYYYMMDD.md    → rapport markdown
```

### Generer le dashboard

```bash
python scripts/dashboard.py
```

Resultat :
```
reports/dashboard_YYYYMMDD.html    → ouvre dans le navigateur
```

### Tout d'un coup

```bash
python scripts/scan.py && python scripts/report.py && python scripts/dashboard.py
```

## Dashboard

Ouvre `reports/dashboard_*.html` dans ton navigateur :

```
┌─────────────────────────────────────────────────┐
│  CyberScan Dashboard                           │
│                                                 │
│  ┌──────┐  ┌──────┐  ┌──────┐                 │
│  │  12  │  │ 4521 │  │  5   │                 │
│  │outils│  │stars │  │langs │                 │
│  └──────┘  └──────┘  └──────┘                 │
│                                                 │
│  Repository          Stars  Lang  Description  │
│  ─────────────────────────────────────────────  │
│  berylliumsec/nebula  981   Py   AI pentest... │
│  tirrenotechnologies  1.4k  PHP  Threat det... │
└─────────────────────────────────────────────────┘
```

## Automatisation (GitHub Actions)

Le scan tourne automatiquement **tous les 3 jours** sur GitHub Actions.

### Comment ca marche

1. GitHub Actions allume un serveur Ubuntu
2. Lance `scripts/scan.py`
3. Genere le rapport et le dashboard
4. Sauvegarde les fichiers en artefacts (90 jours)

### Voir les resultats

1. Va sur https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro/actions
2. Clique sur le dernier scan
3. En bas, clique sur **"cyberreport-xxx"** (Artifacts)
4. Telecharge le zip

### Lancer manuellement

1. Va sur l'onglet Actions
2. Clique sur "CyberScan"
3. Clique "Run workflow"

## Structure du projet

```
.
├── scripts/
│   ├── scan.py           # Scan GitHub (13 requetes)
│   ├── report.py         # Rapport markdown
│   └── dashboard.py      # Dashboard HTML
├── data/
│   ├── last_scan.json    # Dernier scan
│   ├── seen.json         # Historique
│   └── init.sql          # Schema SQL (pour plus tard)
├── reports/
│   ├── rapport_*.md      # Rapports markdown
│   └── dashboard_*.html  # Dashboards HTML
├── src/
│   ├── scanner.py        # Scanner complet (avec API)
│   └── database.py       # PostgreSQL (pour plus tard)
├── .github/
│   ├── workflows/
│   │   ├── scan.yml      # Scan auto tous les 3 jours
│   │   └── deploy.yml    # CI/CD (lint + tests)
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
├── LICENSE               # MIT
├── CODE_OF_CONDUCT.md    # Code de conduite
├── CONTRIBUTING.md       # Guide de contribution
├── SECURITY.md           # Politique de securite
├── CHANGELOG.md          # Historique
├── requirements.txt
└── README.md
```

## Comment ca marche (technique)

### Les 13 requetes GitHub

```
C2 framework pushed:>DATE stars:>1
phishing kit pushed:>DATE stars:>1
reverse shell pushed:>DATE stars:>1
credential stealer pushed:>DATE stars:>1
RAT malware pushed:>DATE stars:>1
exploit tool pushed:>DATE stars:>1
red team tool pushed:>DATE stars:>2
pentest tool pushed:>DATE stars:>2
malware analysis pushed:>DATE stars:>2
threat intel pushed:>DATE stars:>2
osint tool pushed:>DATE stars:>2
security tool pushed:>DATE stars:>3 language:go
security tool pushed:>DATE stars:>3 language:rust
```

### Filtre anti-bruit

Le script elimine :
- Les repos sans description
- Les forks
- Les repos avec 0 etoiles et 0 forks
- Les "awesome lists", "tutorials", "courses"

### Deduplication

Chaque repo est hash (MD5) et stocke dans `data/seen.json`. Les doublons sont ignores.

## FAQ

### "Est-ce que ca marche sans token ?"

Oui, mais plus lentement. L'API GitHub limite a 10 requetes/minute sans token.

### "Combien de temps dure un scan ?"

~2-3 minutes (13 requetes * 3 secondes de pause).

### "Ou sont les donnees ?"

Dans `data/` (JSON) et `reports/` (HTML/MD). Pas de base de donnees pour l'instant.

### "Comment ajouter une base de donnees ?"

Plus tard. Pour l'instant, les fichiers JSON suffisent.

### "Le CI/CD ne marche pas"

Verifie https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro/actions. Si c'est rouge, clique pour voir l'erreur.

## Contribuer

Lisez [CONTRIBUTING.md](CONTRIBUTING.md) pour les regles de contribution.

## Securite

Lisez [SECURITY.md](SECURITY.md) pour la politique de securite.

## Dependances

```
requests    # Appels API GitHub
```

C'est tout. Pas de Docker. Pas de PostgreSQL. Pas de NLP.

## Prochaines etapes

1. **Maintenant** : Lance le scan, regarde les resultats
2. **Semaine 2** : Envoie le rapport a 3 analystes CTI
3. **Si valide** : Ajoute PostgreSQL, scoring, dashboard avance
4. **Si non** : Arrete ou pivote

## Licence

Distribue sous la licence [MIT](LICENSE).
