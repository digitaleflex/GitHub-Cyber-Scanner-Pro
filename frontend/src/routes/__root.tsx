import { useState, useCallback, useRef, useEffect } from 'react'
import { Link, Outlet, createRootRoute, useRouter } from '@tanstack/react-router'
import { Menu, X, Play, Shield, User, Building2, Settings, ChevronDown, Sun, Moon } from 'lucide-react'
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
    <button onClick={() => setDark(!dark)} className="nav-link" title={dark ? 'Mode clair' : 'Mode sombre'}>
      {dark ? <Sun size={15} /> : <Moon size={15} />}
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
    <div className="hidden sm:flex items-center gap-2 surface-secondary rounded-full px-3 py-1 text-xs" style={{ border: 'none' }}>
      <User size={12} style={{ color: 'var(--color-brand-text)' }} />
      <span className="font-medium capitalize" style={{ color: 'var(--color-text)' }}>{profile.role || 'non_defini'}</span>
      {org && <><span className="text-disabled">·</span><Building2 size={11} style={{ color: 'var(--color-text-disabled)' }} /><span className="truncate max-w-[80px]" style={{ color: 'var(--color-text-disabled)' }}>{org.name}</span></>}
    </div>
  )
}

function Dropdown({ children, items }: { children: React.ReactNode; items: { label: string; to: string; icon?: React.ReactNode }[] }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => { const h = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }; if (open) document.addEventListener('click', h); return () => document.removeEventListener('click', h) }, [open])
  return (
    <div ref={ref} className="relative">
      <button onClick={() => setOpen(!open)} className="nav-link flex items-center gap-1">
        {children} <ChevronDown size={11} className={`transition ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="absolute top-full right-0 mt-1 surface p-1.5 min-w-[160px] z-50 animate-fade" style={{ boxShadow: 'var(--shadow-elevated)' }}>
          {items.map(item => (
            <Link key={item.to} to={item.to as any} onClick={() => setOpen(false)} className="dropdown-item">
              {item.icon && <span className="shrink-0">{item.icon}</span>}
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
    if (isScanning) return; setScanning(true)
    try {
      const res = await fetch('/api/scan', { method: 'POST' })
      if (res.ok) { setTimeout(() => { refetch(); router.invalidate() }, 1000) }
    } catch {}
    setTimeout(() => setScanning(false), 2000)
  }, [isScanning, refetch, router])
  return (
    <button onClick={handleScan} disabled={isScanning}
      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full glass text-indigo-300 hover:text-white hover:border-indigo-500/30 disabled:opacity-40 transition">
      <Play size={11} className={isScanning ? 'animate-pulse' : ''} /> {isScanning ? 'Scan...' : 'Scanner'}
    </button>
  )
}

function RootLayout() {
  const [menuOpen, setMenuOpen] = useState(false)
  useSearchHotkey()

  return (
    <div className="min-h-screen" style={{ color: 'var(--text)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <header className="flex items-center justify-between py-3 sm:py-4" style={{ borderBottom: `1px solid var(--border)` }}>
          <Link to="/" className="flex items-center gap-2.5 hover:opacity-80 transition shrink-0">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm" style={{ background: 'var(--brand)', color: 'var(--brand-text)' }}>H</div>
            <div className="hidden sm:block">
              <span className="text-sm font-semibold tracking-tight">HashCode</span>
              <span className="text-[10px] font-medium ml-1.5 px-1.5 py-0.5 rounded" style={{ background: 'var(--brand-bg)', color: 'var(--brand-text)' }}>Decision OS</span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-0.5">
            <Link to="/" className="nav-link [&.active]:nav-active">Aujourd'hui</Link>
            <Link to="/threats" className="nav-link [&.active]:nav-active">Menaces</Link>
            <Link to="/missions" className="nav-link [&.active]:nav-active">Missions</Link>
            <Link to="/tools" className="nav-link [&.active]:nav-active">Outils</Link>
          </nav>

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
                Plus
              </Dropdown>
              <Dropdown items={[
                { label: 'Assets', to: '/assets', icon: <Shield size={11} /> },
                { label: 'Organisation', to: '/organization', icon: <Building2 size={11} /> },
                { label: 'Parametres', to: '/settings', icon: <Settings size={11} /> },
                { label: 'A propos', to: '/about' },
              ]}>
                <Settings size={14} />
              </Dropdown>
            </div>
            <ScanBtn />
            <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden p-1" style={{ color: 'var(--text-secondary)' }}>
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </header>

        {menuOpen && (
          <nav className="md:hidden flex flex-col gap-1 pb-4 -mt-1 mb-4 surface rounded-xl p-2 animate-fade">
            <Link to="/" onClick={() => setMenuOpen(false)} className="text-sm py-2.5 px-3 rounded-lg font-medium" style={{ color: 'var(--text)' }}>Aujourd'hui</Link>
            <Link to="/threats" onClick={() => setMenuOpen(false)} className="text-sm py-2.5 px-3 rounded-lg" style={{ color: 'var(--text-secondary)' }}>Menaces</Link>
            <Link to="/missions" onClick={() => setMenuOpen(false)} className="text-sm py-2.5 px-3 rounded-lg" style={{ color: 'var(--text-secondary)' }}>Missions</Link>
            <Link to="/tools" onClick={() => setMenuOpen(false)} className="text-sm py-2.5 px-3 rounded-lg" style={{ color: 'var(--text-secondary)' }}>Outils</Link>
            <div className="separator my-1" />
            <Link to="/timeline" className="text-sm py-2 px-3 rounded-lg text-disabled">Timeline</Link>
            <Link to="/reports" className="text-sm py-2 px-3 rounded-lg text-disabled">Rapports</Link>
            <Link to="/assistant" className="text-sm py-2 px-3 rounded-lg text-disabled">Assistant</Link>
            <Link to="/cves" className="text-sm py-2 px-3 rounded-lg text-disabled">CVE</Link>
            <div className="separator my-1" />
            <Link to="/assets" className="text-sm py-2 px-3 rounded-lg text-disabled">Assets</Link>
            <Link to="/organization" className="text-sm py-2 px-3 rounded-lg text-disabled">Organisation</Link>
            <Link to="/settings" className="text-sm py-2 px-3 rounded-lg text-disabled">Parametres</Link>
          </nav>
        )}

        <Outlet />

        <footer className="py-8 mt-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs" style={{ borderTop: `1px solid var(--border)` }}>
          <div className="flex items-center gap-3">
            <span className="text-secondary">HashCode Decision OS</span>
            <span className="w-1 h-1 rounded-full" style={{ background: 'var(--border)' }} />
            <Link to="/about" className="text-disabled hover:text-[var(--text)] transition">A propos</Link>
          </div>
          <span className="text-disabled">Decision Engine · NVD · Exploit-DB · EPSS · CISA KEV</span>
        </footer>
      </div>
    </div>
  )
}
