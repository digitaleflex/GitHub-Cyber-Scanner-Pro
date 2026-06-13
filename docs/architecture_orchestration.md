# 🏗️ Architecture Technique : Orchestration et Traitement Distribué

Pour supporter la charge d'une indexation massive (> 10 000 dépôts) tout en assurant des traitements lourds (NLP, IA Vectorielle, Analyse de Sécurité), l'application repose désormais sur une architecture orientée événements et asynchrone orchestrée par **Celery** et **Redis**.

## 🧩 Modèle d'Orchestration (Workers)

L'application est divisée en plusieurs agents (Workers) spécialisés, gérés par `compose.yml`. Cela permet de ne pas surcharger le processus principal et de répartir intelligemment les ressources CPU/RAM.

```mermaid
graph TD
    A[Scraper / Scheduler] -->|Envoi des URLs| B(Redis: cyber-queue)
    B -->|Queue: harvester| C[Worker: Harvester (Scraping & Clone)]
    B -->|Queue: nlp| D[Worker: NLP (Vecteurs IA Qdrant)]
    B -->|Queue: security| E[Worker: Security (Trivy/Semgrep via Docker)]
    C --> F[(PostgreSQL)]
    D --> G[(Qdrant)]
    E --> F
    H[Flower Dashboard] -.->|Monitoring| B
```

### 1. File d'Attente et Cache (Redis)
Le conteneur `cyber-queue` (Redis) sert de "Broker". Il reçoit les tâches à effectuer et les distribue aux workers disponibles selon la file (queue) désignée.

### 2. Les Agents Intelligents (Celery Workers)

* **worker-harvester (`--queue=harvester`)** : Gère la récupération asynchrone des données (via `aiohttp`) et le clonage éphémère (via `GitPython` avec l'argument `--depth 1`). Configuration CPU large (`-c 4`).
* **worker-nlp (`--queue=nlp`)** : Agent lourd en calcul. Gère le framework NLP (`spaCy`) et le calcul des vecteurs (`sentence-transformers`), avant de stocker les vecteurs dans **Qdrant**. Configuration CPU modérée (`-c 2`).
* **worker-security (`--queue=security`)** : Agent responsable des audits de sécurité de code locaux. Exécute Trivy, Semgrep et Gitleaks de manière dynamique en utilisant le socket Docker monté (`/var/run/docker.sock`). Configuration CPU minimale pour ne pas asphyxier les I/O du disque (`-c 1`).

### 3. Monitoring (Flower)
L'interface **Flower** est exposée sur le port `5555`. Elle permet de visualiser en temps réel l'avancement des tâches Celery, les erreurs éventuelles et le débit d'ingestion. **L'accès est sécurisé** via authentification basique définie par la variable d'environnement `FLOWER_BASIC_AUTH`.

## 📦 Data Stack 100% Open Source

* **PostgreSQL (JSONB)** : Source de vérité principale. Stocke les logs, utilisateurs, et données relationnelles.
* **Qdrant** : Moteur de recherche sémantique avec latence sub-milliseconde.
* **Redis** : File d'attente à haute performance.
* **SearXNG** : Dorking OSINT pour trouver la donnée brute de base sans payer d'APIs tierces.

Cette architecture est souveraine, gratuite, sans licence payante et ne dépend d'aucun service Cloud tiers (AWS, GCP, etc.).