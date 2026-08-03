# 02 — Decision Engine

> Module : `src/priority_engine.py` · API : `GET /api/priority/cves`

---

## Fonction

Transformer N CVE candidates en top K décisions priorisées, chacune justifiée par un score,
des raisons, un niveau de confiance, un risque si ignorée, et les sources utilisées.

---

## Formule de scoring

```
SCORE = CVSS(0-40) + EXPLOIT(0-25) + KEV(0-20) + EPSS(0-25) + CONTEXTE(0-10) + RECENCE(0-5)
        → capé à 100

NIVEAU  : ≥75 CRITIQUE | ≥50 ÉLEVÉ | ≥25 MOYEN | <25 BAS
```

---

## Signaux détaillés

### CVSS — 0 à 40 points

| Source | Champ | Calcul | Exemple |
|--------|-------|--------|---------|
| NVD 2.0 | `cvss_score` | `min(score × 4, 40)` | 9.8 → 39.2 pts |
| NVD 2.0 | `severity` (fallback si cvss NULL) | `SEVERITY_BASE × 4` | CRITICAL → 40 pts |

Le fallback par `severity` textuel existe car les CVE V2 n'ont pas toujours
leur `cvss_score` rempli immédiatement (le backfill NVD progresse encore).

### Exploit public — 0 à 25 points

| Source | Calcul | Exemple |
|--------|--------|---------|
| Exploit-DB (cache CSV) | `min(N_exploits × 6, 25)` | 3 exploits → 18 pts |

Le cache (`src/correlation.py : _exploitdb_cache`) est chargé paresseusement
au premier appel et mappe 25 045 CVE vers leurs exploits.

### CISA KEV — 0 ou 20 points

| Condition | Points |
|-----------|--------|
| CVE dans le catalogue CISA KEV (exploitation active documentée) | +20 |
| + ransomware connu | mention ajoutée dans `reasons` |

Détection : marqueur `CISA_KEV` dans la colonne `weaknesses` (écrit par `osint_enricher.import_cisa_kev`).
Le CSV enrichi (`data/cisa_kev.csv`, 1 656 entrées) fournit `product`, `vendor`, `dueDate`, `requiredAction`.

### EPSS — 0 à 25 points

| Source | Calcul | Exemple |
|--------|--------|---------|
| FIRST.org EPSS | `min(epss × 25, 25)` | epss=0.45 → 11.25 pts |

Cache en DB (`epss_scores`). Batch-fetch au scoring, fallback silencieux si API indisponible.
EPSS prédit la probabilité d'exploitation dans les 30 jours (0-1). Complément au CVSS :
CVSS dit « c'est grave », EPSS dit « ça va être exploité ».

### Contexte — 0 à 10 points

| Méthode | Calcul |
|---------|--------|
| Reranker HF (mxbai-rerank) | `min(score × 10, 10)` |
| Fallback : token matching | `min(N_hits × 2.5, 10)` |

Si un `profile_id` est fourni, le contexte est le profil personnel (organisation, assets, rôle).
Sinon, contexte global dérivé des 18k repos.

Le reranker compare sémantiquement le contexte utilisateur avec chaque description CVE.
Le fallback lexical (intersection de tokens) n'est utilisé que si HF est indisponible.

### Récence — 0 à 5 points

| Âge de la CVE | Points |
|---------------|--------|
| ≤ 30 jours | +5 |
| ≤ 90 jours | +3 |
| > 90 jours | 0 |

---

## Sortie : structure d'une décision

```json
{
  "cve_id": "CVE-2026-0770",
  "score": 75,
  "level": "CRITIQUE",
  "severity": "CRITICAL",
  "cvss_score": 9.8,
  "published": "2026-07-15",
  "description": "...",
  "is_kev": false,
  "exploits_count": 1,
  "factors": {"cvss": 39.2, "exploit": 6, "epss": 18.5, "stack": 4.3, "recency": 5},
  "reasons": [
    "Score CVSS 9.8 (severite maximale)",
    "1 exploit(s) public(s) disponible(s)",
    "Probabilite d'exploitation imminente: 74% (EPSS)",
    "Pertinent pour votre contexte (score semantique: 0.43)",
    "Publiee il y a moins de 30 jours"
  ],
  "risk_if_ignored": "Exploit public disponible → risque d'utilisation dans des campagnes...",
  "confidence": "Elevee",
  "sources": ["NVD", "Exploit-DB", "EPSS", "reranker"]
}
```

---

## Fonctions

| Fonction | Rôle |
|----------|------|
| `score_cve(cve, stack_kws, exploits, kev_row, rerank_score, epss)` | Score individuel |
| `get_priority_decisions(days, limit, profile_id)` | Pipeline complet → top N |
| `get_decision_summary(days)` | Compteurs (critiques, KEV actives) |
| `build_stack_keywords()` | Contexte global depuis les repos (fallback) |
| `_candidate_rows(days)` | Requête SQL : CVE CRITICAL+HIGH + KEV |
| `_load_kev()` | Cache du CSV CISA KEV |

---

## Ajouter un nouveau signal

1. Ajouter la source de données (table, API, cache)
2. Ajouter un bloc `if signal:` dans `score_cve()` avec `score += pts`, `factors["signal"]`, `reasons.append(...)`, `sources.append(...)`
3. Mettre à jour `get_priority_decisions()` pour précharger le signal en batch
4. Mettre à jour la doc (ce fichier)
