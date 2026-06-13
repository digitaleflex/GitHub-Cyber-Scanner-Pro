# 📋 Cahier des Charges Fonctionnel : User Stories MVP 🚀

Ce document formalise les exigences fonctionnelles et les critères d'acceptation sous forme de **User Stories** pour les 4 chantiers technologiques majeurs de la version commerciale (MVP) du **GitHub Cyber Scanner Pro**.

---

## 🛡️ Chantier 1 : L'Analyseur de "Santé et Sécurité" du Code (Filtre de Confiance)

### 👤 US 1.1 : Lancement de l'analyse statique automatique
* **En tant que** : Pentesteur ou chercheur en sécurité,
* **Je souhaite** : Que chaque outil ou script référencé sur la plateforme soit automatiquement scanné à la recherche de portes dérobées (backdoors) ou de fonctions suspectes,
* **Afin de** : M'assurer que je peux cloner et exécuter le code sur ma machine de test sans risque d'infection ou de compromission.

#### 🏁 Critères d'acceptation :
- [ ] Dès qu'un nouveau dépôt de type `Tool` est détecté par le scanner, le script Python télécharge de manière éphémère ses fichiers sources critiques.
- [ ] L'analyseur exécute automatiquement **Bandit** (pour Python) et des règles **Semgrep** ciblées (détection de chaînes obfusquées, d'adresses IP suspectes codées en dur, d'appels système inhabituels).
- [ ] Le résultat du scan (Sain, Suspect, Critique) est enregistré en base de données.

---

### 👤 US 1.2 : Visualisation des certificats de confiance sur le Dashboard
* **En tant qu'** : Utilisateur professionnel de la plateforme,
* **Je souhaite** : Voir un badge de sécurité "Certifié Sain" ou un indicateur de risque sur chaque carte d'outil,
* **Afin de** : Filtrer et sélectionner uniquement les dépôts validés par le filtre de confiance.

#### 🏁 Critères d'acceptation :
- [ ] Un badge vert **"Certifié Sain"** s'affiche si aucun avertissement critique n'est levé par Bandit/Semgrep.
- [ ] Un badge rouge **"Non certifié / Suspect"** s'affiche en cas d'alerte, accompagné d'une info-bulle résumant les menaces détectées (ex: *"Présence de fonctions d'obfuscation suspectes"*).
- [ ] L'interface propose un filtre à bascule : `"Afficher uniquement les outils certifiés sers"` (activé par défaut pour la formule gratuite).

---

### 👤 US 1.3 : Workflow de clonage ephemere et de nettoyage automatique
* **En tant que** : Developpeur ou administrateur de la plateforme,
* **Je souhaite** : Que le code source des depots soit clone de maniere temporaire et sans historique (depth 1), puis supprime directement apres le scan SAST,
* **Afin de** : Minimiser l'espace disque consomme et la bande passante sur mon serveur tout en garantissant un audit complet et local.

#### 🏁 Criteres d'acceptation :
- [ ] Le script Python lance la commande `git clone --depth 1 [URL_DU_REPO] [DOSSIER_TEMP]` pour telecharger uniquement le dernier commit.
- [ ] Les analyses de securite (Trivy, Semgrep, Gitleaks) sont executees en local via Docker sur ce dossier temporaire.
- [ ] Une fois les rapports JSON charges en base de donnees, le script supprime recursivement le dossier temporaire.
- [ ] Aucune donnee de code source n'est conservee sur le disque dur apres traitement.

---

## 🧠 Chantier 2 : Le Générateur Automatique de Fiches de Synthèse (LLM Local)

### 👤 US 2.1 : Génération de la fiche technique standardisée
* **En tant qu'** : Abonné professionnel ou veilleur cyber,
* **Je souhaite** : Que chaque dépôt contienne un résumé automatique standardisé de 3 lignes (Objectif, Prérequis, Commande flash),
* **Afin de** : Comprendre instantanément comment tester et déployer l'outil sans avoir à lire le fichier README complet.

#### 🏁 Critères d'acceptation :
- [ ] Le scanner envoie la description et le README nettoyés au conteneur local **Ollama** (`Mistral-7B` ou `Llama-3`).
- [ ] Le prompt force le LLM à répondre sous un format standardisé de 3 lignes :
  1. **Objectif** : Ce que fait l'outil en une phrase claire.
  2. **Prérequis** : Langage et OS requis (ex: Python 3, Linux).
  3. **Commande Flash** : L'instruction en ligne de commande exacte pour l'exécuter.
- [ ] Le résultat est stocké dans PostgreSQL et n'est régénéré que si le README subit des modifications majeures.

---

### 👤 US 2.2 : Affichage des fiches de synthèse interactives
* **En tant qu'** : Utilisateur consultant ou ingénieur pressé,
* **Je souhaite** : Cliquer sur une ressource pour afficher sa fiche de synthèse dans une fenêtre pop-up ou un tiroir coulissant (drawer) élégant,
* **Afin de** : Copier rapidement la commande de démarrage en un clic.

#### 🏁 Critères d'acceptation :
- [ ] L'interface propose un bouton interactif "Fiche Flash" sur chaque carte.
- [ ] Le clic ouvre une modale glassmorphic contenant le résumé généré par le LLM.
- [ ] Un bouton de copie rapide (Copy to Clipboard) est présent à côté de la "Commande flash".

---

## 📊 Chantier 3 : Le Détecteur de Tendances et de "Morts" (Cycle de Vie)

### 👤 US 3.1 : Calcul dynamique du Score de Vitalité
* **En tant que** : Veilleur ou ingénieur cyber en mission,
* **Je souhaite** : Connaître l'état d'activité et de maintenance de chaque outil grâce à un score dynamique,
* **Afin d'** : Éviter d'intégrer ou d'étudier des projets obsolètes ou abandonnés.

#### 🏁 Critères d'acceptation :
- [ ] Le démon calcule quotidiennement le **Score de Vitalité** (sur 100) en interrogeant les métadonnées de l'API GitHub (date du dernier commit, ratio d'issues résolues, activité récente des contributeurs).
- [ ] Si le dernier commit date de plus de 18 mois, le score perd automatiquement 50 points et la mention **"Obsolète / Non maintenu"** est appliquée.
- [ ] Si le dépôt enregistre une croissance fulgurante (ex: +200 stars en moins de 7 jours), il reçoit un badge **"Tendance Chaude"** (Hot).

---

### 👤 US 3.2 : Tri et masquage des projets obsolètes
* **En tant qu'** : Utilisateur,
* **Je souhaite** : Pouvoir filtrer et ordonner les résultats par Score de Vitalité, ou masquer les projets classés comme abandonnés,
* **Afin de** : Gagner du temps lors de mes recherches d'outils opérationnels.

#### 🏁 Critères d'acceptation :
- [ ] Ajout d'une option de tri dans le menu déroulant principal : `"Trier par Vitalité (Maintenance)"`.
- [ ] Ajout d'une case à cocher dans la barre latérale des filtres : `"Masquer les projets obsolètes"`.

---

## 📰 Chantier 4 : L'Interconnexion avec l'Actualité (Le Pont Cyber)

### 👤 US 4.1 : Agrégation des alertes et menaces mondiales
* **En tant que** : Analyste SOC ou RSSI,
* **Je souhaite** : Que ma plateforme de veille se connecte aux flux RSS officiels du CERT-FR, de l'ANSSI et des médias cyber de référence,
* **Afin d'** : Avoir une vue d'ensemble des failles critiques du jour.

#### 🏁 Critères d'acceptation :
- [ ] Un démon d'arrière-plan interroge toutes les heures les flux RSS de l'ANSSI/CERT-FR, de The Hacker News et de Bleeping Computer.
- [ ] Les mots-clés et entités nommées (CVE, logiciels comme *Active Directory*, *Exchange*, *Apache*) sont extraits des titres d'actualité via NLP.
- [ ] Les 3 dernières actualités cyber brûlantes sont affichées dans un bandeau d'alerte animé en haut du Dashboard.

---

### 👤 US 4.2 : Corrélation automatique actualités - base de données
* **En tant qu'** : Ingénieur confronté à une nouvelle menace urgente,
* **Je souhaite** : Cliquer sur une alerte d'actualité pour voir instantanément toutes les ressources associées présentes dans la base de données,
* **Afin de** : Trouver immédiatement des scripts de test (PoC) et des checklists de durcissement (Hardening) pour neutraliser la menace.

#### 🏁 Critères d'acceptation :
- [ ] Un clic sur l'alerte d'actualité lance automatiquement une recherche sémantique avec les mots-clés extraits sur notre base PostgreSQL.
- [ ] Les résultats associés (outils de détection, guides de remédiation, signatures Yara) sont poussés en haut de la liste avec un indicateur **"Recommandé pour l'actualité en cours"**.
