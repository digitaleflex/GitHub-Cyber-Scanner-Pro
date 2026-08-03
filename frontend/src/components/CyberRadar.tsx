import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Radar, ResponsiveContainer, Tooltip,
} from 'recharts'
import { useStats, useRepos } from '../lib/api'
import { Shield, Activity, Star, Code2, HardDrive, AlertTriangle } from 'lucide-react'

export default function CyberRadar() {
  const { data: stats, isLoading: statsLoading } = useStats()
  const { data: repoData } = useRepos()

  if (statsLoading || !stats) {
    return (
      <div className="glass-card rounded-2xl p-5">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2"><Activity size={14} className="text-cyan-400" />Vue 360</h2>
        <div className="h-72 bg-slate-800/50 rounded animate-pulse" />
      </div>
    )
  }

  const repos = repoData?.repos ?? []
  const avgStars = repos.length > 0 ? Math.round(repos.reduce((s, r) => s + r.stars, 0) / repos.length) : 0
  const recentActivity = repos.filter((r) => Date.now() - new Date(r.updated).getTime() < 90 * 86400000).length
  const scoredRepos = repos.filter((r) => r.security_verdict).length
  const maxStars = Math.max(...repos.map((r) => r.stars), 1)

  const dimensions = [
    { key: 'stars', label: 'Stars', value: Math.min(100, Math.round((avgStars / Math.max(5000, maxStars)) * 100)), icon: Star, raw: avgStars.toLocaleString() },
    { key: 'securite', label: 'Securite', value: Math.round((scoredRepos / Math.max(repos.length, 1)) * 100), icon: Shield, raw: `${scoredRepos}/${repos.length}` },
    { key: 'langages', label: 'Langages', value: Math.min(100, stats.languages * 8), icon: Code2, raw: `${stats.languages} lang` },
    { key: 'activite', label: 'Activite', value: Math.min(100, Math.round((recentActivity / Math.max(repos.length, 1)) * 100)), icon: Activity, raw: `${recentActivity} recents` },
    { key: 'volume', label: 'Volume', value: Math.min(100, Math.round(Math.log2(repos.length + 1) * 10)), icon: HardDrive, raw: `${stats.total_repos} repos` },
    { key: 'alertes', label: 'Alertes', value: Math.max(0, 100 - Math.min(100, (stats.security_critique + stats.security_suspect) * 5)), icon: AlertTriangle, raw: `${stats.security_critique + stats.security_suspect} alertes` },
  ]

  const chartData = dimensions.map((d) => ({ metric: d.label, value: d.value }))

  return (
    <div className="glass-card rounded-2xl p-4 sm:p-5">
      <h2 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
        <Activity size={14} className="text-cyan-400" />Vue 360 — Cyber Posture
      </h2>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 h-52 md:h-72">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={chartData} margin={{ top: 10, right: 30, bottom: 10, left: 10 }}>
              <PolarGrid stroke="rgba(99, 102, 241, 0.12)" strokeDasharray="3 3" />
              <PolarAngleAxis dataKey="metric" tick={{ fill: '#6b7280', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }} axisLine={{ stroke: 'rgba(99, 102, 241, 0.08)' }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={{ stroke: 'rgba(99, 102, 241, 0.06)' }} />
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(99, 102, 241, 0.2)', borderRadius: '8px', color: '#e2e8f0', fontSize: '12px' }} formatter={(value: number) => [`${value}%`, 'Score']} />
              <Radar name="Posture" dataKey="value" stroke="#818cf8" strokeWidth={1.5} fill="#6366f1" fillOpacity={0.15} animationDuration={800} animationBegin={100} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
        <div className="flex flex-col gap-2 justify-center">
          {dimensions.map((d, i) => {
            const Icon = d.icon
            const barColor = d.value >= 70 ? 'bg-indigo-400' : d.value >= 40 ? 'bg-amber-400' : 'bg-rose-400'
            const textColor = d.value >= 70 ? 'text-indigo-400' : d.value >= 40 ? 'text-amber-400' : 'text-rose-400'
            return (
              <div key={d.key} className="animate-slide flex items-center gap-3 text-xs" style={{ animationDelay: `${i * 60}ms` }}>
                <Icon size={12} className={`${textColor} shrink-0`} />
                <span className="text-slate-500 w-16 shrink-0 font-mono">{d.label}</span>
                <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden"><div className={`h-full rounded-full ${barColor} transition-all duration-1000`} style={{ width: `${d.value}%` }} /></div>
                <span className={`${textColor} font-mono w-16 text-right`}>{d.raw}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
