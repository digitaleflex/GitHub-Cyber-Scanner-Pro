import { useState } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import { Shield, Clock, CheckCircle2, Target, ArrowRight, ChevronRight, Brain, Wifi, AlertTriangle, Play, AlertCircle } from 'lucide-react'
import { useStats } from '../lib/api'
import { SkeletonHero, EmptyState } from '../components/Skeleton'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/', component: HomePage })

interface PriorityDecision {
  cve_id: string; score: number; level: string; severity: string; cvss_score: number | null
  published: string | null; description: string; is_kev: boolean; exploits_count: number
  factors: Record<string, number>; reasons: string[]; risk_if_ignored: string; confidence: string; sources: string[]
}

const LEVEL_CLASS: Record<string, string> = {
  CRITIQUE: 'bg-rose-50 text-rose-600 border-rose-200',
  ELEVE: 'bg-amber-50 text-amber-600 border-amber-200',
  MOYEN: 'bg-blue-50 text-blue-600 border-blue-200',
  BAS: 'bg-slate-100 text-slate-500 border-slate-200',
}

function HomePage() {
  const { data: stats } = useStats()
  const { data: org } = useQuery({ queryKey: ['organization', 1], queryFn: () => fetch('/api/organization?profile_id=1').then(r => r.json()), staleTime: 300_000 })
  const orgId = org?.organization?.id
  const { data: priority, isLoading, error } = useQuery({
    queryKey: ['priority-home'],
    queryFn: async () => { const r = await fetch('/api/priority/cves?days=90&limit=6'); if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() },
    staleTime: 120_000,
  })

  const summary = priority?.summary
  const decisions: PriorityDecision[] = priority?.decisions || []
  const today = decisions.slice(0, 3)
  const upcoming = decisions.slice(3, 5)
  const repoCount = stats?.total_repos ? (stats.total_repos >= 1000 ? `${(stats.total_repos / 1000).toFixed(0)}K` : stats.total_repos.toLocaleString()) : '0'
  const cveCount = stats?.total_cves ? (stats.total_cves >= 1000 ? `${(stats.total_cves / 1000).toFixed(0)}K` : stats.total_cves.toLocaleString()) : '0'

  return (
    <div className="max-w-4xl mx-auto w-full" role="main" aria-label="Tableau de bord">
      <section className="py-6 sm:py-10 animate-fade">
        <p className="text-sm text-secondary mb-1">Bonjour</p>
        <h1 className="text-xl sm:text-2xl font-semibold mb-3" style={{ color: 'var(--text)' }}>
          Que dois-je faire aujourd'hui&nbsp;?
        </h1>
        <div className="flex flex-wrap items-center gap-3 text-xs sm:text-sm">
          <span className="flex items-center gap-1.5" style={{ color: 'var(--text-secondary)' }}>
            <Shield size={13} className="text-brand-text" />
            <span className="font-medium" style={{ color: 'var(--text)' }}>{cveCount}</span> CVE suivies
          </span>
          <span className="flex items-center gap-1.5" style={{ color: 'var(--text-secondary)' }}>
            <Wifi size={13} className="text-blue-500" />
            <span className="font-medium" style={{ color: 'var(--text)' }}>{repoCount}</span> outils analyses
          </span>
          {summary?.critiques > 0 && (
            <span className="flex items-center gap-1.5" style={{ color: 'var(--text-secondary)' }}>
              <AlertTriangle size={13} className="text-amber-600" />
              <span className="font-medium" style={{ color: 'var(--text)' }}>{summary.critiques.toLocaleString()}</span> critiques actives
            </span>
          )}
        </div>
      </section>

      {isLoading && (
        <div aria-label="Chargement des decisions" role="status">
          <SkeletonHero />
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="surface p-4 space-y-2" style={{ border: 'none' }}><div className="h-4 w-2/3 rounded animate-pulse" style={{ background: 'var(--surface-secondary)' }} /><div className="h-3 w-full rounded animate-pulse" style={{ background: 'var(--surface-secondary)' }} /></div>
            <div className="surface p-4 space-y-2" style={{ border: 'none' }}><div className="h-4 w-2/3 rounded animate-pulse" style={{ background: 'var(--surface-secondary)' }} /><div className="h-3 w-full rounded animate-pulse" style={{ background: 'var(--surface-secondary)' }} /></div>
          </div>
        </div>
      )}

      {error && (
        <div className="surface-secondary p-6 text-center" role="alert">
          <AlertCircle size={24} className="mx-auto text-amber-500 mb-3" />
          <p className="text-sm font-medium" style={{ color: 'var(--text)' }}>Decision Engine temporairement indisponible</p>
          <p className="text-xs text-secondary mt-1">Les donnees NVD sont peut-etre en cours de backfill.</p>
        </div>
      )}

      {!isLoading && !error && decisions.length > 0 && (
        <>
          <DecisionHero decision={decisions[0]} orgId={orgId} />
          <section className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
            <DecisionBlock title="Aujourd'hui" subtitle={`${today.length} decision${today.length > 1 ? 's' : ''}`}
              icon={<Target size={15} />} decisions={today} color="#166534" />
            <DecisionBlock title="A venir" subtitle={`${upcoming.length} en attente`}
              icon={<Clock size={15} />} decisions={upcoming} color="#2563EB" />
          </section>
        </>
      )}

      {!isLoading && !error && decisions.length === 0 && (
        <EmptyState
          icon={<CheckCircle2 size={22} />}
          title="Aucune decision urgente aujourd'hui"
          description="Le Decision Engine surveille vos menaces. Configurez votre organisation pour des resultats personnalises."
          action={!orgId ? { label: 'Configurer l\'organisation', href: '/organization' } : undefined}
        />
      )}
    </div>
  )
}

function DecisionHero({ decision, orgId }: { decision: PriorityDecision; orgId?: number }) {
  const [creating, setCreating] = useState(false)
  const [done, setDone] = useState(false)
  const dl = decision.level === 'CRITIQUE' ? 'CRITIQUE' : decision.level === 'ELEVE' ? 'ELEVE' : decision.level === 'MOYEN' ? 'MOYEN' : 'BAS'

  const startMission = async () => {
    if (!orgId) { window.location.href = '/organization'; return }
    setCreating(true)
    await fetch(`/api/missions?org_id=${orgId}&cve_id=${encodeURIComponent(decision.cve_id)}&desc=${encodeURIComponent(decision.description.slice(0, 200))}&cvss=${decision.cvss_score || 0}`, { method: 'POST' })
    setCreating(false); setDone(true); setTimeout(() => setDone(false), 2000)
  }

  return (
    <div className="surface p-5 sm:p-7" role="region" aria-label="Decision principale" style={{ borderColor: 'var(--border)' }}>
      <span className="badge badge-brand mb-2">Votre prochaine decision</span>
      <h2 className="text-lg sm:text-xl font-semibold mb-1.5" style={{ color: 'var(--text)' }}>{decision.description.slice(0, 120)}</h2>

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <span className="text-xs font-mono text-blue-600 font-semibold">{decision.cve_id}</span>
        {decision.cvss_score != null && <span className="text-xs font-semibold text-rose-600">CVSS {decision.cvss_score}</span>}
        <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${LEVEL_CLASS[dl] || LEVEL_CLASS.BAS}`}>{decision.level}</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        {[
          { v: decision.score, l: 'Score', c: 'var(--text)' },
          { v: decision.confidence, l: 'Confiance', c: 'var(--text)' },
          { v: decision.exploits_count, l: `Exploit${decision.exploits_count > 1 ? 's' : ''}`, c: 'var(--text)' },
          { v: decision.is_kev ? 'Oui' : 'Non', l: 'CISA KEV', c: decision.is_kev ? '#D97706' : 'var(--text-secondary)' },
        ].map((s, i) => (
          <div key={i} className="surface rounded-xl p-3 text-center" style={{ borderColor: 'var(--border)' }}>
            <div className="text-lg font-bold" style={{ color: s.c }}>{s.v}</div>
            <div className="text-[10px] text-secondary">{s.l}</div>
          </div>
        ))}
      </div>

      <div className="space-y-2 mb-4">
        {decision.reasons.map((r, i) => (
          <div key={i} className="flex items-start gap-2 text-sm" style={{ color: 'var(--text)' }}>
            <ChevronRight size={14} className="shrink-0 mt-0.5" style={{ color: '#166534' }} />
            <span>{r}</span>
          </div>
        ))}
      </div>

      <div className="surface rounded-xl p-4 mb-4" role="alert" style={{ borderColor: 'var(--border)' }}>
        <p className="text-[10px] uppercase tracking-widest text-amber-600 mb-1 font-semibold">Si vous ignorez</p>
        <p className="text-sm" style={{ color: 'var(--text)' }}>{decision.risk_if_ignored}</p>
      </div>

      <div className="flex items-center gap-2 text-[10px] text-secondary mb-4"><Brain size={11} />Sources: {decision.sources.join(', ')}</div>

      <button onClick={startMission} disabled={creating} aria-label={orgId ? 'Commencer la mission' : 'Configurer l organisation'}
        className="btn-primary inline-flex items-center gap-2">
        {creating ? 'Creation...' : done ? 'Mission creee !' : orgId ? <><Play size={15} /> Commencer la mission</> : <>Configurer l'organisation <ArrowRight size={15} /></>}
      </button>
    </div>
  )
}

function DecisionBlock({ title, subtitle, icon, decisions, color }: {
  title: string; subtitle: string; icon: React.ReactNode; decisions: PriorityDecision[]; color: string
}) {
  return (
    <div className="surface p-4 sm:p-5" role="region" aria-label={title} style={{ borderColor: 'var(--border)' }}>
      <div className="flex items-center gap-2 mb-1">
        <span style={{ color }}>{icon}</span>
        <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>{title}</h3>
      </div>
      <p className="text-[10px] text-secondary mb-3">{subtitle}</p>

      {decisions.length === 0 ? (
        <p className="text-xs text-secondary py-4 text-center">Aucune decision</p>
      ) : (
        <div className="space-y-2">
          {decisions.map((d, i) => {
            const dl = d.level === 'CRITIQUE' ? 'CRITIQUE' : d.level === 'ELEVE' ? 'ELEVE' : d.level === 'MOYEN' ? 'MOYEN' : 'BAS'
            const dot = dl === 'CRITIQUE' ? '#EF4444' : dl === 'ELEVE' ? '#D97706' : '#94A3B8'
            return (
              <div key={i} className="surface rounded-xl p-3 flex items-center justify-between gap-2" style={{ borderColor: 'var(--border)' }}>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: dot }} />
                    <span className="text-xs font-mono text-blue-600 font-semibold">{d.cve_id}</span>
                  </div>
                  <p className="text-xs text-secondary line-clamp-1">{d.description.slice(0, 90)}</p>
                </div>
                <span className="text-sm font-bold shrink-0" style={{ color: 'var(--text)' }}>{d.score}</span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
