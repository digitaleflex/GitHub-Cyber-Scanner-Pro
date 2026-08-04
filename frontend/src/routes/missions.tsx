import { useState } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Target, Shield, CheckCircle2, ChevronRight } from 'lucide-react'
import { CyberLoader } from '../components/CyberLoader'
import { MissionCard } from '../components/MissionCard'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/missions',
  component: MissionsPage,
})

interface MissionStep { id: number; step_order: number; title: string; description: string; status: string; action_type: string; estimated_minutes: number; completed_at: string | null }

interface Mission { id: number; title: string; description: string; objective: string; status: string; progress: number; estimated_minutes: number; risk_reduction_percent: number; cve_ids: string; responsible: string; created_at: string; steps?: MissionStep[] }

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
            <Target size={15} style={{ color: 'var(--amber)' }} />
            <h2 className="h3" style={{ color: 'var(--text)' }}>En cours</h2>
            <span className="text-xs text-muted">{active.length}</span>
          </div>
          <div className="space-y-3">
            {active.map(m => (
              <div key={m.id}>
                <div className="relative">
                  <span className="absolute top-3 right-3 z-10 shrink-0 px-2 py-0.5 rounded-full text-[10px] font-semibold border"
                    style={{
                      background: m.status === 'in_progress' ? 'var(--surface-elevated)' : 'var(--lime-light)',
                      color: m.status === 'in_progress' ? 'var(--cyan)' : 'var(--lime)',
                      borderColor: m.status === 'in_progress' ? 'var(--cyan)' : 'var(--lime)',
                    }}>
                    {m.status === 'in_progress' ? 'En cours' : 'Active'}
                  </span>
                  <MissionCard
                    title={m.title}
                    objective={m.objective}
                    progress={m.progress}
                    estimatedMinutes={m.estimated_minutes}
                    riskReduction={m.risk_reduction_percent}
                    status={m.status as 'active' | 'in_progress'}
                    onStart={() => handleStart(m.id)}
                    onViewSteps={() => toggleExpand(m.id)}
                  />
                  {m.cve_ids && (
                    <Link to="/cve/$id" params={{ id: m.cve_ids }} className="absolute bottom-3 right-3 z-10 text-xs font-semibold" style={{ color: 'var(--cyan)' }}>
                      {m.cve_ids}
                    </Link>
                  )}
                </div>
                {expanded === m.id && detail?.steps && (
                  <div className="mt-2 p-3 space-y-1.5 rounded-xl" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
                    {detail.steps.map((s: MissionStep) => (
                      <div key={s.id} className={`rounded-lg p-3 flex items-center gap-3 ${s.status === 'done' ? 'opacity-50' : ''}`}
                        style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border-light)' }}>
                        <button onClick={() => handleStepDone(m.id, s.id)} disabled={s.status === 'done'}
                          className="shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors"
                          style={{
                            borderColor: s.status === 'done' ? 'var(--lime)' : 'var(--border)',
                            background: s.status === 'done' ? 'var(--lime-light)' : 'transparent',
                          }}>
                          {s.status === 'done' && <CheckCircle2 size={12} style={{ color: 'var(--lime)' }} />}
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
                    <span className="text-[10px]" style={{ color: 'var(--lime)' }}>-{m.risk_reduction_percent}% risque</span>
                    <CheckCircle2 size={15} style={{ color: 'var(--lime)' }} />
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
