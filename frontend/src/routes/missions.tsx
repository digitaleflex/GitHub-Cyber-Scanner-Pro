import { useState } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Target, Shield, CheckCircle2, Play, ChevronRight } from 'lucide-react'
import { CyberLoader } from '../components/CyberLoader'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/missions',
  component: MissionsPage,
})

interface MissionStep { id: number; step_order: number; title: string; description: string; status: string; action_type: string; estimated_minutes: number; completed_at: string | null }

interface Mission { id: number; title: string; description: string; objective: string; status: string; progress: number; estimated_minutes: number; risk_reduction_percent: number; cve_ids: string; responsible: string; created_at: string; steps?: MissionStep[] }

function ProgressBar({ pct }: { pct: number }) {
  return (
    <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--border)' }}>
      <div className="h-full rounded-full transition-all duration-500" style={{
        width: `${Math.min(pct, 100)}%`,
        background: pct >= 100 ? 'var(--success)' : pct >= 50 ? 'var(--info)' : 'var(--text-muted)',
      }} />
    </div>
  )
}

function MissionsPage() {
  const qc = useQueryClient()
  const [expanded, setExpanded] = useState<number | null>(null)
  const profileId = 1
  const { data: org } = useQuery({
    queryKey: ['organization', profileId],
    queryFn: () => fetch(`/api/organization?profile_id=${profileId}`).then(r => r.json()),
  })
  const orgId = org?.organization?.id
  const { data: missionsData, isLoading } = useQuery({
    queryKey: ['missions', orgId],
    queryFn: () => fetch(`/api/missions?org_id=${orgId}&limit=20`).then(r => r.json()),
    enabled: !!orgId,
  })
  const { data: detail } = useQuery({
    queryKey: ['mission-detail', expanded],
    queryFn: () => fetch(`/api/missions/${expanded}`).then(r => r.json()),
    enabled: !!expanded,
  })

  const missions: Mission[] = missionsData?.missions || []
  const active = missions.filter(m => m.status === 'active' || m.status === 'in_progress')
  const completed = missions.filter(m => m.status === 'completed')

  const toggleExpand = async (id: number) => {
    if (expanded === id) { setExpanded(null); return }
    setExpanded(id)
  }

  const handleStepDone = async (missionId: number, stepId: number) => {
    await fetch(`/api/missions/${missionId}/steps/${stepId}/done`, { method: 'POST' })
    qc.invalidateQueries({ queryKey: ['mission-detail', missionId] })
    qc.invalidateQueries({ queryKey: ['missions'] })
  }

  const handleComplete = async (missionId: number) => {
    await fetch(`/api/missions/${missionId}/complete`, { method: 'POST' })
    setExpanded(null)
    qc.invalidateQueries({ queryKey: ['missions'] })
  }

  const handleStart = async (missionId: number) => {
    await fetch(`/api/missions/${missionId}/start`, { method: 'POST' })
    qc.invalidateQueries({ queryKey: ['missions'] })
  }

  if (!orgId) return (
    <div className="w-full py-24 text-center animate-fade">
      <Shield size={40} className="mx-auto text-muted mb-4" />
      <p className="text-secondary mb-3">Définissez votre organisation pour activer les missions.</p>
      <Link to="/organization" className="btn-secondary inline-flex items-center gap-1.5 text-xs">
        Configurer l'organisation <ChevronRight size={12} />
      </Link>
    </div>
  )

  if (isLoading) return (
    <div className="w-full py-4 sm:py-8 animate-fade" role="status" aria-label="Chargement des missions">
      <CyberLoader text="Chargement des missions..." />
      <div className="mt-4"><CyberLoader text="Analyse des objectifs..." /></div>
    </div>
  )

  return (
    <div className="w-full py-4 sm:py-8 animate-fade">
      <h1 className="h1 mb-1" style={{ color: 'var(--text)' }}>Missions</h1>
      <p className="body-sm text-secondary mb-6">Comment réduire mon risque ? Chaque mission est un plan d'action mesurable.</p>

      {active.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Target size={15} style={{ color: 'var(--brand)' }} />
            <h2 className="h3" style={{ color: 'var(--text)' }}>En cours</h2>
            <span className="text-xs text-muted">{active.length}</span>
          </div>
          <div className="space-y-3">
            {active.map(m => (
              <div key={m.id}>
                <div className="card-hero p-4 sm:p-5" style={{ border: '1px solid var(--border)' }}>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="min-w-0">
                      <h3 className="h3" style={{ color: 'var(--text)' }}>{m.title}</h3>
                      <p className="text-xs text-secondary mt-0.5">{m.objective}</p>
                    </div>
                    <span className="shrink-0 px-2 py-0.5 rounded-full text-[10px] font-semibold border"
                      style={{
                        background: m.status === 'in_progress' ? 'var(--info-light)' : '#F0FDF4',
                        color: m.status === 'in_progress' ? 'var(--info-text)' : '#166534',
                        borderColor: m.status === 'in_progress' ? 'var(--info)' : 'var(--success)',
                      }}>
                      {m.status === 'in_progress' ? 'En cours' : 'Active'}
                    </span>
                  </div>

                  <ProgressBar pct={m.progress} />

                  <div className="grid grid-cols-3 gap-2 mt-3">
                    <div className="rounded-lg p-2 text-center" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                      <div className="text-sm font-bold" style={{ color: 'var(--text)' }}>{m.progress}%</div>
                      <div className="text-[9px] text-muted">Progression</div>
                    </div>
                    <div className="rounded-lg p-2 text-center" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                      <div className="text-sm font-bold" style={{ color: 'var(--text)' }}>{m.estimated_minutes || '?'} min</div>
                      <div className="text-[9px] text-muted">Estimé</div>
                    </div>
                    <div className="rounded-lg p-2 text-center" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                      <div className="text-sm font-bold" style={{ color: 'var(--brand)' }}>-{m.risk_reduction_percent || 0}%</div>
                      <div className="text-[9px] text-muted">Risque</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 mt-3 pt-3" style={{ borderTop: '1px solid var(--border)' }}>
                    {m.status === 'active' ? (
                      <button onClick={() => handleStart(m.id)}
                        className="btn-primary text-xs" style={{ padding: '6px 16px' }}>
                        <Play size={11} /> Démarrer
                      </button>
                    ) : (
                      <button onClick={() => toggleExpand(m.id)}
                        className="btn-ghost text-xs">
                        {expanded === m.id ? 'Masquer' : 'Voir les étapes'}
                      </button>
                    )}
                    {m.cve_ids && (
                      <Link to="/cve/$id" params={{ id: m.cve_ids }} className="text-xs font-semibold ml-auto" style={{ color: 'var(--info-text)' }}>
                        {m.cve_ids}
                      </Link>
                    )}
                  </div>

                  {expanded === m.id && detail?.steps && (
                    <div className="mt-3 pt-3 space-y-1.5" style={{ borderTop: '1px solid var(--border)' }}>
                      {detail.steps.map((s: MissionStep) => (
                        <div key={s.id} className={`rounded-lg p-3 flex items-center gap-3 ${s.status === 'done' ? 'opacity-50' : ''}`}
                          style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                          <button onClick={() => handleStepDone(m.id, s.id)} disabled={s.status === 'done'}
                            className="shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors"
                            style={{
                              borderColor: s.status === 'done' ? 'var(--success)' : 'var(--border)',
                              background: s.status === 'done' ? 'var(--success-light)' : 'transparent',
                            }}>
                            {s.status === 'done' && <CheckCircle2 size={12} style={{ color: '#166534' }} />}
                          </button>
                          <div className="min-w-0 flex-1">
                            <div className="text-xs" style={{
                              color: s.status === 'done' ? 'var(--text-muted)' : 'var(--text)',
                              textDecoration: s.status === 'done' ? 'line-through' : 'none',
                            }}>{s.title}</div>
                            <div className="text-[10px] text-muted">{s.action_type} · {s.estimated_minutes} min</div>
                          </div>
                        </div>
                      ))}
                      {detail.steps.every((s: MissionStep) => s.status === 'done') && (
                        <button onClick={() => handleComplete(m.id)}
                          className="btn-primary text-xs w-full justify-center mt-2">
                          <CheckCircle2 size={13} /> Mission terminée
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {completed.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle2 size={15} className="text-muted" />
            <h2 className="h3" style={{ color: 'var(--text-secondary)' }}>Terminées</h2>
            <span className="text-xs text-muted">{completed.length}</span>
          </div>
          <div className="space-y-2">
            {completed.map(m => (
              <div key={m.id} className="surface rounded-xl p-4 opacity-60" style={{ border: '1px solid var(--border)' }}>
                <div className="flex items-center justify-between gap-2">
                  <div className="min-w-0">
                    <h3 className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>{m.title}</h3>
                    <p className="text-[10px] text-muted">{m.objective?.slice(0, 80)}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[10px]" style={{ color: '#166534' }}>-{m.risk_reduction_percent}% risque</span>
                    <CheckCircle2 size={15} style={{ color: '#166534' }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {active.length === 0 && completed.length === 0 && (
        <div className="surface rounded-2xl p-8 text-center" style={{ border: '1px solid var(--border)' }}>
          <Target size={32} className="mx-auto text-muted mb-3" />
          <p className="body-sm text-secondary mb-1">Aucune mission pour le moment</p>
          <p className="text-xs text-muted">Depuis la page d'accueil, cliquez sur "Commencer la mission" pour créer votre première mission.</p>
        </div>
      )}
    </div>
  )
}
