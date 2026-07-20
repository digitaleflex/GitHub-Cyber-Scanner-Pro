import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import CveTable from '../components/CveTable'

function CvesPage() {
  return (
    <div>
      <CveTable />
    </div>
  )
}

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/cves',
  component: CvesPage,
})
