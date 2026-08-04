import { Play, CheckCircle2 } from 'lucide-react'

interface Props {
  title: string
  objective: string
  progress: number
  estimatedMinutes?: number
  riskReduction?: number
  status: 'active' | 'in_progress' | 'completed'
  onStart?: () => void
  onViewSteps?: () => void
}

export function MissionCard({ title, objective, progress, estimatedMinutes, riskReduction, status, onStart, onViewSteps }: Props) {
  const isCompleted = status === 'completed'
  return (
    <div
      className="rounded-xl p-4 transition-all hover:-translate-y-0.5"
      style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        opacity: isCompleted ? 0.7 : 1,
      }}
    >
      <div className="h-1 rounded-full overflow-hidden mb-4" style={{ background: 'var(--border-light)' }}>
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${progress}%`,
            background: isCompleted ? 'var(--lime)' : progress >= 50 ? 'var(--cyan)' : 'var(--amber)',
          }}
        />
      </div>

      <div className="flex items-start justify-between gap-3 mb-2">
        <div>
          <h3 className="text-h3">{title}</h3>
          <p className="text-body-sm t-s line-clamp-1">{objective}</p>
        </div>
        {isCompleted && <CheckCircle2 size={18} style={{ color: 'var(--lime)' }} />}
      </div>

      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="rounded-lg p-2 text-center" style={{ background: 'var(--surface-elevated)' }}>
          <div className="font-display text-h2">{progress}%</div>
          <div className="text-caption t-m">Prog.</div>
        </div>
        <div className="rounded-lg p-2 text-center" style={{ background: 'var(--surface-elevated)' }}>
          <div className="font-display text-h2">{estimatedMinutes ?? '?'}</div>
          <div className="text-caption t-m">Min</div>
        </div>
        <div className="rounded-lg p-2 text-center" style={{ background: 'var(--surface-elevated)' }}>
          <div className="font-display text-h2" style={{ color: 'var(--lime)' }}>-{riskReduction ?? 0}%</div>
          <div className="text-caption t-m">Risque</div>
        </div>
      </div>

      {!isCompleted && (
        <button
          onClick={status === 'active' ? onStart : onViewSteps}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-body-sm font-semibold transition-all active:scale-[0.98]"
          style={{ background: 'var(--amber)', color: 'var(--text-inverse)' }}
        >
          {status === 'active' ? <><Play size={14} /> Démarrer</> : <>Voir les étapes</>}
        </button>
      )}
    </div>
  )
}
