import { useReports, useStats } from '../lib/api'
import { Clock, FileText, BarChart3, AlertTriangle } from 'lucide-react'

export default function ActivityFeed() {
  const { data: reports } = useReports()
  const { data: stats } = useStats()

  const allItems = [
    ...(reports?.dashboards ?? []).map((n) => ({
      type: 'dashboard' as const,
      name: n,
      date: n.replace('dashboard_', '').replace('.html', ''),
    })),
    ...(reports?.reports ?? []).map((n) => ({
      type: 'report' as const,
      name: n,
      date: n.replace('rapport_', '').replace('.md', ''),
    })),
  ].sort((a, b) => b.date.localeCompare(a.date)).slice(0, 8)

  if (allItems.length === 0 && !stats) return null

  return (
    <div className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-5 hover:bg-white/[0.06] hover:-translate-y-0.5 transition-all duration-300">
      <h2 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
        <Clock size={14} />
        Activité
      </h2>

      <div className="space-y-0.5">
        {stats?.status?.includes('en cours') && (
          <div className="flex items-center gap-3 py-2.5 text-sm animate-pulse">
            <span className="w-2 h-2 rounded-full bg-green-400 shrink-0" />
            <span className="text-green-400 font-medium">Scan en cours...</span>
          </div>
        )}

        {stats && (stats.security_critique > 0 || stats.security_suspect > 0) && (
          <div className="flex items-center gap-3 py-2.5 text-sm">
            <AlertTriangle size={14} className="text-red-400 shrink-0" />
            <span className="text-gray-400">
              <span className="text-red-400 font-medium">{stats.security_critique}</span>
              {' critique, '}
              <span className="text-yellow-400 font-medium">{stats.security_suspect}</span>
              {' suspect'}
            </span>
          </div>
        )}

        {allItems.map((item) => {
          const Icon = item.type === 'dashboard' ? BarChart3 : FileText
          const iconColor = item.type === 'dashboard' ? 'text-indigo-400' : 'text-gray-500'
          const label = item.date.replace(/_/g, ' ').slice(0, 16)
          return (
            <div key={item.name} className="flex items-center gap-3 py-2 text-sm">
              <Icon size={14} className={`${iconColor} shrink-0`} />
              <span className="text-gray-500">{label}</span>
              <span className="text-gray-600 text-xs ml-auto">{item.type === 'dashboard' ? 'Dashboard' : 'Rapport'}</span>
            </div>
          )
        })}
      </div>

      {allItems.length === 0 && (
        <p className="text-gray-600 text-sm py-4 text-center">Aucune activité récente</p>
      )}
    </div>
  )
}
