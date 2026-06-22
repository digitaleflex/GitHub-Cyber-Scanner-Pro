# Journal des Modifications

Format : [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.1.0] - 2026-06-22

### Ameliorations
- Scripts scan, report, dashboard plus propres
- Filtres anti-bruit etendus (learning, beginner, resources)
- Dashboard avec stats detaillees (max etoiles, total)
- Support parametre `days` pour scan.py

---

## [2.0.0] - 2026-06-22

### Simplification majeure
Retour a l'objectif initial : decouvrir les outils cybersecurite sur GitHub.

#### Ajoute
- Scan auto tous les 3 jours via GitHub Actions
- Dashboard HTML interactif
- Rapport markdown automatique
- Export JSON des donnees
- Fichiers communautaires (LICENSE, CODE_OF_CONDUCT, SECURITY)

#### Supprime
- Moteur NLP (spacy, sentence-transformers)
- Moteur LLM (Ollama, Mistral)
- Scanner SAST (Trivy, Semgrep, Bandit, Gitleaks)
- 21 connecteurs OSINT
- Frontend React (TanStack Start)
- Workers Celery + Redis

---

## [1.6.8] - 2026-06-13

### Corrections
- Divers bugfixes

---

## [1.6.0] - 2026-06-13

### Plateforme Cyber Intelligence Pro
- Pipeline SAST automatise
- Flash Cards IA (Ollama)
- 20 connecteurs OSINT
- Frontend TanStack Start
