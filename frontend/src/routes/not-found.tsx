import { Link, createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { Shield, Search } from 'lucide-react'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/not-found',
  component: NotFoundPage,
})

export default function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center py-20 sm:py-24 px-4 text-center animate-fade">
      <Shield size={36} className="text-muted mb-4" />
      <h1 className="h1 mb-2" style={{ color: 'var(--text)' }}>404</h1>
      <p className="body mb-6" style={{ color: 'var(--text-secondary)' }}>Page introuvable</p>
      <div className="flex items-center gap-3">
        <Link to="/" className="btn-primary">Accueil</Link>
        <Link to="/tools" className="btn-secondary flex items-center gap-1.5">
          <Search size={14} /> Explorer les outils
        </Link>
      </div>
    </div>
  )
}
