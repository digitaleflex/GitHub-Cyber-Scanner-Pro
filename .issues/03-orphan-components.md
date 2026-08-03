# #3 — Composants orphelins jamais utilisés

**Priorité** : 🟡 Moyen  
**Fichiers** : `frontend/src/components/`

## Problème
9 composants React existent dans le codebase mais ne sont **jamais montés** dans aucun route. Code mort.

- `ReposTable.tsx` — Table complète avec CSV, filtres, pagination
- `BooksTable.tsx` — Table des livres/ressources cyber
- `FicheFlashModal.tsx` — Modal vue rapide d'un repo
- `StatsCards.tsx` — 8 cartes de stats dashboard
- `LangDistribution.tsx` — Distribution des langages
- `CyberRadar.tsx` — Radar chart 6 dimensions
- `TopRepos.tsx` — Top 5 repos par stars
- `CveTable.tsx` — Table CVE avec badges sévérité
- `ActivityFeed.tsx` — Fil d'activité (scan, rapports)

## Solution
Les intégrer dans les pages appropriées :
- `StatsCards` → page d'accueil ou admin dashboard
- `CyberRadar` → page d'accueil (section posture cyber)
- `ActivityFeed` → admin dashboard
- `ReposTable` → alternative à la vue grid pour les outils
- `CveTable` → remplacer la liste inline dans cves.tsx
- `BooksTable` → nouvelle route `/books`
- `TopRepos`, `LangDistribution`, `FicheFlashModal` → bonus dans les pages existantes
