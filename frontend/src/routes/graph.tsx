import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import GraphView from '../components/GraphView'
import AdminGuard from '../components/AdminGuard'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/graph',
  component: () => <AdminGuard><GraphPage /></AdminGuard>,
})

function GraphPage() {
  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-lg font-semibold text-white mb-1">Knowledge Graph Neo4j</h1>
      <p className="text-xs text-slate-500 mb-4">Relations entre Hackers, APT Campaigns, Outils, CVEs et Repos GitHub.</p>
      <GraphView />
    </div>
  )
}
