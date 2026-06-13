# 📓 Journal des Modifications (CHANGELOG) - GitHub Cyber Scanner Pro

Toutes les modifications notables de ce projet seront documentées dans ce fichier. Le format est basé sur [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.5.0] - 2026-06-13
### 🚀 Architecture Distribuée & Gouvernance GitHub (Prêt pour Production)
Cette version marque la fin de la phase de conception technique. L'infrastructure est désormais prête pour le lancement du Sprint 1 (Ingestion de masse).

#### 🏗️ Architecture & Infrastructure
*   **Migration Docker Compose V2** : Renommage de `docker-compose.yml` en `compose.yml` selon les derniers standards.
*   **Orchestration Distribuée** : Intégration de **Celery** (Workers) et **Redis** (Broker) pour le traitement asynchrone des tâches (Harvester, NLP, Security).
*   **Moteur Sémantique** : Intégration native de **Qdrant** pour la recherche vectorielle haute performance.
*   **Base de Données** : Création du script `data/scanner_sqlite_dump.sql` (PostgreSQL) incluant le support JSONB, le scoring cyber et l'historique des scans de sécurité.
*   **Supervision** : Ajout de **Flower** pour le monitoring en temps réel des tâches Celery.

#### 🛠️ Choix de la Stack (Souveraineté & Performance)
*   **Frontend Pro** : Adoption de **TanStack Start** (React) pour un auto-hébergement souverain et performant (Exit Next.js/Vercel).
*   **Gestionnaire pnpm** : Passage à **pnpm** pour des builds Docker ultra-rapides et une consommation de RAM optimisée.
*   **Backend robuste** : Confirmation de **FastAPI** pour l'API et de **Python 3.11** pour le pipeline IA.

#### 🤝 Gouvernance & Workflow GitHub
*   **Guide de Contribution** : Création de `CONTRIBUTING.md` définissant les normes de code, de sécurité (SAST) et les conventions de commit.
*   **Templates d'Issues** : Mise en place de formulaires interactifs (`feature_request.yml`, `bug_report.yml`) pour structurer le développement dès la source.
*   **Documentation technique** : Création de `docs/stack_technique.md` et `docs/architecture_orchestration.md`.

---

## [1.4.0] - 2026-06-13
### Pipeline OSINT Souveraine & Moteur de Recherche (Zéro API)
Transition stratégique vers une infrastructure entièrement auto-hébergée.

#### Ajouté
*   **Conteneur SearXNG** : Intégration du méta-moteur open-source dans `compose.yml` pour le Google Dorking gratuit.
*   **Feuille de route 2026** : Création de `docs/roadmap_strategique_2026.md`.
*   **Validation Sécurité** : Intégration du socket Docker pour piloter **Trivy**, **Semgrep** et **Gitleaks** localement.

---

## [1.3.0] - 2026-06-12
### Initialisation du Projet
*   Structure initiale du scanner Python.
*   Support SQLite et exportation Excel (Pandas).
*   Modèle NLP de base (SpaCy).
