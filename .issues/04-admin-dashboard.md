# #4 — Dashboard Admin inexistant

**Priorité** : 🔴 Critique
**Statut** : ✅ Résolu
**Fichier** : `frontend/src/routes/admin.tsx`

## Problème (initial)
18 endpoints admin (scan, import CVE, bulk-seed, harvest, AI verdict, etc.) n'avaient **aucune interface**. Le panel admin ne contenait que 4 liens basiques sans contrôles opérationnels.

## Solution appliquée
Une page `/admin` complète a été créée (`routes/admin.tsx`) avec :
- **Statuts en direct** : scanner actif/idle, bulk seed, harvest, HF models (`StatusDot`)
- **Boutons d'action** : Scan manuel (`/api/scan`), Bulk Seed, Harvest, HF Guard scan (`/api/hf/guard`), import CVE
- **Indicateurs** : statut des modèles HuggingFace (`hf-status`)
- **Intégration** : `CyberRadar` + `ActivityFeed` (importés lignes 5-6), boutons via `ActionBtn` avec `getAuthHeaders()`
- **Contrôles protégés** : tous les appels POST passent `getAuthHeaders()`

## Vérification
✅ Le cockpit admin opérationnel existe, est authentifié et expose les contrôles clés. Issue fermée.
