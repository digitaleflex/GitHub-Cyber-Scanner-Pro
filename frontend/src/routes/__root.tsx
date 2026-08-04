import { useState, useCallback, useRef, useEffect } from 'react'
import { Link, Outlet, createRootRoute, useRouter } from '@tanstack/react-router'
import { Menu, X, Shield, Building2, Settings, ChevronDown, Sun, Moon, Search, Activity } from 'lucide-react'
import { useScanStatus } from '../lib/api'
import { useQuery } from '@tanstack/react-query'
import useSearchHotkey from '../lib/useSearchHotkey'
import NotFound from './not-found'

export const Route = createRootRoute({ component: RootLayout, notFoundComponent: NotFound })

function ThemeToggle() {
  const [dark, setDark] = useState(() => {
    if (typeof window === 'undefined') return false
    const stored = localStorage.getItem('theme')
    if (stored) return stored === 'dark'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  return (
    <button
      onClick={() => setDark(!dark)}
      className="relative w-9 h-9 rounded-lg flex items-center justify-center transition-all hover:bg-[var(--surface-hover)]"
      title={dark ? 'Mode clair' : 'Mode sombre'}
      aria-label={dark ? 'Passer en mode clair' : 'Passer en mode sombre'}
    >
      <span className="transition-all duration-300" style={{ transform: dark ? 'rotate(180deg) scale(0)' : 'rotate(0deg) scale(1)', position: dark ? 'absolute' : 'relative', color: 'var(--text-secondary)' }}>
        <Sun size={17} />
      </span>
      <span className="transition-all duration-300" style={{ transform: dark ? 'rotate(0deg) scale(1)' : 'rotate(-180deg) scale(0)', position: dark ? 'relative' : 'absolute', color: 'var(--text-secondary)' }}>
        <Moon size={17} />
      </span>
    </button>
  )
}

function UserBadge() {
  const { data } = useQuery({
    queryKey: ['user-badge'],
    queryFn: () => fetch('/api/organization?profile_id=1').then(r => r.json()),
    staleTime: 300_000,
  })
  const profile = data?.profile
  const org = data?.organization
  if (!profile) return null
  return (
    <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full text-xs surface-flat" style={{ border: '1px solid var(--border)' }}>
      <span className="w-2 h-2 rounded-full" style={{ background: 'var(--success)' }} />
      <span className="font-medium capitalize" style={{ color: 'var(--text)' }}>{profile.role || 'non_defini'}</span>
      {org && (
        <>
          <span className="text-muted">·</span>
          <Building2 size={11} className="text-muted" />
          <span className="truncate max-w-[80px] text-muted">{org.name}</span>
        </>
      )}
    </div>
  )
}

function Dropdown({ children, items }: { children: React.ReactNode; items: { label: string; to: string; icon?: React.ReactNode }[] }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const h = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }
    if (open) document.addEventListener('click', h)
    return () => document.removeEventListener('click', h)
  }, [open])
  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
        style={{ color: open ? 'var(--text)' : 'var(--text-secondary)' }}
      >
        {children}
        <ChevronDown size={12} className={`transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div
          className="absolute top-full right-0 mt-2 py-1.5 px-1 min-w-[180px] z-50 animate-fade"
          style={{
            background: 'var(--surface-elevated)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-lg)',
            boxShadow: 'var(--shadow-xl)',
          }}
        >
          {items.map(item => (
            <Link
              key={item.to}
              to={item.to as any}
              onClick={() => setOpen(false)}
              className="dropdown-item"
            >
              {item.icon && <span className="shrink-0" style={{ color: 'var(--text-muted)' }}>{item.icon}</span>}
              {item.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

function ScanBtn() {
  const { data, refetch } = useScanStatus()
  const [scanning, setScanning] = useState(false)
  const router = useRouter()
  const isScanning = scanning || data?.status?.includes('en cours')

  const handleScan = useCallback(async () => {
    if (isScanning) return
    setScanning(true)
    try {
      const res = await fetch('/api/scan', { method: 'POST' })
      if (res.ok) { setTimeout(() => { refetch(); router.invalidate() }, 1000) }
    } catch {}
    setTimeout(() => setScanning(false), 2000)
  }, [isScanning, refetch, router])

  return (
    <button
      onClick={handleScan}
      disabled={isScanning}
      aria-label={isScanning ? 'Scan en cours' : 'Lancer un scan'}
      className={`flex items-center gap-2 px-3.5 py-2 rounded-full text-xs font-semibold transition-all ${
        isScanning ? 'opacity-60 cursor-not-allowed' : 'hover:shadow-lg hover:scale-[1.02] active:scale-[0.98]'
      }`}
      style={{
        background: isScanning ? 'var(--surface)' : 'var(--brand)',
        color: isScanning ? 'var(--text-secondary)' : 'var(--brand-text)',
        border: isScanning ? '1px solid var(--border)' : 'none',
      }}
    >
      <Activity size={13} className={isScanning ? 'animate-pulse' : ''} />
      {isScanning ? 'Scan...' : 'Scanner'}
    </button>
  )
}

function RootLayout() {
  const [menuOpen, setMenuOpen] = useState(false)
  const router = useRouter()
  const currentPath = router.state.location.pathname
  useSearchHotkey()

  const isActive = (path: string) => currentPath === path || (path !== '/' && currentPath.startsWith(path))

  return (
    <div className="min-h-screen" style={{ color: 'var(--text)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <header
          className="flex items-center justify-between py-3 sm:py-4 gap-4"
          style={{ borderBottom: `1px solid var(--border)` }}
        >
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 shrink-0 group" style={{ textDecoration: 'none' }}>
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm transition-all group-hover:scale-105 group-hover:shadow-lg"
              style={{
                background: 'var(--brand)',
                color: 'var(--brand-text)',
                boxShadow: '0 0 0 4px var(--brand-ring)',
              }}
            >
              H
            </div>
            <div className="hidden sm:block">
              <div className="text-sm font-bold tracking-tight" style={{ color: 'var(--text)' }}>HashCode</div>
              <div className="text-[10px] font-semibold tracking-wide" style={{ color: 'var(--text-secondary)' }}>
                Decision <span style={{ color: 'var(--brand-text)' }}>OS</span>
              </div>
            </div>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-1" role="navigation" aria-label="Navigation principale">
            {[
              { to: '/', label: "Aujourd'hui" },
              { to: '/threats', label: 'Menaces' },
              { to: '/missions', label: 'Missions' },
              { to: '/tools', label: 'Outils' },
            ].map(item => (
              <Link
                key={item.to}
                to={item.to as any}
                className={`nav-link ${isActive(item.to) ? 'active' : ''}`}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-2 sm:gap-3">
            <ThemeToggle />
            <UserBadge />
            <div className="hidden md:flex items-center gap-1">
              <Dropdown items={[
                { label: 'Timeline', to: '/timeline' },
                { label: 'Rapports', to: '/reports' },
                { label: 'Assistant', to: '/assistant' },
                { label: 'CVE', to: '/cves' },
              ]}>
                <Search size={15} />
              </Dropdown>
              <Dropdown items={[
                { label: 'Assets', to: '/assets', icon: <Shield size={11} /> },
                { label: 'Organisation', to: '/organization', icon: <Building2 size={11} /> },
                { label: 'Paramètres', to: '/settings', icon: <Settings size={11} /> },
                { label: 'À propos', to: '/about' },
              ]}>
                <Settings size={15} />
              </Dropdown>
            </div>
            <ScanBtn />

            {/* Mobile menu toggle */}
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="md:hidden p-2 rounded-lg transition-colors hover:bg-[var(--surface-hover)]"
            >
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </header>

        {/* Mobile nav overlay */}
        {menuOpen && (
          <nav
            className="md:hidden flex flex-col gap-0.5 pb-4 -mt-1 mb-4 animate-scale p-3"
            style={{
              background: 'var(--surface-elevated)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-lg)',
              boxShadow: 'var(--shadow-xl)',
            }}
          >
            <Link to="/" onClick={() => setMenuOpen(false)} className={`nav-link ${isActive('/') ? 'active' : ''}`}>Aujourd'hui</Link>
            <Link to="/threats" onClick={() => setMenuOpen(false)} className={`nav-link ${isActive('/threats') ? 'active' : ''}`}>Menaces</Link>
            <Link to="/missions" onClick={() => setMenuOpen(false)} className={`nav-link ${isActive('/missions') ? 'active' : ''}`}>Missions</Link>
            <Link to="/tools" onClick={() => setMenuOpen(false)} className={`nav-link ${isActive('/tools') ? 'active' : ''}`}>Outils</Link>
            <div className="separator my-2" />
            <Link to="/timeline" onClick={() => setMenuOpen(false)} className="nav-link text-muted">Timeline</Link>
            <Link to="/reports" onClick={() => setMenuOpen(false)} className="nav-link text-muted">Rapports</Link>
            <Link to="/assistant" onClick={() => setMenuOpen(false)} className="nav-link text-muted">Assistant</Link>
            <Link to="/cves" onClick={() => setMenuOpen(false)} className="nav-link text-muted">CVE</Link>
            <div className="separator my-2" />
            <Link to="/assets" onClick={() => setMenuOpen(false)} className="nav-link text-muted">Assets</Link>
            <Link to="/organization" onClick={() => setMenuOpen(false)} className="nav-link text-muted">Organisation</Link>
            <Link to="/settings" onClick={() => setMenuOpen(false)} className="nav-link text-muted">Paramètres</Link>
          </nav>
        )}

        <Outlet />

        <footer className="py-8 mt-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs" style={{ borderTop: `1px solid var(--border)` }}>
          <div className="flex items-center gap-3">
            <span className="font-medium" style={{ color: 'var(--text-secondary)' }}>HashCode Decision OS</span>
            <span className="w-1 h-1 rounded-full" style={{ background: 'var(--border)' }} />
            <Link to="/about" className="hover:underline" style={{ color: 'var(--text-muted)' }}>À propos</Link>
          </div>
          <span className="text-muted">Decision Engine · NVD · Exploit-DB · EPSS · CISA KEV</span>
        </footer>
      </div>
    </div>
  )
}
