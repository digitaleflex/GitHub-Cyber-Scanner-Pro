import { useState, useCallback, useEffect } from 'react'
import { Link, Outlet, createRootRoute, useRouter } from '@tanstack/react-router'
import { Menu, X, Play, Shield, Download, Star, TrendingUp, AlertTriangle } from 'lucide-react'
import { startScan, useScanStatus, useStats } from '../lib/api'
import { useQuery } from '@tanstack/react-query'

export const Route = createRootRoute({ component: RootLayout })

function useCountUp(target: number, duration = 1500) {
  const [count, setCount] = useState(0)
  useEffect(() => {
    if (!target) return
    let start = 0; const step = Math.ceil(target / (duration / 16))
    const timer = setInterval(() => { start += step; if (start >= target) { setCount(target); clearInterval(timer) } else setCount(start) }, 16)
    return () => clearInterval(timer)
  }, [target, duration])
  return count
}

function ScanBtn() {
  const { data, refetch } = useScanStatus()
  const [scanning, setScanning] = useState(false)
  const router = useRouter()
  const isScanning = scanning || data?.status?.includes('en cours')
  const handleScan = useCallback(async () => {
    if (isScanning) return; setScanning(true)
    try { await startScan(); setTimeout(() => { refetch(); router.invalidate() }, 1000) } catch {}
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
  const { data: stats } = useStats()
  const { data: digest } = useQuery({ queryKey: ['digest-hero'], queryFn: () => fetch('/api/digest').then(r => r.json()), staleTime: 300_000 })

  const repos = useCountUp(stats?.total_repos || 0, 2000)
  const stars = useCountUp(stats?.total_stars || 0, 2500)
  const cves = 56000
  const criticalThreats = digest?.top_threats?.filter((t: any) => t.severity === 'CRITIQUE').length || 0

  return (
    <div className="min-h-screen text-slate-200">
      {/* Background gradients */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 left-1/4 w-1/2 h-96 bg-indigo-500/5 rounded-full blur-[180px]" />
        <div className="absolute bottom-0 right-1/4 w-1/3 h-64 bg-violet-500/5 rounded-full blur-[150px]" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Nav */}
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
            <Link to="/search" className="px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition [&.active]:text-indigo-400">Recherche</Link>
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
            <Link to="/search" onClick={() => setMenuOpen(false)} className="text-xs text-slate-300 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5">Recherche avancee</Link>
            <a href="/api/download" onClick={() => setMenuOpen(false)} className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white py-2 px-3 rounded-lg hover:bg-white/5"><Download size={11} /> Telecharger le rapport</a>
          </nav>
        )}

        {/* Hero section */}
        <section className="py-8 sm:py-16 text-center animate-fade">
          {/* Authority badges */}
          <div className="flex items-center justify-center gap-2 mb-4 sm:mb-6 flex-wrap">
            <span className="glass px-2.5 py-1 rounded-full text-[10px] sm:text-xs text-slate-400 flex items-center gap-1.5">
              <Shield size={10} className="text-indigo-400" /> Groq AI
            </span>
            <span className="glass px-2.5 py-1 rounded-full text-[10px] sm:text-xs text-slate-400 flex items-center gap-1.5">
              <Star size={10} className="text-amber-400" /> GitHub API
            </span>
            <span className="glass px-2.5 py-1 rounded-full text-[10px] sm:text-xs text-slate-400 flex items-center gap-1.5">
              <Shield size={10} className="text-rose-400" /> NVD CVE
            </span>
          </div>

          <h1 className="text-2xl sm:text-4xl lg:text-5xl font-bold tracking-tight mb-3 sm:mb-4">
            <span className="bg-gradient-to-r from-indigo-400 via-white to-violet-400 bg-clip-text text-transparent">
              Veille Cyber Intelligence
            </span>
          </h1>
          <p className="text-sm sm:text-base text-slate-400 max-w-xl mx-auto mb-6 sm:mb-8 leading-relaxed">
            {repos.toLocaleString()}+ outils de securite audites par IA. Decouvrez les menaces du jour, explorez la base de connaissances cyber.
          </p>

          {/* Threat alert */}
          {criticalThreats > 0 && (
            <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full mb-6 sm:mb-8 pulse-ring">
              <AlertTriangle size={14} className="text-rose-400" />
              <span className="text-xs sm:text-sm font-medium text-rose-300">
                {criticalThreats} menace{criticalThreats > 1 ? 's' : ''} critique{criticalThreats > 1 ? 's' : ''} aujourd'hui
              </span>
            </div>
          )}

          {/* Live counters */}
          <div className="grid grid-cols-3 gap-3 sm:gap-6 max-w-lg mx-auto mb-6 sm:mb-8">
            {[
              { label: 'Outils', value: repos.toLocaleString(), icon: <Star size={14} className="text-amber-400" />, delay: '0s' },
              { label: 'Stars', value: stars.toLocaleString(), icon: <TrendingUp size={14} className="text-indigo-400" />, delay: '0.2s' },
              { label: 'CVE', value: cves.toLocaleString(), icon: <Shield size={14} className="text-rose-400" />, delay: '0.4s' },
            ].map((c, i) => (
              <div key={i} className="glass-card rounded-xl p-3 sm:p-4 text-center animate-slide" style={{ animationDelay: c.delay }}>
                <div className="flex justify-center mb-1">{c.icon}</div>
                <div className="text-lg sm:text-2xl font-bold text-white tabular-nums">{c.value}</div>
                <div className="text-[10px] sm:text-xs text-slate-500 mt-0.5">{c.label}</div>
              </div>
            ))}
          </div>

          {/* Search bar */}
          <Outlet />
        </section>

        {/* Footer */}
        <footer className="py-8 border-t border-white/[0.03] flex flex-col sm:flex-row items-center justify-between gap-2 text-[10px] sm:text-xs text-slate-600">
          <div className="flex items-center gap-3">
            <span>CyberScan Pro v2.2</span>
            <span className="w-1 h-1 rounded-full bg-slate-700" />
            <span>https://cyberbook.eurin.tech</span>
          </div>
          <span>Powered by Groq AI + GitHub + NVD</span>
        </footer>
      </div>
    </div>
  )
}
