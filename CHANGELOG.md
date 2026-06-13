# Journal des Modifications (Changelog)

Toutes les modifications notables apportées à ce projet seront documentées dans ce fichier.

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
