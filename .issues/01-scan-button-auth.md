# #1 — Bouton Scan non fonctionnel

**Priorité** : 🔴 Critique
**Statut** : ✅ Résolu
**Fichiers** : `frontend/src/routes/__root.tsx`, `frontend/src/routes/login.tsx`

## Problème (initial)
Le bouton "Scanner" de la navbar appelait `POST /api/scan` **sans header d'authentification admin**. L'endpoint backend requiert `Depends(src.auth.verify_admin)`, donc le scan échouait systématiquement (en silence) pour les visiteurs.

## Solution appliquée
- **Auth passée** : l'appel utilise désormais `getAuthHeaders()` (`__root.tsx:20-21`), qui injecte les headers Basic Auth de la session admin.
- **Bouton masqué pour les non-admins** : le bouton n'est rendu que si `isAdminAuthenticated()` renvoie `true` (`__root.tsx:26`).
- **Garde-fou supplémentaire** : `handleScan` ne fait rien si `!isAdmin` (`__root.tsx:18`).

## Vérification
✅ Double protection : l'en-tête Basic Auth est envoyé **et** le bouton est invisible hors session admin. Issue fermée.
