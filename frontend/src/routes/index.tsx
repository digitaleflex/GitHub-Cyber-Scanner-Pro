import { useState } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import {
  Shield, Clock, CheckCircle2, Target, ArrowRight, ChevronRight,
  Brain, Wifi, AlertTriangle, Play, AlertCircle, TrendingUp, Zap,
} from 'lucide-react'
import { useStats } from '../lib/api'
import { PageLoader } from '../components/CyberLoader'
import { EmptyState } from '../components/Skeleton'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/', component: HomePage })

interface PriorityDecision {
  cve_id: string; score: number; level: string; severity: string; cvss_score: number | null
  published: string | null; description: string; is_kev: boolean; exploits_count: number
  factors: Record<string, number>; reasons: string[]; risk_if_ignored: string; confidence: string; sources: string[]
}

const LEVEL_LABEL: Record<string, string> = {
  CRITIQUE: 'Critique',
  ELEVE: 'Élevé',
  MOYEN: 'Moyen',
  BAS: 'Faible',
}

const LEVEL_COLOR: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  CRITIQUE: { bg: 'var(--critical-light)', text: 'var(--critical-text)', border: 'var(--critical)', dot: '#DC2626' },
  ELEVE: { bg: 'var(--mission-light)', text: 'var(--mission-text)', border: 'var(--mission)', dot: '#D97706' },
  MOYEN: { bg: 'var(--decision-light)', text: 'var(--decision-text)', border: 'var(--decision)', dot: '#2563EB' },
  BAS: { bg: 'var(--surface-hover)', text: 'var(--text-muted)', border: 'var(--border)', dot: '#94A3B8' },
}

function HomePage() {
  const { data: stats } = useStats()
  const { data: org } = useQuery({
    queryKey: ['organization', 1],
    queryFn: () => fetch('/api/organization?profile_id=1').then(r => r.json()),
    staleTime: 300_000,
  })
  const orgId = org?.organization?.id

  const { data: priority, isLoading, error } = useQuery({
    queryKey: ['priority-home'],
    queryFn: async () => {
      const r = await fetch('/api/priority/cves?days=90&limit=6')
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      return r.json()
    },
    staleTime: 120_000,
  })

  const summary = priority?.summary
  const decisions: PriorityDecision[] = priority?.decisions || []
  const today = decisions.slice(0, 3)
  const upcoming = decisions.slice(3, 5)
  const cveCount = stats?.total_cves ? (stats.total_cves >= 1000 ? `${(stats.total_cves / 1000).toFixed(0)}K` : stats.total_cves.toLocaleString()) : '0'
  const repoCount = stats?.total_repos ? (stats.total_repos >= 1000 ? `${(stats.total_repos / 1000).toFixed(0)}K` : stats.total_repos.toLocaleString()) : '0'

  return (
    <div className="max-w-5xl mx-auto w-full" role="main" aria-label="Tableau de bord">
      {/* ── Hero ──────────────────────────────────────────────── */}
      <section className="py-8 sm:py-12 animate-fade">
        <p className="caption mb-2" style={{ color: 'var(--brand-text)' }}>Votre tableau de bord</p>
        <h1 className="h1 mb-4" style={{ color: 'var(--text)' }}>
          Que dois-je faire aujourd'hui&nbsp;?
        </h1>

        {/* KPI strip */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          <div className="surface rounded-xl px-4 py-2.5 flex items-center gap-2.5" style={{ border: '1px solid var(--border)' }}>
            <Shield size={15} style={{ color: 'var(--brand-text)' }} />
            <div>
              <span className="body-sm font-semibold" style={{ color: 'var(--text)' }}>{cveCount}</span>
              <span className="text-muted ml-1 text-xs">CVE suivies</span>
            </div>
          </div>
          <div className="surface rounded-xl px-4 py-2.5 flex items-center gap-2.5" style={{ border: '1px solid var(--border)' }}>
            <Wifi size={15} style={{ color: 'var(--decision)' }} />
            <div>
              <span className="body-sm font-semibold" style={{ color: 'var(--text)' }}>{repoCount}</span>
              <span className="text-muted ml-1 text-xs">outils analysés</span>
            </div>
          </div>
          {summary?.critiques > 0 && (
            <div className="surface rounded-xl px-4 py-2.5 flex items-center gap-2.5" style={{ border: '1px solid var(--border)' }}>
              <AlertTriangle size={15} style={{ color: 'var(--critical)' }} />
              <div>
                <span className="body-sm font-semibold" style={{ color: 'var(--text)' }}>{summary.critiques.toLocaleString()}</span>
                <span className="text-muted ml-1 text-xs">critiques actives</span>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ── Loading ───────────────────────────────────────────── */}
      {isLoading && (
        <div aria-label="Chargement des décisions" role="status">
          <PageLoader text="Priorisation des menaces..." />
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="surface p-5 space-y-3" style={{ border: '1px solid var(--border)' }}>
              <div className="h-4 w-2/3 rounded animate-pulse" style={{ background: 'var(--bg-alt)' }} />
              <div className="h-3 w-full rounded animate-pulse" style={{ background: 'var(--bg-alt)' }} />
            </div>
            <div className="surface p-5 space-y-3" style={{ border: '1px solid var(--border)' }}>
              <div className="h-4 w-2/3 rounded animate-pulse" style={{ background: 'var(--bg-alt)' }} />
              <div className="h-3 w-full rounded animate-pulse" style={{ background: 'var(--bg-alt)' }} />
            </div>
          </div>
        </div>
      )}

      {/* ── Error ──────────────────────────────────────────────── */}
      {error && (
        <div
          className="rounded-2xl p-8 text-center"
          style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
          role="alert"
        >
          <AlertCircle size={28} className="mx-auto mb-3" style={{ color: 'var(--mission)' }} />
          <p className="body font-semibold" style={{ color: 'var(--text)' }}>Decision Engine temporairement indisponible</p>
          <p className="body-sm mt-1 text-secondary">Les données NVD sont peut-être en cours de backfill.</p>
        </div>
      )}

      {/* ── Decisions ──────────────────────────────────────────── */}
      {!isLoading && !error && decisions.length > 0 && (
        <>
          <DecisionHero decision={decisions[0]} orgId={orgId} />

          <section className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
            <DecisionBlock
              title="Aujourd'hui"
              subtitle={`${today.length} décision${today.length > 1 ? 's' : ''}`}
              icon={<Target size={16} />}
              decisions={today}
              color="var(--brand-text)"
            />
            <DecisionBlock
              title="À venir"
              subtitle={`${upcoming.length} en attente`}
              icon={<Clock size={16} />}
              decisions={upcoming}
              color="var(--decision)"
            />
          </section>
        </>
      )}

      {/* ── Empty ──────────────────────────────────────────────── */}
      {!isLoading && !error && decisions.length === 0 && (
        <EmptyState
          icon={<CheckCircle2 size={22} />}
          title="Aucune décision urgente aujourd'hui"
          description="Le Decision Engine surveille vos menaces. Configurez votre organisation pour des résultats personnalisés."
          action={!orgId ? { label: "Configurer l'organisation", href: '/organization' } : undefined}
        />
      )}

      {/* ── Quick links footer ─────────────────────────────────── */}
      <div className="mt-12 grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { to: '/threats', icon: <TrendingUp size={15} />, label: 'Menaces', desc: 'CISA KEV, EPSS, critiques' },
          { to: '/missions', icon: <Target size={15} />, label: 'Missions', desc: 'Plans d\'action prioritaires' },
          { to: '/tools', icon: <Zap size={15} />, label: 'Outils', desc: 'Catalogue cybersécurité' },
          { to: '/cves', icon: <Shield size={15} />, label: 'CVE', desc: 'Base de vulnérabilités' },
        ].map(link => (
          <Link
            key={link.to}
            to={link.to as any}
            className="surface rounded-xl p-4 cursor-pointer transition-all hover:shadow-md hover:-translate-y-0.5"
            style={{ border: '1px solid var(--border)', textDecoration: 'none' }}
          >
            <div style={{ color: 'var(--brand-text)' }} className="mb-2">{link.icon}</div>
            <div className="body-sm font-semibold" style={{ color: 'var(--text)' }}>{link.label}</div>
            <div className="text-xs mt-0.5 text-muted">{link.desc}</div>
          </Link>
        ))}
      </div>
    </div>
  )
}

/* ── Decision Hero Card ─────────────────────────────────────── */

function DecisionHero({ decision, orgId }: { decision: PriorityDecision; orgId?: number }) {
  const [creating, setCreating] = useState(false)
  const [done, setDone] = useState(false)
  const dl = decision.level === 'CRITIQUE' ? 'CRITIQUE' : decision.level === 'ELEVE' ? 'ELEVE' : decision.level === 'MOYEN' ? 'MOYEN' : 'BAS'
  const colors = LEVEL_COLOR[dl] || LEVEL_COLOR.BAS

  const startMission = async () => {
    if (!orgId) { window.location.href = '/organization'; return }
    setCreating(true)
    await fetch(`/api/missions?org_id=${orgId}&cve_id=${encodeURIComponent(decision.cve_id)}&desc=${encodeURIComponent(decision.description.slice(0, 200))}&cvss=${decision.cvss_score || 0}`, { method: 'POST' })
    setCreating(false); setDone(true); setTimeout(() => setDone(false), 2000)
  }

  return (
    <div
      className="card-hero p-6 sm:p-8"
      role="region"
      aria-label="Décision principale"
      style={{ borderLeft: `4px solid ${colors.border}` }}
    >
      {/* Top label */}
      <span className="badge badge-brand mb-3">Votre prochaine décision</span>

      {/* Title */}
      <h2 className="h2 mb-3" style={{ color: 'var(--text)' }}>
        {decision.description.slice(0, 140)}
      </h2>

      {/* Meta */}
      <div className="flex flex-wrap items-center gap-2.5 mb-5">
        <span className="mono font-semibold" style={{ color: 'var(--decision-text)' }}>
          {decision.cve_id}
        </span>
        {decision.cvss_score != null && (
          <span className="text-xs font-bold" style={{ color: 'var(--critical-text)' }}>
            CVSS {decision.cvss_score}
          </span>
        )}
        <span
          className="text-xs font-semibold px-2 py-0.5 rounded-full border"
          style={{ background: colors.bg, color: colors.text, borderColor: colors.border }}
        >
          {LEVEL_LABEL[dl] || dl}
        </span>
        {decision.is_kev && (
          <span
            className="text-xs font-semibold px-2 py-0.5 rounded-full border flex items-center gap-1"
            style={{ background: 'var(--critical-light)', color: 'var(--critical-text)', borderColor: 'var(--critical)' }}
          >
            <AlertTriangle size={10} /> CISA KEV
          </span>
        )}
      </div>

      {/* Score grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
        {[
          { value: decision.score, label: 'Score priorité' },
          { value: decision.confidence, label: 'Confiance' },
          { value: decision.exploits_count, label: `Exploit${decision.exploits_count > 1 ? 's' : ''} publics` },
          { value: decision.is_kev ? 'Oui' : 'Non', label: 'CISA KEV' },
        ].map((s, i) => (
          <div
            key={i}
            className="rounded-xl p-3.5 text-center"
            style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}
          >
            <div className="text-xl font-bold" style={{ color: 'var(--text)' }}>{s.value}</div>
            <div className="text-xs mt-0.5 text-muted">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Reasons */}
      <div className="space-y-2.5 mb-5">
        {decision.reasons.map((r, i) => (
          <div key={i} className="flex items-start gap-2.5 body-sm" style={{ color: 'var(--text)' }}>
            <ChevronRight size={15} className="shrink-0 mt-0.5" style={{ color: 'var(--brand-text)' }} />
            <span>{r}</span>
          </div>
        ))}
      </div>

      {/* Risk if ignored */}
      <div
        className="rounded-xl p-4 mb-5"
        style={{ background: 'var(--mission-light)', border: '1px solid var(--mission)', borderLeft: '4px solid var(--mission)' }}
        role="alert"
      >
        <p className="caption mb-1" style={{ color: 'var(--mission-text)' }}>Si vous ignorez</p>
        <p className="body-sm" style={{ color: 'var(--text)' }}>{decision.risk_if_ignored}</p>
      </div>

      {/* Sources */}
      <div className="flex items-center gap-2 text-xs text-muted mb-5">
        <Brain size={12} />
        <span>Sources : {decision.sources.join(', ')}</span>
      </div>

      {/* CTA */}
      <button
        onClick={startMission}
        disabled={creating}
        aria-label={orgId ? 'Commencer la mission' : "Configurer l'organisation"}
        className="btn-primary text-sm"
      >
        {creating ? 'Création...' : done ? '✓ Mission créée !' : orgId ? (
          <><Play size={16} /> Commencer la mission</>
        ) : (
          <>Configurer l'organisation <ArrowRight size={16} /></>
        )}
      </button>
    </div>
  )
}

/* ── Decision Block ─────────────────────────────────────────── */

function DecisionBlock({ title, subtitle, icon, decisions, color }: {
  title: string; subtitle: string; icon: React.ReactNode; decisions: PriorityDecision[]; color: string
}) {
  return (
    <div
      className="surface p-5 sm:p-6"
      role="region"
      aria-label={title}
      style={{ border: '1px solid var(--border)' }}
    >
      <div className="flex items-center gap-2.5 mb-1">
        <span style={{ color }}>{icon}</span>
        <h3 className="h3" style={{ color: 'var(--text)' }}>{title}</h3>
      </div>
      <p className="caption mb-4 text-muted">{subtitle}</p>

      {decisions.length === 0 ? (
        <p className="body-sm text-muted py-6 text-center">Aucune décision</p>
      ) : (
        <div className="space-y-2.5">
          {decisions.map((d, i) => {
            const dl = d.level === 'CRITIQUE' ? 'CRITIQUE' : d.level === 'ELEVE' ? 'ELEVE' : d.level === 'MOYEN' ? 'MOYEN' : 'BAS'
            const colors = LEVEL_COLOR[dl] || LEVEL_COLOR.BAS
            return (
              <Link
                key={i}
                to="/cve/$id"
                params={{ id: d.cve_id }}
                className="rounded-xl p-3.5 flex items-center justify-between gap-2 cursor-pointer transition-all hover:-translate-y-0.5"
                style={{
                  background: 'var(--bg-alt)',
                  border: '1px solid var(--border-light)',
                  textDecoration: 'none',
                }}
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ background: colors.dot }} />
                    <span className="mono font-semibold" style={{ color: 'var(--decision-text)' }}>{d.cve_id}</span>
                    <span
                      className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full border"
                      style={{ background: colors.bg, color: colors.text, borderColor: colors.border }}
                    >
                      {LEVEL_LABEL[dl]}
                    </span>
                  </div>
                  <p className="text-xs text-secondary line-clamp-1">{d.description.slice(0, 90)}</p>
                </div>
                <span className="text-lg font-bold shrink-0" style={{ color: 'var(--text)' }}>{d.score}</span>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
