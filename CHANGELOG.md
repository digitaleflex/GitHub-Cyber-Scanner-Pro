# Journal des Modifications (Changelog)

Toutes les modifications notables apportées à ce projet seront documentées dans ce fichier.

---

## [Unreleased] - v4.0.0 - Aspirateur OSINT Global & Monétisation SaaS
### Planifié (Roadmap - Mois 6+)
* Connexion autonome de SearXNG au script Python pour le dorking web automatique.
* Indexation des ressources hors-GitHub (PDF universitaires, rapports de pentest, PoC) dans Qdrant.
* Lancement de la plateforme SaaS avec 3 niveaux : Gratuit, PRO (19€/mois), Enterprise.

---

## [Unreleased] - v3.0.0 - Validateur de Confiance
### Planifié (Roadmap - Mois 3-4)
* Workflow SAST éphémère : clone partiel → Trivy/Semgrep/Gitleaks → suppression immédiate.
* Calcul et affichage du Score de Confiance (0 à 100) avec badges visuels par ressource.
* Limite de 5 clones simultanés maximum (Semaphore) pour éviter la saturation disque.

---

## [Unreleased] - v2.0.0 - Cerveau Sémantique Multilingue
### Planifié (Roadmap - Mois 1-2)
* Migration de pgvector vers Qdrant pour la recherche vectorielle < 2ms sur 15 000+ ressources.
* Intégration du modèle IA multilingue `paraphrase-multilingual-MiniLM-L12-v2` (50+ langues).
* Activation du Batch Processing (lots de 128 dépôts) dans `nlp_processor.py`.
* Déploiement d'Ollama (Mistral-7B) pour la génération automatique de fiches techniques JSON.

---

## [1.5.0] - 2026-06-13
### Architecture 100% Souveraine & Moteur OSINT (Zéro API Payante)

Transition stratégique vers une infrastructure entièrement auto-hébergée, éliminant toute dépendance aux API commerciales payantes (Shodan, Censys, Google API). Coût opérationnel mensuel : 0€.

#### Ajouté
* **Conteneur SearXNG :** Intégration du méta-moteur open-source dans `docker-compose.yml` pour remplacer toutes les API Google/Bing. Requête les moteurs de recherche en arrière-plan et renvoie les résultats au format JSON sans clé ni blocage d'IP.
* **Configuration SearXNG (`searxng/settings.yml`) :** Fichier de configuration initial activant la sortie JSON, le mode OSINT (safe_search=0) et les moteurs Google, Bing et DuckDuckGo.
* **Base vectorielle Qdrant :** Conteneur dédié à la recherche vectorielle haute performance (HNSW), remplaçant pgvector pour les comparaisons d'embeddings sémantiques.
* **Documentation OSINT :** Création de `docs/moteur_osint_searxng.md` (architecture SearXNG et générateur de Dorks) et `docs/moteurs_specialises_osint.md` (stratégie des alternatives libres à Shodan/Censys).
* **Feuille de route 2026 :** Création de `docs/roadmap_strategique_2026.md` définissant les 4 phases de développement jusqu'au lancement SaaS.
* **Issues GitHub Roadmap (42-51) :** Création de 4 nouveaux jalons (v1.0.0 à v4.0.0) et 10 issues détaillées avec critères d'acceptation pour le développeur.

#### Modifié
* **`docker-compose.yml` :** Refactorisation complète pour intégrer Qdrant et SearXNG dans l'architecture multi-conteneurs.

---

## [1.4.0] - 2026-06-13
### Pipeline CI/CD Sécurisée & Qualité du Code (Standard EHAF)

Mise en place d'un pipeline de validation automatique bloquant tout déploiement non sécurisé, conformément au standard de sécurité EHAF (Security Engineering Standard).

#### Ajouté
* **Job CI `code-quality` (GitHub Actions) :** Exécution automatique de Ruff (linting architecture), Bandit (SAST sécurité Python) et Pytest (tests unitaires) avant chaque build Docker.
* **Scan d'image Trivy :** Intégration de `aquasecurity/trivy-action` dans la pipeline. Tout déploiement est bloqué si une vulnérabilité de niveau `HIGH` ou `CRITICAL` est détectée dans l'image Docker.
* **Configuration Ruff (`.ruff.toml`) :** Règles de linting strictes (PEP8, variables inutilisées, imports non triés) pour garantir un code professionnel et maintenable.
* **Suite de tests unitaires (`tests/`) :** Création du dossier `tests/` avec les premiers tests Pytest pour `nlp_processor.py` (lemmatisation, ontologie) et `database.py` (connexion, schéma, TSQuery) via des mocks.
* **Correction Docker Buildx :** Résolution de l'erreur `Cache export is not supported for the docker driver` en ajoutant `docker/setup-buildx-action@v3`.

#### Modifié
* **`.github/workflows/deploy.yml` :** Ajout des jobs `code-quality` (prérequis au build) et du scan Trivy entre la construction locale et la publication sur GHCR.

---

## [1.3.0] - 2026-06-13
### Moteur de Veille OSINT & Connecteurs Spécialisés

#### Ajouté
* **Issues OSINT (37-41) :** Création des issues GitHub pour le chantier OSINT (jalon v1.5.0) : SearXNG Docker, générateur de dorks Python, indexation PDF hors-GitHub, architecture en plugins pour les connecteurs spécialisés.
* **Jalon v1.5.0 :** Création du milestone `v1.5.0 - Veille OSINT & Google Dorking` sur GitHub.

---

## [1.1.0] - 2026-06-13
### Recherche Sémantique & Moteur de Scoring IA 🧠

Cette mise à jour majeure intègre des capacités de traitement automatique du langage naturel (NLP) et d'apprentissage profond pour transformer le scanner en moteur de recherche cyber intelligent et révéler les pépites méconnues de la communauté.

#### Ajouté
* **Analyseur NLP Spacy :** Intégration de Spacy avec modèles bilingues (`en_core_web_sm` / `fr_core_news_sm`) pour la lemmatisation, la détection linguistique et l'extraction sémantique des groupes nominaux.
* **Embeddings Vectoriels (Sentence-Transformers) :** Génération automatique de vecteurs sémantiques à 384 dimensions via le modèle `all-MiniLM-L6-v2` pour capturer le contexte des descriptions.
* **Calcul de Score de Qualité (IA) :** Algorithme intelligent (`score_qualite` sur 100) valorisant la densité sémantique, la présence de concepts cyber clés (Active Directory, Buffer Overflow, etc.), le classement logarithmique des stars, tout en appliquant des pénalités sur le spam (crypto, forex).
* **Base PostgreSQL & pgvector :** Migration de SQLite vers PostgreSQL (image `pgvector/pgvector:pg16`) pour la gestion des données persistantes, avec support des requêtes vectorielles et index GIN sur TSVector pour une recherche plein texte ultra-rapide.
* **Migration SQLite vers Postgres Rétroactive :** Logique de migration automatique au démarrage avec calcul et backfill à la volée des scores de qualité et des embeddings.
* **Tri IA dans les Exports :** Inclusion du score de qualité et tri multicritères sémantiques dans les fichiers JSON et Excel générés.

#### Modifié
* **Recherche temps réel asynchrone :** L'interface utilisateur utilise désormais une recherche sémantique debouncée côté serveur via l'API PostgreSQL.
* **Dockerfile optimisé :** Compilation optimisée de PyTorch en mode CPU uniquement (réduction de 1.5 Go de l'image Docker) et pré-téléchargement des modèles d'IA à la construction de l'image.

## [1.0.0] - 2026-06-13
### Version Monstre 🚀

Cette version initiale marque la transition d'un simple script d'extraction en ligne de commande vers une application web robuste, conteneurisée et autonome.

#### Ajouté
* **Dashboard Web Glassmorphic :** Interface utilisateur en mode sombre (Dark Mode) avec compteurs statistiques, onglets interactifs pour les dépôts et livres, filtres rapides par catégorie et barre de recherche globale en temps réel.
* **Moteur FastAPI & Uvicorn :** Serveur Web léger intégré pour exposer l'API REST et servir l'interface utilisateur.
* **Base de données SQLite (`scanner.db`) :** Remplacement des structures de fichiers temporaires par une base de données relationnelle persistante et optimisée.
* **Démon de validation de disponibilité (Link Checker) :** Thread d'arrière-plan analysant périodiquement la validité de chaque lien de ressource découvert via des requêtes HTTP optimisées (HEAD/GET partiel).
* **Indicateurs de Disponibilité Visuels :** Badges lumineux animés (Vert/Rouge/Orange) avec info-bulles de date sur l'interface et gestion d'opacité atténuée sur les ressources hors ligne.
* **Exportation JSON structuré :** Génération automatique de `cyber_security_catalogues.json` organisant les ressources par dépôts à chaque cycle, en plus du fichier Excel multi-onglets.
* **Gestion du Rate Limiting & Robustesse :** Prise en charge des limites d'appels de l'API GitHub via gestion des en-têtes ETag/Last-Modified en cache SQLite, et logique de retry avec Exponential Backoff.
* **Dockerisation complète :** Conteneurisation de l'application via `Dockerfile` (python:3.11-slim) et configuration de volume persistant dans `docker-compose.yml`.

#### Sécurité
* Création d'un fichier `.gitignore` robuste excluant automatiquement le fichier `.env` contenant le Token GitHub, le répertoire de base de données local `data/` et les fichiers caches ou temporaires.
