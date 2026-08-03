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
    <div className="glass-card rounded-2xl p-5">
      <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
        <Clock size={14} className="text-cyan-400" />
        Activite
      </h2>

      <div className="space-y-0.5 font-mono text-xs">
        {stats?.status?.includes('en cours') && (
          <div className="flex items-center gap-3 py-2 text-sm animate-pulse">
            <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)] shrink-0" />
            <span className="text-emerald-400 font-medium">Scan en cours...</span>
          </div>
        )}

        {stats && (stats.security_critique > 0 || stats.security_suspect > 0) && (
          <div className="flex items-center gap-3 py-2 text-sm">
            <AlertTriangle size={14} className="text-rose-400 shrink-0" />
            <span className="text-slate-400 font-mono text-xs">
              <span className="text-rose-400 font-medium">{stats.security_critique}</span>
              {' critique, '}
              <span className="text-amber-400 font-medium">{stats.security_suspect}</span>
              {' suspect'}
            </span>
          </div>
        )}

        {allItems.map((item) => {
          const Icon = item.type === 'dashboard' ? BarChart3 : FileText
          const label = item.date.replace(/_/g, ' ').slice(0, 16)
          return (
            <div key={item.name} className="flex items-center gap-3 py-1.5 text-xs group">
              <Icon size={12} className="text-slate-500 group-hover:text-indigo-400 transition-colors shrink-0" />
              <span className="text-slate-500 group-hover:text-slate-300 transition-colors">{label}</span>
              <span className="text-slate-700 text-[10px] ml-auto uppercase tracking-wider">{item.type === 'dashboard' ? 'Dashboard' : 'Rapport'}</span>
            </div>
          )
        })}
      </div>

      {allItems.length === 0 && (
        <p className="text-slate-600 text-xs py-4 text-center">Aucune activite recente</p>
      )}

      <div className="mt-3 pt-3 border-t border-white/[0.04] flex items-center gap-2 text-[10px] text-slate-700">
        <span className="w-1 h-1 rounded-full bg-indigo-400/40" />
        <span className="tracking-wider">SYSTEM READY</span>
        <span className="w-1 h-1 rounded-full bg-indigo-400/40 animate-pulse" />
        <span className="tracking-wider ml-1">{allItems.length} ENREGISTREMENTS</span>
      </div>
    </div>
  )
}
