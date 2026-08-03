# 07 — Research Roadmap (R&D)

> Axes de recherche pour améliorer le Decision Engine

---

## Axe 1 — Cyber Impact Score (CIS)

### Objectif

Remplacer le score additif actuel par un score pondéré appris ou calibré, combinant :

- CVSS (sévérité intrinsèque)
- EPSS (probabilité d'exploitation)
- Exposition (asset exposé à Internet)
- Criticité métier (asset critique → score × multiplicateur)
- Dépendances (asset utilisé par N autres assets)
- Tendance (augmentation des mentions dans la dernière semaine)

### Approche

- Régression logistique calibrée sur données historiques KEV + EPSS
- Learning to Rank (LambdaMART) pour ordonner les décisions par impact réel
- A/B testing : score additif vs score appris → mesurer le taux d'action

---

## Axe 2 — Context Relevance Algorithm (CRA)

### Objectif

Améliorer le matching contexte → CVE au-delà du reranker sémantique générique :

- Embedding du profil utilisateur (technos, secteur, compliance, historique)
- Embedding de la CVE (description, CWE, produits affectés)
- Score cosinus + reranker cross-encoder → pertinence fine

### Approche

- Fine-tuner un modèle de similarité sur des paires (CVE, profil) annotées
- Utiliser le Knowledge Graph Neo4j pour propager la pertinence (CVE → produit → asset)

---

## Axe 3 — Decision Confidence Algorithm (DCA)

### Objectif

Remplacer `|signaux| ≥ 3 → Élevée` par une calibration probabiliste :

- Pour chaque signal, estimer sa fiabilité historique (taux de faux positifs)
- Combiner via une régression logistique calibrée (Platt scaling)
- Sortie : probabilité que la décision soit « correcte » (l'utilisateur agit)

---

## Axe 4 — Noise Reduction Algorithm (NRA)

### Objectif

Passer de « quelques centaines de CVE candidates » à « exactement N décisions
que l'utilisateur va réellement traiter ».

### Approche

- Apprendre un seuil de score minimum par rôle (un RSSI ignore ce qu'un pentester traite)
- Feedback loop : si une décision est systématiquement ignorée par un rôle,
  réduire son poids pour ce rôle
- Personal PageRank sur le Knowledge Graph pour identifier les CVE « périphériques »

---

## Axe 5 — Predictive Risk Evolution (PRE)

### Objectif

Prédire « quel sera mon plus grand risque dans 7 jours ? »

### Approche

- Série temporelle EPSS par CVE + tendance des mentions
- Modèle de survie (Combien de temps avant qu'un exploit public apparaisse ?)
- Features : âge de la CVE, CVSS, nombre de repos GitHub qui la mentionnent,
  présence KEV, secteur d'activité ciblé

---

## Axe 6 — Action Optimization Algorithm (AOA)

### Objectif

Ordonner N actions correctives pour maximiser la réduction du risque
dans un temps contraint.

### Approche

- Knapsack problem : chaque action a un coût (temps) et un bénéfice (réduction de risque)
- Programmation dynamique pour le plan optimal
- Contrainte : temps disponible, ressources humaines, fenêtre de maintenance

---

## Axe 7 — Collective Intelligence Engine (CIE)

### Objectif

Exploiter les décisions de tous les utilisateurs (anonymisées) pour améliorer
les recommandations de chacun.

### Approche

- Filtrage collaboratif : « les RSSI du secteur finance traitent cette CVE en priorité »
- Signaux agrégés : taux d'action par CVE, par secteur, par rôle
- Privacy : données agrégées uniquement, jamais de PII
