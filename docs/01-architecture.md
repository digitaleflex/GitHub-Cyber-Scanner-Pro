# 01 — Architecture Globale

> Module racine : `src/` · Conteneur : `cyber_github_scanner` · Port : 8000

---

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                    API REST (FastAPI + FastMCP)              │
│                     http://0.0.0.0:8000                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Decision     │  │ Context      │  │ Skills IA    │       │
│  │ Engine       │  │ Engine       │  │              │       │
│  │ score_cve()  │  │ organizations│  │ rerank()     │       │
│  │ get_priority │  │ user_profiles│  │ classify()   │       │
│  │ EPSS + KEV   │  │ assets       │  │ summarize()  │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                  │               │
│  ┌──────┴─────────────────┴──────────────────┴───────┐       │
│  │                PostgreSQL 16 (pgvector)            │       │
│  │  cve_entries · exploits · repositories · epss     │       │
│  │  organizations · asset_inventory · user_profiles  │       │
│  └───────────────────────────────────────────────────┘       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │               Collectors & Background Threads         │    │
│  │  NVD Importer (tous les jours + startup)             │    │
│  │  Exploit-DB Loader (tous les jours à 03:00 UTC)      │    │
│  │  CISA KEV Importer                                    │    │
│  │  GitHub Repos Collector                               │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Services (compose.yml)

| Service | Image | Port | Rôle |
|---------|-------|------|------|
| `cyber_github_scanner` | build local | 8000 | Application FastAPI + collecteurs |
| `cyber_scanner_db` | pgvector/pgvector:pg16 | 5432 | Base principale |
| `cyber_neo4j` | neo4j:5 | 7474, 7687 | Graphe de connaissance |
| `cyber_searxng` | searxng/searxng | — | Moteur de recherche OSINT |

---

## Backend — modules clés

| Module | Fichier | Rôle |
|--------|---------|------|
| Decision Engine | `src/priority_engine.py` | Score, ranking, justification |
| Context Engine | `src/context_engine.py` | Profil, org, assets → contexte utilisateur |
| Skills IA | `src/skills/` | Capacités IA (registry + skills) |
| EPSS | `src/epss.py` | Prédiction d'exploitation FIRST.org |
| Corrélation | `src/correlation.py` | CVE ↔ Exploit-DB ↔ Outils |
| NVD Importer | `src/cve_importer.py` | Backfill sévérité/CVSS (trimestriel) |
| Exploit Loader | `src/exploit_loader.py` | Import Exploit-DB (46k+ exploits) |
| DB Layer | `src/db/` | Schéma, accès PostgreSQL |

---

## Tables principales

| Table | Volume | Usage |
|-------|--------|-------|
| `cve_entries` | 372 703 | CVE + sévérité + CVSS |
| `exploits` | 46 636 | Exploit-DB |
| `repositories` | 18 379 | Repos GitHub (verdict, vitalité) |
| `epss_scores` | — | Prédictions EPSS |
| `organizations` | — | Profils organisation |
| `asset_inventory` | — | Assets technologiques |
| `user_profiles` | — | Profils utilisateur |
| `resource_chunks` | 12 092 | Chunks README (RAG) |
| `discovered_keywords` | 52 842 | Mots-clés dorking |

---

## Threads d'arrière-plan (scanner.py)

| Thread | Fréquence | Action |
|--------|-----------|--------|
| CVE Updater | Démarrage + 24h | `import_cve_all()` → upsert NVD |
| Exploit Updater | 03:00 UTC | `load_exploitdb()` → rafraîchit les exploits |
| Ontology Bootstrap | Démarrage | `import_ontology_to_db()` → termes pentest |

---

## Flux de décision

```
GET /api/priority/cves?profile_id=1&days=90

1. Context Engine → contexte utilisateur (profile, org, assets)
2. _candidate_rows() → CVE CRITICAL+HIGH + KEV dans la fenêtre
3. Skills.rerank() → batch sémantique (contexte vs descriptions CVE)
4. EPSS.batch_get_epss() → prédiction d'exploitation imminente
5. score_cve() × N → score, raisons, niveau, risque, confiance
6. Tri décroissant → top N
```
