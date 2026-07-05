import { Shield, Star, Code2, Database, type LucideIcon } from 'lucide-react'
import { useStats } from '../lib/api'

function timeAgo(dateStr: string): string {
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diff = now - then
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return "À l'instant"
  if (minutes < 60) return `Il y a ${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `Il y a ${hours}h`
  const days = Math.floor(hours / 24)
  if (days < 7) return `Il y a ${days}j`
  return new Date(dateStr).toLocaleDateString("fr-FR")
}

const cards: {
  key: string
  label: string
  icon: LucideIcon
  value: (data: NonNullable<ReturnType<typeof useStats>["data"]>) => string
}[] = [
  { key: 'total_repos', label: 'Outils trouvés', icon: Shield, value: (d) => d.total_repos.toLocaleString() },
  { key: 'total_stars', label: 'Étoiles totales', icon: Star, value: (d) => d.total_stars.toLocaleString() },
  { key: 'languages', label: 'Langages', icon: Code2, value: (d) => d.languages.toString() },
  { key: 'last_scan', label: 'Dernier scan', icon: Database, value: (d) => d.last_scan ? timeAgo(d.last_scan) : '-' },
]

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

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      {cards.map((card) => (
        <div
          key={card.key}
          className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-5 backdrop-blur-sm hover:bg-white/[0.06] transition-colors"
        >
          <div className="text-indigo-400 mb-3"><card.icon size={24} /></div>
          <div className="text-2xl font-bold text-white">{card.value(data)}</div>
          <div className="text-sm text-gray-500 mt-1">{card.label}</div>
        </div>
      ))}
    </div>
  )
}
