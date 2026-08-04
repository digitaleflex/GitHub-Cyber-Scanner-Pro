import { memo } from 'react'
import type { LucideIcon } from 'lucide-react'

export type ChipVariant = 'verdict' | 'severity' | 'status' | 'category' | 'default'

const verdictStyles: Record<string, { bg: string; text: string; border: string }> = {
  'sain':     { bg: 'var(--success-light)', text: 'var(--success-text)', border: 'var(--success)' },
  'suspect':  { bg: 'var(--warning-light)', text: 'var(--warning-text)', border: 'var(--warning)' },
  'critique': { bg: 'var(--danger-light)', text: 'var(--danger-text)', border: 'var(--danger)' },
}

const severityStyles: Record<string, { bg: string; text: string; border: string }> = {
  'critical': { bg: 'var(--danger-light)', text: 'var(--danger-text)', border: 'var(--danger)' },
  'high':     { bg: 'var(--warning-light)', text: 'var(--warning-text)', border: 'var(--warning)' },
  'medium':   { bg: 'var(--warning-light)', text: 'var(--warning-text)', border: 'var(--warning)' },
  'low':      { bg: 'var(--bg-alt)', text: 'var(--text-muted)', border: 'var(--border)' },
}

const statusStyles: Record<string, { bg: string; text: string; border: string }> = {
  'active':     { bg: 'var(--success-light)', text: 'var(--success-text)', border: 'var(--success)' },
  'idle':       { bg: 'var(--bg-alt)', text: 'var(--text-muted)', border: 'var(--border)' },
  'error':      { bg: 'var(--danger-light)', text: 'var(--danger-text)', border: 'var(--danger)' },
  'en cours':   { bg: 'var(--warning-light)', text: 'var(--warning-text)', border: 'var(--warning)' },
  'pret':       { bg: 'var(--bg-alt)', text: 'var(--text-muted)', border: 'var(--border)' },
  'ok':         { bg: 'var(--success-light)', text: 'var(--success-text)', border: 'var(--success)' },
  'oui':        { bg: 'var(--success-light)', text: 'var(--success-text)', border: 'var(--success)' },
  'non':        { bg: 'var(--bg-alt)', text: 'var(--text-muted)', border: 'var(--border)' },
  'gratuit':    { bg: 'var(--success-light)', text: 'var(--success-text)', border: 'var(--success)' },
  'pro':        { bg: 'var(--warning-light)', text: 'var(--warning-text)', border: 'var(--warning)' },
  'enterprise': { bg: 'var(--ai-light)', text: 'var(--ai-text)', border: 'var(--ai)' },
  'completed':  { bg: 'var(--success-light)', text: 'var(--success-text)', border: 'var(--success)' },
  'in_progress':{ bg: 'var(--info-light)', text: 'var(--info-text)', border: 'var(--info)' },
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
    style = { bg: 'var(--info-light)', text: 'var(--info-text)', border: 'var(--info)' }
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
