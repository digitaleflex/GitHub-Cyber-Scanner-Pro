# #5 — Page OSINT incomplète

**Priorité** : 🔴 Critique
**Statut** : ✅ Résolu
**Fichier** : `frontend/src/routes/osint.tsx`

## Problème (initial)
La page `/osint` n'exposait que `/api/osint/investigate`. **11 endpoints OSINT** du backend étaient invisibles.

## Résolution
La page `/osint` expose désormais les 11 endpoints via 7 onglets :
- `PersonTab` → `POST /api/osint/investigate`
- `V2Tab` → `POST /api/osint/investigate-v2`
- **`PlanTab` (nouveau)** → `POST /api/osint/plan` — l'IA analyse la cible, recommande les outils + méthodologie, et affiche : analyse, outils recommandés (avec statut prêt/requis), ordre d'exécution, résultats attendus, limitations et approche alternative
- `PipelineTab` → `POST /api/osint/pipeline`
- `ProTab` → `email`, `phone`, `domain`, `report`
- `DorksTab` → `POST /api/osint/dorks`
- `ToolsTab` → `GET /api/osint/tools` + `POST /api/osint/run-all`

## Vérification
✅ Les 11 endpoints sont exposés. `npm run build` + `npm run lint` passent (0 erreur). Issue fermée.
