# #6 — Recherche IA non activée

**Priorité** : 🟡 Moyen  
**Fichier** : `frontend/src/routes/search.tsx`

## Problème
La page `/search` utilise l'API de recherche basique. Les endpoints de recherche IA existent mais ne sont pas utilisés :
- `GET /api/search/ai` — Recherche hybride avec re-ranking Groq
- `GET /api/search/semantic` — Recherche sémantique par cosine similarity

## Solution
Ajouter un toggle "Recherche IA" qui bascule entre la recherche classique et `/api/search/ai`. Ajouter aussi un onglet "Sémantique".
