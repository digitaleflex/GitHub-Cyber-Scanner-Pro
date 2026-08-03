import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useReports } from '../lib/api'
import AdminGuard from '../components/AdminGuard'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import { FileText, ExternalLink, FolderOpen } from 'lucide-react'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/reports',
  component: () => <AdminGuard><ReportsPage /></AdminGuard>,
})

function ReportsPage() {
  const { data, isLoading, error, refetch } = useReports()

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-lg font-semibold text-white mb-4">Rapports</h1>
      {isLoading ? (
        <div className="space-y-2" role="status">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-14 bg-white/5 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <div className="glass-card rounded-2xl">
          <ErrorState compact onRetry={() => refetch()} />
        </div>
      ) : data?.reports?.length ? (
        <div className="space-y-2">
          {data.reports.map((r: any, i: number) => (
            <a key={i} href={r.url || '#'} target="_blank" rel="noopener"
              className="flex items-center gap-3 bg-slate-900/60 border border-slate-800 rounded-lg p-3 hover:border-slate-700 transition">
              <FileText size={16} className="text-slate-500" />
              <div className="flex-1">
                <span className="text-sm text-slate-200">{r.name || r.filename || r.title}</span>
                {r.date && <span className="text-[10px] text-slate-500 ml-2">{r.date}</span>}
              </div>
              <ExternalLink size={13} className="text-slate-500" />
            </a>
          ))}
        </div>
      ) : (
        <div className="glass-card rounded-2xl">
          <EmptyState icon={FolderOpen} title="Aucun rapport disponible"
            description="Les rapports seront generes apres les scans et l'enrichissement IA." />
        </div>
      )}
    </div>
  )
}
