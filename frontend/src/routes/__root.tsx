import { useState, useCallback } from 'react'
import { Link, Outlet, createRootRoute, useRouter } from '@tanstack/react-router'
import { Menu, X, Play } from 'lucide-react'
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
        <div className="hidden sm:flex items-center gap-1.5 text-xs">
          <span className={`w-1.5 h-1.5 rounded-full ${isScanning ? 'bg-green-400 animate-pulse' : 'bg-gray-600'}`} />
          <span className="text-gray-500">{isScanning ? 'Scan en cours...' : 'Prêt'}</span>
        </div>
      )}
      <button
        onClick={handleScan}
        disabled={isScanning}
        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50"
      >
        <Play size={14} className={isScanning ? 'animate-pulse' : ''} />
        {isScanning ? 'Scan...' : 'Scan'}
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
    <div className="min-h-screen bg-[#0a0e17] text-white">
      <div className="fixed top-0 left-0 w-full h-full pointer-events-none z-0">
        <div className="absolute -top-1/4 -left-1/4 w-1/2 h-1/2 bg-indigo-500/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-1/4 -right-1/4 w-1/2 h-1/2 bg-purple-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <header className="flex items-center justify-between py-6 border-b border-white/[0.06] mb-8">
          <div>
            <h1 className="text-2xl font-extrabold bg-gradient-to-r from-indigo-300 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
              CyberScan
            </h1>
            <p className="text-gray-600 text-sm mt-0.5">
              Veille cybersécurité automatisée
            </p>
          </div>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-6">
            {navLinks.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                className="text-gray-400 hover:text-white transition-colors text-sm font-medium [&.active]:text-indigo-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 rounded"
              >
                {l.label}
              </Link>
            ))}
            <ScanButton />
          </nav>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden text-gray-400 hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 rounded"
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
                className="text-gray-400 hover:text-white transition-colors text-sm font-medium py-2 px-3 rounded-lg hover:bg-white/[0.04] [&.active]:text-indigo-400 [&.active]:bg-indigo-500/10"
              >
                {l.label}
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

        <footer className="py-6 border-t border-white/[0.06] text-center text-gray-700 text-xs">
          CyberScan Pro
        </footer>
      </div>
    </div>
  )
}
