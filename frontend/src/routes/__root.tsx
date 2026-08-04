import { useState, useCallback, useRef, useEffect } from 'react'
import { Link, Outlet, createRootRoute, useRouter } from '@tanstack/react-router'
import { Menu, X, Play, Shield, User, Building2, Settings, ChevronDown } from 'lucide-react'
import { useScanStatus } from '../lib/api'
import { useQuery } from '@tanstack/react-query'
import useSearchHotkey from '../lib/useSearchHotkey'
import NotFound from './not-found'

export const Route = createRootRoute({ component: RootLayout, notFoundComponent: NotFound })

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
    <div className="min-h-screen" style={{ color: 'var(--color-text)' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <header className="flex items-center justify-between py-3 sm:py-4 border-b" style={{ borderColor: 'var(--color-border)' }}>
          <Link to="/" className="flex items-center gap-2.5 hover:opacity-80 transition shrink-0">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm" style={{ background: 'var(--color-brand)', color: 'var(--color-brand-text)' }}>H</div>
            <div className="hidden sm:block">
              <span className="text-sm font-semibold tracking-tight" style={{ color: 'var(--color-text)' }}>HashCode</span>
              <span className="text-[10px] font-medium ml-1.5 px-1.5 py-0.5 rounded" style={{ background: 'var(--color-brand-bg)', color: 'var(--color-brand-text)' }}>Decision OS</span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-0.5">
            <Link to="/" className="nav-link [&.active]:nav-active">Aujourd'hui</Link>
            <Link to="/threats" className="nav-link [&.active]:nav-active">Menaces</Link>
            <Link to="/missions" className="nav-link [&.active]:nav-active">Missions</Link>
            <Link to="/tools" className="nav-link [&.active]:nav-active">Outils</Link>
          </nav>

          <div className="flex items-center gap-2 sm:gap-3">
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
            <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden p-1" style={{ color: 'var(--color-text-secondary)' }}>
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </header>

        {menuOpen && (
          <nav className="md:hidden flex flex-col gap-1 pb-4 -mt-1 mb-4 surface rounded-xl p-2 animate-fade">
            <Link to="/" onClick={() => setMenuOpen(false)} className="text-sm py-2.5 px-3 rounded-lg hover:bg-[var(--color-surface-secondary)] font-medium">Aujourd'hui</Link>
            <Link to="/threats" onClick={() => setMenuOpen(false)} className="text-sm py-2.5 px-3 rounded-lg hover:bg-[var(--color-surface-secondary)]">Menaces</Link>
            <Link to="/missions" onClick={() => setMenuOpen(false)} className="text-sm py-2.5 px-3 rounded-lg hover:bg-[var(--color-surface-secondary)]">Missions</Link>
            <Link to="/tools" onClick={() => setMenuOpen(false)} className="text-sm py-2.5 px-3 rounded-lg hover:bg-[var(--color-surface-secondary)]">Outils</Link>
            <div className="separator my-1" />
            <Link to="/timeline" onClick={() => setMenuOpen(false)} className="text-sm py-2 px-3 rounded-lg hover:bg-[var(--color-surface-secondary)]" style={{ color: 'var(--color-text-secondary)' }}>Timeline</Link>
            <Link to="/reports" onClick={() => setMenuOpen(false)} className="text-sm py-2 px-3 rounded-lg hover:bg-[var(--color-surface-secondary)]" style={{ color: 'var(--color-text-secondary)' }}>Rapports</Link>
            <Link to="/assistant" onClick={() => setMenuOpen(false)} className="text-sm py-2 px-3 rounded-lg hover:bg-[var(--color-surface-secondary)]" style={{ color: 'var(--color-text-secondary)' }}>Assistant</Link>
            <Link to="/cves" onClick={() => setMenuOpen(false)} className="text-sm py-2 px-3 rounded-lg hover:bg-[var(--color-surface-secondary)]" style={{ color: 'var(--color-text-secondary)' }}>CVE</Link>
            <div className="separator my-1" />
            <Link to="/assets" onClick={() => setMenuOpen(false)} className="text-sm py-2 px-3 rounded-lg hover:bg-[var(--color-surface-secondary)]" style={{ color: 'var(--color-text-disabled)' }}>Assets</Link>
            <Link to="/organization" onClick={() => setMenuOpen(false)} className="text-sm py-2 px-3 rounded-lg hover:bg-[var(--color-surface-secondary)]" style={{ color: 'var(--color-text-disabled)' }}>Organisation</Link>
            <Link to="/settings" onClick={() => setMenuOpen(false)} className="text-sm py-2 px-3 rounded-lg hover:bg-[var(--color-surface-secondary)]" style={{ color: 'var(--color-text-disabled)' }}>Parametres</Link>
          </nav>
        )}

        <Outlet />

        <footer className="py-8 border-t mt-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs" style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-disabled)' }}>
          <div className="flex items-center gap-3">
            <span style={{ color: 'var(--color-text-secondary)' }}>HashCode Decision OS</span>
            <span className="w-1 h-1 rounded-full" style={{ background: 'var(--color-border)' }} />
            <Link to="/about" className="hover:text-[var(--color-text)] transition">A propos</Link>
          </div>
          <span>Decision Engine · NVD · Exploit-DB · EPSS · CISA KEV</span>
        </footer>
      </div>
    </div>
  )
}
