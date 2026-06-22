# CyberBook Collector

Outil simple pour capturer tous les repos GitHub qui partagent des livres et ressources sur la cybersécurité.

## Ce que fait l'outil

1. **Scanne GitHub** avec des requêtes ciblées (cybersecurity books, hacking resources, pentest guides...)
2. **Parse les README** pour extraire les liens vers livres, PDFs, cheatsheets, outils
3. **Catégorise** automatiquement (Offensive, Defensive, Certification, Général)
4. **Exporte** en Excel et JSON

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Créez un fichier `.env` :

```env
GITHUB_TOKENS=ghp_votre_token
GITHUB_REPO=votre_user/votre_repo
DB_HOST=localhost
DB_PORT=5432
DB_NAME=scanner_db
DB_USER=postgres
DB_PASSWORD=votre_password
```

## Utilisation

### Scan complet
```bash
python src/scanner.py
```

Lance le scan automatique + serveur web sur http://localhost:8000

### Endpoints API

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard HTML |
| `GET /api/stats` | Statistiques (repos, livres) |
| `GET /api/books` | Liste des livres/resources |
| `GET /api/books?q=python` | Recherche par titre/catégorie |
| `GET /api/repositories` | Liste des repos scannés |
| `GET /api/download` | Export Excel |
| `GET /api/download/json` | Export JSON |
| `POST /api/scan` | Déclencher un scan manuel |

## Docker (optionnel)

```bash
docker compose up -d --build
```

## Structure

```
src/
├── scanner.py      # Scanner GitHub + parser README + API
├── database.py     # PostgreSQL (CRUD simple)
└── __init__.py

templates/
└── index.html      # Dashboard HTML

data/
└── init.sql        # Schéma base de données
```

## Comment ça marche

Le scanner utilise 26+ requêtes GitHub pour trouver les repos pertinents :
- `cybersecurity books`
- `hacking resources`
- `pentest cheatsheet`
- `CTF write-ups`
- etc.

Pour chaque repo trouvé, il télécharge le README et extrait les liens avec des regex. Les liens sont catégorisés puis exportés.
