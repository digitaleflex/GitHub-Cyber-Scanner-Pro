# Deploiement VPS

Guide complet pour deployer CyberScan sur un VPS avec interface web, API, et SSL automatique.

## Architecture

```
Internet → Traefik (SSL) → FastAPI (uvicorn) → data/*.json
                           + React frontend (statique)
```

## Pre-requis

- VPS avec **Docker** et **Docker Compose** (v2+)
- **Traefik** deja installe et configure (reseau `traefik`)
- Un **domaine** pointe vers l'IP de votre VPS

## Installation rapide

```bash
# 1. Connexion au VPS
ssh root@votre-vps

# 2. Cloner le projet
git clone https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro.git
cd GitHub-Cyber-Scanner-Pro

# 3. Editer .env avec votre domaine
nano .env
# → DOMAIN=cyberbook.eurin.tech

# 4. Lancer la stack
docker compose -f compose.prod.yml up -d
```

Traefik detecte automatiquement le conteneur via les labels et genere le certificat SSL Let's Encrypt. Votre site est en ligne sur `https://cyberbook.eurin.tech` en quelques secondes.

## Structure des fichiers

```
/opt/cyberscan/
├── compose.prod.yml    # Stack de production (backend + labels Traefik)
├── .env                # Variables d'environnement (domaine)
├── data/               # Donnees de scan (volume persistant)
│   ├── last_scan.json  # Dernier scan
│   └── seen.json       # Historique des repos deja vus
└── reports/            # Rapports generes (volume persistant)
    ├── rapport_*.md    # Rapports markdown
    └── dashboard_*.html # Dashboards HTML
```

## Arret et redemarrage

```bash
# Arreter
docker compose -f compose.prod.yml down

# Voir les logs
docker compose -f compose.prod.yml logs -f

# Redemarrer
docker compose -f compose.prod.yml restart
```

## Mise a jour

```bash
cd /opt/cyberscan
git pull
docker compose -f compose.prod.yml build --no-cache
docker compose -f compose.prod.yml up -d
```

## Developpement local

```bash
# Terminal 1 : Backend
cd GitHub-Cyber-Scanner-Pro
pip install -r requirements.txt
uvicorn src.app:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 : Frontend
cd GitHub-Cyber-Scanner-Pro/frontend
npm install
npm run dev
```

Le frontend en dev tourne sur `http://localhost:5173` avec proxy vers l'API sur `:8000`.

## API disponible

| Route | Description |
|---|---|
| `GET /` | Interface web React (dashboard) |
| `GET /api/repos?q=mot` | Liste des repos (filtrable) |
| `GET /api/stats` | Statistiques globales |
| `GET /api/reports` | Liste des rapports disponibles |
| `GET /reports/{fichier}` | Contenu d'un rapport (.md) |
| `GET /dashboards/{fichier}` | Dashboard HTML archive |

## Securite

- Traefik gere SSL automatiquement (Let's Encrypt)
- Le backend n'expose que le port 8000 en interne
- Les donnees sont persistees dans des volumes Docker
- Aucune base de donnees externe requise

## Support

Ouvrez une issue sur [GitHub](https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro/issues) en cas de probleme.
