# #6 — Recherche IA non activée

**Priorité** : 🟡 Moyen
**Statut** : ✅ Résolu
**Fichier** : `frontend/src/routes/search.tsx`

## Problème (initial)
La page `/search` n'utilisait que la recherche basique, sans utiliser les endpoints IA du backend :
- `GET /api/search/ai` — recherche hybride avec re-ranking Groq
- `GET /api/search/semantic` — recherche sémantique par cosine similarity

## Solution appliquée
La page `/search` a désormais **3 modes commutables** (`search.tsx:46`) :
- **Recherche classique** (endpoint par défaut)
- **IA** → `/api/search/ai`
- **Sémantique** → `/api/search/semantic`

Les onglets IA/sémantique sont clairement labelisés ("Recherche IA avec re-ranking Groq (Llama 3.3)" / "Recherche sémantique par similarité cosine").

## Vérification
✅ Toggle 3 modes présent et fonctionnel. Issue fermée.
