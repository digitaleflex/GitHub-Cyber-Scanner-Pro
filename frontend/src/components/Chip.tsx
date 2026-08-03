import type { LucideIcon } from 'lucide-react'

export type ChipVariant = 'verdict' | 'severity' | 'status' | 'category' | 'default'

const verdictColors: Record<string, string> = {
  'sain': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  'suspect': 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  'critique': 'bg-rose-500/10 text-rose-400 border-rose-500/20',
}

const severityColors: Record<string, string> = {
  'critical': 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  'high': 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  'medium': 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  'low': 'bg-slate-500/10 text-slate-400 border-slate-500/20',
}

const statusColors: Record<string, string> = {
  'active': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  'idle': 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  'error': 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  'en cours': 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  'pret': 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  'ok': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  'oui': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  'non': 'bg-slate-500/10 text-slate-500 border-slate-500/20',
  'gratuit': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  'pro': 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  'enterprise': 'bg-violet-500/10 text-violet-400 border-violet-500/20',
}

export type ChipProps = {
  variant: ChipVariant
  value: string
  icon?: LucideIcon
  className?: string
}

export default function Chip({ variant, value, icon: Icon, className = '' }: ChipProps) {
  let colorClass = 'glass text-slate-400'

  if (variant === 'verdict') {
    const key = value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    colorClass = verdictColors[key] || 'glass text-slate-400'
  } else if (variant === 'severity') {
    const key = value.toLowerCase()
    colorClass = severityColors[key] || 'glass text-slate-400'
  } else if (variant === 'status') {
    const key = value.toLowerCase()
    colorClass = statusColors[key] || 'glass text-slate-400'
  } else if (variant === 'category') {
    colorClass = 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
  }

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border ${colorClass} ${className}`}>
      {Icon && <Icon size={10} />}
      {value}
    </span>
  )
}
