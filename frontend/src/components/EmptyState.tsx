import type { LucideIcon } from 'lucide-react'
import { Inbox } from 'lucide-react'

type EmptyStateProps = {
  title?: string
  description?: string
  icon?: LucideIcon
  action?: React.ReactNode
  compact?: boolean
}

export default function EmptyState({
  title = 'Aucune donnée',
  description,
  icon: Icon = Inbox,
  action,
  compact = false,
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center text-center ${compact ? 'py-8' : 'py-16'} px-4`}
      role="status"
    >
      <div
        className="w-12 h-12 rounded-2xl flex items-center justify-center mb-3"
        style={{
          background: 'var(--surface-elevated)',
          border: '1px solid var(--border)',
        }}
      >
        <Icon size={20} style={{ color: 'var(--text-muted)' }} />
      </div>
      <p className="body-sm font-medium mb-1" style={{ color: 'var(--text-secondary)' }}>{title}</p>
      {description && (
        <p className="text-xs max-w-xs leading-relaxed" style={{ color: 'var(--text-muted)' }}>{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
