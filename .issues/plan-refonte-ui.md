# Refonte UI/UX CyberScan Pro — Plan d'Architecture

> Analyse concurrentielle approfondie : Shodan, VirusTotal, Censys, SpiderFoot, urlscan.io  
> Objectif : Passer d'une interface "moteur de recherche" à une **plateforme CTI professionnelle**

---

## 1. Architecture d'Information — Nouvelle Structure

### Avant (actuel) → Après (refonte)

| Avant | Problème | Après |
|---|---|---|
| Hero sur toutes les pages | Écrase le contenu | ✅ Hero uniquement sur `/` (déjà fait) |
| 1 seule page d'accueil scroll infini | Pas de hiérarchie | **Dashboard + Explore + Labs** séparés |
| `/search` redondant avec la home | Confusion | `/search` = recherche avancée puissante |
| Card grid partout | Pas de vues tableau | Vues multiples : grid / table / graph |
| Admin en 4 liens basiques | Aucun workflow | Admin = cockpit opérationnel |
| OSINT en 1 seul formulaire | 17 endpoints cachés | OSINT = lab multi-onglets |
| AI Lab coincé en bas de page | Enterré | AI Lab = page dédiée |
| Pas de live/activité visible | Site statique | Live feed + activité temps réel |

### Nouvelle navigation principale

```
/                 Accueil — Dashboard + Alertes + Flux live
/tools            Outils Cyber — Grid / Table / Graph
/tool/:name       Fiche outil — Trust score + Similaires + CVE liées
/osint            OSINT Lab — 5 onglets (Enquête, Pipeline, Pro, Dorks, Outils)
/search           Recherche avancée — IA / Sémantique / Classique
/labs             AI Lab — 22 modèles, playground
/cves             Base CVE — Tableau + filtres + détail
/graph            Knowledge Graph — Neo4j interactif
/about            À propos
/admin            Administration — Cockpit opérationnel (protégé)
```

**Supprimé** : rien — tout est conservé et enrichi.

---

## 2. Design System — Refonte Visuelle

### Inspiration par concurrent

| Élément | Shodan | VirusTotal | urlscan.io | **CyberScan (nouveau)** |
|---|---|---|---|---|
| **Fond** | Dark brut | Dark (#161625) | Bootstrap dark | Dark slate (#020617) ✅ Garder |
| **Accent** | Rouge/Jaune/Bleu | Material Blue | Vert | **Cyan/Indigo/Violet/Ambre** ✅ Garder |
| **Typo** | Monospace | Roboto | Bootstrap | **Inter + JetBrains Mono + Orbitron** ✅ Garder |
| **Glassmorphism** | ❌ Non | ❌ Non | ❌ Non | ✅ **Notre signature visuelle** |
| **Interactions** | `/` hotkey | Drawer + Chips | Tableaux live | **Hotkeys + Drawers + Chips** (nouveau) |
| **Widgets** | Cards | Expandable KV | Screenshots | **Glass-cards + Expand + Graph** (mix) |

### Nouveaux composants UI à créer

```
┌─────────────────────────────────────────────────┐
│  COMPOSANTS MANQUANTS (vs concurrents)           │
├─────────────────────────────────────────────────┤
│  1. DataTable universel — tri, filtre, export    │
│  2. Drawer / Side panel — détail sans navigation │
│  3. Chips/Badges — verdict, sévérité, catégorie  │
│  4. Live Feed — activité temps réel              │
│  5. Search Bar avancée — hotkey `/`, suggestions │
│  6. Status Indicator — scanner, imports en cours │
│  7. Expandable sections — progressive disclosure │
│  8. Copy-to-clipboard — IOC, hash, IP            │
│  9. Tabs universelles — contenu multi-facettes   │
│ 10. Skeleton loaders — au lieu de "Chargement..."│
└─────────────────────────────────────────────────┘
```

---

## 3. Page par Page — Design Détaillé

---

### 3.1 HOME `/` — Dashboard + Live Feed

**Problème actuel** : Trop long, sections empilées sans hiérarchie, pas de vue d'ensemble.

**Refonte** :

```
┌──────────────────────────────────────────────────────┐
│  [Navbar]                               [Scan] [Menu]│
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │  🛡️ CYBERSCAN PRO            v3.1  │  🟢 Live  │    │
│  │  Veille Cyber Intelligence                 │    │
│  │  7 000+ outils audités par IA              │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ┌─ RECHERCHE ──────────────────────────────────┐    │
│  │  🔍  Rechercher un outil, CVE, technique...  │    │
│  │  [Outils] [CVE] [Ressources] [Mots-clés]     │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐    │
│  │ 12       │ │ 3 CRIT.  │ │ 5 HIGH   │ │ 🔴   │    │
│  │ menaces  │ │ ajd      │ │ ajd      │ │ Live │    │
│  │ ce mois  │ │          │ │          │ │ Scan │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────┘    │
│                                                      │
│  ┌─ DIGEST IA DU JOUR ──────────────────────────┐    │
│  │  📰 2 menaces critiques aujourd'hui           │    │
│  │  • CVE-2024-XXXX — Exploit PoC publié        │    │
│  │  • Nouveau ransomware cible VMware           │    │
│  │  💡 Insight: Vérifier vos ESXi...            │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ┌─ TENDANCES ───────┐ ┌─ DERNIERS OUTILS ──────┐   │
│  │ 🔥 tool-1   ★1.2k │ │ 🆕 repo-1      ★342   │   │
│  │ 🔥 tool-2   ★890  │ │ 🆕 repo-2      ★128   │   │
│  │ 🔥 tool-3   ★756  │ │ 🆕 repo-3       ★95   │   │
│  └───────────────────┘ └────────────────────────┘   │
│                                                      │
│  ┌─ ACTIVITÉ RÉCENTE ───────────────────────────┐    │
│  │  14:32  Scan terminé — 47 nouveaux repos      │    │
│  │  12:15  Digest IA généré                      │    │
│  │  09:00  Import CVE: 234 nouvelles vulns       │    │
│  └──────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

**Changements clés** :
- Hero compact en haut, pas full-screen
- Barre de recherche directement en dessous — **inspiration Shodan**
- 4 KPI cards au lieu de 3 compteurs animés seuls
- Digest IA + Tendances + Nouveaux outils en grille 2 colonnes
- **Live feed d'activité** (inspiration urlscan.io) — le site "respire"

---

### 3.2 OUTILS `/tools` — Tableau Professionnel

**Problème actuel** : Uniquement des cards. Pas de vue tableau, pas de tri, pas de filtres avancés.

**Refonte** :

```
┌──────────────────────────────────────────────────────┐
│  Outils Cyber                              7 234 résultats │
├──────────────────────────────────────────────────────┤
│  [🔍 Filtrer...]  [Verdict ▼] [Sévérité ▼] [Lang ▼] │
│  [Grid] [Table] [Stats]                     [CSV ⬇]  │
├──────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────┐  │
│  │ NOM              │ ★     │ Verdict  │ Vital.  │  │
│  │────────────────────────────────────────────────│  │
│  │ tool-1/repo      │ 1.2k  │ Sain     │ 89/100  │  │
│  │ tool-2/repo      │  890  │ Suspect  │ 45/100  │  │
│  │ tool-3/repo      │  756  │ Critique │ 12/100  │  │
│  │ ...                                             │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ◀ 1 2 3 ... 362 ▶                       20 par page│
└──────────────────────────────────────────────────────┘
```

**Changements clés** :
- Vue **tableau par défaut** (inspiration urlscan.io) avec colonnes triables
- Toggle Grid/Table/Stats
- Filtres rapides en haut (verdict, sévérité, langage)
- Export CSV en 1 clic
- Pagination proprement affichée

---

### 3.3 FICHE OUTIL `/tool/:name` — Side Panel

**Problème actuel** : Navigation complète vers une nouvelle page, perte de contexte.

**Refonte** : Ouvrir dans un **drawer latéral** (inspiration VirusTotal) :

```
┌──────────────────────────────────────────────────────┐
│  Outils Cyber                      [✕] ┌─ DRAWER ──┐│
│  ┌──────────────────────────────────┐   │           ││
│  │ tool-1  ★1.2k  Sain  89/100     │   │ Trust 78  ││
│  │ tool-2  ★890   Suspect  45      │   │ ████░░    ││
│  │ tool-3  ★756   Critique 12      │   │           ││
│  │ ...                              │   │ Stats     ││
│  └──────────────────────────────────┘   │ ★ 1 234   ││
│                                         │ 🐍 Python ││
│                                         │ Vital. 89 ││
│                                         │           ││
│                                         │ Similaires││
│                                         │ • repo-a  ││
│                                         │ • repo-b  ││
│                                         │           ││
│                                         │ [GitHub]  ││
│                                         └───────────┘│
└──────────────────────────────────────────────────────┘
```

Le drawer permet de **naviguer dans la liste sans perdre le contexte** — on peut cliquer outil après outil sans recharger la page entière.

---

### 3.4 OSINT `/osint` — Lab Pro

**Problème actuel** : Un seul formulaire, 17 endpoints cachés.

**Refonte** : Interface à la **SpiderFoot** — workflow en étapes visuelles :

```
┌──────────────────────────────────────────────────────┐
│  OSINT Lab                                  7 outils  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─ CIBLE ──────────────────────────────────────┐   │
│  │  Décrivez qui vous cherchez...                │   │
│  │  [________________________________] [🔍 Go]  │   │
│  │  Ou renseignez: [Nom] [Email] [Tel] [Domaine] │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌─ PIPELINE ───────────────────────────────────┐   │
│  │  ① Extraction IA  ✓  John Doe, Berlin        │   │
│  │  ② Classification ✓  Chercheur sécurité      │   │
│  │  ③ GitHub Search  →  3 profils trouvés       │   │
│  │  ④ Social Search  →  5 plateformes           │   │
│  │  ⑤ Dorking       →  12 résultats            │   │
│  │  ⑥ Analyse        ⏳ En cours...             │   │
│  │  ⑦ Rapport        ⏸                         │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌─ RÉSULTATS ──────────────────────────────────┐   │
│  │  GitHub         Social         Dorks          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐    │   │
│  │  │ jdoe     │  │ Twitter  │  │ Blog post│    │   │
│  │  │ Berlin   │  │ GitHub   │  │ Conf     │    │   │
│  │  │ 342 ★   │  │ LinkedIn │  │ Paper    │    │   │
│  │  └──────────┘  └──────────┘  └──────────┘    │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

**Changements clés** :
- Formulaire enrichi : texte libre + champs structurés (nom, email, tel, domaine)
- **Pipeline visuel** : étapes ①→⑦ avec statut (✓ ⏳ ⏸ ❌)
- Résultats par catégorie avec onglets
- Carte de chaque profil avec avatar, bio, followers
- Vue "Rapport complet" qui agrège tout

---

### 3.5 RECHERCHE `/search` — Power User

**Problème actuel** : Redondant avec la home, pas assez puissant.

**Refonte** : Interface à la **Shodan** — une barre + des résultats denses :

```
┌──────────────────────────────────────────────────────┐
│  Recherche avancée                                   │
├──────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐    │
│  │  🔍  CVE-2024 OR ransomware lang:python      │    │
│  │  Appuyez / pour chercher                      │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  Mode: [● Classique] [○ IA Groq] [○ Sémantique]     │
│  Types: [Outils] [CVE] [Ressources] [Mots-clés]     │
│  Filtres: Sévérité [Toutes ▼] Verdict [Tous ▼]      │
│                                                      │
│  ┌─ 1 234 RÉSULTATS ────────────────────────────┐   │
│  │                                               │   │
│  │  Facettes:          Résultats:                │   │
│  │  ┌──────────────┐  ┌──────────────────────┐  │   │
│  │  │ Types        │  │ 🔴 CVE-2024-1234     │  │   │
│  │  │ Outils   892 │  │ Critical | CVSS 9.8  │  │   │
│  │  │ CVE      234 │  │ Exploit PoC publié   │  │   │
│  │  │ Docs     108 │  │                      │  │   │
│  │  │                │  │ 🟡 CVE-2024-5678    │  │   │
│  │  │ Langages       │  │ High | CVSS 7.5     │  │   │
│  │  │ Python   456 │  │ ...                  │  │   │
│  │  │ Go       234 │  └──────────────────────┘  │   │
│  │  │ Rust      89 │                            │   │
│  │  └──────────────┘                            │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

**Changements clés** :
- **Query syntax hints** — l'utilisateur tape des mots-clés comme sur Shodan
- Facettes à gauche (inspiration Elasticsearch/urlscan.io)
- Résultats denses avec métadonnées visibles
- Hotkey `/` pour focuser la barre de recherche
- Mode IA et Sémantique clairement visibles

---

### 3.6 AI LAB `/labs` — Nouvelle Page

**Problème actuel** : Coincé en bas de la home, invisible.

**Refonte** : Page dédiée qui **montre les 22 modèles** :

```
┌──────────────────────────────────────────────────────┐
│  AI Lab — 22 modèles HuggingFace                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─ PLAYGROUND ─────────────────────────────────┐   │
│  │  [Classification] [Q&A] [Vuln] [Embed] [Guard]│   │
│  │                                               │   │
│  │  ┌─ INPUT ──────────────────────────────┐    │   │
│  │  │  outil de scan réseau pour pentest   │    │   │
│  │  └──────────────────────────────────────┘    │   │
│  │                                               │   │
│  │  ┌─ RÉSULTAT ───────────────────────────┐    │   │
│  │  │  Red Team     ████████████  89%      │    │   │
│  │  │  Blue Team    ████          31%      │    │   │
│  │  │  OSINT        ██            15%      │    │   │
│  │  └──────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌─ MODÈLES DISPONIBLES ────────────────────────┐   │
│  │  🟢 roberta-squad2       Q&A                 │   │
│  │  🟢 SecBERT              Vuln Detection      │   │
│  │  🟢 bart-large-mnli      Zero-Shot Classif   │   │
│  │  🟢 Granite Guardian     Content Safety      │   │
│  │  🟢 all-MiniLM-L6        Embeddings          │   │
│  │  ... 17 autres modèles chargés               │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

---

### 3.7 CVE `/cves` — Base Professionnelle

**Problème actuel** : Liste simple, pas de tableau, pas de stats globales.

**Refonte** :

```
┌──────────────────────────────────────────────────────┐
│  Base CVE — 354 821 vulnérabilités                   │
├──────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐    │
│  │ 12 450   │ │ 2 340    │ │ 89       │ │ KEV  │    │
│  │ CRITICAL │ │ HIGH     │ │ EXPLOITÉS│ │ 1 104│    │
│  └──────────┘ └──────────┘ └──────────┘ └──────┘    │
│                                                      │
│  [🔍 CVE-2024...]  [Sévérité ▼] [Année ▼] [KEV ✓]  │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │ CVE ID         │ CVSS  │ Sev. │ Exploits │ KEV│   │
│  │──────────────────────────────────────────────│    │
│  │ CVE-2024-3094  │ 10.0  │ CRIT │ 3        │ ✓  │   │
│  │ CVE-2024-1234  │  9.8  │ CRIT │ 1        │ ✓  │   │
│  │ CVE-2024-5678  │  7.5  │ HIGH │ 0        │ -  │   │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ◀ 1 2 3 ... 17 741 ▶                      20/page  │
└──────────────────────────────────────────────────────┘
```

**Changements clés** :
- 4 KPI en haut : CRITICAL / HIGH / EXPLOITÉS / KEV
- **Tableau avec colonnes** : CVSS, sévérité, nb exploits, KEV flag
- Filtres rapides : sévérité + année + KEV uniquement
- Lien direct vers la fiche détail CVE
- Stats globales visibles immédiatement

---

### 3.8 ADMIN `/admin` — Cockpit Opérationnel

**Problème actuel** : Boutons éparpillés, pas de workflow, pas de statuts live.

**Refonte** : Véritable cockpit avec **workflows visuels** :

```
┌──────────────────────────────────────────────────────┐
│  ⚙️ Administration                    CyberScan v3.1 │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─ STATUT SYSTÈME ─────────────────────────────┐   │
│  │  Scanner   🟢 Prêt    │ CVE Import 🟢 354K   │   │
│  │  Tokens    🟢 3 actifs│ Harvest   ⚪ Idle    │   │
│  │  Embed     🟡 45%    │ Models HF 🟢 22/22   │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌─ WORKFLOW: SCAN GITHUB ──────────────────────┐   │
│  │                                               │   │
│  │  ① [ Scan standard ]    500-2000 repos       │   │
│  │  ② [ Bulk Seed    ]     ~1M repos (lent)     │   │
│  │  ③ [ Slicer       ]     Par tranches         │   │
│  │  ④ [ Dorking      ]     Code Search profond  │   │
│  │                                               │   │
│  │  ▸ Dernier scan: il y a 2h — 47 repos        │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌─ WORKFLOW: ENRICHISSEMENT ───────────────────┐   │
│  │                                               │   │
│  │  ① [ IA Verdict    ]  Auditer 30 repos       │   │
│  │  ② [ IA Keywords   ]  Découvrir 25 termes    │   │
│  │  ③ [ Catégoriser   ]  Classifier 15 repos    │   │
│  │  ④ [ Ontologie     ]  MITRE ATT&CK/CAPEC     │   │
│  │  ⑤ [ Mots-clés ext.]  CVE/OWASP/Exploit-DB   │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌─ WORKFLOW: IMPORT ───────────────────────────┐   │
│  │  ① [ Import CVE   ]  300K vulns (long)       │   │
│  │  ② [ Exploit-DB   ]  46K exploits            │   │
│  │  ③ [ Harvest      ]  Issues + Commits        │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌─ SÉCURITÉ ───────────────────────────────────┐   │
│  │  Critique: 12 │ Suspect: 45 │ Sain: 6903     │   │
│  │  Vitalité moy: 67/100 │ Morts: 234           │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌─ RAPPORTS ───────────────────────────────────┐   │
│  │  📄 rapport_2026-08-01.md      2.3 MB        │   │
│  │  📊 dashboard_2026-08-01.html  4.1 MB        │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

**Changements clés** :
- **Barre de statut système** en haut : scanner, tokens, embeddings, modèles HF
- **Workflows groupés par thème** : Scan, Enrichissement, Import — clair et visible
- **Statuts live** avec couleurs (🟢 🟡 🔴 ⚪) — inspiration VirusTotal/urlscan
- **Historique** des dernières exécutions visible
- Statistiques de sécurité agrégées
- Rapports listés avec taille et date

---

### 3.9 GRAPH `/graph` — Knowledge Graph

**Problème actuel** : Fonctionnel mais basique, pas de recherche, pas de contexte.

**Refonte** :

```
┌──────────────────────────────────────────────────────┐
│  Knowledge Graph Neo4j            245 nœuds · 890 relations │
├──────────────────────────────────────────────────────┤
│  [🔍 Rechercher un noeud...]                         │
│  Filtres: [Tout] [Hacker] [APT] [Tool] [CVE] [Repo] │
│                                                      │
│  ┌─ GRAPH ──────────────────────────────────────┐   │
│  │                                               │   │
│  │         ● ←── ●                              │   │
│  │        ╱ ╲    ╱ ╲                            │   │
│  │       ●   ●──●   ●                           │   │
│  │      ╱ ╲        ╱ ╲                          │   │
│  │     ●   ●      ●   ●                         │   │
│  │                                               │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌─ DÉTAIL SÉLECTIONNÉ ─────────────────────────┐   │
│  │  🟣 Repo: metasploit-framework               │   │
│  │  ⭐ 34 200 stars                             │   │
│  │  🔗 Lié à 12 CVEs, 3 APT campaigns           │   │
│  │  [Voir sur GitHub] [Fiche outil]             │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌─ LÉGENDE ────────────────────────────────────┐   │
│  │  🟣 Repo  🔴 CVE  🟢 Tool  🟡 Hacker  🟠 APT  │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

---

## 4. Comparaison Avant/Après — Synthèse

| Dimension | Avant | Après (refonte) | Inspiration |
|---|---|---|---|
| **Page d'accueil** | Scroll infini, sections enterrées | Dashboard compact + live feed + sections | Shodan + urlscan.io |
| **Outils** | Cards uniquement | Tableau pro + Grid + Stats + CSV | urlscan.io + Censys |
| **Fiche outil** | Page entière, perte contexte | Drawer latéral, navigation fluide | VirusTotal |
| **OSINT** | 1 formulaire | 5 onglets + pipeline visuel + pro | SpiderFoot + Maltego |
| **Recherche** | Redondante, basique | Query syntax + facettes + 3 modes | Shodan + urlscan.io |
| **AI Lab** | Caché en bas | Page dédiée, 22 modèles visibles | HuggingFace Spaces |
| **CVE** | Liste simple | Tableau pro + KPI + filtres + KEV | NVD + VulDB |
| **Admin** | 4 liens + boutons | Cockpit workflows + statuts live | VirusTotal + SpiderFoot |
| **Graph** | SVG basique | Recherche + détail panel + légende | Maltego + Neo4j Bloom |
| **Navigation** | Liens texte | Icônes + compteurs + sous-pages | Shodan quickbar |
| **Live/Activité** | Aucun | Feed d'activité temps réel | urlscan.io Live |
| **Hotkeys** | Aucun | `/` = search, `?` = help | Shodan, GitHub |
| **Export** | 1 lien "Rapport" | CSV partout, Excel, JSON, STIX | Tous |

---

## 5. Plan de Mise en Œuvre (par priorité)

### Phase 1 — Fondations (2-3 jours)
1. **Composant DataTable** universel (tri, filtre, pagination, export)
2. **Composant Skeleton** loaders
3. **Composant Chips/Badges** standardisés
4. **Hotkey `/`** sur toutes les pages

### Phase 2 — Pages publiques (3-4 jours)
5. Refonte **Home** : Dashboard + live feed + layout compact
6. Refonte **Outils** : Tableau pro + drawer
7. Refonte **CVE** : Tableau + KPI + filtres
8. Refonte **Recherche** : Query syntax + facettes

### Phase 3 — Labs & OSINT (2-3 jours)
9. Nouvelle page **AI Lab** dédiée
10. Refonte **OSINT** : Pipeline visuel + 5 onglets
11. Amélioration **Graph** : Recherche + détail panel

### Phase 4 — Admin (2 jours)
12. Refonte **Admin** : Cockpit workflows + statuts live
13. Intégration **ActivityFeed** dans l'admin

### Phase 5 — Polish (1-2 jours)
14. Export CSV/JSON/STIX partout
15. Dark/Light mode toggle
16. Responsive mobile vérification
17. Animations et transitions
