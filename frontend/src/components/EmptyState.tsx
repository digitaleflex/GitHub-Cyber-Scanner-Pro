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
  title = 'Aucune donnee',
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
      <div className="w-12 h-12 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mb-3">
        <Icon size={20} className="text-slate-500" />
      </div>
      <p className="text-sm font-medium text-slate-400 mb-1">{title}</p>
      {description && <p className="text-xs text-slate-500 max-w-xs leading-relaxed">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
