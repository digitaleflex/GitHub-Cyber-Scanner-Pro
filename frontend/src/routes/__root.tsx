import { Suspense } from 'react'
import { Outlet, createRootRoute } from '@tanstack/react-router'
import { Sidebar } from '../components/Sidebar'
import { TopBar } from '../components/TopBar'
import { CyberLoader } from '../components/CyberLoader'
import useSearchHotkey from '../lib/useSearchHotkey'
import NotFound from './not-found'

export const Route = createRootRoute({
  component: RootLayout,
  notFoundComponent: NotFound,
})

function RootLayout() {
  useSearchHotkey()
  return (
    <div className="min-h-screen flex" style={{ background: 'var(--bg)' }}>
      <Sidebar />
      <div className="flex-1 flex flex-col" style={{ marginLeft: '240px' }}>
        <TopBar title="Poste de contrôle" />
        <main className="flex-1 p-6 overflow-auto animate-fade">
          <Suspense fallback={<CyberLoader text="Chargement..." />}>
            <Outlet />
          </Suspense>
        </main>
      </div>
    </div>
  )
}
