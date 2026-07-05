import { Link, Outlet, createRootRoute } from '@tanstack/react-router'

export const Route = createRootRoute({
  component: RootLayout,
})

function RootLayout() {
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
          <nav className="flex items-center gap-6">
            <Link
              to="/"
              className="text-gray-400 hover:text-white transition-colors text-sm font-medium [&.active]:text-indigo-400"
            >
              Dashboard
            </Link>
            <Link
              to="/reports"
              className="text-gray-400 hover:text-white transition-colors text-sm font-medium [&.active]:text-indigo-400"
            >
              Rapports
            </Link>
          </nav>
        </header>

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
