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
    <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan hover:neon-glow-cyan transition-all duration-300">
      <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2 font-cyber">
        <Clock size={14} className="text-neon-cyan" />
        Activité
      </h2>

      <div className="space-y-0.5 font-mono text-xs">
        {stats?.status?.includes('en cours') && (
          <div className="flex items-center gap-3 py-2 text-sm animate-pulse">
            <span className="w-2 h-2 rounded-full bg-neon-green shadow-[0_0_8px_rgba(0,255,102,0.5)] shrink-0" />
            <span className="text-neon-green font-medium">Scan en cours...</span>
          </div>
        )}

        {stats && (stats.security_critique > 0 || stats.security_suspect > 0) && (
          <div className="flex items-center gap-3 py-2 text-sm">
            <AlertTriangle size={14} className="text-neon-red shrink-0" />
            <span className="text-gray-400 font-mono text-xs">
              <span className="text-neon-red font-medium">{stats.security_critique}</span>
              {' critique, '}
              <span className="text-neon-amber font-medium">{stats.security_suspect}</span>
              {' suspect'}
            </span>
          </div>
        )}

        {allItems.map((item) => {
          const Icon = item.type === 'dashboard' ? BarChart3 : FileText
          const label = item.date.replace(/_/g, ' ').slice(0, 16)
          return (
            <div key={item.name} className="flex items-center gap-3 py-1.5 text-xs group">
              <Icon size={12} className="text-neon-cyan/60 group-hover:text-neon-cyan transition-colors shrink-0" />
              <span className="text-gray-500 group-hover:text-gray-300 transition-colors">{label}</span>
              <span className="text-gray-700 text-[10px] ml-auto uppercase tracking-wider">{item.type === 'dashboard' ? 'Dashboard' : 'Rapport'}</span>
            </div>
          )
        })}
      </div>

      {allItems.length === 0 && (
        <p className="text-gray-600 text-xs py-4 text-center font-mono">Aucune activité récente</p>
      )}

      <div className="mt-3 pt-3 border-t border-white/[0.04] flex items-center gap-2 text-[10px] text-gray-700 font-mono">
        <span className="w-1 h-1 rounded-full bg-neon-cyan/40" />
        <span className="tracking-wider">SYSTEM READY</span>
        <span className="w-1 h-1 rounded-full bg-neon-cyan/40 animate-glow-pulse" />
        <span className="tracking-wider ml-1">{allItems.length} ENREGISTREMENTS</span>
      </div>
    </div>
  )
}
