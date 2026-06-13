# 🛡️ Spécification des Garde-fous Techniques : Robustesse à l'Ingestion (10 000+ Dépôts) 🚀

Ce document détaille les garde-fous techniques à implémenter pour éviter les pannes disques, la pollution de la base de données par des doublons de forks, et le biais linguistique lié à la recherche multilingue.

---

## 1. Garde-fou 1 : Protection du Disque (Clonage Éphémère et Concurrence)

> [!CAUTION]
> **Le Risque :** Si le scanner asynchrone clone des dizaines de dépôts simultanément, et que certains contiennent de gros fichiers de dictionnaires (comme *SecLists*, pesant plusieurs Go), le disque dur du serveur va saturer immédiatement, provoquant le crash de tout le système.

### 🛠️ Spécifications d'Implémentation
* **Limitation de la Concurrence :** Utiliser un sémaphore asynchrone (`asyncio.Semaphore(5)`) pour limiter à un maximum de **5 clonages et scans simultanés**.
* **Clonage Partiel et Économe (Blobless Clone) :** Utiliser les options Git pour limiter le téléchargement au strict minimum (dernier commit, pas d'historique de branches, pas de blobs inutiles) :
  ```bash
  git clone --depth 1 --filter=blob:none [URL_DU_REPO] [DOSSIER_TEMP]
  ```
* **Nettoyage Destructif Automatique :** Encapsuler l'appel du scanner dans un bloc `try...finally` pour garantir la suppression complète du dossier temporaire quoi qu'il arrive :
  ```python
  import shutil
  try:
      # Téléchargement et analyse
  finally:
      shutil.rmtree(temp_dir, ignore_errors=True)
  ```

---

## 2. Garde-fou 2 : Déduplication de Contenu par Hachage ( SHA-256 )

> [!WARNING]
> **Le Risque :** Les développeurs font fréquemment des forks (copies conformes) de projets célèbres. Sans déduplication, votre moteur affichera 50 fois le même README sous des noms d'utilisateurs différents, polluant les résultats.

### 🛠️ Spécifications d'Implémentation
* **Signature Numérique (Hash) :** Avant de passer un README ou une description à l'IA, calculer son empreinte numérique unique SHA-256 :
  ```python
  import hashlib
  def calculate_text_hash(text):
      return hashlib.sha256(text.strip().lower().encode('utf-8')).hexdigest()
  ```
* **Index Unique en Base de Données :** Ajouter une colonne `description_hash` (VARCHAR(64)) avec une contrainte d'index unique sur la table PostgreSQL.
* **Ignorer les Doublons :** Lors de l'indexation, si l'empreinte existe déjà, ignorer le dépôt immédiatement pour éviter de consommer de la mémoire et du temps de calcul avec l'IA.

---

## 3. Garde-fou 3 : IA Multilingue (Modèle d'Embedding Multilingue)

> [!IMPORTANT]
> **Le Risque :** Le modèle `all-MiniLM-L6-v2` est optimisé pour l'anglais. Si vous recherchez des ressources écrites en français, l'IA local n'en saisira pas la subtilité sémantique, dégradant fortement le score de pertinence et masquant les meilleures pépites francophones.

### 🛠️ Spécifications d'Implémentation
* **Changement de Modèle :** Remplacer le modèle monolingue par **`paraphrase-multilingual-MiniLM-L12-v2`** de Hugging Face.
  * Ce modèle comprend nativement plus de 50 langues, alignant sémantiquement les concepts français et anglais (ex: "durcissement réseau" et "network hardening" partagent le même espace sémantique).
* **Mise à Jour du Code (`src/nlp_processor.py`) :**
  ```python
  encoder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
  ```
* **Mise à jour du cache Docker (`Dockerfile`) :** Modifier la commande de pré-téléchargement du modèle lors de la phase de build de l'image Docker pour éviter de télécharger le modèle au démarrage du conteneur en production.
