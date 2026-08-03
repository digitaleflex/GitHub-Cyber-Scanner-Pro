# 04 — Knowledge Graph & Data Model

> Base : PostgreSQL 16 + pgvector · Graphe : Neo4j 5 · Cache : data/exploitdb.csv, data/cisa_kev.csv

---

## Sources de données

### Sources autoritatives (fetch au démarrage + périodique)

| Source | Format | Fréquence | Volume | Stockage |
|--------|--------|-----------|--------|----------|
| NVD API 2.0 | JSON paginé | 24h + startup | 372k CVE | `cve_entries` |
| Exploit-DB | CSV (GitLab) | 03:00 UTC | 47k exploits | `exploits` + cache CSV |
| CISA KEV | CSV | OSINT enrichment | 1 656 CVE | Marqueur dans `cve_entries.weaknesses` + CSV |
| GitHub API | REST | Collecte continue | 18k repos | `repositories` |
| FIRST.org EPSS | API REST | À la demande (cache DB) | variable | `epss_scores` |

### Sources IA (à la demande)

| Source | Modèle | Usage |
|--------|--------|-------|
| HuggingFace Router | mxbai-rerank, mDeBERTa, BART… | Reranking, classification, résumé, NER |
| Groq / Gemini | LLaMA / Gemini | Analyse CVE (explication IA) |

---

## Schéma relationnel principal

```
cve_entries ──┐
  cve_id       │  1:N
  severity     ├── epss_scores (cve_id)
  cvss_score   │
  description  │
  weaknesses   │  (contient "CISA_KEV" pour les KEV)

exploits ──────┐
  exploit_id   │  Lié aux CVE via le cache CSV (src/correlation.py)
  description  │  Regex CVE-\d{4}-\d{4,7} sur le champ "codes"
  platform
  type

repositories ──┐
  full_name     │  1:N
  language      ├── resource_chunks (repo_id, chunk_type='readme')
  stars         │
  security_verdict (Sain/Suspect/Malveillant)
  vitality_score (0-100)
  ai_category

organizations ─┐
  id            │  1:N
  name          ├── asset_inventory (org_id)
  sector        │
  compliance    │  1:N
                └── user_profiles (org_id)
```

---

## Graphe Neo4j

Neo4j 5 est configuré sans authentification (`NEO4J_AUTH=none`), exposé sur `localhost:7687` (Bolt) et `localhost:7474` (HTTP).

### Nœuds

- `(:Repo)` — repositories GitHub
- `(:CVE)` — vulnérabilités

### Relations

- `(:Repo)-[:MENTIONS]->(:CVE)` — le repo mentionne la CVE dans sa description

### Population

Le seeder (`src/scanner.py`) peuple le graphe au démarrage :
```
Graph Neo4j seeder: 18376 repos, 500 CVEs, 0 collaborations
```
