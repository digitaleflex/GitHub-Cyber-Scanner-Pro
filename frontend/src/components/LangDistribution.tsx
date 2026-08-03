import { useStats } from '../lib/api'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

const COLORS = [
  '#00f0ff', '#ff00aa', '#00ff66', '#ffbb00',
  '#ff0044', '#8b5cf6', '#ec4899', '#14b8a6',
]

export default function LangDistribution() {
  const { data, isLoading, error } = useStats()

  if (isLoading) {
    return (
      <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan">
        <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider mb-4 font-cyber">
          Langages
        </h2>
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-6 bg-white/5 rounded mb-2 animate-pulse" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan">
        <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider mb-4 font-cyber">
          Langages
        </h2>
        <p className="text-neon-red text-sm py-4 text-center font-mono" role="alert">Erreur de chargement</p>
      </div>
    )
  }

  const dist = data?.lang_distribution ?? {}
  const entries = Object.entries(dist).sort((a, b) => b[1] - a[1]).slice(0, 8)

  if (entries.length === 0) {
    return (
      <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan">
        <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider mb-4 font-cyber">
          Langages
        </h2>
        <p className="text-slate-500 text-sm py-4 text-center font-mono">Aucune donnée</p>
      </div>
    )
  }

  const chartData = entries.map(([lang, count]) => ({ lang, count }))

  return (
    <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan hover:neon-glow-cyan transition-all duration-300">
      <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider mb-4 font-cyber">
        Langages
      </h2>
      <div className="animate-fade-in-up">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 0, right: 0, top: 0, bottom: 0 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="lang"
              tick={{ fill: '#6b7280', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' }}
              axisLine={false}
              tickLine={false}
              width={80}
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
              formatter={(value: number) => [`${value} repos`, 'Nombre']}
            />
            <defs>
              {chartData.map((_, i) => (
                <linearGradient key={`grad-${i}`} id={`barGlow-${i}`} x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0.6} />
                  <stop offset="100%" stopColor={COLORS[i % COLORS.length]} stopOpacity={0.9} />
                </linearGradient>
              ))}
            </defs>
            <Bar
              dataKey="count"
              radius={[0, 4, 4, 0]}
              animationDuration={800}
              animationBegin={0}
              maxBarSize={20}
            >
              {chartData.map((entry, i) => (
                <Cell
                  key={entry.lang}
                  fill={`url(#barGlow-${i})`}
                  style={{ filter: `drop-shadow(0 0 6px ${COLORS[i % COLORS.length]}40)` }}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
