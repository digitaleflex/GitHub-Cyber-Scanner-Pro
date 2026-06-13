# 🛡️ CyberScan Hub 2026 : Plateforme de Veille Cyber Souveraine

## 🎯 Vision du Projet
CyberScan Hub est un SaaS d'intelligence documentaire et de veille cyber **100% Self-Hosted**. Il permet d'indexer, de scorer sémantiquement et d'auditer la sécurité de plus de 10 000 dépôts et ressources mondiales sans dépendre d'API cloud tierces.

---

## 🏗️ Architecture "Sovereign Stack"

L'infrastructure est orchestrée via **Docker Compose** et repose sur les briques suivantes :

*   **Frontend :** TanStack Start (React) + pnpm + Tailwind CSS.
*   **Backend API :** FastAPI (Python 3.11).
*   **Recherche Sémantique :** PostgreSQL 16 (pgvector) + Qdrant (Rust Vector Engine).
*   **Orchestration :** Celery + Redis (Background Jobs).
*   **OSINT Engine :** SearXNG (Méta-moteur local).
*   **NLP & IA :** Sentence-Transformers (Local) + SpaCy.

---

## 🧠 Algorithmes de Pointe (Déjà Implémentés)

Le projet dispose de trois moteurs algorithmiques critiques situés dans `src/` :

1.  **StealthClient (`src/utils/http_client.py`)** : 
    *   *Fonction* : Contournement des WAF (Cloudflare/Akamai).
    *   *Technique* : Usurpation TLS (JA3 Fingerprint) via `curl_cffi` + Backoff exponentiel.
2.  **OSINTHarvester (`src/osint_harvester.py`)** : 
    *   *Fonction* : Usine de transformation Web-to-DB.
    *   *Technique* : Exécution de Dorks, extraction sémantique multilingue, filtrage de qualité (Score > 60).
3.  **RealTimeWatcher (`src/realtime_watcher.py`)** : 
    *   *Fonction* : Radar de découverte instantanée.
    *   *Technique* : Surveillance des flux GitHub Archive (GHArchive) par fenêtres de 5 minutes.

---

## 🚀 Installation & Démarrage (Développeur)

### 1. Configuration des Environnements
Créez un fichier `.env` à la racine :
```env
# API GitHub
GITHUB_TOKENS=ghp_token1,ghp_token2 # Tokens pour le scan
GITHUB_ADMIN_TOKEN=ghp_admin_token   # Token pour sync le backlog GitHub
GITHUB_REPO=votre_user/votre_repo

# Database
DB_PASSWORD=cyberpass
DB_HOST=localhost
```

### 2. Lancement de l'Infrastructure
```bash
docker compose up -d --build
```

### 3. Synchronisation du Backlog (GitHub Issues)
Pour injecter les 22 issues de développement et les 4 Milestones :
```bash
pip install requests python-dotenv
python sync_github_issues.py
```

### 4. Initialisation du Frontend
```bash
cd frontend
pnpm install
pnpm dev
```

---

## 🗺️ Roadmap vers le MVP

*   **Sprint 1 (Fondations)** : Migration des scripts vers Celery, sécurisation JWT, optimisation pgvector.
*   **Sprint 2 (Mass Indexing)** : Activation du Slicing GitHub (10k repos) et synchronisation Qdrant.
*   **Sprint 3 (Audit & OSINT)** : Intégration Trivy/Semgrep et recherche automatisée de PDF via SearXNG.
*   **Sprint 4 (Beta SaaS)** : Interface TanStack Start finale, rapports CVE et exports PDF.

---

## 🛡️ Sécurité & Confidentialité
*   **Zero Cloud Leak** : Aucun scan n'est envoyé vers des API externes.
*   **Stealth Mode** : Rotation d'IP et d'User-Agents systématique.
*   **Isolation** : Analyse des dépôts dans des conteneurs Docker éphémères.

---
*Projet généré et structuré par Gemini CLI - Juin 2026*
