import { memo } from 'react'
import type { LucideIcon } from 'lucide-react'

export type ChipVariant = 'verdict' | 'severity' | 'status' | 'category' | 'default'

const styles: Record<string, { bg: string; text: string; border: string }> = {
  legitimate: { bg: 'var(--lime-light)', text: 'var(--lime)', border: 'var(--lime)' },
  sain: { bg: 'var(--lime-light)', text: 'var(--lime)', border: 'var(--lime)' },
  malicious: { bg: 'var(--red-light)', text: 'var(--red)', border: 'var(--red)' },
  suspicious: { bg: 'var(--amber-light)', text: 'var(--amber)', border: 'var(--amber)' },
  suspect: { bg: 'var(--amber-light)', text: 'var(--amber)', border: 'var(--amber)' },
  neutral: { bg: 'var(--surface-elevated)', text: 'var(--text-secondary)', border: 'var(--border)' },
  unknown: { bg: 'var(--surface-elevated)', text: 'var(--text-muted)', border: 'var(--border)' },
  critical: { bg: 'var(--red-light)', text: 'var(--red)', border: 'var(--red)' },
  high: { bg: 'var(--amber-light)', text: 'var(--amber)', border: 'var(--amber)' },
  medium: { bg: 'var(--amber-light)', text: 'var(--amber)', border: 'var(--amber)' },
  low: { bg: 'var(--surface-elevated)', text: 'var(--text-muted)', border: 'var(--border)' },
  active: { bg: 'var(--cyan-light)', text: 'var(--cyan)', border: 'var(--cyan)' },
  completed: { bg: 'var(--lime-light)', text: 'var(--lime)', border: 'var(--lime)' },
  in_progress: { bg: 'var(--cyan-light)', text: 'var(--cyan)', border: 'var(--cyan)' },
  error: { bg: 'var(--red-light)', text: 'var(--red)', border: 'var(--red)' },
  category: { bg: 'var(--cyan-light)', text: 'var(--cyan)', border: 'var(--cyan)' },
  default: { bg: 'var(--surface-elevated)', text: 'var(--text-secondary)', border: 'var(--border)' },
}

export type ChipProps = {
  variant: ChipVariant
  value: string
  icon?: LucideIcon
  className?: string
}

const Chip = memo(function Chip({ variant: _variant, value, icon: Icon, className = '' }: ChipProps) {
  const key = value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  const style = styles[key] || styles.default

  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-caption font-medium border ${className}`}
      style={{ background: style.bg, color: style.text, borderColor: `${style.border}40` }}
    >
      {Icon && <Icon size={10} />}
      {value}
    </span>
  )
})

export default Chip
