# HashCode Cockpit Design

**Date** : 2026-08-04  
**Statut** : Approuvé par l'équipe produit  
**Domaine** : Refonte complète du design frontend de HashCode  
**Auteur** : OpenCode Design Agent  

---

## 1. Résumé exécutif

Ce document définit la refonte complète du design de l'application HashCode. L'objectif est de quitter l'esthétique "SaaS cyber générique" actuelle pour adopter une identité forte centrée sur la métaphore du **cockpit de threat intelligence**.

Le design vise à créer un sentiment de **contrôle**, de **précision** et de **maîtrise** pour les utilisateurs (RSSI, SOC, pentesters, chercheurs, étudiants). Il repose sur une palette sombre bleu-noir, des accents de type instruments de cockpit (ambre principal, cyan infra, violet IA), une navigation latérale et des modules d'information clairs.

---

## 2. Direction émotionnelle et positionnement

### Émotion dominante
**Contrôle** — l'utilisateur doit se sentir au poste de pilotage de sa sécurité, avec une vision claire et actionnable de son risque.

### Positionnement
> **HashCode — votre cockpit de threat intelligence.**

### Promesse utilisateur
- Réduire le bruit des milliers de signaux cyber quotidiens.
- Prioriser les menaces qui comptent vraiment.
- Transformer chaque décision en plan d'action mesurable.

---

## 3. Identité de marque

### Nom
**HashCode** est le nom unique et définitif de l'application. Les anciennes dénominations suivantes sont abandonnées :
- ❌ CyberScan Pro
- ❌ CyberBook Collector
- ❌ HashCode Decision OS

### Sigle visuel
Le logo reste le "H" stylisé existant, mais il sera mis à jour pour s'intégrer dans la nouvelle palette cockpit. Il sera utilisé dans la sidebar et le favicon.

### Ton de la voix
- Direct et actionnable.
- Technique mais accessible.
- Rassurant sans être faussement alarmiste.

---

## 4. Design tokens

### 4.1 Palette de couleurs

Les valeurs sont fournies en OKLCH (recommandé) et en hexadécimal (compatibilité).

#### Fonds et surfaces

| Token | OKLCH | Hex | Usage |
|-------|-------|-----|-------|
| `--bg` | `oklch(12% 0.02 260)` | `#0B0F17` | Arrière-plan global de l'application |
| `--surface` | `oklch(17% 0.03 260)` | `#111827` | Cards, sidebar, panneaux |
| `--surface-elevated` | `oklch(22% 0.04 260)` | `#1B2433` | Hover, dropdowns, modals, éléments au-dessus |
| `--surface-hover` | `oklch(25% 0.05 260)` | `#232D3D` | État hover sur les éléments interactifs |
| `--border` | `oklch(30% 0.05 260)` | `#2A3648` | Bordures principales |
| `--border-light` | `oklch(22% 0.04 260)` | `#1E2A3A` | Séparateurs internes, bordures discrètes |

#### Texte

| Token | OKLCH | Hex | Usage |
|-------|-------|-----|-------|
| `--text` | `oklch(96% 0.01 260)` | `#F1F5F9` | Texte principal |
| `--text-secondary` | `oklch(75% 0.03 260)` | `#A8B3C5` | Texte secondaire, descriptions |
| `--text-muted` | `oklch(55% 0.04 260)` | `#6B7280` | Métadonnées, légendes |
| `--text-inverse` | `oklch(12% 0.02 260)` | `#0B0F17` | Texte sur fond clair/accent |

#### Accents sémantiques

| Rôle | Token | OKLCH | Hex | Usage |
|------|-------|-------|-----|-------|
| **Ambre** (principal) | `--amber` | `oklch(72% 0.17 75)` | `#F59E0B` | Focus, données importantes, alertes modérées, chiffres clés |
| **Cyan** (infra) | `--cyan` | `oklch(75% 0.15 210)` | `#22D3EE` | Infrastructure, réseau, liens, connexions |
| **Violet** (IA) | `--violet` | `oklch(68% 0.18 290)` | `#A78BFA` | Suggestions IA, analyses, prédictions |
| **Vert lime** (succès) | `--lime` | `oklch(82% 0.21 120)` | `#C5F441` | Actions validées, patchs, réduction du risque |
| **Rouge** (danger) | `--red` | `oklch(58% 0.22 25)` | `#EF4444` | Alertes critiques, KEV, danger immédiat |

#### Variantes d'accents (fond léger)

| Token | Hex | Usage |
|-------|-----|-------|
| `--amber-light` | `rgba(245, 158, 11, 0.12)` | Fond pour badges et alertes ambre |
| `--cyan-light` | `rgba(34, 211, 238, 0.12)` | Fond pour éléments infra |
| `--violet-light` | `rgba(167, 139, 250, 0.12)` | Fond pour blocs IA |
| `--lime-light` | `rgba(197, 244, 65, 0.12)` | Fond pour succès |
| `--red-light` | `rgba(239, 68, 68, 0.12)` | Fond pour danger |

### 4.2 Typographie

#### Polices

| Usage | Police | Fallback |
|-------|--------|----------|
| Titres et grands chiffres | `Rajdhani` | `system-ui, sans-serif` |
| Corps de texte | `Inter` | `system-ui, sans-serif` |
| Code, CVE, hashes, IOCs | `JetBrains Mono` | `SF Mono, Fira Code, monospace` |

#### Échelle typographique

| Classe | Taille | Hauteur de ligne | Poids | Police | Usage |
|--------|--------|------------------|-------|--------|-------|
| `display` | `2.5rem` (40px) | 1.1 | 700 | Rajdhani | Score global, gros KPI |
| `h1` | `1.75rem` (28px) | 1.2 | 600 | Rajdhani | Titre de page |
| `h2` | `1.25rem` (20px) | 1.3 | 600 | Rajdhani | Titre de section |
| `h3` | `0.9375rem` (15px) | 1.4 | 600 | Inter | Sous-section |
| `body` | `0.875rem` (14px) | 1.6 | 400 | Inter | Texte courant |
| `body-sm` | `0.8125rem` (13px) | 1.5 | 400 | Inter | Texte secondaire |
| `caption` | `0.6875rem` (11px) | 1.4 | 500 | Inter | Labels, légendes, uppercase tracking-wide |
| `mono` | `0.75rem` (12px) | 1.5 | 500 | JetBrains Mono | Données techniques |

### 4.3 Espacements

| Token | Valeur | Usage |
|-------|--------|-------|
| `--space-1` | `4px` | Espacement très fin |
| `--space-2` | `8px` | Gap interne petit |
| `--space-3` | `12px` | Padding interne standard |
| `--space-4` | `16px` | Gouttière entre modules |
| `--space-5` | `20px` | Padding interne cards |
| `--space-6` | `24px` | Section spacing |
| `--space-8` | `32px` | Grand espacement |
| `--space-10` | `40px` | Espacement de page |

### 4.4 Rayons de bordure

| Token | Valeur | Usage |
|-------|--------|-------|
| `--radius-sm` | `6px` | Petits éléments, badges, boutons |
| `--radius-md` | `10px` | Boutons, inputs, tags |
| `--radius-lg` | `14px` | Cards, panneaux |
| `--radius-xl` | `18px` | Grands conteneurs, modals |

### 4.5 Ombres et glows

| Token | Valeur | Usage |
|-------|--------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0, 0, 0, 0.24)` | Éléments légers |
| `--shadow-md` | `0 4px 12px rgba(0, 0, 0, 0.32)` | Cards survolées |
| `--shadow-lg` | `0 8px 24px rgba(0, 0, 0, 0.40)` | Modals, drawers |
| `--glow-amber` | `0 0 20px rgba(245, 158, 11, 0.15)` | Focus, alertes modérées |
| `--glow-cyan` | `0 0 16px rgba(34, 211, 238, 0.12)` | Liens actifs, infra |
| `--glow-red` | `0 0 20px rgba(239, 68, 68, 0.20)` | Alertes critiques |
| `--glow-lime` | `0 0 16px rgba(197, 244, 65, 0.15)` | Validation succès |

### 4.6 Transitions

| Token | Valeur | Usage |
|-------|--------|-------|
| `--ease-out` | `cubic-bezier(0.16, 1, 0.3, 1)` | Transitions d'interface |
| `--duration-fast` | `150ms` | Hover, focus, clics |
| `--duration-normal` | `250ms` | Apparitions, changements d'état |
| `--duration-slow` | `400ms` | Transitions de page, dessins SVG |

---

## 5. Layout global

### 5.1 Structure de page

Toutes les pages partagent la même structure :

```
┌─────────────────────────────────────────────────────────────┐
│  SIDEBAR (240px)  │  MAIN CONTENT                            │
│  ───────────────  │  ┌────────────────────────────────────┐  │
│  [H] HashCode     │  │  TOP BAR (56px)                    │  │
│                   │  │  titre | statuts | UTC | scan | profil│ │
│  INSTRUMENTS      │  └────────────────────────────────────┘  │
│  ◉ Aujourd'hui    │                                         │
│  ○ Menaces        │  ┌────────────────────────────────────┐  │
│  ○ Outils         │  │                                    │  │
│  ○ Missions       │  │      CONTENU DE LA PAGE            │  │
│  ○ Bibliothèque   │  │      (modules / grid)              │  │
│                   │  │                                    │  │
│  INTELLIGENCE     │  └────────────────────────────────────┘  │
│  ○ CVE            │                                         │
│  ○ Timeline       │                                         │
│  ○ Assistant      │                                         │
│                   │                                         │
│  ───────────────  │                                         │
│  ⚙ Paramètres     │                                         │
│  ? Aide / Docs    │                                         │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Sidebar cockpit

- **Largeur fixe** : `240px`.
- **Fond** : `--surface`.
- **Bordure** : droite `1px solid var(--border)`.
- **Zones** :
  - Logo HashCode en haut.
  - Groupe **INSTRUMENTS** : Aujourd'hui, Menaces, Outils, Missions, Bibliothèque.
  - Groupe **INTELLIGENCE** : CVE, Timeline, Assistant.
  - Bas de sidebar : Paramètres, Documentation.

#### État d'un item de navigation

- **Par défaut** : texte `--text-secondary`, icône `--text-muted`, fond transparent.
- **Hover** : fond `--surface-elevated`, texte `--text`, transition `150ms`.
- **Actif** :
  - fond `--surface-elevated`, texte `--text`;
  - bandelette ambre de `4px` à gauche;
  - icône en `--amber`;
  - léger glow ambre sur le texte.

### 5.3 Top Bar

Hauteur `56px`, fond `--bg`, bordure inférieure `1px solid var(--border)`.

Contenu (de gauche à droite) :
1. **Titre de page** en `h1` Rajdhani.
2. **Statuts des sources** : petits indicateurs ronds avec label (NVD, CISA, GitHub, etc.). Vert si OK, orange si dégradé, rouge si hors ligne.
3. **Heure UTC** en `mono`.
4. **Bouton Scan** : icône radar + label, devient actif pendant le scan.
5. **Badge profil** : rôle + organisation.

---

## 6. Composants clés

### 6.1 InstrumentPanel

Conteneur de base pour les modules.

- Fond `--surface`.
- Bordure `1px solid var(--border)`.
- Radius `--radius-lg`.
- Padding `--space-5` (20px).
- Optionnel : bordure/glow coloré selon le contenu (ambre pour alerte, cyan pour info).

### 6.2 KpiTile

Tuile de chiffre clé.

- Grand chiffre en `display` Rajdhani.
- Label en `caption` `--text-muted`.
- Couleur du chiffre selon sémantique.
- Optionnel : mini sparkline ou barre de progression en dessous.

### 6.3 AlertTile

Pour les menaces prioritaires.

- Bordure gauche épaisse `3px` selon criticité :
  - Rouge : critique
  - Ambre : élevé
  - Cyan : moyen
  - Gris : faible
- Titre en `h3`.
- Description 2 lignes max en `body-sm` `--text-secondary`.
- Ligne de métriques : CVSS, EPSS, KEV, exploits.
- Hover : `translateY(-2px)` + glow adapté.

### 6.4 MissionCard

- Barre de progression en haut de la card.
- Titre en `h3`.
- Objectif en `body-sm` `--text-secondary`.
- 3 tuiles de métriques : progression, temps estimé, réduction de risque.
- Bouton d'action principal.
- État "en cours" : pulse subtil sur la bordure.

### 6.5 DataTable cockpit

- Header avec fond `--surface-elevated`.
- Cellules padding `--space-3` vertical, `--space-4` horizontal.
- Lignes séparées par `1px solid var(--border-light)`.
- Hover sur ligne entière : fond `--surface-hover`.
- Indicateur de tri : flèche `--amber`.
- Pagination minimaliste en bas.

### 6.6 CommandBar

Barre de commande accessible via `/` ou `Ctrl+K`.

- Overlay modal centré en haut.
- Input avec fond `--surface-elevated`.
- Résultats groupés : CVE, outils, actions.
- Navigation clavier complète.

### 6.7 Badge

- Taille `caption`, padding horizontal `10px`, vertical `2px`.
- Radius `--radius-sm`.
- Bordure `1px solid` de la couleur associée.
- Fond `--*-light`.

### 6.8 Button

Trois variantes :

| Variante | Fond | Texte | Bordure | Usage |
|----------|------|-------|---------|-------|
| **Primary** | `--amber` | `--text-inverse` | none | Action principale |
| **Secondary** | `--surface` | `--text-secondary` | `1px solid var(--border)` | Action secondaire |
| **Ghost** | transparent | `--text-secondary` | none | Action discrète |

Tous les boutons ont :
- padding `10px 20px`;
- radius `--radius-md`;
- hover `translateY(-1px)` + ombre/glow;
- active `scale(0.98)`.

---

## 7. Pages principales

### 7.1 Page `Aujourd'hui`

Page d'accueil sous forme de bureau de modules.

```
┌─────────────────────────────────────────────────────────────┐
│  POSTE DE CONTRÔLE — HashCode                    [UTC] [Scan]│
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌─────────────────────────────────────┐  │
│  │ RISQUE GLOBAL│  │ MENACES PRIORITAIRES                │  │
│  │              │  │ [CVE-2026-xxx] [CVE-2026-yyy] ...   │  │
│  │   [score]    │  └─────────────────────────────────────┘  │
│  │   anneau     │  ┌──────────────────┐ ┌─────────────────┐  │
│  │   animé      │  │ ACTIVITÉ RÉCENTE │ │ MISSIONS ACTIVES│  │
│  └──────────────┘  └──────────────────┘ └─────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ ACCÈS RAPIDE : CVE · Menaces · Outils · Missions · Bib  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### Modules

1. **Risque global** (`lg:col-span-1`)
   - Grand anneau SVG animé avec le HashScore.
   - Niveau de risque en badge.
   - Sparkline d'évolution sur 7 jours.
   - Tendance vs veille.

2. **Menaces prioritaires** (`lg:col-span-2`)
   - 3 à 4 AlertTiles horizontales.
   - Triées par score décroissant.
   - Lien vers la fiche CVE.

3. **Activité récente**
   - Feed style log chronologique.
   - Événements : nouveau KEV, scan terminé, patch disponible, analyse IA.
   - Icône colorée + timestamp.

4. **Missions actives**
   - 2 à 3 MissionCards compacts.
   - Bouton pour voir toutes les missions.

5. **Accès rapide**
   - Barre de 5 tuiles : CVE, Menaces, Missions, Bibliothèque, Documentation.

### 7.2 Page `CVE` (liste)

- **Top Bar** : titre "Base CVE" + bouton export STIX.
- **Row KPIs** : 4 KpiTiles (total CVE, critiques, KEV, nouveaux 7j).
- **Filtres** : recherche par ID/description, filtre par sévérité.
- **DataTable** : ID, sévérité, CVSS, date, description.
- **Pagination** : 20 résultats par page.

### 7.3 Page `CVE/$id` (détail)

Layout deux colonnes (`lg:grid-cols-3`, main `col-span-2`).

#### Colonne principale

1. **Header** : titre, CVE ID, badges sévérité/KEV.
2. **Decision Panel** :
   - Score, confiance, exploits, KEV.
   - Liste des raisons.
   - Bloc "Risque si ignoré" avec fond `--red-light` et bordure rouge.
   - Sources utilisées.
3. **Contexte** : description + CWE.
4. **Exploits publics** : liste avec liens.
5. **Outils associés** : grille de liens.
6. **IOCs** : badges copiables.
7. **MITRE ATT&CK** : techniques avec liens.
8. **Règles de détection** : Sigma, YARA, IDS.
9. **Correctifs** : disponibilité et versions.

#### Colonne latérale

1. **HashScore ring** : anneau animé.
2. **Informations clés** : CVSS, EPSS, KEV, publié, exploits, outils.
3. **Liens externes** : NVD, Exploit-DB.
4. **Export STIX 2.1**.

### 7.4 Page `Outils`

- **Tabs** : Incontournables, Prêts à l'emploi, Par catégorie, Outils pro.
- **Filtres catégories** : Tous, Red Team, Blue Team, Exploits, Malware, OSINT, Réseau.
- **Toggle vue** : tableau ou grille.
- **Drawer droit** pour la fiche complète d'un outil.

### 7.5 Page `Missions`

- **Section "En cours"** : MissionCards avec barre de progression.
- **Section "Terminées"** : liste compacte, grisée.
- **Étapes d'une mission** : checklist avec cases à cocher.
- **Action finale** : bouton "Mission terminée" quand toutes les étapes sont validées.

---

## 8. Animations et micro-interactions

### 8.1 Principes

- Les animations informent avant de décorer.
- Durées courtes : `150-300ms` pour les interactions, `400-800ms` pour les transitions de contenu.
- Respect de `prefers-reduced-motion`.

### 8.2 Animations définies

| Animation | Déclencheur | Effet | Durée |
|-----------|-------------|-------|-------|
| **Page load** | Chargement initial | Fade-in + slide-up de `8px` | `400ms` |
| **Scan radar** | Clic sur bouton Scan | Bouton devient radar rotatif + top bar sources clignotent en séquence | pendant le scan |
| **Score ring draw** | Chargement du score | Anneau SVG se dessine de 0 à valeur | `800ms` |
| **Score change** | Mise à jour du score | Transition fluide de l'arc + couleur | `600ms` |
| **Alert pulse** | Alerte critique | Bordure gauche pulse rouge 3 fois puis stable | `2s` total |
| **Card hover** | Survol d'une card | `translateY(-2px)` + glow sémantique | `150ms` |
| **Button active** | Clic bouton | `scale(0.98)` | `100ms` |
| **Step check** | Validation d'étape | Coche verte + barre de progression remplie | `300ms` |
| **Mission complete** | Toutes étapes cochées | Risque global baisse visuellement + glow lime | `500ms` |
| **CommandBar open** | `/` ou `Ctrl+K` | Scale-in depuis le haut + fade | `200ms` |

### 8.3 Loader

Le `CyberLoader` est revu dans la nouvelle palette :
- Anneau extérieur ambre pulsant.
- Anneau scan tournant.
- Icône bouclier au centre.
- Barre de progression infinie ambre → cyan.
- Texte technique en `mono`.

### 8.4 Accessibilité

- Focus visible : outline `--amber` de `2px`, offset `2px`.
- `prefers-reduced-motion` : toutes les animations non essentielles désactivées.
- Contraste minimum `4.5:1` pour tout texte.
- Icônes accompagnées de labels ou d'attributs `aria-label`.

---

## 9. Migration depuis l'ancien design

### 9.1 Éléments à conserver

- La logique des routes TanStack Router.
- Les hooks React Query.
- La structure des appels API.
- Le composant `Chip` (à réviser visuellement).

### 9.2 Éléments à refondre

- `index.css` : remplacer les tokens et classes utilitaires.
- `__root.tsx` : passer du header au layout sidebar + top bar.
- Toutes les pages : adapter au nouveau système de cards et de grille.
- `StatsCards.tsx` : corriger les classes inexistantes et le style.
- `CyberLoader.tsx` : appliquer la nouvelle palette.
- `DataTable.tsx` : appliquer le style cockpit.

### 9.3 Ordre de migration recommandé

1. Design tokens (`index.css`).
2. Layout global (`__root.tsx` + sidebar + top bar).
3. Composants de base (`InstrumentPanel`, `KpiTile`, `AlertTile`, `MissionCard`).
4. Page d'accueil.
5. Pages CVE (liste + détail).
6. Pages Outils et Missions.
7. Pages secondaires (settings, organization, about, etc.).
8. Polissage animations et accessibilité.

---

## 10. Questions résolues

| Question | Réponse |
|----------|---------|
| Direction émotionnelle | Contrôle / cockpit |
| Nom de marque | HashCode |
| Palette | Cockpit d'avion : ambre, cyan, violet, vert lime, rouge |
| Navigation | Sidebar cockpit 240px |
| Typographie | Rajdhani + Inter + JetBrains Mono |
| Structure home | Bureau de modules |

---

## 11. Prochaines étapes

1. Rédiger le plan d'implémentation détaillé via le skill `writing-plans`.
2. Découper le travail en tickets traçables.
3. Implémenter les tokens CSS.
4. Construire le layout global.
5. Migrer page par page.
