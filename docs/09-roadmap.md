# 09 — Product Roadmap

---

## V1 — Cyber Watch Engine ✅ (actuel)

**Capacité : Décider**

Ce qui est livré :
- ✅ Decision Engine : scoring multi-facteurs (CVSS + Exploit + KEV + EPSS + Reranker + Récence)
- ✅ Backfill sévérité NVD (372k CVE, crawl trimestriel décroissant)
- ✅ Import Exploit-DB (46k exploits, màj quotidienne)
- ✅ CISA KEV intégré (1 600 CVE, marqueur dans weaknesses)
- ✅ Reranker sémantique (mxbai-rerank, fallback lexical)
- ✅ EPSS intégré (FIRST.org, cache DB)
- ✅ Context Engine (organisations, assets, user_profiles)
- ✅ Skills IA orientés capacités (registry, 10 capacités, backward-compat)
- ✅ Frontend outils (featured, ready-to-use, best, par catégorie)
- ✅ Corrélation CVE ↔ Exploit-DB (25k CVEs liées)
- ✅ OSINT pipeline (email, phone, domain, rapport complet)
- ✅ API REST documentée

---

## V2 — Context-Driven OS 📋

**Capacité : Comprendre + Décider (personnalisé)**

- [ ] Onboarding frontend (3 écrans : rôle → technos → objectifs)
- [ ] Profil utilisateur persistant (session, historique, préférences)
- [ ] Contexte personnalisé dans le Decision Engine (profil > global)
- [ ] Page « Aujourd'hui » : top 3 décisions + résumé + actions suggérées
- [ ] Filtres par rôle intégrés au UI
- [ ] Dashboard RSSI (KPI, exposition, conformité)
- [ ] Dashboard Pentester (nouveaux PoC, exploits, outils)

---

## V3 — Action Engine ⚡

**Capacité : Agir**

- [ ] Knowledge Actions : taxonomie d'actions (patcher, bloquer, surveiller, escalader, créer_règle_sigma…)
- [ ] Action Engine : mapper CVE → actions concrètes
- [ ] Remédiation suggérée avec temps estimé
- [ ] Génération de rapports RSSI automatisée
- [ ] Génération de tickets (Jira, Linear) depuis une décision
- [ ] Intégration API : GitHub Issues, Slack, email

---

## V4 — Mission Engine 🎯

**Capacité : Coordonner + Vérifier**

- [ ] Mission Engine : objectif mesurable (« réduire le risque Kubernetes de -70 % »)
- [ ] Ordonnancement optimal des actions (knapsack / AOA)
- [ ] Timeline des décisions (historique complet CVE → exploit → patch → vérifié)
- [ ] Vérification automatique : le risque a-t-il baissé après l'action ?
- [ ] Notifications proactives : « 3 nouvelles CVE te concernent depuis ta dernière visite »
- [ ] Multi-utilisateur par organisation (vues par rôle sur la même infrastructure)

---

## V5 — Decision OS 🤖

**Capacité : Apprendre + Prédire**

- [ ] Learning Engine : feedback loop (décisions acceptées/ignorées → poids ajustés)
- [ ] Predictive Risk Evolution : « ton plus grand risque dans 7 jours »
- [ ] Collective Intelligence : signaux agrégés anonymisés
- [ ] Assistant proactif : « j'ai préparé le plan, les tickets et le rapport RSSI »
- [ ] Cyber Impact Score (CIS) : score unifié appris
- [ ] Integrations : Azure, AWS, GCP, CrowdStrike, Defender, Intune
- [ ] API publique / marketplace de skills
- [ ] Mode hors-ligne / on-premise

---

## Calendrier indicatif

| Version | Timeline | Focus |
|---------|----------|-------|
| V1 | ✅ Livré | Moteur de scoring + contexte |
| V2 | Prochaine | Onboarding + personnalisation |
| V3 | T+3 mois | Actions + remédiation |
| V4 | T+6 mois | Missions + coordination |
| V5 | T+12 mois | Apprentissage + prédiction |
