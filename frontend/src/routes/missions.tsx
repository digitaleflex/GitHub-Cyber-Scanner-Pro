import { useState } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Target, Shield, CheckCircle2, Play, ChevronRight } from 'lucide-react'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/missions',
  component: MissionsPage,
})

interface MissionStep { id: number; step_order: number; title: string; description: string; status: string; action_type: string; estimated_minutes: number; completed_at: string | null }

interface Mission { id: number; title: string; description: string; objective: string; status: string; progress: number; estimated_minutes: number; risk_reduction_percent: number; cve_ids: string; responsible: string; created_at: string; steps?: MissionStep[] }

function ProgressBar({ pct }: { pct: number }) {
  const color = pct >= 100 ? 'bg-emerald-500' : pct >= 50 ? 'bg-indigo-500' : 'bg-slate-500'
  return (
    <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
      <div className={`h-full rounded-full transition-all duration-500 ${color}`} style={{ width: `${Math.min(pct, 100)}%` }} />
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
    <div className="max-w-3xl mx-auto py-24 text-center animate-fade">
      <Shield size={40} className="mx-auto text-slate-600 mb-4" />
      <p className="text-slate-400 mb-3">Definissez votre organisation pour activer les missions.</p>
      <Link to="/organization" className="inline-flex items-center gap-1.5 px-4 py-2 glass rounded-xl text-xs text-emerald-400 hover:text-white transition">
        Configurer l'organisation <ChevronRight size={12} />
      </Link>
    </div>
  )

  if (isLoading) return <div className="flex justify-center py-24"><div className="w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" /></div>

  return (
    <div className="max-w-3xl mx-auto py-4 sm:py-8 animate-fade">
      <h1 className="text-xl sm:text-2xl font-semibold text-white mb-1">Missions</h1>
      <p className="text-sm text-slate-500 mb-6">Comment reduire mon risque ? Chaque mission est un plan d'action mesurable.</p>

      {active.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Target size={15} className="text-emerald-400" />
            <h2 className="text-sm font-semibold text-white">En cours</h2>
            <span className="text-[10px] text-slate-500">{active.length}</span>
          </div>
          <div className="space-y-3">
            {active.map(m => (
              <div key={m.id}>
                <div className="glass-card rounded-2xl p-4 sm:p-5">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold text-white">{m.title}</h3>
                      <p className="text-xs text-slate-400 mt-0.5">{m.objective}</p>
                    </div>
                    <span className={`shrink-0 px-2 py-0.5 rounded text-[10px] font-medium ${
                      m.status === 'in_progress' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' :
                      'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    }`}>
                      {m.status === 'in_progress' ? 'En cours' : 'Active'}
                    </span>
                  </div>

                  <ProgressBar pct={m.progress} />

                  <div className="grid grid-cols-3 gap-2 mt-3">
                    <div className="glass rounded-lg p-2 text-center">
                      <div className="text-sm font-bold text-white">{m.progress}%</div>
                      <div className="text-[9px] text-slate-500">Progression</div>
                    </div>
                    <div className="glass rounded-lg p-2 text-center">
                      <div className="text-sm font-bold text-white">{m.estimated_minutes || '?'} min</div>
                      <div className="text-[9px] text-slate-500">Estime</div>
                    </div>
                    <div className="glass rounded-lg p-2 text-center">
                      <div className="text-sm font-bold text-emerald-400">-{m.risk_reduction_percent || 0}%</div>
                      <div className="text-[9px] text-slate-500">Risque</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 mt-3 pt-3 border-t border-white/[0.04]">
                    {m.status === 'active' ? (
                      <button onClick={() => handleStart(m.id)}
                        className="px-3 py-1.5 rounded-lg bg-emerald-500 text-white text-xs font-medium hover:bg-emerald-400 transition flex items-center gap-1.5">
                        <Play size={11} /> Demarrer
                      </button>
                    ) : (
                      <button onClick={() => toggleExpand(m.id)}
                        className="px-3 py-1.5 rounded-lg glass text-xs text-slate-400 hover:text-white transition">
                        {expanded === m.id ? 'Masquer' : 'Voir les etapes'}
                      </button>
                    )}
                    {m.cve_ids && (
                      <Link to="/cve/$id" params={{ id: m.cve_ids }} className="text-[10px] text-indigo-400 hover:text-indigo-300 ml-auto">
                        {m.cve_ids}
                      </Link>
                    )}
                  </div>

                  {expanded === m.id && detail?.steps && (
                    <div className="mt-3 pt-3 border-t border-white/[0.04] space-y-1.5">
                      {detail.steps.map((s: MissionStep) => (
                        <div key={s.id} className={`glass rounded-lg p-3 flex items-center gap-3 ${s.status === 'done' ? 'opacity-50' : ''}`}>
                          <button onClick={() => handleStepDone(m.id, s.id)} disabled={s.status === 'done'}
                            className={`shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center transition ${
                              s.status === 'done' ? 'border-emerald-500 bg-emerald-500/20' : 'border-slate-600 hover:border-emerald-500'
                            }`}>
                            {s.status === 'done' && <CheckCircle2 size={12} className="text-emerald-400" />}
                          </button>
                          <div className="min-w-0 flex-1">
                            <div className={`text-xs ${s.status === 'done' ? 'text-slate-500 line-through' : 'text-slate-200'}`}>{s.title}</div>
                            <div className="text-[10px] text-slate-500">{s.action_type} · {s.estimated_minutes} min</div>
                          </div>
                        </div>
                      ))}
                      {detail.steps.every((s: MissionStep) => s.status === 'done') && (
                        <button onClick={() => handleComplete(m.id)}
                          className="w-full px-4 py-2 rounded-lg bg-emerald-500 text-white text-xs font-medium hover:bg-emerald-400 transition flex items-center justify-center gap-1.5 mt-2">
                          <CheckCircle2 size={13} /> Mission terminee
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
            <CheckCircle2 size={15} className="text-slate-500" />
            <h2 className="text-sm font-semibold text-slate-400">Terminees</h2>
            <span className="text-[10px] text-slate-600">{completed.length}</span>
          </div>
          <div className="space-y-2">
            {completed.map(m => (
              <div key={m.id} className="glass-card rounded-xl p-4 opacity-60">
                <div className="flex items-center justify-between gap-2">
                  <div className="min-w-0">
                    <h3 className="text-sm font-medium text-slate-400">{m.title}</h3>
                    <p className="text-[10px] text-slate-500">{m.objective?.slice(0, 80)}</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[10px] text-emerald-500">-{m.risk_reduction_percent}% risque</span>
                    <CheckCircle2 size={15} className="text-emerald-600" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {active.length === 0 && completed.length === 0 && (
        <div className="glass-card rounded-2xl p-8 text-center">
          <Target size={32} className="mx-auto text-slate-600 mb-3" />
          <p className="text-sm text-slate-400 mb-1">Aucune mission pour le moment</p>
          <p className="text-xs text-slate-500">Depuis la page d'accueil, cliquez sur "Commencer la mission" pour creer votre premiere mission.</p>
        </div>
      )}
    </div>
  )
}
