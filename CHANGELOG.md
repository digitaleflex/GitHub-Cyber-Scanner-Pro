# Journal des Modifications (Changelog)

Toutes les modifications notables apportées à ce projet seront documentées dans ce fichier.

---

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
