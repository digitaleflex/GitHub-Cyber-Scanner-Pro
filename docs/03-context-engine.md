# 03 — Context Engine

> Module : `src/context_engine.py` · API : `GET /api/profile`, `POST /api/profile/onboard`

---

## Fonction

Construire le contexte personnalisé de chaque utilisateur : qui il est, ce qu'il protège,
quelles technologies il utilise. Ce contexte alimente le reranker sémantique du Decision
Engine et remplace le `build_stack_keywords()` global (18k repos confondus).

---

## Tables

### `organizations`

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | SERIAL PK | Identifiant |
| `name` | VARCHAR(200) | Nom de l'organisation |
| `sector` | VARCHAR(100) | Secteur (finance, santé, défense…) |
| `compliance_frameworks` | TEXT | Frameworks applicables (PCI DSS, ISO 27001…) |

### `asset_inventory`

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | SERIAL PK | Identifiant |
| `org_id` | INTEGER FK | Référence organisation |
| `asset_type` | VARCHAR(30) | product, vendor, language, framework, os |
| `name` | VARCHAR(200) | Nom de l'asset (ex: PostgreSQL, Docker, AWS) |
| `vendor` | VARCHAR(200) | Fournisseur (optionnel) |
| `version` | VARCHAR(50) | Version (optionnel, pour filtres précis) |
| `exposed` | BOOLEAN | Asset exposé à Internet |
| `criticality` | SMALLINT 1-5 | Criticité métier (5 = critique) |

### `user_profiles`

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | SERIAL PK | Identifiant utilisateur |
| `org_id` | INTEGER FK | Organisation (NULL = solo) |
| `role` | VARCHAR(50) | Rôle (devsecops, rssi, pentester, soc…) |
| `display_name` | VARCHAR(200) | Nom affiché |
| `preferences` | JSONB | Préférences (objectifs, filtres, thème…) |
| `onboarding_completed` | BOOLEAN | Onboarding terminé |
| `last_active` | TIMESTAMP | Dernière activité |

---

## Flux d'onboarding

```
1. POST /api/profile           → crée un profil (role = "non_defini")
2. POST /api/profile/onboard   → configure role, org, assets
   ?profile_id=1
   &role=devsecops
   &org_name=MaBoite
   &sector=finance
   &compliance=PCI DSS,ISO 27001
   &assets=[{"type":"product","name":"PostgreSQL","vendor":"PostgreSQL","version":"15"},...]
3. GET /api/priority/cves?profile_id=1 → décisions personnalisées
```

---

## Construction du contexte

La fonction `build_user_context(profile_id)` produit un `(keyword_set, context_string)` :

```python
context_string = (
    "Role: devsecops. "
    "Organisation: MaBoite, Secteur: finance. "
    "Compliance: pci dss iso 27001. "
    "Technologies: PostgreSQL PostgreSQL v15, Docker, Kubernetes, AWS, ... "
    "Objectifs: reduire les risques, preparer les audits. "
    "Priorites recommandees: CVE avec exploit public, CISA KEV, CVSS eleve, EPSS eleve"
)
```

Ce texte est utilisé comme **query** par le reranker sémantique (`mxbai-rerank`).
Le `keyword_set` sert de fallback lexical si le reranker est indisponible.

---

## Fallback global

Si aucun `profile_id` n'est fourni, le Decision Engine utilise `build_stack_keywords()`
(contexte global dérivé des 18 379 repos : langages, catégories, noms d'outils filtrés
par rareté).

---

## Fonctions

| Fonction | Rôle |
|----------|------|
| `ensure_profile(user_id)` | Crée ou récupère un profil |
| `init_profile(profile_id, role, assets, org_name, ...)` | Onboarding complet |
| `build_user_context(profile_id)` | (keywords, texte) pour le reranker |
| `get_user_role(profile_id)` | Rôle (string) |

---

## Rôles supportés

| Rôle | Vue typique |
|------|-------------|
| `rssi` | Risque global, KPI, conformité |
| `pentester` | Nouveaux PoC, exploits, outils |
| `devsecops` | Vulnérabilités de la stack, patchs |
| `developpeur` | Dépendances, versions, mises à jour |
| `soc` | Campagnes actives, IOC, playbooks |
| `cloud_engineer` | AWS, Kubernetes, Docker |
| `etudiant` | CVE expliquées, quiz, labs |
| `non_defini` | Contexte global (fallback) |
