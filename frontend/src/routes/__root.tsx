import { Suspense, useState, useCallback } from 'react'
import { Link, Outlet, createRootRoute, useRouter } from '@tanstack/react-router'
import { Shield, Target, Wrench, Rocket, BookOpen, Bug, Clock, Sparkles, Settings, HelpCircle, Activity, Menu, X } from 'lucide-react'
import { useScanStatus } from '../lib/api'
import useSearchHotkey from '../lib/useSearchHotkey'
import NotFound from './not-found'
import { CyberLoader } from '../components/CyberLoader'

export const Route = createRootRoute({
  component: RootLayout,
  notFoundComponent: NotFound,
})

const NAV_ITEMS = [
  { to: '/', label: "Aujourd'hui", icon: Shield },
  { to: '/threats', label: 'Menaces', icon: Target },
  { to: '/tools', label: 'Outils', icon: Wrench },
  { to: '/missions', label: 'Missions', icon: Rocket },
  { to: '/cves', label: 'CVE', icon: Bug },
  { to: '/library', label: 'Biblio', icon: BookOpen },
]

function ScanBtn() {
  const { data, refetch } = useScanStatus()
  const router = useRouter()
  const [scanning, setScanning] = useState(false)
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
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all active:scale-[0.98] shrink-0"
      style={{
        background: isScanning ? 'var(--surface-elevated)' : 'var(--amber)',
        color: isScanning ? 'var(--text-secondary)' : 'var(--text-inverse)',
        border: isScanning ? '1px solid var(--border)' : 'none',
      }}
    >
      <Activity size={13} className={isScanning ? 'animate-spin-scan' : ''} />
      <span className="hidden sm:inline">{isScanning ? 'Scan...' : 'Scanner'}</span>
    </button>
  )
}

function NavBar() {
  const router = useRouter()
  const pathname = router.state.location.pathname
  const [menuOpen, setMenuOpen] = useState(false)

  const isActive = (to: string) => {
    if (to === '/') return pathname === '/'
    return pathname.startsWith(to)
  }

  return (
    <header
      className="sticky top-0 z-50"
      style={{
        background: 'var(--surface)',
        borderBottom: '1px solid var(--border)',
        boxShadow: '0 1px 12px rgba(0,0,0,0.2)',
      }}
    >
      <div className="px-4 sm:px-6 h-14 flex items-center gap-2 sm:gap-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 shrink-0" style={{ textDecoration: 'none' }}>
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs"
            style={{ background: 'var(--amber)', color: 'var(--text-inverse)' }}
          >
            H
          </div>
          <div className="hidden sm:block">
            <div className="font-display text-h2" style={{ lineHeight: 1, color: 'var(--text)' }}>HashCode</div>
            <div className="text-caption t-m">Cockpit</div>
          </div>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center justify-center gap-0.5 flex-1" role="navigation">
          {NAV_ITEMS.map((item) => {
            const active = isActive(item.to)
            const Icon = item.icon
            return (
              <Link
                key={item.to}
                to={item.to as any}
                className="relative flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all"
                style={{
                  background: active ? 'var(--surface-elevated)' : 'transparent',
                  color: active ? 'var(--text)' : 'var(--text-secondary)',
                }}
              >
                <Icon size={14} style={{ color: active ? 'var(--amber)' : 'var(--text-muted)' }} />
                {item.label}
                {active && (
                  <div
                    className="absolute bottom-0 left-1/2 -translate-x-1/2"
                    style={{ width: 16, height: 3, background: 'var(--amber)', borderRadius: '2px 2px 0 0' }}
                  />
                )}
              </Link>
            )
          })}
        </nav>

        {/* Right side */}
        <div className="flex items-center gap-2 sm:gap-3 ml-auto shrink-0">
          <div className="hidden lg:flex items-center gap-3 text-caption t-m">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--lime)' }} /> NVD
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--lime)' }} /> CISA
            </span>
          </div>
          <div className="hidden sm:block font-mono text-mono t-s">
            {new Date().toISOString().slice(11, 16)} UTC
          </div>
          <ScanBtn />

          {/* Mobile hamburger */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden p-2 rounded-lg transition-colors hover:bg-[var(--surface-elevated)]"
            aria-label={menuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
          >
            {menuOpen ? <X size={18} style={{ color: 'var(--text)' }} /> : <Menu size={18} style={{ color: 'var(--text-secondary)' }} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <nav
          className="md:hidden px-4 py-3 space-y-1 animate-fade"
          style={{ background: 'var(--surface-elevated)', borderTop: '1px solid var(--border)' }}
        >
          {NAV_ITEMS.map((item) => {
            const active = isActive(item.to)
            const Icon = item.icon
            return (
              <Link
                key={item.to}
                to={item.to as any}
                onClick={() => setMenuOpen(false)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all"
                style={{
                  background: active ? 'var(--surface-elevated)' : 'transparent',
                  color: active ? 'var(--text)' : 'var(--text-secondary)',
                  borderLeft: active ? '3px solid var(--amber)' : '3px solid transparent',
                }}
              >
                <Icon size={16} style={{ color: active ? 'var(--amber)' : 'var(--text-muted)' }} />
                {item.label}
              </Link>
            )
          })}
          <div style={{ height: 1, background: 'var(--border)', margin: '8px 0' }} />
          <Link to="/timeline" onClick={() => setMenuOpen(false)}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium t-s">
            <Clock size={16} className="t-m" /> Timeline
          </Link>
          <Link to="/assistant" onClick={() => setMenuOpen(false)}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium t-s">
            <Sparkles size={16} className="t-m" /> Assistant
          </Link>
          <Link to="/settings" onClick={() => setMenuOpen(false)}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium t-s">
            <Settings size={16} className="t-m" /> Paramètres
          </Link>
          <Link to="/docs" onClick={() => setMenuOpen(false)}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium t-s">
            <HelpCircle size={16} className="t-m" /> Documentation
          </Link>
        </nav>
      )}
    </header>
  )
}

function RootLayout() {
  useSearchHotkey()
  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg)' }}>
      <NavBar />
      <main className="flex-1 p-4 sm:p-6 animate-fade" style={{ maxWidth: '1440px', margin: '0 auto', width: '100%' }}>
        <Suspense fallback={<CyberLoader text="Chargement..." />}>
          <Outlet />
        </Suspense>
      </main>
      <footer
        className="mt-auto py-4 px-6"
        style={{ borderTop: '1px solid var(--border)', background: 'var(--surface)' }}
      >
        <div className="flex flex-wrap items-center justify-between gap-3" style={{ maxWidth: '1440px', margin: '0 auto', width: '100%' }}>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-caption">
            <span className="font-display font-semibold t-amber">HashCode</span>
            <Link to="/about" className="t-m hover:underline" style={{ textDecoration: 'none' }}>À propos</Link>
            <Link to="/onboarding" className="t-m hover:underline" style={{ textDecoration: 'none' }}>Configurer</Link>
            <Link to="/docs" className="t-m hover:underline" style={{ textDecoration: 'none' }}>Documentation</Link>
            <Link to="/contact" className="t-m hover:underline" style={{ textDecoration: 'none' }}>Contact</Link>
          </div>
          <div className="text-caption t-m">
            <a href="https://nvd.nist.gov/" className="hover:underline">NVD</a> · <a href="https://attack.mitre.org/" className="hover:underline">MITRE</a> · <a href="https://www.cisa.gov/known-exploited-vulnerabilities-catalog" className="hover:underline">CISA KEV</a> · <a href="https://groq.com/" className="hover:underline">Groq</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
