import { Shield, Star, Code2, AlertTriangle, ShieldAlert, Activity, type LucideIcon } from 'lucide-react'
import { useStats } from '../lib/api'

const cards: {
  key: string
  label: string
  icon: LucideIcon
  value: (data: NonNullable<ReturnType<typeof useStats>["data"]>) => string
  borderClass: string
  glowClass: string
  iconClass: string
  textClass: string
}[] = [
  { key: 'total_repos', label: 'Outils trouvés', icon: Shield,
    value: (d) => d.total_repos.toLocaleString(),
    borderClass: 'hover:neon-glow-cyan', glowClass: 'from-neon-cyan/20 via-neon-cyan/5 to-transparent',
    iconClass: 'text-neon-cyan', textClass: 'text-neon-cyan' },
  { key: 'total_stars', label: 'Étoiles totales', icon: Star,
    value: (d) => d.total_stars.toLocaleString(),
    borderClass: 'hover:neon-glow-magenta', glowClass: 'from-neon-magenta/20 via-neon-magenta/5 to-transparent',
    iconClass: 'text-neon-magenta', textClass: 'text-neon-magenta' },
  { key: 'languages', label: 'Langages', icon: Code2,
    value: (d) => d.languages.toString(),
    borderClass: 'hover:neon-glow-cyan', glowClass: 'from-neon-cyan/20 via-neon-cyan/5 to-transparent',
    iconClass: 'text-neon-cyan', textClass: 'text-neon-cyan' },
  { key: 'avg_vitality', label: 'Vitalité moy.', icon: Activity,
    value: (d) => `${d.avg_vitality}`,
    borderClass: 'hover:neon-glow-cyan', glowClass: 'from-neon-cyan/20 via-neon-cyan/5 to-transparent',
    iconClass: 'text-neon-green', textClass: 'text-neon-green' },
  { key: 'security_critique', label: 'Critique', icon: ShieldAlert,
    value: (d) => d.security_critique.toString(),
    borderClass: 'hover:neon-glow-magenta', glowClass: 'from-neon-red/20 via-neon-red/5 to-transparent',
    iconClass: 'text-neon-red', textClass: 'text-neon-red' },
  { key: 'security_suspect', label: 'Suspect', icon: AlertTriangle,
    value: (d) => d.security_suspect.toString(),
    borderClass: 'hover:neon-glow-cyan', glowClass: 'from-neon-amber/20 via-neon-amber/5 to-transparent',
    iconClass: 'text-neon-amber', textClass: 'text-neon-amber' },
]

export default function StatsCards() {
  const { data, isLoading, error } = useStats()

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-24 bg-white/5 rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="text-neon-red text-sm mb-8 p-4 bg-neon-red/10 rounded-xl border border-neon-red/20">
        Impossible de charger les statistiques
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
      {cards.map((card, i) => (
        <div
          key={card.key}
          className={`relative overflow-hidden bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 backdrop-blur-sm transition-all duration-300 animate-fade-in-up ${card.borderClass}`}
          style={{ animationDelay: `${i * 80}ms` }}
          role="status"
          aria-label={`${card.label}: ${card.value(data)}`}
        >
          <div className={`absolute inset-0 bg-gradient-to-br ${card.glowClass} opacity-0 hover:opacity-100 transition-opacity duration-500`} />
          <div className="relative z-10">
            <div className={card.iconClass}><card.icon size={24} /></div>
            <div className={`text-2xl font-bold font-mono mt-1 ${card.textClass}`}>{card.value(data)}</div>
            <div className="text-xs text-gray-500 mt-1 font-mono tracking-wider">{card.label}</div>
          </div>
        </div>
      ))}
    </div>
  )
}
