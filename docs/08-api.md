# 08 — API Reference

> Base : `http://localhost:8000`

---

## Endpoints — Decision Engine

### `GET /api/priority/cves`

Décisions priorisées du jour. Chaque décision est justifiée.

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `days` | int | 90 | Fenêtre de publication (jours) |
| `limit` | int | 20 | Nombre de décisions retournées |
| `profile_id` | int | null | Profil utilisateur (contexte personnalisé) |

**Réponse :**
```json
{
  "count": 5,
  "summary": {
    "window_days": 90,
    "critiques": 4250,
    "kev_actives": 1566,
    "role": "non_defini"
  },
  "decisions": [
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
      "factors": {"cvss": 39.2, "exploit": 6, "epss": 18.5},
      "reasons": [
        "Score CVSS 9.8 (severite maximale)",
        "1 exploit(s) public(s) disponible(s)",
        "Probabilite d'exploitation imminente: 74% (EPSS)"
      ],
      "risk_if_ignored": "Exploit public disponible → risque d'utilisation...",
      "confidence": "Elevee",
      "sources": ["Exploit-DB", "EPSS", "NVD"]
    }
  ]
}
```

### `GET /api/threats/top`

Ancien endpoint (v1). Utilise `correlation.get_top_threats`.

| Paramètre | Type | Défaut |
|-----------|------|--------|
| `limit` | int | 20 |

---

## Endpoints — Contexte

### `GET /api/profile`

Profil utilisateur.

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `profile_id` | int | 0 | 0 = crée un nouveau profil |

**Réponse :** `{"id": 1, "role": "devsecops", "org_id": 1, "onboarding_completed": true, ...}`

### `POST /api/profile/onboard`

Onboarding : configure le rôle, l'organisation et les assets.

| Paramètre | Type | Description |
|-----------|------|-------------|
| `profile_id` | int | ID du profil à configurer |
| `role` | str | Rôle (devsecops, rssi, pentester, soc, developpeur, cloud_engineer, etudiant) |
| `org_name` | str | Nom de l'organisation |
| `sector` | str | Secteur (finance, santé, défense, éducation…) |
| `compliance` | str | Frameworks (ex: "PCI DSS, ISO 27001") |
| `assets` | JSON | Liste d'assets `[{"type":"product","name":"...","vendor":"...","version":"..."}]` |

**Exemple :**
```
POST /api/profile/onboard?profile_id=1&role=devsecops&org_name=MaBoite&sector=finance
  &compliance=PCI DSS,ISO 27001
  &assets=[{"type":"product","name":"PostgreSQL","vendor":"PostgreSQL","version":"15"},
           {"type":"product","name":"Docker","vendor":"Docker Inc"}]
```

---

## Endpoints — CVE & Exploits

### `GET /api/cves`

Recherche de CVE.

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `q` | str | "" | Recherche textuelle (ILIKE) |
| `severity` | str | "" | Filtre par sévérité |
| `page` | int | 1 | Page |
| `per_page` | int | 20 | CVEs par page |

### `GET /api/cve/{cve_id}/analysis`

Analyse IA d'une CVE (Groq/Gemini).

### `GET /api/cve-status`

État de l'import NVD en cours. Retourne `{"running": true, "imported": 54321, "year": "2024-Q3@0", "mode": "import"}`

### `POST /api/cves/backfill-severity`

Lance un backfill sévérité NVD (admin).

### `POST /api/import-cve`

Import complet NVD en arrière-plan (admin).

### `GET /api/exploits/stats`

Statistiques Exploit-DB.

---

## Endpoints — Repos

### `GET /api/tools/featured`

Outils incontournables (triés par stars).

### `GET /api/tools/readytouse`

Outils prêts à l'emploi.

### `GET /api/tools/by-category`

Outils par catégorie.

| Paramètre | Valeurs |
|-----------|---------|
| `category` | all, red-team, blue-team, exploit, malware, osint, network |

### `GET /api/tools/best`

Classement qualité (vitality_score).

---

## Endpoints — IA

### `GET /api/hf/status`

État des services HuggingFace (modèles disponibles, clé configurée).

### `GET /api/hf/embed?text=...`

Embedding via HF (renvoie 10 premières dimensions).

### `GET /api/hf/classify?text=...`

Zero-shot classification (catégories sécurité).

### `GET /api/hf/qa?question=...&context=...`

Question Answering sur un contexte.

### `GET /api/hf/vuln-type?text=...`

Détection de type de vulnérabilité (SecBERT).

### `POST /api/hf/guard?limit=20`

Content safety scan (admin).

---

## Endpoints — OSINT

### `POST /api/osint/pro/email?email=...`

Email OSINT (breaches + pastebin).

### `POST /api/osint/pro/phone?phone=...`

Analyse de numéro.

### `POST /api/osint/pro/domain?domain=...`

WHOIS/RDAP.

### `POST /api/osint/pro/report`

Rapport OSINT complet (email, phone, domain, free_text).

---

## Authentification

Les endpoints admin (backfill, guard, import) nécessitent l'en-tête
HTTP Basic Auth avec les variables `ADMIN_USER` / `ADMIN_PASSWORD`.

Les endpoints publics (priority, cves, tools, profile) sont ouverts.
