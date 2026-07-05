import { useStats } from '../lib/api'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

const COLORS = [
  '#6366f1', '#10b981', '#f59e0b', '#ef4444',
  '#06b6d4', '#8b5cf6', '#ec4899', '#14b8a6',
]

export default function LangDistribution() {
  const { data, isLoading } = useStats()

  if (isLoading) {
    return (
      <div className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-5">
        <h2 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-4">
          Langages
        </h2>
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-6 bg-white/5 rounded mb-2 animate-pulse" />
        ))}
      </div>
    )
  }

  const dist = data?.lang_distribution ?? {}
  const entries = Object.entries(dist).sort((a, b) => b[1] - a[1]).slice(0, 8)

  if (entries.length === 0) {
    return (
      <div className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-5">
        <h2 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-4">
          Langages
        </h2>
        <p className="text-gray-600 text-sm py-4 text-center">Aucune donnée</p>
      </div>
    )
  }

  const chartData = entries.map(([lang, count]) => ({ lang, count }))

  return (
    <div className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-5 hover:bg-white/[0.06] hover:-translate-y-0.5 transition-all duration-300">
      <h2 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-4">
        Langages
      </h2>
      <div className="animate-fade-in-up">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 0, right: 0, top: 0, bottom: 0 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="lang"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              width={80}
            />
            <Tooltip
              contentStyle={{
                background: '#1a1f2e',
                border: '1px solid rgba(255,255,255,0.06)',
                borderRadius: '8px',
                color: '#e5e7eb',
                fontSize: '13px',
              }}
              formatter={(value: number) => [`${value} repos`, 'Nombre']}
            />
            <Bar dataKey="count" radius={[0, 6, 6, 0]} animationDuration={600} animationBegin={0}>
              {chartData.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
