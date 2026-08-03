# #1 — Bouton Scan non fonctionnel

**Priorité** : 🔴 Critique  
**Fichiers** : `frontend/src/routes/__root.tsx` (lignes 20-36), `src/api_routes.py` (ligne 735)

## Problème
Le bouton "Scanner" dans la navbar appelle `POST /api/scan` mais ne passe **aucun header d'authentification admin**. L'endpoint backend requiert `Depends(src.auth.verify_admin)`, donc le scan échoue systématiquement en silence pour les visiteurs.

## Solution
- Soit passer les headers Basic Auth dans l'appel API
- Soit ne montrer le bouton qu'aux admins authentifiés
- Idéal : faire les deux
