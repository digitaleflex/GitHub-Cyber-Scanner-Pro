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
    <div className="hidden sm:flex items-center gap-2 glass rounded-full px-3 py-1">
      <User size={11} className="text-emerald-400" />
      <span className="text-[10px] text-slate-400 capitalize">{profile.role || 'non_defini'}</span>
      {org && <><span className="text-slate-700">·</span><Building2 size={11} className="text-slate-500" /><span className="text-[10px] text-slate-500 truncate max-w-[80px]">{org.name}</span></>}
    </div>
  )
}

function Dropdown({ children, items }: { children: React.ReactNode; items: { label: string; to: string; icon?: React.ReactNode }[] }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => { const h = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }; if (open) document.addEventListener('click', h); return () => document.removeEventListener('click', h) }, [open])
  return (
    <div ref={ref} className="relative">
      <button onClick={() => setOpen(!open)} className="flex items-center gap-1 px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition">
        {children} <ChevronDown size={10} className={`transition ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="absolute top-full right-0 mt-1 glass rounded-xl p-1.5 min-w-[160px] shadow-xl z-50 animate-fade">
          {items.map(item => (
            <Link key={item.to} to={item.to as any} onClick={() => setOpen(false)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-slate-400 hover:text-white hover:bg-white/5 transition [&.active]:text-emerald-400">
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
    <div className="min-h-screen text-slate-200">
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 left-1/4 w-1/2 h-96 bg-indigo-500/5 rounded-full blur-[180px]" />
        <div className="absolute bottom-0 right-1/4 w-1/3 h-64 bg-violet-500/5 rounded-full blur-[150px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <header className="flex items-center justify-between py-3 sm:py-4">
          <Link to="/" className="flex items-center gap-2 hover:opacity-80 transition shrink-0">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500/30 to-violet-500/30 border border-indigo-500/20 flex items-center justify-center">
              <Shield size={15} className="text-indigo-400" />
            </div>
            <div className="hidden sm:block">
              <span className="text-sm font-bold tracking-tight text-white">CyberScan</span>
              <span className="text-[9px] text-slate-500 font-mono tracking-wider ml-1">PRO</span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            <Link to="/" className="px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition [&.active]:text-emerald-400 [&.active]:bg-emerald-500/10">Aujourd'hui</Link>
            <Link to="/threats" className="px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition [&.active]:text-rose-400 [&.active]:bg-rose-500/10">Menaces</Link>
            <Link to="/missions" className="px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition [&.active]:text-emerald-400 [&.active]:bg-emerald-500/10">Missions</Link>
            <Link to="/tools" className="px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition [&.active]:text-indigo-400 [&.active]:bg-indigo-500/10">Outils</Link>
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
            <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden text-slate-400 hover:text-white p-1">
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </header>

        {menuOpen && (
          <nav className="md:hidden flex flex-col gap-1 pb-4 -mt-1 mb-4 glass rounded-xl p-2 animate-fade">
            <Link to="/" onClick={() => setMenuOpen(false)} className="text-xs text-slate-300 hover:text-white py-2.5 px-3 rounded-lg hover:bg-white/5 font-medium">Aujourd'hui</Link>
            <Link to="/threats" onClick={() => setMenuOpen(false)} className="text-xs text-slate-300 hover:text-white py-2.5 px-3 rounded-lg hover:bg-white/5">Menaces</Link>
            <Link to="/missions" onClick={() => setMenuOpen(false)} className="text-xs text-slate-300 hover:text-white py-2.5 px-3 rounded-lg hover:bg-white/5">Missions</Link>
            <Link to="/tools" onClick={() => setMenuOpen(false)} className="text-xs text-slate-300 hover:text-white py-2.5 px-3 rounded-lg hover:bg-white/5">Outils</Link>
            <div className="border-t border-white/[0.04] my-1" />
            <Link to="/timeline" onClick={() => setMenuOpen(false)} className="text-xs text-slate-400 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5">Timeline</Link>
            <Link to="/reports" onClick={() => setMenuOpen(false)} className="text-xs text-slate-400 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5">Rapports</Link>
            <Link to="/assistant" onClick={() => setMenuOpen(false)} className="text-xs text-slate-400 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5">Assistant</Link>
            <Link to="/cves" onClick={() => setMenuOpen(false)} className="text-xs text-slate-400 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5">CVE</Link>
            <div className="border-t border-white/[0.04] my-1" />
            <Link to="/assets" onClick={() => setMenuOpen(false)} className="text-xs text-slate-500 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5">Assets</Link>
            <Link to="/organization" onClick={() => setMenuOpen(false)} className="text-xs text-slate-500 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5">Organisation</Link>
            <Link to="/settings" onClick={() => setMenuOpen(false)} className="text-xs text-slate-500 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5">Parametres</Link>
          </nav>
        )}

        <Outlet />

        <footer className="py-8 border-t border-white/[0.03] flex flex-col sm:flex-row items-center justify-between gap-2 text-[10px] sm:text-xs text-slate-500 mt-8">
          <div className="flex items-center gap-3">
            <span>HashCode Decision OS</span>
            <span className="w-1 h-1 rounded-full bg-slate-700" />
            <Link to="/about" className="hover:text-slate-400 transition">À propos</Link>
          </div>
          <span>Decision Engine · NVD · Exploit-DB · EPSS · CISA KEV</span>
        </footer>
      </div>
    </div>
  )
}
