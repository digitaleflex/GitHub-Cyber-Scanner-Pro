# #8 — Incohérence de version

**Priorité** : 🟢 Faible
**Statut** : ✅ Résolu
**Fichiers** : `frontend/src/routes/__root.tsx`, `frontend/src/components/AdminSidebar.tsx`

## Problème (initial)
Le footer affichait "CyberScan Pro v3.1" mais l'AdminSidebar affichait "CyberScan Pro v2.2".

## Solution appliquée
Toutes les mentions de version affichent désormais **v3.1** :
- `__root.tsx:105` → "CyberScan Pro v3.1" (footer)
- `AdminSidebar.tsx:19` → "CyberScan Pro v3.1"
- `admin.tsx:97` → "CyberScan Pro v3.1"

## Vérification
✅ Version uniformisée à v3.1 partout. Issue fermée.
