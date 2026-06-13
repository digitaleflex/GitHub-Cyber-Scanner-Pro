# GitHub Cyber Scanner Pro — Version Monstre 🚀

Un scanner de cybersécurité autonome et permanent, conçu pour découvrir des dépôts GitHub, extraire des livres/ressources éducatives (PDF, ePub, liens de téléchargement) et les présenter dans un magnifique Dashboard Web dynamique en mode sombre (Dark Mode) avec suivi de disponibilité en temps réel.

---

## 🌟 Fonctionnalités Clés

* **Recherche Thématique Automatisée :** Interroge l'API GitHub de manière optimisée via plusieurs requêtes ciblées (*offensive, defensive, certifications, cheat sheets, pentest, etc.*).
* **Extraction Intelligente depuis les README :** Analyse le contenu brut du README de chaque dépôt découvert pour y extraire tous les liens de livres ou de ressources éducatives en appliquant des filtres avancés (extensions `.pdf`, `.epub`, domaines cloud comme Google Drive, MEGA, Dropbox, et mots-clés d'apprentissage).
* **Catégorisation Automatique :** Trie les ressources extraites dans 5 catégories distinctes (*Offensive / Red Team*, *Defensive / Blue Team*, *Certifications*, *Cheat Sheets / Références*, *Général / InfoSec*).
* **Vérification de la Disponibilité en Temps Réel (Link Checker) :** Un démon d'arrière-plan valide en continu la disponibilité des liens extraits (toutes les 3 secondes, max 50 par cycle) et met à jour leur statut.
* **Dashboard Web Premium Glassmorphic :** Une interface web responsive en mode sombre avec effets de lueurs colorées (*glow*), filtres par catégorie, recherche instantanée et compteurs statistiques dynamiques.
* **Badges Visuels Intelligents :** Les liens sont affichés avec des badges de statut lumineux :
  * **Disponible (Vert Glow) :** Le lien est actif et téléchargeable.
  * **Hors ligne (Rouge Glow) :** Le lien est mort ou inaccessible. La ligne entière est estompée pour une visibilité immédiate.
  * **Non vérifié (Orange Glow) :** Le lien est en attente de vérification par le démon.
* **Exportations Multi-formats :**
  * Rapport Excel multi-onglets (`cyber_security_catalogues.xlsx`).
  * Fichier JSON structuré (`cyber_security_catalogues.json`).
  * Les deux rapports sont téléchargeables directement en un clic depuis le Dashboard.
* **Optimisation de l'API GitHub & Cache :** Utilise un système de cache des en-têtes `ETag` et `Last-Modified` dans SQLite pour éviter de consommer inutilement votre quota d'appels API.

---

## 🛠️ Architecture du Projet

Le projet fonctionne de manière conteneurisée et s'articule autour de 3 composants exécutés en parallèle :
1. **Démon de Scan GitHub :** Interroge l'API, insère les dépôts et analyse les README.
2. **Démon Link Checker :** Valide les liens stockés en base.
3. **Serveur FastAPI :** Sert l'API JSON et le Dashboard HTML.

La persistance des données est garantie par une base SQLite locale (`data/scanner.db`) montée sous forme de volume Docker.

---

## 🚀 Installation & Déploiement

### Prérequis
* Docker et Docker Compose installés sur votre machine.
* Un **Token d'Accès Personnel (PAT) GitHub** (sans droits particuliers requis, juste pour augmenter vos limites d'appels API).

### Étape 1 : Configuration
Créez un fichier `.env` à la racine du projet avec les variables suivantes :
```env
GITHUB_TOKEN=votre_token_github_ici
SCAN_INTERVAL_SECONDS=3600
DATA_DIR=data
```

### Étape 2 : Lancement de l'application
Démarrez les conteneurs en arrière-plan :
```bash
docker compose up --build -d
```

### Étape 3 : Accéder au Dashboard
Ouvrez votre navigateur et rendez-vous sur :
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 📊 Endpoints API Disponibles

* `GET /` : Dashboard HTML.
* `GET /api/stats` : Statistiques de la base et statut actuel du scanner.
* `GET /api/repositories` : Liste de tous les dépôts indexés triés par étoiles.
* `GET /api/books` : Liste de tous les livres et ressources extraits avec statut et date de vérification.
* `POST /api/scan` : Déclenche un scan manuel immédiat en arrière-plan.
* `GET /api/download` : Téléchargement du fichier Excel généré.
* `GET /api/download/json` : Téléchargement du fichier JSON exporté.

---

## 🔒 Sécurité (Least Privilege)
* Le fichier `.env` contenant votre token secret ainsi que le dossier de données locales `data/` sont exclus du dépôt grâce au fichier `.gitignore`.
* L'application s'exécute de manière isolée dans son conteneur Docker.
