import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import GraphView from '../components/GraphView'

function GraphPage() {
  return (
    <div>
      <GraphView />
    </div>
  )
}

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/graph',
  component: GraphPage,
})
