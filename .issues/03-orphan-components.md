# #3 — Composants orphelins jamais utilisés

**Priorité** : 🟡 Moyen
**Statut** : ✅ Résolu
**Fichier** : `frontend/src/components/`

## Problème (initial)
9 composants React existaient mais n'étaient **jamais montés** dans aucune route (code mort).

## Résolution

**✅ Intégrés (4)** :
- `StatsCards.tsx` → page d'accueil `routes/index.tsx` (remplace le KPI Dashboard statique)
- `TopRepos.tsx` → page d'accueil `routes/index.tsx` (section "Top 5")
- `LangDistribution.tsx` → page d'accueil `routes/index.tsx` (graphique des langages)
- `BooksTable.tsx` → nouvelle route `/books` (`routes/books.tsx` + lien nav "Ressources")

**✅ Supprimés (3)** — redondants avec des pages déjà existantes :
- `ReposTable.tsx` → supprimé (`/tools` fournit déjà DataTable + CSV + tri + pagination)
- `CveTable.tsx` → supprimé (`/cves` fournit déjà DataTable avec liens de détail + tri)
- `KeywordsTable.tsx` → supprimé (ses boutons uniques "+ Sources externes" / "+ MITRE/CAPEC" ont été portés dans `routes/keywords.tsx`)

**✅ Déjà intégrés avant (2)** :
- `CyberRadar.tsx` → `routes/admin.tsx`
- `ActivityFeed.tsx` → `routes/admin.tsx`

## Vérification
✅ Tous les composants de `frontend/src/components/` sont désormais montés dans au moins une route. Aucun code mort. `npm run build` + `npm run lint` passent (0 erreur). Issue fermée.
