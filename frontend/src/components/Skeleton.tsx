import type { ReactNode } from 'react'

export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`rounded-lg animate-pulse ${className}`}
      style={{ background: 'var(--surface-secondary)' }}
      role="status"
      aria-label="Chargement" />
  )
}

export function SkeletonCard({ lines = 3 }: { lines?: number }) {
  return (
    <div className="surface p-5 space-y-3" role="status" aria-label="Chargement du contenu">
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-3 w-full" />
      {lines > 1 && <Skeleton className="h-3 w-5/6" />}
      {lines > 2 && <Skeleton className="h-3 w-2/3" />}
      <div className="flex gap-3 pt-2">
        <Skeleton className="h-8 w-20 rounded-lg" />
        <Skeleton className="h-8 w-24 rounded-lg" />
      </div>
    </div>
  )
}

export function SkeletonHero() {
  return (
    <div className="surface p-6 space-y-4" role="status" aria-label="Chargement de la decision">
      <Skeleton className="h-3 w-40" />
      <Skeleton className="h-6 w-full" />
      <Skeleton className="h-4 w-2/3" />
      <div className="grid grid-cols-4 gap-3 py-2">
        {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-16 rounded-xl" />)}
      </div>
      <div className="space-y-2">
        {[1, 2, 3].map(i => <Skeleton key={i} className="h-4 w-full" />)}
      </div>
      <div className="flex gap-2">
        <Skeleton className="h-10 w-48 rounded-xl" />
        <Skeleton className="h-10 w-32 rounded-xl" />
      </div>
    </div>
  )
}

export function SkeletonKpi({ count = 4 }: { count?: number }) {
  const grid = count === 2 ? 'grid-cols-2' : count === 3 ? 'grid-cols-3' : 'grid-cols-4'
  return (
    <div className={`grid ${grid} gap-3`} role="status" aria-label="Chargement des indicateurs">
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} className="h-20 rounded-xl" />
      ))}
    </div>
  )
}

export function EmptyState({ icon, title, description, action }: {
  icon: ReactNode
  title: string
  description: string
  action?: { label: string; onClick?: () => void; href?: string }
}) {
  return (
    <div className="surface p-10 text-center max-w-md mx-auto" role="status">
      <div className="w-14 h-14 mx-auto mb-4 rounded-2xl flex items-center justify-center"
        style={{ background: 'var(--surface-secondary)', color: 'var(--text-disabled)' }}>
        {icon}
      </div>
      <h3 className="text-sm font-semibold mb-1" style={{ color: 'var(--text)' }}>{title}</h3>
      <p className="text-xs mb-5" style={{ color: 'var(--text-secondary)' }}>{description}</p>
      {action && (
        action.href ? (
          <a href={action.href} className="btn-primary inline-flex no-underline">
            {action.label}
          </a>
        ) : (
          <button onClick={action.onClick} className="btn-primary">
            {action.label}
          </button>
        )
      )}
    </div>
  )
}
