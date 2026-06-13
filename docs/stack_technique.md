# 🛠️ Stack Technologique : Choix et Justifications

Ce document détaille les choix technologiques pour le **GitHub Cyber Scanner Pro**. Ces choix sont dictés par un impératif de **souveraineté**, de **performance** et de **maintenance simplifiée** en mode auto-hébergé (Self-Hosted).

---

## 🎨 Frontend : TanStack Start (React) + pnpm

### Pourquoi TanStack Start ?
Bien que Next.js soit leader, nous avons choisi **TanStack Start** pour les raisons suivantes :
*   **Souveraineté (Anti-Vercel)** : TanStack Start est agnostique et conçu pour tourner parfaitement dans un conteneur Docker standard (via Nitro), sans les complexités d'auto-hébergement de Next.js.
*   **Contrôle Total** : Contrairement à Next.js qui impose des conventions rigides (Server Components), TanStack Start offre un contrôle explicite, crucial pour l'intégration avec nos conteneurs locaux (Qdrant, Redis).
*   **Type Safety End-to-End** : Grâce à TanStack Router, le typage est garanti de l'API jusqu'à l'interface, éliminant les crashs en production.

### Pourquoi pnpm ?
Le gestionnaire de paquets **pnpm** est obligatoire pour ce projet :
*   **Builds Docker ultra-rapides** : Grâce au système de liens rigides (Hard Links), le cache est optimisé, réduisant le temps de build de 3 minutes à 20 secondes.
*   **Économie de RAM** : pnpm est beaucoup plus léger que npm, laissant plus de ressources au serveur pour les calculs IA et les scans de sécurité.

---

## ⚙️ Backend : FastAPI + Celery

### FastAPI
*   **Rapidité** : L'un des frameworks Python les plus rapides (basé sur Starlette et Pydantic).
*   **Async natif** : Parfait pour gérer des milliers de requêtes vers GitHub et SearXNG en parallèle.
*   **Documentation Auto** : Génération automatique de Swagger (`/docs`) pour tester les endpoints.

### Celery & Redis
*   **Traitement Distribué** : Permet de déléguer les tâches lourdes (Scraping, IA, SAST) à des agents (Workers) indépendants.
*   **Robustesse** : Si un scan de sécurité fait planter un worker, la file d'attente Redis conserve la tâche pour la rejouer.

---

## 📊 Stockage Hybride (Souverain)

*   **PostgreSQL 16** : Métadonnées relationnelles et logs de sécurité (Stockage JSONB).
*   **Qdrant** : Moteur de recherche sémantique vectoriel (IA locale).
*   **SearXNG** : OSINT anonyme et gratuit (pas de clés API payantes).

---

## 🛡️ Sécurité (SAST)

*   **Trivy / Semgrep / Gitleaks** : Orchestrés via Docker pour auditer chaque ressource découverte avant certification.
*   **Clonage éphémère** : `git clone --depth 1` avec suppression immédiate après scan.
