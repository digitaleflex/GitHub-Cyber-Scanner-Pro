import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useReports } from '../lib/api'

function ReportsPage() {
  const { data, isLoading } = useReports()

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Rapports & Dashboards</h2>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-16 bg-white/5 rounded-xl animate-pulse" />
          ))}
        </div>
      ) : !data || (data.reports.length === 0 && data.dashboards.length === 0) ? (
        <div className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-12 text-center">
          <p className="text-gray-600">Aucun rapport généré pour le moment</p>
          <p className="text-gray-700 text-sm mt-2">
            Lance un scan depuis GitHub Actions pour voir les rapports ici
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {data.dashboards.length > 0 && (
            <section>
              <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-4">
                Dashboards
              </h3>
              <div className="flex flex-wrap gap-3">
                {data.dashboards.map((name) => (
                  <a
                    key={name}
                    href={`/dashboards/${name}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-5 py-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-300 hover:bg-indigo-500/20 transition-colors text-sm font-medium"
                  >
                    {name.replace('dashboard_', '').replace('.html', '')}
                  </a>
                ))}
              </div>
            </section>
          )}

          {data.reports.length > 0 && (
            <section>
              <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-4">
                Rapports Markdown
              </h3>
              <div className="flex flex-wrap gap-3">
                {data.reports.map((name) => (
                  <a
                    key={name}
                    href={`/reports/${name}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-5 py-3 bg-white/[0.04] border border-white/[0.1] rounded-xl text-gray-300 hover:bg-white/[0.08] transition-colors text-sm font-medium"
                  >
                    {name.replace('rapport_', '').replace('.md', '')}
                  </a>
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  )
}

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/reports',
  component: ReportsPage,
})
