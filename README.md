# CyberBook Collector

Outil simple et autonome pour decouvrir et cataloguer tous les depots GitHub qui partagent des livres, cours et ressources sur la cybersecurite.

## Fonctionnalites

- **Scan GitHub** : 26+ requetes ciblees pour trouver les repos pertinents
- **Parsing README** : Extraction automatique des liens (livres, PDFs, cheatsheets, outils)
- **Categorisation** : Offensive, Defensive, Certification, Général
- **Export** : Excel et JSON, tries par pertinence
- **Dashboard** : Interface web simple pour consulter les resultats
- **API** : Endpoints REST pour integrer a vos propres outils

## Installation

```bash
# Cloner le repo
git clone https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro.git
cd GitHub-Cyber-Scanner-Pro

# Installer les dependances
pip install -r requirements.txt
```

## Configuration

Creer un fichier `.env` a la racine :

```env
# Token GitHub (requis pour l'API GitHub)
GITHUB_TOKENS=ghp_votre_token

# Repo pour les issues (optionnel)
GITHUB_REPO=votre_user/votre_repo

# Base de donnees PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=scanner_db
DB_USER=postgres
DB_PASSWORD=votre_password
```

### Obtenir un token GitHub

1. Aller sur https://github.com/settings/tokens
2. Generer un token (Classic)
3. Donner les permissions `public_repo` (lecture des depots publics)

## Utilisation

### Lancer le scan

```bash
python src/scanner.py
```

Ceci lance :
- Le scan automatique des depots GitHub (toutes les 30 minutes)
- Le serveur web FastAPI sur http://localhost:8000

### Endpoints API

| Methode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | Dashboard HTML |
| GET | `/api/stats` | Nombre de repos et livres |
| GET | `/api/books` | Liste des livres et ressources |
| GET | `/api/books?q=python` | Recherche par titre ou categorie |
| GET | `/api/repositories` | Liste des depots scannes |
| GET | `/api/download` | Export Excel |
| GET | `/api/download/json` | Export JSON |
| POST | `/api/scan` | Declencher un scan manuel |

### Docker (optionnel)

```bash
docker compose up -d --build
```

## Structure du projet

```
.
├── src/
│   ├── scanner.py          # Scanner GitHub + parser README + API FastAPI
│   ├── database.py         # Connexion PostgreSQL et operations CRUD
│   └── __init__.py
├── templates/
│   └── index.html          # Dashboard web integre
├── data/
│   ├── init.sql            # Schema de la base de donnees
│   ├── cyber_security_catalogues.json   # Export JSON
│   └── cyber_security_catalogues.xlsx   # Export Excel
├── tests/
│   └── test_database.py    # Tests unitaires
├── requirements.txt        # Dependances Python
├── compose.yml             # Configuration Docker
├── Dockerfile              # Image Docker
├── .env.example            # Template de configuration
└── README.md               # Ce fichier
```

## Comment ca marche

### 1. Scan GitHub

Le scanner utilise 26+ requetes pour couvrir tous les aspects de la cybersecurite :

```
cybersecurity books
hacking resources
pentest cheatsheet
CTF write-ups
malware analysis
incident response
digital forensics
blue team resources
red team tools
...
```

Les requetes sont decoupees par tranche d'etoiles (1-10, 10-50, 50-100, etc.) pour contourner la limite de 1000 resultats de l'API GitHub.

### 2. Parsing README

Pour chaque depot decouvert, le scanner :
1. Telecharge le fichier README
2. Extrait tous les liens (URLs) avec des expressions regulieres
3. Filtre les liens pertinents (PDFs, sites de livres, cheatsheets)
4. Categorise chaque lien (Offensive, Defensive, Certification, General)

### 3. Export

Les donnees sont exportees dans deux formats :
- **Excel** : Fichier multi-lignes avec toutes les informations
- **JSON** : Format hierarchique pour l'integration programmatique

## Base de donnees

Le schema PostgreSQL contient 3 tables :

- **repositories** : Les depots GitHub decouverts
- **books** : Les liens extraits des README
- **etag_cache** : Cache des requetes API GitHub

Voir `data/init.sql` pour le schema complet.

## Dependances

```
requests          # Appels API GitHub
pandas            # Manipulation de donnees
openpyxl          # Export Excel
python-dotenv     # Configuration .env
fastapi           # API web
uvicorn           # Serveur ASGI
psycopg2          # Client PostgreSQL
```

## Licence

Projet open source.
