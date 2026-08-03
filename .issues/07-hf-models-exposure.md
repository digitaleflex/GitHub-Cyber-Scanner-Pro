# #7 — Modèles HuggingFace sous-exposés

**Priorité** : 🟡 Moyen  
**Fichier** : `frontend/src/routes/index.tsx` (section AiLabSection)

## Problème
L'AI Lab sur la home page n'expose que la classification zero-shot. Les autres endpoints HF sont absents :
- `GET /api/hf/qa` — Question Answering
- `GET /api/hf/vuln-type` — Détection type vulnérabilité (SecBERT)
- `GET /api/hf/status` — Statut des 22 modèles
- `GET /api/hf/embed` — Génération d'embedding
- `POST /api/hf/guard` — Content safety scan

## Solution
Transformer l'AI Lab en section multi-onglets avec QA, vuln-type, embed, status.
