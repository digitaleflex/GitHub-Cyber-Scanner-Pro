import { useStats } from '../lib/api'

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
  const maxCount = entries[0]?.[1] ?? 1

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

  return (
    <div className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-5 hover:bg-white/[0.06] hover:-translate-y-0.5 transition-all duration-300">
      <h2 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-4">
        Langages
      </h2>
      <div className="space-y-2">
        {entries.map(([lang, count], i) => (
          <div key={lang} className="flex items-center gap-3 animate-fade-in-up" style={{ animationDelay: `${i * 60}ms` }}>
            <span className="text-gray-400 text-sm w-20 truncate shrink-0">{lang}</span>
            <div className="flex-1 h-2 bg-white/[0.06] rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${Math.max(3, (count / maxCount) * 100)}%`,
                  backgroundColor: COLORS[i % COLORS.length],
                }}
              />
            </div>
            <span className="text-gray-500 text-xs w-8 text-right shrink-0">{count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
