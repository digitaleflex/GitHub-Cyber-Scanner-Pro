# #7 — Modèles HuggingFace sous-exposés

**Priorité** : 🟡 Moyen
**Statut** : ✅ Résolu (endpoints exposés, répartis sur 3 pages)
**Fichiers** : `frontend/src/routes/index.tsx`, `frontend/src/routes/labs.tsx`, `frontend/src/routes/admin.tsx`

## Problème (initial)
L'AI Lab de la home page n'exposait que la classification zero-shot. Les autres endpoints HF étaient absents :
- `GET /api/hf/qa` — Question Answering
- `GET /api/hf/vuln-type` — Détection type vulnérabilité (SecBERT)
- `GET /api/hf/status` — Statut des 22 modèles
- `GET /api/hf/embed` — Génération d'embedding
- `POST /api/hf/guard` — Content safety scan

## Vérification du statut

**✅ Tous les endpoints sont maintenant exposés** (répartis sur 3 pages au lieu d'une seule) :

| Endpoint | Page | Localisation |
|---|---|---|
| `/api/hf/classify` | Home — AI Lab, onglet Classify | `index.tsx:371` |
| `/api/hf/qa` | Home — AI Lab, onglet QA | `index.tsx:372` |
| `/api/hf/vuln-type` | Home — AI Lab, onglet Vuln | `index.tsx:373` |
| `/api/hf/status` | `/labs` + `/admin` | `labs.tsx:44`, `admin.tsx:80` |
| `/api/hf/embed` | `/labs` | `labs.tsx:204` |
| `/api/hf/guard` | `/admin` (HF Guard scan) | `admin.tsx:166` |

## Note
La solution diffère de la proposition initiale (un seul AI Lab multi-onglets sur la home) : l'AI Lab home couvre classify/qa/vuln, et `/labs` + `/admin` couvrent status/embed/guard. Fonctionnellement, tout est exposé. Issue fermée.
