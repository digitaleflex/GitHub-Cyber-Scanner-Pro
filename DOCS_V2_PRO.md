# 🛡️ Manuel de la Plateforme Cyber Intelligence Pro (V2) 🚀

Cette documentation détaille le fonctionnement de la nouvelle architecture souveraine de veille cyber massive.

## 🏗️ Architecture Globale

La plateforme repose sur 4 piliers technologiques :
1.  **Scanner de Masse** : Découverte continue sur GitHub (Asynchrone + Star Slicing).
2.  **Audit de Santé (SAST)** : Analyse statique du code (Bandit/Semgrep) pour garantir l'absence de malwares.
3.  **Intelligence Artificielle (Ollama)** : Génération de fiches techniques flash (Objectif/Prérequis/Commande).
4.  **Grand Orchestrateur OSINT** : Synchronisation de 20 sources mondiales (Exploits, NIST, arXiv, CISA).

---

## 🌍 Les 20 Sources OSINT Intégrées

Votre plateforme aspire désormais les données des sources suivantes :
*   **Offensif** : Exploit-DB, 0day.today, CXSecurity, Packet Storm.
*   **Défensif & Intel** : CISA KEV (Failles exploitées), ThreatFox (IoC), AlienVault OTX, Malpedia.
*   **Académique & Normes** : NIST (SP 800), arXiv (cs.CR), ENISA, SANS Reading Room.
*   **Communauté & Audit** : CIS Benchmarks, Public Pentest Reports, Codeberg, Archive.org.

---

## 🛠️ Guide d'Utilisation

### 1. Lancement Rapide (Bouton Turbo)
- **Windows** : Double-cliquez sur `run_platform.bat`.
- **Linux/macOS** : `./run_platform.sh`.
*Ceci lance l'infrastructure, télécharge le modèle IA et ouvre le dashboard.*

### 2. Interface CLI (Cyber Terminal)
Utilisez la commande `cyber` pour une interaction experte :
- `cyber stats` : État de la base.
- `cyber search <query>` : Chercher un outil GitHub.
- `cyber intel <query>` : Chercher un exploit ou un rapport NIST.
- `cyber flash <repo>` : Voir la fiche IA d'un outil.

---

## ⚙️ Configuration Technique

### Variables d'Environnement (`.env`)
- `GITHUB_TOKEN` : Pour éviter les limites de l'API GitHub.
- `LLM_MODEL` : Modèle Ollama à utiliser (par défaut `mistral`).
- `DB_PASSWORD` : Mot de passe de la base PostgreSQL.

### Structure des Dossiers
- `src/connectors/` : Les 20 scripts d'aspiration OSINT.
- `src/security_analyzer.py` : Le moteur d'audit SAST.
- `src/llm_summarizer.py` : L'interface avec Ollama.
- `src/orchestrator.py` : Le cerveau de synchronisation.

---

## 📊 Roadmap & Évolutions
- **Phase 3** : Corrélation automatique entre Exploits et Outils GitHub.
- **Phase 4** : Module RAG pour discuter avec les PDF du NIST et d'arXiv.

---
*Documentation générée le 13 juin 2026 — Plateforme Souveraine v2.0*
