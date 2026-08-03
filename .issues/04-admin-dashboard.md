# #4 — Dashboard Admin inexistant

**Priorité** : 🔴 Critique  
**Fichiers** : Nouvelle route `frontend/src/routes/admin.tsx`

## Problème
18 endpoints admin (scan, import CVE, bulk-seed, harvest, AI verdict, etc.) n'ont **aucune interface**. Le panel admin actuel ne contient que 4 liens basiques (CVEs, Mots-clés, Graph, Rapports) sans contrôles opérationnels.

## Solution
Créer une page `/admin` avec :
- **Statuts en direct** : scanner, CVE import, harvest, bulk-seed
- **Boutons d'action** : Scan manuel, Import CVE, Bulk Seed, Harvest, AI Verdict, AI Keywords, Dorking Scan, Slicer Scan
- **Indicateurs** : nb tokens, data points, embeddings status
- **Intégration** : StatsCards + ActivityFeed + CyberRadar
