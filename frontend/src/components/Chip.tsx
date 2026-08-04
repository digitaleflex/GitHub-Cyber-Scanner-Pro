import { memo } from 'react'
import type { LucideIcon } from 'lucide-react'

export type ChipVariant = 'verdict' | 'severity' | 'status' | 'category' | 'default'

const verdictStyles: Record<string, { bg: string; text: string; border: string }> = {
  'sain':     { bg: 'var(--success-light)', text: 'var(--success-text)', border: 'var(--success)' },
  'suspect':  { bg: 'var(--mission-light)', text: 'var(--mission-text)', border: 'var(--mission)' },
  'critique': { bg: 'var(--critical-light)', text: 'var(--critical-text)', border: 'var(--critical)' },
}

const severityStyles: Record<string, { bg: string; text: string; border: string }> = {
  'critical': { bg: 'var(--critical-light)', text: 'var(--critical-text)', border: 'var(--critical)' },
  'high':     { bg: 'var(--mission-light)', text: 'var(--mission-text)', border: 'var(--mission)' },
  'medium':   { bg: 'var(--warning-light)', text: 'var(--warning-text)', border: 'var(--mission)' },
  'low':      { bg: 'var(--bg-alt)', text: 'var(--text-muted)', border: 'var(--border)' },
}

const statusStyles: Record<string, { bg: string; text: string; border: string }> = {
  'active':     { bg: 'var(--success-light)', text: 'var(--success-text)', border: 'var(--success)' },
  'idle':       { bg: 'var(--bg-alt)', text: 'var(--text-muted)', border: 'var(--border)' },
  'error':      { bg: 'var(--critical-light)', text: 'var(--critical-text)', border: 'var(--critical)' },
  'en cours':   { bg: 'var(--mission-light)', text: 'var(--mission-text)', border: 'var(--mission)' },
  'pret':       { bg: 'var(--bg-alt)', text: 'var(--text-muted)', border: 'var(--border)' },
  'ok':         { bg: 'var(--success-light)', text: 'var(--success-text)', border: 'var(--success)' },
  'oui':        { bg: 'var(--success-light)', text: 'var(--success-text)', border: 'var(--success)' },
  'non':        { bg: 'var(--bg-alt)', text: 'var(--text-muted)', border: 'var(--border)' },
  'gratuit':    { bg: 'var(--success-light)', text: 'var(--success-text)', border: 'var(--success)' },
  'pro':        { bg: 'var(--mission-light)', text: 'var(--mission-text)', border: 'var(--mission)' },
  'enterprise': { bg: 'var(--ai-light)', text: 'var(--ai-text)', border: 'var(--ai)' },
  'completed':  { bg: 'var(--success-light)', text: 'var(--success-text)', border: 'var(--success)' },
  'in_progress':{ bg: 'var(--decision-light)', text: 'var(--decision-text)', border: 'var(--decision)' },
}

export type ChipProps = {
  variant: ChipVariant
  value: string
  icon?: LucideIcon
  className?: string
}

const Chip = memo(function Chip({ variant, value, icon: Icon, className = '' }: ChipProps) {
  let style: { bg: string; text: string; border: string } = {
    bg: 'var(--bg-alt)',
    text: 'var(--text-secondary)',
    border: 'var(--border)',
  }

  if (variant === 'verdict') {
    const key = value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    style = verdictStyles[key] || style
  } else if (variant === 'severity') {
    const key = value.toLowerCase()
    style = severityStyles[key] || style
  } else if (variant === 'status') {
    const key = value.toLowerCase()
    style = statusStyles[key] || style
  } else if (variant === 'category') {
    style = { bg: 'var(--decision-light)', text: 'var(--decision-text)', border: 'var(--decision)' }
  }

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium border ${className}`}
      style={{
        background: style.bg,
        color: style.text,
        borderColor: style.border,
      }}
    >
      {Icon && <Icon size={10} />}
      {value}
    </span>
  )
})

export default Chip
