import { useStats } from '../lib/api'

const cards = [
  { key: 'total_repos', label: 'Outils trouvés', icon: '🛠️' },
  { key: 'total_stars', label: 'Étoiles totales', icon: '⭐' },
  { key: 'languages', label: 'Langages', icon: '🔤' },
  { key: 'total_repos', label: 'Dans la base', icon: '📦' },
] as const

export default function StatsCards() {
  const { data, isLoading, error } = useStats()

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-24 bg-white/5 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="text-red-400 text-sm mb-8 p-4 bg-red-900/20 rounded-xl border border-red-800/30">
        Impossible de charger les statistiques
      </div>
    )
  }

  const values = [
    data.total_repos.toLocaleString(),
    data.total_stars.toLocaleString(),
    data.languages.toString(),
    data.total_repos.toLocaleString(),
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      {cards.map((card, i) => (
        <div
          key={card.key + i}
          className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-5 backdrop-blur-sm hover:bg-white/[0.06] transition-colors"
        >
          <div className="text-2xl mb-2">{card.icon}</div>
          <div className="text-2xl font-bold text-white">{values[i]}</div>
          <div className="text-sm text-gray-500 mt-1">{card.label}</div>
        </div>
      ))}
    </div>
  )
}
