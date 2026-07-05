# Deploiement VPS

Guide complet pour deployer CyberScan sur un VPS avec interface web, API, et SSL automatique.

## Architecture

```
Internet → Caddy (SSL) → FastAPI (uvicorn) → data/*.json
                          + React frontend (statique)
```

## Pre-requis

- VPS avec **Docker** et **Docker Compose** (v2+)
- Un **domaine** pointe vers l'IP de votre VPS (ex: `cyberscan.example.com`)
- Ports **80** et **443** ouverts

## Installation rapide

```bash
# 1. Connexion au VPS
ssh root@votre-vps

# 2. Cloner le projet
git clone https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro.git
cd GitHub-Cyber-Scanner-Pro

# 3. Configurer le domaine
# Editez Caddyfile et remplacez cyberscan.example.com par votre domaine
nano Caddyfile

# 4. Lancer la stack
docker compose -f compose.prod.yml up -d
```

Caddy genere automatiquement les certificats SSL Let's Encrypt. Votre site est en ligne sur `https://votre-domaine.com` en quelques secondes.

## Structure des fichiers

```
/opt/cyberscan/
├── compose.prod.yml    # Stack de production (backend + Caddy)
├── Caddyfile           # Reverse proxy + SSL automatique
├── .env                # Variables d'environnement
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

## Personnalisation

### Changer de port

Editez `compose.prod.yml` :
```yaml
services:
  cyber-scanner:
    expose:
      - "8000"  # Port interne (ne pas changer)
```

Caddy ecoute sur 80/443, pas besoin de changer le port expose.

### Ajouter un sous-domaine

Dans `Caddyfile` :
```
cyberscan.example.com, autre.example.com {
    reverse_proxy cyber-scanner:8000
}
```

## Securite

- Caddy gere SSL automatiquement (Let's Encrypt)
- Le backend n'expose que le port 8000 en interne
- Les donnees sont persistees dans des volumes Docker
- Aucune base de donnees externe requise

## Support

Ouvrez une issue sur [GitHub](https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro/issues) en cas de probleme.
