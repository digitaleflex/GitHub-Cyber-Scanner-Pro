# 00 — Vision & Manifesto

> Version 1.0 · HashCode Research Lab

---

## Problème

La cybersécurité n'a jamais eu autant de données : CVE, IOC, bulletins CERT, exploits,
rapports, alertes EDR. Pourtant, les professionnels passent l'essentiel de leur temps à
trier ce flot pour trouver ce qui les concerne vraiment. Le problème n'est plus l'accès
aux données — c'est la **fatigue décisionnelle**.

---

## Mission

> Transformer des millions d'événements de cybersécurité en quelques décisions fiables,
> personnalisées et immédiatement actionnables.

---

## Vision

Construire le premier **Cyber Decision Operating System** : une plateforme qui comprend
*qui est l'utilisateur, ce qu'il protège, quelles technologies il utilise*, puis produit
automatiquement les risques prioritaires, les actions recommandées et leur justification.

---

## Les 7 questions fondatrices

Toute fonctionnalité doit répondre à au moins une de ces questions :

| # | Question | Module |
|---|----------|--------|
| 1 | Qu'est-ce qui est important aujourd'hui ? | Decision Engine |
| 2 | Pourquoi est-ce important ? | Decision Engine (reasons, factors, confidence) |
| 3 | Est-ce que cela me concerne ? | Context Engine |
| 4 | Que dois-je faire ? | Action Engine (à venir) |
| 5 | Qui doit agir ? | Context Engine (role mapping) |
| 6 | Que se passe-t-il si je ne fais rien ? | Decision Engine (risk_if_ignored) |
| 7 | Comment réduire le risque le plus vite ? | Mission Engine (à venir) |

---

## Principes non négociables

1. **La décision avant la donnée** — aucune information sans décision attachée
2. **Le contexte avant le contenu** — une CVE reliée à un asset, pas flottante
3. **La justification avant la confiance** — chaque recommandation expliquée
4. **L'organisation avant l'individu** — le contexte de vérité est l'organisation
5. **L'action à la place de l'information** — l'utilisateur veut que ce soit fait
6. **La boucle, pas la ligne droite** — chaque décision améliore la suivante

---

## Ce qu'on n'est PAS

- Un scanner de vulnérabilités
- Une plateforme de Threat Intelligence classique
- Un SIEM
- Un agrégateur de CVE

## Ce qu'on est

Un **moteur d'orchestration contextuelle** qui transforme des millions de signaux
en décisions personnalisées, justifiées et actionnables.

---

*Voir aussi : [MANIFESTO.md](../MANIFESTO.md) — le manifeste produit (version longue).*
