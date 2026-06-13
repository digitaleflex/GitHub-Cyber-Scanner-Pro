# 🤝 Guide de Contribution (GitHub Cyber Scanner)

Bienvenue sur le projet **GitHub Cyber Scanner** ! Ce document définit les standards de développement pour garantir la robustesse de notre architecture distribuée.

## 🚀 Workflow de Développement

1.  **Issue d'abord** : Toute modification doit commencer par une Issue GitHub (utilisez les templates fournis).
2.  **Branche dédiée** : Créez une branche avec un nom explicite : `feature/nom-tache` ou `fix/nom-bug`.
3.  **Pull Request (PR)** : Soumettez une PR vers la branche `main`. Une revue de code est obligatoire.

## 🏗️ Architecture & Standards de Code

*   **Langage** : Python 3.11+. Respectez la norme **PEP 8**.
*   **Asynchronisme** : Utilisez `aiohttp` pour les requêtes réseau de masse et `Celery` pour les tâches de fond.
*   **Sécurité (Mandatoire)** :
    *   Ne jamais coder de clés d'API en dur. Utilisez les variables d'environnement (`.env`).
    *   Toute nouvelle brique de scan doit être isolée dans un conteneur éphémère si possible.
*   **Documentation** : Tout nouveau composant doit être documenté dans le dossier `docs/` et ajouté au schéma de l'architecture.

## 🐳 Docker & Environnement

Le projet utilise exclusivement `compose.yml`. Assurez-vous que votre modification ne casse pas la liaison entre les différents services (Redis, Qdrant, Postgres).

## 📝 Conventions de Commit

Nous utilisons des messages de commit clairs :
*   `feat:` pour une nouvelle fonctionnalité.
*   `fix:` pour une correction.
*   `docs:` pour la documentation.
*   `refactor:` pour une amélioration du code sans changement de comportement.

*Exemple : `feat: ajout du worker d'analyse semgrep`*

## 🛡️ Politique de Sécurité

Si vous découvrez une faille de sécurité critique dans le scanner, merci de ne pas ouvrir d'issue publique. Contactez directement les mainteneurs via une issue privée ou un canal sécurisé.

---
Merci de contribuer à rendre la cyber-veille plus intelligente et souveraine !
