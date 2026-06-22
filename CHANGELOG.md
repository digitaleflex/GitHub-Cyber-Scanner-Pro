# Journal des Modifications

Toutes les modifications notables sont documentees dans ce fichier. Format : [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.0.0] - 2026-06-22

### Simplification majeure

Retour a l'objectif initial : un outil simple pour collecter les livres et ressources cybersecurite sur GitHub.

#### Supprime
- Moteur NLP (spacy, sentence-transformers, TF-IDF)
- Moteur LLM (Ollama, Mistral, Flash Cards)
- Scanner de securite SAST (Trivy, Semgrep, Bandit, Gitleaks)
- 21 connecteurs OSINT (NIST, ExploitDB, arXiv, etc.)
- Frontend React (TanStack Start)
- Moteur vectoriel Qdrant
- Workers Celery + Redis
- Moteur OSINT SearXNG
- CLI Rich

#### Simplifie
- `database.py` : 729 -> 319 lignes (suppression Qdrant, pgvector, security, LLM)
- `scanner.py` : nettoyage des daemons overkill
- `requirements.txt` : 16 -> 7 dependances
- `compose.yml` : 9 -> 1 service Docker
- `Dockerfile` : image minimaliste (suppression Trivy, PyTorch, spacy)
- Documentation : 16 -> 3 fichiers

---

## [1.6.0] - 2026-06-13

### Plateforme Cyber Intelligence Pro

Version majeure transformant le scanner en plateforme d'intelligence cyber.

#### Ajoute
- Pipeline SAST automatise (Bandit + Semgrep)
- Verdict de securite (SAIN/SUSPECT/CRITIQUE)
- Ollama local pour les Flash Cards IA
- 20 connecteurs OSINT strategiques
- CLI pour piloter la plateforme
- Architecture distribuee (Celery + Redis)
- Moteur semantique Qdrant
- Frontend TanStack Start

---

## [1.4.0] - 2026-06-13

### Pipeline OSINT Souveraine

Transition vers une infrastructure auto-hebergee.

#### Ajoute
- Conteneur SearXNG pour le Google Dorking
- Integration Trivy, Semgrep, Gitleaks

---

## [1.3.0] - 2026-06-12

### Initialisation

- Structure initiale du scanner Python
- Support SQLite et export Excel
- Modele NLP de base (SpaCy)
