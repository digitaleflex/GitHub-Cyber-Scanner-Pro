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
      <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan">
        <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
          <Activity size={14} />
          <span>Vue 360</span>
        </h2>
        <div className="h-72 bg-white/5 rounded animate-pulse" />
      </div>
    )
  }

  const repos = repoData?.repos ?? []
  const avgStars = repos.length > 0
    ? Math.round(repos.reduce((s, r) => s + r.stars, 0) / repos.length)
    : 0

  const recentActivity = repos.filter((r) => {
    const d = new Date(r.updated)
    return Date.now() - d.getTime() < 90 * 86400000
  }).length

  const scoredRepos = repos.filter((r) => r.security_verdict).length
  const maxStars = Math.max(...repos.map((r) => r.stars), 1)

  const dimensions = [
    {
      key: 'stars',
      label: 'Stars',
      value: Math.min(100, Math.round((avgStars / Math.max(5000, maxStars)) * 100)),
      icon: Star,
      raw: avgStars.toLocaleString(),
    },
    {
      key: 'securite',
      label: 'Sécurité',
      value: Math.round((scoredRepos / Math.max(repos.length, 1)) * 100),
      icon: Shield,
      raw: `${scoredRepos}/${repos.length}`,
    },
    {
      key: 'langages',
      label: 'Langages',
      value: Math.min(100, stats.languages * 8),
      icon: Code2,
      raw: `${stats.languages} lang`,
    },
    {
      key: 'activite',
      label: 'Activité',
      value: Math.min(100, Math.round((recentActivity / Math.max(repos.length, 1)) * 100)),
      icon: Activity,
      raw: `${recentActivity} récents`,
    },
    {
      key: 'volume',
      label: 'Volume',
      value: Math.min(100, Math.round(Math.log2(repos.length + 1) * 10)),
      icon: HardDrive,
      raw: `${stats.total_repos} repos`,
    },
    {
      key: 'alertes',
      label: 'Alertes',
      value: Math.max(0, 100 - Math.min(100,
        (stats.security_critique + stats.security_suspect) * 5)),
      icon: AlertTriangle,
      raw: `${stats.security_critique + stats.security_suspect} alertes`,
    },
  ]

  const chartData = dimensions.map((d) => ({ metric: d.label, value: d.value }))

  return (
    <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan hover:neon-glow-cyan transition-all duration-500">
      <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider mb-4 flex items-center gap-2">
        <Activity size={14} />
        <span>Vue 360° — Cyber Posture</span>
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 h-72 animate-fade-in-up">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={chartData} margin={{ top: 10, right: 30, bottom: 10, left: 10 }}>
              <PolarGrid
                stroke="rgba(0, 240, 255, 0.12)"
                strokeDasharray="3 3"
              />
              <PolarAngleAxis
                dataKey="metric"
                tick={{ fill: '#6b7280', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }}
                axisLine={{ stroke: 'rgba(0, 240, 255, 0.08)' }}
              />
              <PolarRadiusAxis
                angle={30}
                domain={[0, 100]}
                tick={false}
                axisLine={{ stroke: 'rgba(0, 240, 255, 0.06)' }}
              />
              <Tooltip
                contentStyle={{
                  background: '#0d1225',
                  border: '1px solid rgba(0, 240, 255, 0.2)',
                  borderRadius: '8px',
                  color: '#00f0ff',
                  fontSize: '12px',
                  fontFamily: 'JetBrains Mono, monospace',
                  boxShadow: '0 0 20px rgba(0, 240, 255, 0.1)',
                }}
                formatter={(value: number) => [`${value}%`, 'Score']}
              />
              <defs>
                <linearGradient id="radarGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00f0ff" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#00f0ff" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <Radar
                name="Posture"
                dataKey="value"
                stroke="#00f0ff"
                strokeWidth={1.5}
                fill="url(#radarGradient)"
                fillOpacity={0.3}
                animationDuration={800}
                animationBegin={100}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        <div className="flex flex-col gap-2 justify-center">
          {dimensions.map((d, i) => {
            const Icon = d.icon
            const barColor = d.value >= 70
              ? 'bg-neon-cyan'
              : d.value >= 40
                ? 'bg-neon-amber'
                : 'bg-neon-red'
            const textColor = d.value >= 70
              ? 'text-neon-cyan'
              : d.value >= 40
                ? 'text-neon-amber'
                : 'text-neon-red'
            return (
              <div
                key={d.key}
                className="animate-fade-in-up flex items-center gap-3 text-xs"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <Icon size={12} className={`${textColor} shrink-0`} />
                <span className="text-gray-500 w-16 shrink-0 font-mono">{d.label}</span>
                <div className="flex-1 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${barColor} transition-all duration-1000`}
                    style={{ width: `${d.value}%`, boxShadow: d.value > 50 ? '0 0 8px rgba(0,240,255,0.3)' : 'none' }}
                  />
                </div>
                <span className={`${textColor} font-mono w-16 text-right`}>{d.raw}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
