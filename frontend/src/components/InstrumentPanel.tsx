import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
  title?: string
  icon?: ReactNode
  accent?: 'amber' | 'cyan' | 'violet' | 'red' | 'lime'
  className?: string
}

export function InstrumentPanel({ children, title, icon, accent, className = '' }: Props) {
  const accentColor = accent ? `var(--${accent})` : undefined
  return (
    <div
      className={`rounded-xl ${className}`}
      style={{
        background: 'var(--surface)',
        border: accent ? `1px solid ${accentColor}` : '1px solid var(--border)',
        boxShadow: accent ? `0 0 20px ${accentColor}15` : 'none',
        padding: 'var(--space-5)',
      }}
    >
      {(title || icon) && (
        <div className="flex items-center gap-2 mb-4">
          {icon && <span style={{ color: accentColor || 'var(--text-muted)' }}>{icon}</span>}
          {title && <h2 className="text-h2 font-display">{title}</h2>}
        </div>
      )}
      {children}
    </div>
  )
}
