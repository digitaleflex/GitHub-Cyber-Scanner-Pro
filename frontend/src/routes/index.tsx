import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import StatsCards from '../components/StatsCards'
import TopRepos from '../components/TopRepos'
import LangDistribution from '../components/LangDistribution'
import ReposTable from '../components/ReposTable'
import ActivityFeed from '../components/ActivityFeed'
import CyberRadar from '../components/CyberRadar'
import CyberNews from '../components/CyberNews'

function DashboardPage() {
  return (
    <div>
      <StatsCards />

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
        <div className="lg:col-span-2">
          <TopRepos />
        </div>
        <ActivityFeed />
        <CyberNews />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <LangDistribution />
      </div>

      <div className="mb-8">
        <CyberRadar />
      </div>

      <ReposTable />
    </div>
  )
}

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/',
  component: DashboardPage,
})
