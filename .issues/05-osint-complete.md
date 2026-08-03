# #5 — Page OSINT incomplète

**Priorité** : 🔴 Critique  
**Fichier** : `frontend/src/routes/osint.tsx`

## Problème
La page `/osint` n'expose que `/api/osint/investigate` (enquête basique).
**11 endpoints OSINT supplémentaires** sont disponibles dans le backend mais totalement invisibles.

## Endpoints à exposer
- `POST /api/osint/pro/email` — Email breaches + pastebin
- `POST /api/osint/pro/phone` — Phone analysis
- `POST /api/osint/pro/domain` — Domain WHOIS/RDAP
- `POST /api/osint/pro/report` — Rapport pro complet
- `POST /api/osint/investigate-v2` — Multi-candidats + scoring
- `POST /api/osint/pipeline` — 12 modèles IA chaînés
- `POST /api/osint/plan` — IA recommande les outils
- `POST /api/osint/run-all` — Sherlock, Maigret, Holehe
- `POST /api/osint/dorks` — Multi-engine dorking
- `GET /api/osint/tools` — État des outils
