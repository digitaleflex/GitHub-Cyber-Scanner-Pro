import { useState, useCallback } from 'react'
import { Link, Outlet, createRootRoute, useRouter } from '@tanstack/react-router'
import { Menu, X, Play, Radio, ChevronRight } from 'lucide-react'
import { startScan, useScanStatus } from '../lib/api'

export const Route = createRootRoute({
  component: RootLayout,
})

function ScanButton() {
  const { data, refetch } = useScanStatus()
  const [scanning, setScanning] = useState(false)
  const router = useRouter()

  const isScanning = scanning || data?.status?.includes('en cours')

  const handleScan = useCallback(async () => {
    if (isScanning) return
    setScanning(true)
    try {
      await startScan()
      setTimeout(() => { refetch(); router.invalidate() }, 1000)
    } catch { /* ignore */ }
    setTimeout(() => setScanning(false), 2000)
  }, [isScanning, refetch, router])

  return (
    <div className="flex items-center gap-3">
      {data?.status && (
        <div className="hidden sm:flex items-center gap-1.5 text-xs font-mono">
          <span className={`w-1.5 h-1.5 rounded-full ${isScanning ? 'bg-neon-green shadow-[0_0_8px_rgba(0,255,102,0.5)] animate-pulse' : 'bg-gray-600'}`} />
          <span className={`${isScanning ? 'text-neon-green' : 'text-gray-600'}`}>
            {isScanning ? 'SCAN EN COURS' : 'PRÊT'}
          </span>
        </div>
      )}
      <button
        onClick={handleScan}
        disabled={isScanning}
        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-neon-cyan/20 to-transparent border border-neon-cyan/30 hover:border-neon-cyan/60 hover:shadow-[0_0_20px_rgba(0,240,255,0.15)] disabled:opacity-40 disabled:cursor-not-allowed text-neon-cyan text-sm font-medium rounded-lg font-mono tracking-wider transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50"
      >
        <Play size={14} className={isScanning ? 'animate-pulse' : ''} />
        {isScanning ? 'SCAN...' : 'LANCER SCAN'}
      </button>
    </div>
  )
}

function RootLayout() {
  const [menuOpen, setMenuOpen] = useState(false)

  const navLinks = [
    { to: '/', label: 'Dashboard' },
    { to: '/reports', label: 'Rapports' },
  ]

  return (
    <div className="min-h-screen text-white scanline-overlay">
      {/* Animated grid background */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 left-1/4 w-1/3 h-1/3 bg-neon-cyan/5 rounded-full blur-[120px] animate-glow-pulse" />
        <div className="absolute bottom-0 right-1/4 w-1/4 h-1/4 bg-neon-magenta/5 rounded-full blur-[120px]" style={{ animationDelay: '1s' }} />
      </div>

      {/* Top decorative bar */}
      <div className="fixed top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-neon-cyan/30 to-transparent z-50" />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <header className="flex items-center justify-between py-5 border-b border-white/[0.06] mb-8">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-neon-cyan/20 to-neon-magenta/20 border border-neon-cyan/20 flex items-center justify-center">
                <Radio size={16} className="text-neon-cyan" />
              </div>
              <div>
                <h1 className="text-xl font-cyber font-bold tracking-wider bg-gradient-to-r from-neon-cyan via-white to-neon-magenta bg-clip-text text-transparent">
                  CyberScan
                </h1>
                <p className="text-gray-700 text-[10px] font-mono tracking-[0.2em] uppercase">
                  Security Operations Center
                </p>
              </div>
            </div>
          </div>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-6">
            {navLinks.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                className="text-gray-500 hover:text-neon-cyan transition-colors text-xs font-mono tracking-wider uppercase [&.active]:text-neon-cyan [&.active]:border-b [&.active]:border-neon-cyan/50 pb-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50 rounded"
              >
                {l.label}
              </Link>
            ))}
            <ScanButton />
          </nav>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden text-gray-400 hover:text-neon-cyan transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50 rounded"
            aria-label={menuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
          >
            {menuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </header>

        {/* Mobile menu */}
        {menuOpen && (
          <nav className="md:hidden flex flex-col gap-2 pb-6 -mt-4 mb-6 border-b border-white/[0.06]">
            {navLinks.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                onClick={() => setMenuOpen(false)}
                className="text-gray-400 hover:text-neon-cyan transition-colors text-xs font-mono tracking-wider uppercase py-2 px-3 rounded-lg hover:bg-white/[0.04] [&.active]:text-neon-cyan [&.active]:bg-neon-cyan/10"
              >
                <div className="flex items-center gap-2">
                  <ChevronRight size={12} className="[&.active]:text-neon-cyan text-transparent" />
                  {l.label}
                </div>
              </Link>
            ))}
            <div className="px-3 pt-2">
              <ScanButton />
            </div>
          </nav>
        )}

        <main className="pb-12">
          <Outlet />
        </main>

        <footer className="py-6 border-t border-white/[0.06] flex items-center justify-between">
          <div className="flex items-center gap-3 text-[10px] font-mono tracking-wider">
            <span className="text-gray-700">CYBERSCAN PRO</span>
            <span className="w-1 h-1 rounded-full bg-gray-800" />
            <span className="text-gray-700">SOC v1.2</span>
            <span className="w-1 h-1 rounded-full bg-gray-800" />
            <span className="text-gray-700 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-neon-green shadow-[0_0_6px_rgba(0,255,102,0.3)]" />
              SYSTEM ONLINE
            </span>
          </div>
          <div className="text-gray-800 text-[10px] font-mono">
            {new Date().toISOString().slice(0, 16).replace('T', ' ')} UTC
          </div>
        </footer>
      </div>
    </div>
  )
}
