import { useState, useCallback } from 'react'
import { Link, Outlet, createRootRoute, useRouter } from '@tanstack/react-router'
import { Menu, X, Play, Shield, Download, Settings } from 'lucide-react'
import { useScanStatus } from '../lib/api'
import { isAdminAuthenticated, getAuthHeaders } from './login'
import useSearchHotkey from '../lib/useSearchHotkey'
import NotFound from './not-found'

export const Route = createRootRoute({ component: RootLayout, notFoundComponent: NotFound })

function ScanBtn() {
  const { data, refetch } = useScanStatus()
  const [scanning, setScanning] = useState(false)
  const router = useRouter()
  const isAdmin = isAdminAuthenticated()
  const isScanning = scanning || data?.status?.includes('en cours')
  const handleScan = useCallback(async () => {
    if (isScanning || !isAdmin) return; setScanning(true)
    try {
      const headers = getAuthHeaders()
      const res = await fetch('/api/scan', { method: 'POST', headers })
      if (res.ok) { setTimeout(() => { refetch(); router.invalidate() }, 1000) }
    } catch {}
    setTimeout(() => setScanning(false), 2000)
  }, [isScanning, refetch, router, isAdmin])
  if (!isAdmin) return null
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
            <Link to="/" className="px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition [&.active]:text-indigo-400 [&.active]:bg-indigo-500/10">Explorer</Link>
            <Link to="/tools" className="px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition [&.active]:text-indigo-400 [&.active]:bg-indigo-500/10">Outils</Link>
            <Link to="/osint" className="px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition [&.active]:text-indigo-400 [&.active]:bg-indigo-500/10">OSINT</Link>
            <Link to="/search" className="px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition [&.active]:text-indigo-400">Recherche</Link>
            <Link to="/labs" className="px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition [&.active]:text-violet-400">AI Lab</Link>
            <Link to="/features" className="px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition [&.active]:text-emerald-400">Fonctionnalites</Link>
            <Link to="/pricing" className="px-3 py-1.5 text-xs text-amber-400 hover:text-white hover:bg-amber-500/10 rounded-lg transition border border-amber-500/10">Pro</Link>
            {isAdminAuthenticated() && (
              <Link to="/admin" className="px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition [&.active]:text-amber-400 flex items-center gap-1">
                <Settings size={11} /> Admin
              </Link>
            )}
            <a href="/api/download" className="flex items-center gap-1 px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition">
              <Download size={11} /> Rapport
            </a>
          </nav>

          <div className="flex items-center gap-2 sm:gap-3">
            <ScanBtn />
            <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden text-slate-400 hover:text-white p-1">
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </header>

        {menuOpen && (
          <nav className="md:hidden flex flex-col gap-1 pb-4 -mt-1 mb-4 glass rounded-xl p-2 animate-fade">
            <Link to="/" onClick={() => setMenuOpen(false)} className="text-xs text-slate-300 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5">Explorer</Link>
            <Link to="/tools" onClick={() => setMenuOpen(false)} className="text-xs text-slate-300 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5">Outils</Link>
            <Link to="/osint" onClick={() => setMenuOpen(false)} className="text-xs text-slate-300 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5">OSINT</Link>
            <Link to="/search" onClick={() => setMenuOpen(false)} className="text-xs text-slate-300 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5">Recherche avancee</Link>
            <Link to="/labs" onClick={() => setMenuOpen(false)} className="text-xs text-slate-300 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5">AI Lab</Link>
            <Link to="/features" onClick={() => setMenuOpen(false)} className="text-xs text-slate-300 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5">Fonctionnalites</Link>
            <Link to="/pricing" onClick={() => setMenuOpen(false)} className="text-xs text-amber-400 hover:text-amber-300 py-2 px-3 rounded-lg hover:bg-amber-500/10">Pro — a partir de 29€</Link>
            {isAdminAuthenticated() && (
              <Link to="/admin" onClick={() => setMenuOpen(false)} className="text-xs text-slate-300 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5 flex items-center gap-1.5"><Settings size={11} /> Admin</Link>
            )}
            <a href="/api/download" onClick={() => setMenuOpen(false)} className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5"><Download size={11} /> Telecharger le rapport</a>
          </nav>
        )}

        <Outlet />

        <footer className="py-8 border-t border-white/[0.03] flex flex-col sm:flex-row items-center justify-between gap-2 text-[10px] sm:text-xs text-slate-600 mt-8">
          <div className="flex items-center gap-3">
            <span>CyberScan Pro v3.1</span>
            <span className="w-1 h-1 rounded-full bg-slate-700" />
            <Link to="/about" className="hover:text-slate-400 transition">A propos</Link>
            <span className="w-1 h-1 rounded-full bg-slate-700" />
            <Link to="/features" className="hover:text-slate-400 transition">Fonctionnalites</Link>
            <span className="w-1 h-1 rounded-full bg-slate-700" />
            <Link to="/pricing" className="hover:text-amber-400 transition">Pro</Link>
          </div>
          <span>Powered by Groq AI + GitHub + NVD + 30 sources</span>
        </footer>
      </div>
    </div>
  )
}
