import { AlertTriangle, RefreshCw } from 'lucide-react'

type ErrorStateProps = {
  title?: string
  description?: string
  onRetry?: () => void
  compact?: boolean
}

export default function ErrorState({
  title = 'Erreur de chargement',
  description,
  onRetry,
  compact = false,
}: ErrorStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center text-center ${compact ? 'py-8' : 'py-16'} px-4`}
      role="alert"
    >
      <div
        className="w-12 h-12 rounded-2xl flex items-center justify-center mb-3"
        style={{
          background: 'var(--red-light)',
          border: '1px solid var(--red)',
          opacity: 0.6,
        }}
      >
        <AlertTriangle size={20} style={{ color: 'var(--red)' }} />
      </div>
      <p className="body-sm font-medium mb-1" style={{ color: 'var(--red)', opacity: 0.8 }}>{title}</p>
      {description && (
        <p className="text-xs max-w-xs leading-relaxed mb-1" style={{ color: 'var(--text-muted)' }}>{description}</p>
      )}
      {onRetry && (
        <button
          onClick={onRetry}
          className="btn-secondary mt-3 text-xs"
        >
          <RefreshCw size={11} /> Réessayer
        </button>
      )}
    </div>
  )
}
