# 05 — Algorithms & Mathematical Foundations

---

## Decision Score Formula

```
S(cve) = S_cvss + S_exploit + S_kev + S_epss + S_context + S_recency

Où :
  S_cvss    = min(cvss_score × 4, 40)            si cvss_score ≠ NULL
            = SEVERITY_BASE[severity] × 4        sinon (fallback textuel)

  S_exploit = min(|exploits| × 6, 25)

  S_kev     = 20 si CVE ∈ CISA KEV, 0 sinon

  S_epss    = min(epss × 25, 25)

  S_context = min(rerank_score × 10, 10)         si reranker dispo
            = min(|hits| × 2.5, 10)              sinon (fallback lexical)

  S_recency = 5  si age ≤ 30 jours
            = 3  si age ≤ 90 jours
            = 0  sinon

Score final = min(S, 100)
```

---

## Niveau de décision

```
CRITIQUE  : score ≥ 75
ÉLEVÉ     : 50 ≤ score < 75
MOYEN     : 25 ≤ score < 50
BAS       : score < 25
```

---

## Confiance

Basée sur le nombre de signaux non nuls ayant contribué au score :

```
|signaux| ≥ 3  → Élevée
|signaux| = 2  → Moyenne
|signaux| ≤ 1  → Basse
```

---

## Reranker sémantique

Le reranker (`mixedbread-ai/mxbai-rerank-large-v1`) est un **cross-encoder** :
il prend un couple (query, document) et produit un score de pertinence 0-1.

```
rerank(query = contexte_utilisateur, documents = [desc_cve_1, ..., desc_cve_N])
→ [{index: i, score: 0.0-1.0}, ...]
```

Le contexte utilisateur est une chaîne descriptive :
```
"Role: devsecops. Organisation: MaBoite, Secteur: finance.
 Technologies: PostgreSQL, Docker, Kubernetes, AWS. Compliance: PCI DSS, ISO 27001."
```

Avantage par rapport au matching lexical : capture la similarité sémantique
(« base de données » ≈ PostgreSQL, « conteneurisation » ≈ Docker)
même sans correspondance exacte de tokens.

---

## EPSS (Exploit Prediction Scoring System)

Probabilité qu'une CVE soit exploitée dans les 30 prochains jours.
Score continu [0, 1] avec un percentile dans la distribution EPSS globale.

```
epss = P(exploitation dans 30 jours)

Transformation linéaire dans notre formule :
S_epss = min(epss × 25, 25)
→ epss = 0.5 → 12.5 pts
→ epss = 0.9 → 22.5 pts
```

L'EPSS est indépendant du CVSS : une CVE CVSS 4.0 peut avoir un EPSS 0.8
(peu sévère mais très exploitée), et inversement (CVSS 9.8, EPSS 0.01).

---

## Réduction du bruit

### Filtrage des candidats

Seules les CVE répondant à **au moins un** de ces critères sont candidates au scoring :

1. `severity ∈ {CRITICAL, HIGH}` ET `published` dans la fenêtre (défaut : 90 jours)
2. CISA KEV (peu importe l'âge)

Ce pré-filtre élimine ~95 % des 372k CVE avant le scoring.

### Limite de candidats

La requête SQL plafonne à 3 000 lignes. En pratique, la fenêtre de 90 jours
+ le filtre CRITICAL/HIGH donnent ~100-500 candidats.

---

## Risk if Ignored — heuristique textuelle

```
si KEV     → "Exploitation active documentée → compromission probable;
              patcher avant l'échéance CISA {dueDate}."

si EXPLOIT → "Exploit public disponible → risque d'utilisation dans
              des campagnes; patcher rapidement."

si CVSS≥9  → "Score critique sans exploit public connu —
              surveiller de près et prévoir un correctif."

si CRITIQUE → "Vulnérabilité à haute priorité; à intégrer dans le
  ou ÉLEVÉ    cycle de patching."

sinon      → "Priorité à surveiller."
```

---

## Pagination NVD — fenêtres trimestrielles

L'API NVD 2.0 rejette les plages de dates > 120 jours (HTTP 404) et la pagination
profonde par `startIndex` sur de grands ensembles (>100 000 résultats) souffre de
**drift** (désynchronisation des pages). Solution :

```
Pour chaque année de 2026 à 2002 :
  Pour chaque trimestre (Q1, Q2, Q3, Q4) :
    GET /cves/2.0?pubStartDate=...&pubEndDate=...&resultsPerPage=2000&startIndex=0
    → paginer dans la fenêtre (≤ 50 pages par trimestre, pas de drift)
```

L'ordre est **décroissant** (2026 → 2002) pour remplir les CVE récentes en premier,
garantissant que le Decision Engine ait des données fraîches même si le conteneur
redémarre avant la fin du crawl complet (~30 min).
