# GitHub Cyber Scanner Pro — Recherche Sémantique & Scoring IA 🧠🚀

Un moteur de recherche et de veille souverain en cybersécurité, autonome et permanent. Il découvre des dépôts, extrait et catégorise automatiquement des ressources techniques (livres, write-ups de CTF, guides de durcissement, modèles de rapports d'audit, questions d'entretiens, et signatures threat intel) en utilisant du **Traitement Automatique du Langage Naturel (Spacy)**, des **Embeddings vectoriels (Sentence-Transformers)**, et les stocke dans **PostgreSQL (pgvector & TSVector)**.

Toutes les ressources sont présentées dans un Dashboard Web d'avant-garde responsive avec tri par pertinence sémantique et score de qualité IA, s'affranchissant du simple classement classique par étoiles.

---

## 🌟 Proposition de Valeur : Framework VUPF & Mom Test 🎯

Le projet répond directement aux défis majeurs de l'apprentissage et de la veille en cybersécurité. Il s'inscrit parfaitement dans le framework **VUPF (Valuable/Douloureux, Urgent, Popular, Frequent)** :

### 1. 💔 Douloureux (Valuable) : L'infobésité et le bruit visuel sur GitHub
* **Le problème :** L'information sur GitHub est surabondante. Chercher des ressources ou outils sur un sujet comme le "Pentest Active Directory" renvoie plus de 5 000 résultats. Cependant, **95 % d'entre eux sont des projets abandonnés, obsolètes ou de simples copier-coller (forks) sans valeur**.
* **La douleur :** Un ingénieur cyber ou un étudiant perd des heures précieuses à cloner des dépôts pour s'apercevoir qu'ils ne fonctionnent plus ou ne contiennent rien de pertinent.
* **La solution :** Notre moteur élimine ce bruit en triant les ressources par pertinence sémantique et score de qualité (via NLP & IA), et non par simple popularité brute (stars).

### 2. ⚡ Urgent : La course contre la montre face aux vulnérabilités (Zero-Day)
* **Le problème :** En cybersécurité, les techniques d'attaque et de défense évoluent à un rythme effréné. Une méthode apprise il y a deux ans peut être totalement inutile aujourd'hui. L'accès à la ressource la plus récente est une question de survie professionnelle.
* **L'urgence :** Lors de la sortie d'une faille majeure (comme un nouveau Zero-Day), les experts ont besoin de trouver instantanément les meilleurs scripts de test (PoC) et documentations associés.
* **La solution :** Notre scanner permanent capture ces pépites à la minute où elles sont publiées sur GitHub, avant même qu'elles ne soient indexées par Google ou partagées sur les réseaux sociaux.

### 3. 📈 Populaire : Une communauté mondiale en explosion
* **Le problème :** Le marché de la cybersécurité fait face à une pénurie critique de main-d'œuvre qualifiée à l'échelle mondiale. Des centaines de milliers de personnes (étudiants, administrateurs système en reconversion, développeurs) cherchent à se former au quotidien.
* **La popularité :** Le succès phénoménal des listes statiques "Awesome" (dépassant parfois les 50 000 étoiles sur GitHub) démontre une demande gigantesque pour des catalogues structurés. La communauté cherche constamment des guides d'étude, des banques de questions d'entretien et des outils d'entraînement.
* **La solution :** Centraliser et catégoriser dynamiquement les meilleures ressources (Livres, Write-ups, Checklists, Modèles, Outils) pour offrir un guichet unique d'apprentissage cyber de confiance.

### 4. 🔄 Fréquent : Un besoin quotidien pour les praticiens
* **Le problème :** Un professionnel de la sécurité n'effectue pas de recherche une fois par an. C'est un besoin quotidien lié aux missions en cours : *"Aujourd'hui je dois auditer un serveur Kubernetes, où est la meilleure checklist de durcissement ?"*, *"Demain je dois tester une application Web, quel est le payload le plus récent pour contourner ce WAF ?"*.
* **La fréquence :** Notre outil devient un véritable rituel quotidien, le "Google de confiance" de l'ingénieur cyber, consulté à chaque démarrage de projet ou d'audit.

---

> [!TIP]
> ### 🎯 Le "Mom Test" du projet
> Si l'on applique les principes du livre *The Mom Test* à cette idée : les utilisateurs ne se contenteraient pas de dire *"C'est une bonne idée"* pour faire plaisir. Ils utiliseraient la plateforme immédiatement et activement car elle résout directement leur frustration quotidienne de recherche de code et de ressources de qualité. **Le projet passe ainsi du statut de gadget à celui d'infrastructure de productivité incontournable.**

---

## ⚡ Fonctionnalités Clés

* **Analyseur NLP Spacy (Bilingue en/fr) :** Lemmatisation, filtrage grammatical (Part-of-Speech) et extraction sémantique des concepts clés de confiance.
* **Embeddings Vectoriels 384D :** Vectorisation profonde des descriptions avec le modèle `all-MiniLM-L6-v2` (Sentence-Transformers) pré-caché au build Docker.
* **Recherche Sémantique de Pointe :** PostgreSQL avec extension `pgvector` et indexation GIN sur type `tsvector` pour des recherches instantanées, asynchrones (debounced 350ms) et pertinentes.
* **Scoring de Qualité IA (`score_qualite` / 100) :** Algorithme qui valorise la richesse sémantique, la présence de jargon cyber d'autorité, applique un poids logarithmique modéré aux étoiles et inflige de lourdes pénalités au spam (crypto, forex, airdrop).
* **Scan Hybride Continu & Découverte :** Deux boucles de scan pour chaque thématique : par **popularité** (références solides) et par **activité récente** (découverte de nouveaux dépôts récents avec peu d'étoiles).
* **Catégorisation en 7 Types de Ressources (IA) :** Classement automatique des liens extraits :
  * 🧬 **Book** (Livres PDF, ePub, cours)
  * 🔴 **Threat-Intel** (Règles Yara/Sigma, listes d'IoC)
  * 🔵 **Hardening** (Checklists de sécurisation, guides CIS)
  * 🟢 **Write-up** (Résolutions de CTF, méthodologies de Bug Bounty)
  * 🟣 **Interview** (Questions d'embauche cyber, notes d'examens OSCP/CISSP)
  * 💖 **Template** (Modèles de rapports de pentest, PSSI, livrables pro)
  * 🛠️ **Tool** (Scripts et outils associés)
* **Vérification Automatique des Liens (Link Checker) :** Démon d'arrière-plan testant en HEAD/GET asynchrone la disponibilité des ressources toutes les 3 secondes.
* **Dashboard Premium Glassmorphic :** Interface utilisateur en mode sombre avec badges de statut animés, filtres par type/catégorie et téléchargements multi-formats.

---

## 🛠️ Architecture Technique

Le projet s'exécute dans une architecture multi-conteneurs Docker orchestrée par `docker-compose` :

```
             ┌────────────────────────┐
             │    fastapi (scanner)   │ <─── Port 8000 (UI / API REST)
             └────────────────────────┘
                │                  │
         (NLP Spacy / embedding)   │ (Persistance / Vector search)
                │                  ▼
                │       ┌──────────────────────┐
                └─────> │   db (pgvector:16)   │ <─── Port 5432
                        └──────────────────────┘
```

1. **Service `scanner` :** FastAPI + Uvicorn + sentence-transformers (all-MiniLM-L6-v2) + Spacy (en/fr). Exécute l'API web et les démons (Scan GitHub, Link checker).
2. **Service `db` :** PostgreSQL 16 avec extension `pgvector` et stockage persistant.

---

## 🚀 Installation & Déploiement

### Étape 1 : Configuration
Créez un fichier `.env` à la racine du projet :
```env
GITHUB_TOKEN=votre_token_github_ici
SCAN_INTERVAL_SECONDS=3600
DB_HOST=db
DB_PORT=5432
DB_NAME=scanner_db
DB_USER=postgres
DB_PASSWORD=cyberpass
```

### Étape 2 : Lancement
Démarrez les conteneurs (compilation de PyTorch CPU et téléchargement des modèles d'IA au premier build) :
```bash
docker compose up --build -d
```

### Étape 3 : Accéder au Dashboard
Rendez-vous sur : 👉 **[http://localhost:8000](http://localhost:8000)**

---

## 🔗 CI/CD GitHub Actions & Déploiement Privé

Le fichier `.github/workflows/deploy.yml` configure un déploiement sécurisé en circuit fermé :
1. **Build & Push Privé** : L'image de code est compilée et stockée sur le registre privé **GitHub Container Registry (GHCR)**.
2. **Déploiement à chaud sans perte** : SSH sur votre serveur de production pour télécharger la nouvelle image et relancer le scanner. La base PostgreSQL (montée via volume physique persistant) reste intacte et n'est jamais exposée.

Pour l'utiliser, configurez les secrets suivants dans les paramètres de votre dépôt GitHub :
* `SERVER_HOST` : IP de votre serveur.
* `SERVER_USER` : Utilisateur SSH (ex: `ubuntu`, `root`).
* `SERVER_SSH_KEY` : Votre clé SSH privée.
* `CR_PAT` : Un Personal Access Token (PAT) GitHub avec le droit `read:packages` pour que votre serveur puisse télécharger l'image privée.

---

## 📊 Endpoints API Disponibles

* `GET /` : Interface Web Glassmorphic.
* `GET /api/stats` : Statistiques de la base et statut du scanner.
* `GET /api/repositories` : Liste des dépôts triés par score de qualité (IA).
* `GET /api/books` : Liste des ressources triées par pertinence sémantique et score de qualité, avec support de recherche textuelle via `?q=recherche`.
* `POST /api/scan` : Déclenche un cycle de scan hybride manuel en tâche de fond.
* `GET /api/download` : Téléchargement du rapport Excel complet (`cyber_security_catalogues.xlsx`).
* `GET /api/download/json` : Téléchargement de la base au format JSON structuré (`cyber_security_catalogues.json`).

---

## 🔒 Sécurité (EHAF Standard)
* Secrets exclus via `.gitignore`.
* Circuit fermé souverain : aucune donnée collectée n'est transmise à un tiers.
* Pas de comptes privilégiés dans les conteneurs et volume PostgreSQL isolé.
