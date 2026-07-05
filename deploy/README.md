# Deploiement VPS

## Pre-requis

- Un VPS avec Docker et Docker Compose installes
- Un domaine pointe vers l'IP de votre VPS
- Les ports 80 et 443 ouverts

## Installation

```bash
# 1. Cloner le projet
git clone https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro.git
cd GitHub-Cyber-Scanner-Pro

# 2. Copier la config production
cp .env.prod .env
# Editer .env pour mettre votre domaine

# 3. Configurer le domaine dans Caddyfile
sed -i 's/cyberscan.example.com/votre-domaine.com/' Caddyfile

# 4. Lancer
docker compose -f compose.prod.yml up -d

# 5. SSL automatique ! Caddy genere les certificats Let's Encrypt tout seul
```

## Mise a jour

```bash
git pull
docker compose -f compose.prod.yml build
docker compose -f compose.prod.yml up -d
```

## Structure

```
/opt/cyberscan/
├── compose.prod.yml    # Production stack (backend + caddy)
├── Caddyfile           # Reverse proxy + SSL auto
├── .env                # Variables d'environnement
├── data/               # Donnees de scan (monte en volume)
│   ├── last_scan.json
│   └── seen.json
└── reports/            # Rapports generes
    ├── rapport_*.md
    └── dashboard_*.html
```

## Developpement local

```bash
# Backend
uvicorn src.app:app --reload

# Frontend (dans un autre terminal)
cd frontend && npm run dev
```
