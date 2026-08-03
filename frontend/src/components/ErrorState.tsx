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
      <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mb-3">
        <AlertTriangle size={20} className="text-rose-400" />
      </div>
      <p className="text-sm font-medium text-rose-300 mb-1">{title}</p>
      {description && <p className="text-xs text-slate-500 max-w-xs leading-relaxed mb-1">{description}</p>}
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 glass rounded-lg text-xs text-slate-300 hover:text-white hover:border-indigo-500/30 transition"
        >
          <RefreshCw size={11} /> Reessayer
        </button>
      )}
    </div>
  )
}
