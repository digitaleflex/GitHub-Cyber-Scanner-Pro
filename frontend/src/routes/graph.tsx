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
      <h2 className="text-lg font-semibold text-white mb-4">Graph Neo4j</h2>
      <GraphView />
    </div>
  )
}
