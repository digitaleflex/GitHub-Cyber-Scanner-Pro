# 🗺️ Feuille de Route Stratégique - De Script à Plateforme Cyber Leader 2026

Ce document définit la trajectoire complète de l'application, du scanner GitHub initial vers une plateforme SaaS de renseignement cyber mondiale.

---

## Vue d'ensemble

```
[ Jours 1-7  ]  🚀 Phase 1 : Le Moissonneur        → 15 000+ dépôts en base
      │
[ Mois 1-2   ]  🧠 Phase 2 : Le Cerveau Sémantique  → Qdrant + IA multilingue
      │
[ Mois 3-4   ]  🛡️ Phase 3 : Le Validateur          → Trivy/Semgrep intégrés
      │
[ Mois 6+    ]  🌐 Phase 4 : L'Aspirateur OSINT      → SearXNG + Monétisation SaaS
```

---

## 🚀 Phase 1 - Sprint 1 (Jours 1 à 7) : Le Moissonneur Automatique

**Objectif :** Briser la barrière de l'infobésité et passer de 520 à 15 000+ dépôts.

### Instructions pour le développeur

1. **Déployer le scanner asynchrone** (`src/mass_async_scanner.py`) sous Docker avec la technique du "Slicing" par tranches d'étoiles.
2. **Configurer les GitHub Tokens** multiples dans `.env` (rotation automatique en cas de rate-limit).
3. **Lancer le scan initial** via `docker compose up -d` et surveiller les logs.
4. **Vérifier le remplissage** de la base PostgreSQL via l'API `/api/stats`.

**Résultat attendu :** En 48h, la base passe à 15 000+ ressources brutes (livres, outils, guides).

**Jalons de succès :**
- [ ] 5 000 dépôts en base à J+1
- [ ] 10 000 dépôts en base à J+3
- [ ] 15 000 dépôts en base à J+7

---

## 🧠 Phase 2 (Mois 1-2) : Le Cerveau Sémantique Multilingue

**Objectif :** Comprendre le sens plutôt que les mots. Une recherche en français remonte des résultats en anglais.

### Instructions pour le développeur

1. **Migrer pgvector vers Qdrant** pour la recherche vectorielle haute performance.
2. **Intégrer le modèle multilingue** `paraphrase-multilingual-MiniLM-L12-v2`.
3. **Activer le Batch Processing** (lots de 128 repos) dans `nlp_processor.py`.
4. **Déployer Ollama** avec Mistral-7B pour la génération automatique de fiches techniques (format JSON structuré).

**Résultat attendu :** Recherche sémantique opérationnelle < 2ms pour 15 000 ressources, fiches IA générées.

---

## 🛡️ Phase 3 (Mois 3-4) : Le Validateur de Confiance

**Objectif :** Devenir le premier catalogue cyber mondial certifié "sain et fonctionnel".

### Instructions pour le développeur

1. **Activer le socket Docker** (`/var/run/docker.sock`) dans le `docker-compose.yml` (déjà fait).
2. **Implémenter le workflow SAST éphémère :**
   - `git clone --depth 1` du dépôt cible dans un dossier temporaire.
   - Lancer Trivy, Semgrep et Gitleaks via Docker sur ce dossier.
   - Supprimer le dossier temporaire (`rm -rf`) immédiatement après le scan.
3. **Calculer le Score de Confiance** (0 à 100) basé sur les résultats des scanners.

**Résultat attendu :** Chaque ressource affiche un badge de confiance (`✅ Certifié`, `⚠️ À vérifier`, `❌ Suspect`).

---

## 🌐 Phase 4 (Mois 6+) : L'Aspirateur OSINT Global & Monétisation

**Objectif :** Sortir de GitHub, aspirer l'ensemble du web public, générer des revenus.

### Instructions pour le développeur

1. **Connecter SearXNG** (déjà dans `docker-compose.yml`) au script Python.
2. **Générer des Dorks automatiques** (PDF universitaires, rapports de pentest, PoC).
3. **Indexer les résultats hors-GitHub** dans Qdrant (même pipeline que GitHub).
4. **Lancer la plateforme SaaS :**
   - Version **Gratuite** : Recherche GitHub classique, 10 recherches/jour.
   - Version **PRO (19 €/mois)** : Alertes Zero-Day, OSINT Web, historique illimité.
   - Version **Enterprise** : Déploiement Docker on-premise chez le client.

---

## 📊 Métriques de Suivi

| Phase | Indicateur Clé | Objectif |
|-------|---------------|---------|
| Phase 1 | Nombre de dépôts en base | 15 000+ |
| Phase 2 | Latence de recherche sémantique | < 2ms |
| Phase 3 | % de ressources avec Score de Confiance | 100% |
| Phase 4 | Abonnés PRO actifs | 100+ |
