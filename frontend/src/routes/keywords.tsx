import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import KeywordsTable from '../components/KeywordsTable'

function KeywordsPage() {
  return (
    <div>
      <KeywordsTable />
    </div>
  )
}

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/keywords',
  component: KeywordsPage,
})
