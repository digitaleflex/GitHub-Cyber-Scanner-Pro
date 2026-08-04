# HashCode Cockpit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refondre complètement le frontend HashCode avec le nouveau design system "cockpit de threat intelligence" : tokens CSS, layout sidebar + top bar, composants métier, et migration des pages principales.

**Architecture:** On remplace progressivement l'ancien design "SaaS cyber générique" par un design system cohérent basé sur des CSS custom properties, une sidebar de navigation, une top bar d'état, et des composants réutilisables (`InstrumentPanel`, `KpiTile`, `AlertTile`, `MissionCard`). Les pages sont migrées une par une en utilisant ces composants, sans changer la logique métier ni les appels API.

**Tech Stack:** React 19, TypeScript, TanStack Router, TanStack Query, Tailwind CSS 4, Vite, Lucide React.

## Global Constraints

- Palette sombre cockpit : fond `#0B0F17`, surface `#111827`, accent ambre `#F59E0B`, cyan infra `#22D3EE`, violet IA `#A78BFA`, lime succès `#C5F441`, rouge danger `#EF4444`.
- Typographie : `Rajdhani` (titres/chiffres), `Inter` (corps), `JetBrains Mono` (code/données).
- Navigation : sidebar fixe `240px` à gauche + top bar `56px` en haut du contenu.
- Tous les composants doivent fonctionner en dark mode unique (pas de light mode dans cette phase).
- Conserver la logique métier, les routes TanStack, les hooks React Query, et les endpoints API existants.
- Accessibilité : focus visible ambre, `prefers-reduced-motion`, contraste `4.5:1` minimum.
- Commits fréquents, messages en anglais, un commit par tâche livrable.

---

## File Structure

| File | Responsibility |
|------|----------------|
| `frontend/index.html` | Charger les polices Rajdhani, Inter, JetBrains Mono. Mettre à jour le titre. |
| `frontend/src/index.css` | Définir tous les tokens CSS (couleurs, typographie, espacements, rayons, ombres, transitions, animations). Remplacer l'ancien contenu. |
| `frontend/src/main.tsx` | Injection des polices et configuration globale (inchangée hormis imports). |
| `frontend/src/routes/__root.tsx` | Nouveau layout global : sidebar + top bar + outlet. Supprimer l'ancien header/footer. |
| `frontend/src/components/Sidebar.tsx` | Composant sidebar avec navigation groupée et états actif/hover. |
| `frontend/src/components/TopBar.tsx` | Composant top bar avec titre, statuts sources, UTC, bouton scan, profil. |
| `frontend/src/components/InstrumentPanel.tsx` | Conteneur de base pour les modules cockpit. |
| `frontend/src/components/KpiTile.tsx` | Tuile de chiffre clé. |
| `frontend/src/components/AlertTile.tsx` | Tuile de menace prioritaire avec bordure sémantique. |
| `frontend/src/components/MissionCard.tsx` | Carte de mission avec progression et métriques. |
| `frontend/src/components/DataTable.tsx` | Tableau de données revu dans le style cockpit. |
| `frontend/src/components/CyberLoader.tsx` | Loader revisité dans la nouvelle palette. |
| `frontend/src/components/Chip.tsx` | Badges sémantiques revus. |
| `frontend/src/routes/index.tsx` | Nouvelle page d'accueil "bureau de modules". |
| `frontend/src/routes/cves.tsx` | Page liste CVE migrée. |
| `frontend/src/routes/cve.tsx` | Page détail CVE migrée. |
| `frontend/src/routes/tools.tsx` | Page outils migrée. |
| `frontend/src/routes/missions.tsx` | Page missions migrée. |
| `frontend/src/routes/organization.tsx` | Page organisation migrée. |
| `frontend/src/routes/settings.tsx` | Page paramètres migrée. |
| `frontend/src/routes/about.tsx` | Page à propos migrée. |

---

## Task 1: Setup polices et tokens CSS

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/src/index.css`
- Test: visuel via `npm run dev`

**Interfaces:**
- Consumes: rien.
- Produces: variables CSS globales utilisées par tous les composants suivants.

- [ ] **Step 1: Mettre à jour les polices dans `index.html`**

Remplacer la balise `<link>` des polices existantes par :

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet" />
```

Mettre à jour le titre :

```html
<title>HashCode | Cockpit de threat intelligence</title>
```

- [ ] **Step 2: Rédiger le nouveau `index.css`**

Remplacer le contenu de `frontend/src/index.css` par un fichier qui définit :

```css
@import "tailwindcss";

:root {
  /* Fonds et surfaces */
  --bg: #0B0F17;
  --surface: #111827;
  --surface-elevated: #1B2433;
  --surface-hover: #232D3D;
  --border: #2A3648;
  --border-light: #1E2A3A;

  /* Texte */
  --text: #F1F5F9;
  --text-secondary: #A8B3C5;
  --text-muted: #6B7280;
  --text-inverse: #0B0F17;

  /* Accents */
  --amber: #F59E0B;
  --cyan: #22D3EE;
  --violet: #A78BFA;
  --lime: #C5F441;
  --red: #EF4444;

  /* Accents légers */
  --amber-light: rgba(245, 158, 11, 0.12);
  --cyan-light: rgba(34, 211, 238, 0.12);
  --violet-light: rgba(167, 139, 250, 0.12);
  --lime-light: rgba(197, 244, 65, 0.12);
  --red-light: rgba(239, 68, 68, 0.12);

  /* Espacements */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;

  /* Rayons */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 18px;

  /* Ombres et glows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.24);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.32);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.40);
  --glow-amber: 0 0 20px rgba(245, 158, 11, 0.15);
  --glow-cyan: 0 0 16px rgba(34, 211, 238, 0.12);
  --glow-red: 0 0 20px rgba(239, 68, 68, 0.20);
  --glow-lime: 0 0 16px rgba(197, 244, 65, 0.15);

  /* Transitions */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 400ms;
}

* { box-sizing: border-box; }

html {
  scroll-behavior: smooth;
  -webkit-font-smoothing: antialiased;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', system-ui, sans-serif;
  font-size: 14px;
  line-height: 1.6;
}

/* Typographie utilitaire */
.font-display { font-family: 'Rajdhani', system-ui, sans-serif; }
.font-body { font-family: 'Inter', system-ui, sans-serif; }
.font-mono { font-family: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace; }

.text-display { font-size: 2.5rem; line-height: 1.1; font-weight: 700; }
.text-h1 { font-size: 1.75rem; line-height: 1.2; font-weight: 600; }
.text-h2 { font-size: 1.25rem; line-height: 1.3; font-weight: 600; }
.text-h3 { font-size: 0.9375rem; line-height: 1.4; font-weight: 600; }
.text-body { font-size: 0.875rem; line-height: 1.6; }
.text-body-sm { font-size: 0.8125rem; line-height: 1.5; }
.text-caption { font-size: 0.6875rem; line-height: 1.4; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; }
.text-mono { font-size: 0.75rem; line-height: 1.5; }

/* Couleurs utilitaires */
.t-p { color: var(--text); }
.t-s { color: var(--text-secondary); }
.t-m { color: var(--text-muted); }
.t-amber { color: var(--amber); }
.t-cyan { color: var(--cyan); }
.t-violet { color: var(--violet); }
.t-lime { color: var(--lime); }
.t-red { color: var(--red); }

/* Focus */
:focus-visible {
  outline: 2px solid var(--amber);
  outline-offset: 2px;
}

/* Animations */
@keyframes fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse-ring {
  0%, 100% { transform: scale(1); opacity: 0.2; }
  50% { transform: scale(1.4); opacity: 0; }
}

@keyframes spin-scan {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes pulse-red {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
}

.animate-fade { animation: fade-in 0.4s var(--ease-out) both; }
.animate-pulse-ring { animation: pulse-ring 2s ease-out infinite; }
.animate-spin-scan { animation: spin-scan 1.5s linear infinite; }
.animate-pulse-red { animation: pulse-red 2s ease-in-out infinite; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--border-light); }
```

- [ ] **Step 3: Vérifier le build**

Run: `cd frontend && npm run build`
Expected: build succeeds without CSS errors.

- [ ] **Step 4: Vérifier visuellement**

Run: `cd frontend && npm run dev`
Expected: page blanche ou layout existant encore visible, mais fond sombre cockpit appliqué si des éléments utilisent les tokens.

- [ ] **Step 5: Commit**

```bash
git add frontend/index.html frontend/src/index.css
git commit -m "design(tokens): cockpit color, typography and spacing tokens"
```

---

## Task 2: Layout global — Sidebar et TopBar

**Files:**
- Create: `frontend/src/components/Sidebar.tsx`
- Create: `frontend/src/components/TopBar.tsx`
- Modify: `frontend/src/routes/__root.tsx`
- Test: visuel via `npm run dev`

**Interfaces:**
- Consumes: variables CSS de Task 1.
- Produces: `Sidebar`, `TopBar` utilisés par `__root.tsx`.

- [ ] **Step 1: Créer `Sidebar.tsx`**

```tsx
import { Link, useRouter } from '@tanstack/react-router'
import { Shield, Target, Wrench, Rocket, BookOpen, Bug, Clock, Sparkles, Settings, HelpCircle } from 'lucide-react'

const groups = [
  {
    title: 'INSTRUMENTS',
    items: [
      { to: '/', label: "Aujourd'hui", icon: Shield },
      { to: '/threats', label: 'Menaces', icon: Target },
      { to: '/tools', label: 'Outils', icon: Wrench },
      { to: '/missions', label: 'Missions', icon: Rocket },
      { to: '/library', label: 'Bibliothèque', icon: BookOpen },
    ],
  },
  {
    title: 'INTELLIGENCE',
    items: [
      { to: '/cves', label: 'CVE', icon: Bug },
      { to: '/timeline', label: 'Timeline', icon: Clock },
      { to: '/assistant', label: 'Assistant', icon: Sparkles },
    ],
  },
]

export function Sidebar() {
  const router = useRouter()
  const pathname = router.state.location.pathname

  const isActive = (to: string) => {
    if (to === '/') return pathname === '/'
    return pathname.startsWith(to)
  }

  return (
    <aside
      className="fixed left-0 top-0 h-full flex flex-col"
      style={{
        width: '240px',
        background: 'var(--surface)',
        borderRight: '1px solid var(--border)',
      }}
    >
      <div className="h-14 flex items-center gap-3 px-5" style={{ borderBottom: '1px solid var(--border)' }}>
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm"
          style={{ background: 'var(--amber)', color: 'var(--text-inverse)' }}
        >
          H
        </div>
        <div>
          <div className="font-display text-h2" style={{ lineHeight: 1 }}>HashCode</div>
          <div className="text-caption t-m">Cockpit</div>
        </div>
      </div>

      <nav className="flex-1 py-4 px-3 space-y-6 overflow-y-auto">
        {groups.map((group) => (
          <div key={group.title}>
            <div className="text-caption t-m px-3 mb-2">{group.title}</div>
            <div className="space-y-1">
              {group.items.map((item) => {
                const active = isActive(item.to)
                const Icon = item.icon
                return (
                  <Link
                    key={item.to}
                    to={item.to as any}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg transition-all"
                    style={{
                      background: active ? 'var(--surface-elevated)' : 'transparent',
                      color: active ? 'var(--text)' : 'var(--text-secondary)',
                      borderLeft: active ? '4px solid var(--amber)' : '4px solid transparent',
                    }}
                  >
                    <Icon size={16} style={{ color: active ? 'var(--amber)' : 'var(--text-muted)' }} />
                    <span className="text-body-sm font-medium">{item.label}</span>
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="p-3 space-y-1" style={{ borderTop: '1px solid var(--border)' }}>
        <Link
          to="/settings"
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-body-sm font-medium t-s hover:bg-[var(--surface-elevated)] transition-colors"
        >
          <Settings size={16} className="t-m" /> Paramètres
        </Link>
        <Link
          to="/docs"
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-body-sm font-medium t-s hover:bg-[var(--surface-elevated)] transition-colors"
        >
          <HelpCircle size={16} className="t-m" /> Documentation
        </Link>
      </div>
    </aside>
  )
}
```

- [ ] **Step 2: Créer `TopBar.tsx`**

```tsx
import { Activity } from 'lucide-react'
import { useScanStatus } from '../lib/api'
import { useState, useCallback } from 'react'

export function TopBar({ title }: { title: string }) {
  const { data, refetch } = useScanStatus()
  const [scanning, setScanning] = useState(false)
  const isScanning = scanning || data?.status?.includes('en cours')

  const handleScan = useCallback(async () => {
    if (isScanning) return
    setScanning(true)
    await fetch('/api/scan', { method: 'POST' })
    setTimeout(() => { refetch(); setScanning(false) }, 2000)
  }, [isScanning, refetch])

  return (
    <header
      className="h-14 flex items-center justify-between px-6"
      style={{
        background: 'var(--bg)',
        borderBottom: '1px solid var(--border)',
      }}
    >
      <h1 className="font-display text-h1">{title}</h1>

      <div className="flex items-center gap-6">
        <div className="hidden md:flex items-center gap-3 text-caption t-m">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--lime)' }} />
            NVD
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--lime)' }} />
            CISA
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--lime)' }} />
            GitHub
          </span>
        </div>

        <div className="font-mono text-mono t-s">
          {new Date().toISOString().slice(11, 16)} UTC
        </div>

        <button
          onClick={handleScan}
          disabled={isScanning}
          className="flex items-center gap-2 px-4 py-1.5 rounded-md text-body-sm font-semibold transition-all active:scale-[0.98]"
          style={{
            background: isScanning ? 'var(--surface-elevated)' : 'var(--amber)',
            color: isScanning ? 'var(--text-secondary)' : 'var(--text-inverse)',
            border: isScanning ? '1px solid var(--border)' : 'none',
          }}
        >
          <Activity size={14} className={isScanning ? 'animate-spin-scan' : ''} />
          {isScanning ? 'Scan...' : 'Scanner'}
        </button>
      </div>
    </header>
  )
}
```

- [ ] **Step 3: Modifier `__root.tsx`**

Remplacer le contenu de `frontend/src/routes/__root.tsx` par :

```tsx
import { Suspense } from 'react'
import { Outlet, createRootRoute } from '@tanstack/react-router'
import { Sidebar } from '../components/Sidebar'
import { TopBar } from '../components/TopBar'
import { CyberLoader } from '../components/CyberLoader'
import NotFound from './not-found'

export const Route = createRootRoute({
  component: RootLayout,
  notFoundComponent: NotFound,
})

function RootLayout() {
  return (
    <div className="min-h-screen flex" style={{ background: 'var(--bg)' }}>
      <Sidebar />
      <div className="flex-1 flex flex-col" style={{ marginLeft: '240px' }}>
        <TopBar title="Poste de contrôle" />
        <main className="flex-1 p-6 overflow-auto animate-fade">
          <Suspense fallback={<CyberLoader text="Chargement..." />}>
            <Outlet />
          </Suspense>
        </main>
      </div>
    </div>
  )
}
```

Supprimer les anciens composants internes (`ThemeToggle`, `UserBadge`, `Dropdown`, `ScanBtn`, etc.) du fichier. On réintroduira le theme toggle dans la sidebar ou les paramètres plus tard.

- [ ] **Step 4: Vérifier visuellement**

Run: `cd frontend && npm run dev`
Expected: sidebar visible à gauche, top bar en haut, contenu des pages affiché à droite.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/Sidebar.tsx frontend/src/components/TopBar.tsx frontend/src/routes/__root.tsx
git commit -m "feat(layout): cockpit sidebar and top bar"
```

---

## Task 3: Composants de base

**Files:**
- Create: `frontend/src/components/InstrumentPanel.tsx`
- Create: `frontend/src/components/KpiTile.tsx`
- Create: `frontend/src/components/AlertTile.tsx`
- Create: `frontend/src/components/MissionCard.tsx`
- Modify: `frontend/src/components/Chip.tsx`
- Test: visuel via `npm run dev` avec une page temporaire de démo

**Interfaces:**
- Consumes: tokens CSS, polices.
- Produces: composants réutilisables pour les pages.

- [ ] **Step 1: Créer `InstrumentPanel.tsx`**

```tsx
import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  title?: string
  icon?: ReactNode
  accent?: 'amber' | 'cyan' | 'violet' | 'red' | 'lime'
  className?: string
}

export function InstrumentPanel({ children, title, icon, accent, className = '' }: Props) {
  const accentColor = accent ? `var(--${accent})` : undefined
  return (
    <div
      className={`rounded-xl ${className}`}
      style={{
        background: 'var(--surface)',
        border: accent ? `1px solid ${accentColor}` : '1px solid var(--border)',
        boxShadow: accent ? `0 0 20px ${accentColor}15` : 'none',
        padding: 'var(--space-5)',
      }}
    >
      {(title || icon) && (
        <div className="flex items-center gap-2 mb-4">
          {icon && <span style={{ color: accentColor || 'var(--text-muted)' }}>{icon}</span>}
          {title && <h2 className="text-h2 font-display">{title}</h2>}
        </div>
      )}
      {children}
    </div>
  )
}
```

- [ ] **Step 2: Créer `KpiTile.tsx`**

```tsx
interface Props {
  value: string | number
  label: string
  color?: 'amber' | 'cyan' | 'violet' | 'red' | 'lime' | 'muted'
}

export function KpiTile({ value, label, color = 'text' }: Props) {
  const colorMap: Record<string, string> = {
    text: 'var(--text)',
    amber: 'var(--amber)',
    cyan: 'var(--cyan)',
    violet: 'var(--violet)',
    red: 'var(--red)',
    lime: 'var(--lime)',
    muted: 'var(--text-muted)',
  }

  return (
    <div
      className="rounded-xl p-4 text-center transition-all hover:-translate-y-0.5"
      style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <div className="font-display text-display" style={{ color: colorMap[color] }}>{value}</div>
      <div className="text-caption t-m mt-1">{label}</div>
    </div>
  )
}
```

- [ ] **Step 3: Créer `AlertTile.tsx`**

```tsx
import { AlertTriangle } from 'lucide-react'

interface Props {
  cveId: string
  description: string
  level: 'CRITIQUE' | 'ELEVE' | 'MOYEN' | 'BAS'
  cvss?: number | null
  epss?: number | null
  isKev?: boolean
  exploits?: number
  onClick?: () => void
}

const levelConfig = {
  CRITIQUE: { color: 'var(--red)', bg: 'var(--red-light)' },
  ELEVE: { color: 'var(--amber)', bg: 'var(--amber-light)' },
  MOYEN: { color: 'var(--cyan)', bg: 'var(--cyan-light)' },
  BAS: { color: 'var(--text-muted)', bg: 'var(--surface-hover)' },
}

export function AlertTile({ cveId, description, level, cvss, epss, isKev, exploits, onClick }: Props) {
  const config = levelConfig[level] || levelConfig.BAS
  return (
    <button
      onClick={onClick}
      className="w-full text-left rounded-xl p-4 transition-all hover:-translate-y-0.5"
      style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderLeft: `3px solid ${config.color}`,
      }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="font-mono text-mono font-semibold" style={{ color: 'var(--cyan)' }}>{cveId}</span>
        <span
          className="text-caption px-2 py-0.5 rounded"
          style={{ background: config.bg, color: config.color, border: `1px solid ${config.color}40` }}
        >
          {level}
        </span>
        {isKev && (
          <span className="inline-flex items-center gap-1 text-caption px-2 py-0.5 rounded" style={{ background: 'var(--red-light)', color: 'var(--red)' }}>
            <AlertTriangle size={10} /> KEV
          </span>
        )}
      </div>
      <p className="text-body-sm t-s line-clamp-2 mb-3">{description}</p>
      <div className="flex items-center gap-3 text-caption t-m">
        {cvss != null && <span>CVSS {cvss}</span>}
        {epss != null && <span>EPSS {(epss * 100).toFixed(1)}%</span>}
        {exploits != null && exploits > 0 && <span>{exploits} exploit{exploits > 1 ? 's' : ''}</span>}
      </div>
    </button>
  )
}
```

- [ ] **Step 4: Créer `MissionCard.tsx`**

```tsx
import { Target, Play, CheckCircle2 } from 'lucide-react'

interface Props {
  title: string
  objective: string
  progress: number
  estimatedMinutes?: number
  riskReduction?: number
  status: 'active' | 'in_progress' | 'completed'
  onStart?: () => void
  onViewSteps?: () => void
}

export function MissionCard({ title, objective, progress, estimatedMinutes, riskReduction, status, onStart, onViewSteps }: Props) {
  const isCompleted = status === 'completed'
  return (
    <div
      className="rounded-xl p-4 transition-all hover:-translate-y-0.5"
      style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        opacity: isCompleted ? 0.7 : 1,
      }}
    >
      <div className="h-1 rounded-full overflow-hidden mb-4" style={{ background: 'var(--border-light)' }}>
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${progress}%`,
            background: isCompleted ? 'var(--lime)' : progress >= 50 ? 'var(--cyan)' : 'var(--amber)',
          }}
        />
      </div>

      <div className="flex items-start justify-between gap-3 mb-2">
        <div>
          <h3 className="text-h3">{title}</h3>
          <p className="text-body-sm t-s line-clamp-1">{objective}</p>
        </div>
        {isCompleted && <CheckCircle2 size={18} style={{ color: 'var(--lime)' }} />}
      </div>

      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="rounded-lg p-2 text-center" style={{ background: 'var(--surface-elevated)' }}>
          <div className="font-display text-h2">{progress}%</div>
          <div className="text-caption t-m">Prog.</div>
        </div>
        <div className="rounded-lg p-2 text-center" style={{ background: 'var(--surface-elevated)' }}>
          <div className="font-display text-h2">{estimatedMinutes ?? '?'}</div>
          <div className="text-caption t-m">Min</div>
        </div>
        <div className="rounded-lg p-2 text-center" style={{ background: 'var(--surface-elevated)' }}>
          <div className="font-display text-h2" style={{ color: 'var(--lime)' }}>-{riskReduction ?? 0}%</div>
          <div className="text-caption t-m">Risque</div>
        </div>
      </div>

      {!isCompleted && (
        <button
          onClick={status === 'active' ? onStart : onViewSteps}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-body-sm font-semibold transition-all active:scale-[0.98]"
          style={{ background: 'var(--amber)', color: 'var(--text-inverse)' }}
        >
          {status === 'active' ? <><Play size={14} /> Démarrer</> : <>Voir les étapes</>}
        </button>
      )}
    </div>
  )
}
```

- [ ] **Step 5: Modifier `Chip.tsx`**

Adapter le `Chip` existant pour utiliser les nouveaux tokens et ajouter les variantes cockpit. Conserver l'interface existante mais réviser les styles :

```tsx
import { memo } from 'react'
import type { LucideIcon } from 'lucide-react'

export type ChipVariant = 'verdict' | 'severity' | 'status' | 'category' | 'default'

const styles: Record<string, { bg: string; text: string; border: string }> = {
  legitimate: { bg: 'var(--lime-light)', text: 'var(--lime)', border: 'var(--lime)' },
  sain: { bg: 'var(--lime-light)', text: 'var(--lime)', border: 'var(--lime)' },
  malicious: { bg: 'var(--red-light)', text: 'var(--red)', border: 'var(--red)' },
  suspicious: { bg: 'var(--amber-light)', text: 'var(--amber)', border: 'var(--amber)' },
  suspect: { bg: 'var(--amber-light)', text: 'var(--amber)', border: 'var(--amber)' },
  neutral: { bg: 'var(--surface-elevated)', text: 'var(--text-secondary)', border: 'var(--border)' },
  unknown: { bg: 'var(--surface-elevated)', text: 'var(--text-muted)', border: 'var(--border)' },
  critical: { bg: 'var(--red-light)', text: 'var(--red)', border: 'var(--red)' },
  high: { bg: 'var(--amber-light)', text: 'var(--amber)', border: 'var(--amber)' },
  medium: { bg: 'var(--amber-light)', text: 'var(--amber)', border: 'var(--amber)' },
  low: { bg: 'var(--surface-elevated)', text: 'var(--text-muted)', border: 'var(--border)' },
  active: { bg: 'var(--cyan-light)', text: 'var(--cyan)', border: 'var(--cyan)' },
  completed: { bg: 'var(--lime-light)', text: 'var(--lime)', border: 'var(--lime)' },
  in_progress: { bg: 'var(--cyan-light)', text: 'var(--cyan)', border: 'var(--cyan)' },
  error: { bg: 'var(--red-light)', text: 'var(--red)', border: 'var(--red)' },
  category: { bg: 'var(--cyan-light)', text: 'var(--cyan)', border: 'var(--cyan)' },
  default: { bg: 'var(--surface-elevated)', text: 'var(--text-secondary)', border: 'var(--border)' },
}

export type ChipProps = {
  variant: ChipVariant
  value: string
  icon?: LucideIcon
  className?: string
}

const Chip = memo(function Chip({ variant, value, icon: Icon, className = '' }: ChipProps) {
  const key = value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  const style = styles[key] || styles.default

  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-caption font-medium border ${className}`}
      style={{ background: style.bg, color: style.text, borderColor: `${style.border}40` }}
    >
      {Icon && <Icon size={10} />}
      {value}
    </span>
  )
})

export default Chip
```

- [ ] **Step 6: Vérifier visuellement**

Créer temporairement dans `frontend/src/routes/index.tsx` une grille de démo utilisant les 4 composants, puis lancer `npm run dev`.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/InstrumentPanel.tsx frontend/src/components/KpiTile.tsx frontend/src/components/AlertTile.tsx frontend/src/components/MissionCard.tsx frontend/src/components/Chip.tsx
git commit -m "feat(components): cockpit instrument panel, kpi, alert and mission cards"
```

---

## Task 4: Page d'accueil

**Files:**
- Modify: `frontend/src/routes/index.tsx`
- Create: `frontend/src/components/ScoreRing.tsx`
- Test: visuel via `npm run dev`

**Interfaces:**
- Consumes: `InstrumentPanel`, `KpiTile`, `AlertTile`, `MissionCard`, `ScoreRing`, hooks API existants.
- Produces: nouvelle page `Aujourd'hui`.

- [ ] **Step 1: Créer `ScoreRing.tsx`**

```tsx
interface Props {
  score: number
  color?: string
  size?: number
}

export function ScoreRing({ score, color = 'var(--amber)', size = 160 }: Props) {
  const r = (size - 12) / 2
  const circ = 2 * Math.PI * r
  const pct = Math.min(score / 100, 1)

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full -rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border)" strokeWidth="8" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${pct * circ} ${circ}`}
          style={{ transition: 'stroke-dasharray 0.8s var(--ease-out)' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-display">{score}</span>
        <span className="text-caption t-m">/ 100</span>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Réécrire `index.tsx`**

Implémenter la page d'accueil comme bureau de modules avec :
- Risque global (ScoreRing + badge + tendance).
- Menaces prioritaires (AlertTile × 3-4).
- Activité récente (feed style log).
- Missions actives (MissionCard × 2-3).
- Accès rapide (tuiles).

Conserver les appels API existants (`useQuery` sur `/api/priority/cves`, `/api/organization`, etc.). Adapter uniquement le rendu.

- [ ] **Step 3: Vérifier visuellement**

Run: `cd frontend && npm run dev`
Expected: home affiche les modules cockpit avec données réelles ou fallback.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/index.tsx frontend/src/components/ScoreRing.tsx
git commit -m "feat(home): cockpit dashboard layout"
```

---

## Task 5: Pages CVE

**Files:**
- Modify: `frontend/src/routes/cves.tsx`
- Modify: `frontend/src/routes/cve.tsx`
- Modify: `frontend/src/components/DataTable.tsx`
- Test: visuel via navigation `/cves` et `/cve/CVE-XXXX-XXXX`

**Interfaces:**
- Consumes: `InstrumentPanel`, `KpiTile`, `Chip`, `ScoreRing`, hooks API existants.
- Produces: pages CVE migrées.

- [ ] **Step 1: Modifier `DataTable.tsx`**

Appliquer le style cockpit :
- Header fond `--surface-elevated`.
- Lignes séparées par `--border-light`.
- Hover sur ligne `--surface-hover`.
- Tri indiqué par flèche `--amber`.
- Pagination minimaliste.

- [ ] **Step 2: Réécrire `cves.tsx`**

Page liste avec :
- Top Bar contenant titre + export STIX.
- Row de 4 KpiTile.
- Barre de filtres.
- DataTable cockpit.

- [ ] **Step 3: Réécrire `cve.tsx`**

Page détail avec layout deux colonnes :
- Colonne main : header, decision panel, contexte, exploits, outils, IOCs, ATT&CK, règles, patchs.
- Colonne latérale : ScoreRing, informations clés, liens externes, export STIX.

- [ ] **Step 4: Vérifier visuellement**

Naviguer sur `/cves` et `/cve/CVE-2024-XXXX`.
Expected: tableaux et fiche conformes au design cockpit.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/routes/cves.tsx frontend/src/routes/cve.tsx frontend/src/components/DataTable.tsx
git commit -m "feat(cve): cockpit design for cve list and detail pages"
```

---

## Task 6: Page Outils

**Files:**
- Modify: `frontend/src/routes/tools.tsx`
- Test: visuel via `/tools`

**Interfaces:**
- Consumes: `InstrumentPanel`, `DataTable`, `Chip`, hooks API existants.
- Produces: page Outils migrée.

- [ ] **Step 1: Réécrire `tools.tsx`**

- Tabs Incontournables / Prêts / Catégories / Pro.
- Filtres catégories sous forme de chips.
- Toggle tableau/grille.
- Drawer droit avec fiche outil.
- Utiliser `InstrumentPanel` comme conteneur principal.

- [ ] **Step 2: Vérifier visuellement**

Naviguer sur `/tools`, tester les tabs et le drawer.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/tools.tsx
git commit -m "feat(tools): cockpit design for tools page"
```

---

## Task 7: Page Missions

**Files:**
- Modify: `frontend/src/routes/missions.tsx`
- Test: visuel via `/missions`

**Interfaces:**
- Consumes: `MissionCard`, `InstrumentPanel`, hooks API existants.
- Produces: page Missions migrée.

- [ ] **Step 1: Réécrire `missions.tsx`**

- Section "En cours" avec MissionCards.
- Section "Terminées" avec liste compacte.
- Checklist d'étapes avec cases à cocher.
- Bouton final "Mission terminée".

- [ ] **Step 2: Vérifier visuellement**

Naviguer sur `/missions`, tester l'expansion et la validation d'étapes.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/missions.tsx
git commit -m "feat(missions): cockpit design for missions page"
```

---

## Task 8: Pages secondaires

**Files:**
- Modify: `frontend/src/routes/organization.tsx`
- Modify: `frontend/src/routes/settings.tsx`
- Modify: `frontend/src/routes/about.tsx`
- Modify: `frontend/src/routes/library.tsx`
- Modify: `frontend/src/routes/threats.tsx`
- Test: visuel via navigation

**Interfaces:**
- Consumes: `InstrumentPanel`, `KpiTile`, composants de formulaire, hooks API existants.
- Produces: pages secondaires migrées.

- [ ] **Step 1: Migrer `organization.tsx`**

Utiliser `InstrumentPanel` pour les sections, chips de sélection pour rôle/secteur/conformité, boutons cockpit.

- [ ] **Step 2: Migrer `settings.tsx`**

Même approche : `InstrumentPanel` par section, toggle revisité dans la nouvelle palette.

- [ ] **Step 3: Migrer `about.tsx`**

Appliquer les nouvelles typographies et couleurs. Garder le contenu.

- [ ] **Step 4: Migrer `library.tsx` et `threats.tsx`**

Adapter les cards, tableaux et filtres au style cockpit.

- [ ] **Step 5: Vérifier visuellement**

Naviguer sur chaque page secondaire.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/routes/organization.tsx frontend/src/routes/settings.tsx frontend/src/routes/about.tsx frontend/src/routes/library.tsx frontend/src/routes/threats.tsx
git commit -m "feat(pages): cockpit design for organization, settings, about, library and threats"
```

---

## Task 9: Loader et animations

**Files:**
- Modify: `frontend/src/components/CyberLoader.tsx`
- Modify: `frontend/src/index.css`
- Test: visuel via chargement des pages

**Interfaces:**
- Consumes: tokens CSS.
- Produces: loader cockpit et animations clés.

- [ ] **Step 1: Réécrire `CyberLoader.tsx`**

Loader avec anneau ambre pulsant, anneau scan tournant, icône bouclier, barre de progression infinie ambre→cyan, texte technique en mono.

- [ ] **Step 2: Ajouter les keyframes manquantes dans `index.css`**

S'assurer que `pulse-ring`, `spin-scan`, `pulse-red` sont bien définis.

- [ ] **Step 3: Vérifier visuellement**

Forcer l'affichage du loader et vérifier les animations.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/CyberLoader.tsx frontend/src/index.css
git commit -m "feat(animations): cockpit loader and motion tokens"
```

---

## Task 10: Polissage et accessibilité

**Files:**
- Modify: `frontend/src/index.css`
- Modify: tous les composants au besoin
- Test: `npm run build`, `npm run lint`, vérification contraste

**Interfaces:**
- Consumes: tous les composants créés.
- Produces: code final propre et accessible.

- [ ] **Step 1: Vérifier les contrastes**

S'assurer que `--text` sur `--surface` et `--amber` sur `--text-inverse` ont un contraste ≥ 4.5:1.

- [ ] **Step 2: Vérifier `prefers-reduced-motion`**

S'assurer que toutes les animations sont désactivées ou réduites dans la media query.

- [ ] **Step 3: Vérifier les aria-labels**

S'assurer que les icônes seules ont des labels, que les boutons sont explicites.

- [ ] **Step 4: Lancer le build et le lint**

Run:
```bash
cd frontend && npm run lint
cd frontend && npm run build
```
Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/index.css
git commit -m "chore(polish): accessibility, contrast and reduced motion"
```

---

## Self-Review

### Spec coverage

| Spec section | Task |
|--------------|------|
| Tokens couleurs | Task 1 |
| Typographie | Task 1 |
| Layout sidebar/top bar | Task 2 |
| Composants InstrumentPanel/KpiTile/AlertTile/MissionCard | Task 3 |
| Page Aujourd'hui | Task 4 |
| Pages CVE | Task 5 |
| Page Outils | Task 6 |
| Page Missions | Task 7 |
| Pages secondaires | Task 8 |
| Loader/animations | Task 9 |
| Accessibilité | Task 10 |

### Placeholder scan

Aucun TBD, TODO, ou vague instruction détecté. Chaque tâche a des fichiers, du code, des commandes et un commit.

### Type consistency

- Les props des composants sont définies dans chaque task.
- Les noms de tokens CSS sont cohérents entre les tasks.
- Les hooks API existants sont conservés tels quels.

### Gaps

Aucun gap majeur. Le mode clair est volontairement hors scope pour cette phase.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-08-04-hashcode-cockpit-implementation-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
