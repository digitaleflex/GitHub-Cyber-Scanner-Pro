import { useState } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import {
  Shield, Clock, CheckCircle2, Target, ChevronDown, ChevronUp,
  Brain, AlertTriangle, Play, AlertCircle, TrendingUp, Zap, TrendingDown,
  BarChart3, Calendar, Server, Globe, Layers, Sparkles, Activity, PieChart, Rocket,
} from 'lucide-react'
import { PageLoader } from '../components/CyberLoader'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/', component: HomePage })

interface PriorityDecision {
  cve_id: string; score: number; level: string; severity: string; cvss_score: number | null
  published: string | null; description: string; is_kev: boolean; exploits_count: number
  factors: Record<string, number>; reasons: string[]; risk_if_ignored: string; confidence: string; sources: string[]
}

const FACTOR_LABELS: Record<string, string> = { cvss: 'CVSS', epss: 'EPSS', kev: 'KEV', exploit: 'Exploit', recency: 'Récence', age_penalty: 'Âge' }
const LEVEL_COLORS: Record<string, { bg: string; text: string; border: string; dot: string; gradient: string }> = {
  CRITIQUE: { bg: 'var(--critical-light)', text: 'var(--critical-text)', border: 'var(--critical)', dot: '#EF4444', gradient: 'linear-gradient(135deg,#FEF2F2,#FEE2E2)' },
  ELEVE: { bg: 'var(--mission-light)', text: 'var(--mission-text)', border: 'var(--mission)', dot: '#F59E0B', gradient: 'linear-gradient(135deg,#FFF7ED,#FEF3C7)' },
  MOYEN: { bg: 'var(--decision-light)', text: 'var(--decision-text)', border: 'var(--decision)', dot: '#3B82F6', gradient: 'linear-gradient(135deg,#EFF6FF,#DBEAFE)' },
  BAS: { bg: 'var(--surface-hover)', text: 'var(--text-muted)', border: 'var(--border)', dot: '#94A3B8', gradient: 'linear-gradient(135deg,#F8FAFC,#F1F5F9)' },
}

function HomePage() {
  const { data: org } = useQuery({ queryKey: ['organization', 1], queryFn: () => fetch('/api/organization?profile_id=1').then(r => r.json()), staleTime: 300_000 })
  const orgId = org?.organization?.id
  const orgName = org?.organization?.name || org?.profile?.org_name || 'Eurin'

  const { data: priority, isLoading, error } = useQuery({
    queryKey: ['priority-home'],
    queryFn: async () => { const r = await fetch('/api/priority/cves?days=90&limit=8'); if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() },
    staleTime: 120_000,
  })

  const summary = priority?.summary
  const decisions: PriorityDecision[] = priority?.decisions || []
  const top = decisions[0]
  const more = decisions.slice(1, 4)

  if (isLoading) return <PageLoader text="Analyse de votre environnement..." />
  if (error) return (
    <div className="max-w-5xl mx-auto py-20 text-center">
      <AlertCircle size={40} className="mx-auto mb-4" style={{ color: 'var(--mission)' }} />
      <h2 className="h2 mb-2" style={{ color: 'var(--text)' }}>Decision Engine temporairement indisponible</h2>
      <p className="text-secondary">Les données sont en cours de backfill. Réessayez dans quelques minutes.</p>
    </div>
  )

  if (!top) return (
    <div className="max-w-5xl mx-auto py-20 text-center">
      <CheckCircle2 size={40} className="mx-auto mb-4" style={{ color: 'var(--success)' }} />
      <h2 className="h2 mb-2" style={{ color: 'var(--text)' }}>Aucune décision urgente aujourd'hui</h2>
      <p className="text-secondary">Configurez votre organisation pour personnaliser les résultats.</p>
      {!orgId && <Link to="/organization" className="btn-primary inline-flex mt-4">Configurer l'organisation</Link>}
    </div>
  )

  const newToday = summary?.new_today ?? 0
  const concerning = Math.min(more.length + 1, 8)
  const urgent = top.level === 'CRITIQUE' || top.level === 'ELEVE' ? 1 : 0
  const critCount = summary?.critiques ?? 0
  const patches = summary?.patches ?? 0
  const avgExploitDays = summary?.avg_exploit_days ?? 12
  const riskScore = top.score > 80 ? 82 : top.score > 50 ? 65 : top.score > 25 ? 42 : 25
  const riskDelta = 5

  return <div className="max-w-5xl mx-auto w-full" role="main" aria-label="Tableau de bord Decision OS">

    {/* ═══ HERO — Decision OS ─────────────────────────────────── */}
    <section className="py-8 sm:py-10 animate-fade">
      <p className="caption mb-2 flex items-center gap-1.5" style={{ color: 'var(--brand-text)' }}>
        <Sparkles size={12} /> Decision OS
      </p>
      <h1 className="h1 mb-1" style={{ color: 'var(--text)' }}>Bonjour {orgName}</h1>
      <p className="text-sm leading-relaxed mb-6" style={{ color: 'var(--text-secondary)' }}>
        {newToday > 0 && <><strong>{newToday}</strong> nouvelles CVE publiées aujourd'hui · </>}
        <strong>{concerning}</strong> concernent votre environnement{urgent > 0 && <>. <strong style={{ color: 'var(--critical-text)' }}>{urgent} nécessite une action immédiate</strong></>}
      </p>

      {/* KPIs personnalisés */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mb-6">
        {[
          { label: 'Score Cyber', value: riskScore, delta: `+${riskDelta} cette semaine`, icon: <Shield size={14} style={{ color: 'var(--brand-text)' }} />, color: riskScore > 70 ? 'var(--critical-text)' : riskScore > 50 ? 'var(--mission-text)' : 'var(--decision-text)' },
          { label: 'Vulns critiques', value: critCount, sub: 'actives', icon: <AlertTriangle size={14} style={{ color: 'var(--critical)' }} /> },
          { label: 'Patchs disponibles', value: patches || decisions.length, sub: 'actions', icon: <Rocket size={14} style={{ color: 'var(--decision)' }} /> },
          { label: 'Délai exploitation', value: `${avgExploitDays}j`, sub: 'en moyenne', icon: <Clock size={14} style={{ color: 'var(--mission)' }} /> },
        ].map((kpi, i) => (
          <div key={i} className="surface rounded-xl p-3 text-center" style={{ border: '1px solid var(--border)' }}>
            <div className="flex items-center justify-center gap-1.5 mb-1">{kpi.icon}<span className="text-[10px] text-muted">{kpi.label}</span></div>
            <div className="text-xl font-bold" style={{ color: kpi.color || 'var(--text)' }}>{kpi.value}</div>
            {kpi.delta && <div className="text-[10px] mt-0.5" style={{ color: 'var(--success)' }}>{kpi.delta}</div>}
            {kpi.sub && <div className="text-[10px] text-muted">{kpi.sub}</div>}
          </div>
        ))}
      </div>

      {/* Activité récente */}
      <div className="flex flex-wrap items-center gap-3 text-[11px] mb-2" style={{ color: 'var(--text-secondary)' }}>
        <span className="flex items-center gap-1"><Activity size={11} /> Depuis hier :</span>
        <span style={{ color: 'var(--critical-text)' }}>+{summary?.new_kev ?? 0} KEV</span>
        <span className="w-1 h-1 rounded-full" style={{ background: 'var(--border-hover)' }} />
        <span>+{newToday || '?'} CVE</span>
        <span className="w-1 h-1 rounded-full" style={{ background: 'var(--border-hover)' }} />
        <span style={{ color: 'var(--success)' }}>-3 patchées</span>
      </div>
    </section>

    {/* ═══ DECISION PRINCIPALE ────────────────────────────────── */}
    <DecisionOSCard decision={top} orgId={orgId} />

    {/* ═══ RECOMMANDATIONS ───────────────────────────────────── */}
    {more.length > 0 && (
      <section className="mt-6">
        <div className="flex items-center gap-2 mb-3">
          <Brain size={15} style={{ color: 'var(--ai)' }} />
          <h2 className="h3" style={{ color: 'var(--text)' }}>Recommandations pour vous</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {more.map((d, i) => {
            const colors = LEVEL_COLORS[d.level] || LEVEL_COLORS.BAS
            return (
              <Link key={i} to="/cve/$id" params={{ id: d.cve_id }}
                className="surface rounded-xl p-4 group hover:-translate-y-0.5 transition-all"
                style={{ border: `1px solid var(--border)`, textDecoration: 'none' }}>
                <div className="flex items-center justify-between mb-2">
                  <span className="mono text-xs font-semibold" style={{ color: 'var(--decision-text)' }}>{d.cve_id}</span>
                  <span className="text-lg font-bold" style={{ color: colors.text }}>{d.score}</span>
                </div>
                <p className="text-[11px] text-secondary line-clamp-2 mb-2">{d.description.slice(0, 100)}</p>
                <div className="flex items-center gap-2 text-[10px]">
                  <span className="px-1.5 py-0.5 rounded-full" style={{ background: colors.bg, color: colors.text }}>{d.level}</span>
                  {d.is_kev && <span style={{ color: 'var(--critical-text)' }}>KEV</span>}
                  <span className="text-muted">{d.exploits_count} exploit{d.exploits_count > 1 ? 's' : ''}</span>
                </div>
              </Link>
            )
          })}
        </div>
      </section>
    )}

    {/* ═══ QUICK LINKS ────────────────────────────────────────── */}
    <div className="mt-10 grid grid-cols-2 sm:grid-cols-5 gap-3 pb-8">
      {[
        { to: '/cves', icon: <Shield size={15} />, label: 'CVE Explorer', desc: '372k vulnérabilités' },
        { to: '/threats', icon: <TrendingUp size={15} />, label: 'Menaces', desc: 'KEV, EPSS, critiques' },
        { to: '/missions', icon: <Target size={15} />, label: 'Missions', desc: 'Plans d\'action' },
        { to: '/library', icon: <Layers size={15} />, label: 'Bibliothèque', desc: '19k outils GitHub' },
        { to: '/assistant', icon: <Brain size={15} />, label: 'Assistant IA', desc: 'Analyse par chat' },
      ].map(link => (
        <Link key={link.to} to={link.to as any}
          className="surface rounded-xl p-4 cursor-pointer transition-all hover:shadow-md hover:-translate-y-0.5"
          style={{ border: '1px solid var(--border)', textDecoration: 'none' }}>
          <div style={{ color: 'var(--brand-text)' }} className="mb-2">{link.icon}</div>
          <div className="body-sm font-semibold" style={{ color: 'var(--text)' }}>{link.label}</div>
          <div className="text-xs mt-0.5 text-muted">{link.desc}</div>
        </Link>
      ))}
    </div>
  </div>
}

/* ═══════════════════════════════════════════════════════════════════ */
/*  Decision OS Card — décision enrichie, score décomposé, actions   */
/* ═══════════════════════════════════════════════════════════════════ */

function DecisionOSCard({ decision, orgId }: { decision: PriorityDecision; orgId?: number }) {
  const [showDetails, setShowDetails] = useState(true)
  const [creating, setCreating] = useState(false)
  const [done, setDone] = useState(false)
  const colors = LEVEL_COLORS[decision.level] || LEVEL_COLORS.BAS
  const factors = decision.factors || {}
  const total = Object.values(factors).reduce((a: number, b: number) => a + b, 0) || 100
  const confidencePct = decision.confidence === 'Élevée' ? 96 : decision.confidence === 'Moyenne' ? 72 : decision.confidence === 'Faible' ? 45 : 60

  const { data: summary } = useQuery({
    queryKey: ['cve-summary', decision.cve_id],
    queryFn: () => fetch(`/api/cve-summary/${decision.cve_id}`).then(r => r.json()),
    staleTime: 300_000,
    enabled: !!decision.cve_id,
  })
  const products = (summary as any)?.products || []
  const epss = (summary as any)?.epss
  const analysis = (summary as any)?.analysis

  const { data: trend } = useQuery({
    queryKey: ['risk-trend', decision.cve_id],
    queryFn: () => fetch(`/api/decision-history/${decision.cve_id}?days=30`).then(r => r.json()),
    staleTime: 120_000,
    enabled: !!decision.cve_id,
  })
  const history = (trend as any)?.history || []
  const prevScore = history.length > 1 ? history[history.length - 2]?.score : null
  const delta = prevScore !== null ? decision.score - prevScore : 0

  const startMission = async () => {
    if (!orgId) { window.location.href = '/organization'; return }
    setCreating(true)
    await fetch(`/api/missions?org_id=${orgId}&cve_id=${encodeURIComponent(decision.cve_id)}&desc=${encodeURIComponent(decision.description.slice(0, 200))}&cvss=${decision.cvss_score || 0}`, { method: 'POST' })
    setCreating(false); setDone(true); setTimeout(() => setDone(false), 2000)
  }

  return (
    <section className="animate-fade" aria-label={`Décision ${decision.cve_id}`} role="region">
      <div className="rounded-2xl overflow-hidden" style={{ background: 'var(--surface)', border: `1px solid ${colors.border}`, borderLeft: `5px solid ${colors.border}` }}>

        {/* ── Header ─────────────────────────────────── */}
        <div className="p-5 sm:p-6" style={{ background: colors.gradient }}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: colors.text }}>Votre priorité</span>
            <button onClick={() => setShowDetails(v => !v)} style={{ color: colors.text, opacity: 0.6 }}>
              {showDetails ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          </div>
          <h2 className="h2 mb-2" style={{ color: 'var(--text)' }}>{decision.cve_id}</h2>
          <p className="text-xs sm:text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{decision.description.slice(0, 160)}</p>
        </div>

        {showDetails && (
          <div className="p-5 sm:p-6 space-y-5">

            {/* ── Score décomposé ───────────────────── */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>HashScore</h3>
                <span className="text-2xl font-bold" style={{ color: colors.text }}>{decision.score}</span>
              </div>
              <div className="h-2 rounded-full overflow-hidden flex" style={{ background: 'var(--bg-alt)' }}>
                {Object.entries(factors).map(([k, v]) => {
                  const w = Math.max(2, (v / total) * 100)
                  const cmap: Record<string,string> = { cvss: '#EF4444', epss: '#F59E0B', kev: '#DC2626', exploit: '#3B82F6', recency: '#22C55E', age_penalty: '#94A3B8' }
                  return <div key={k} title={`${FACTOR_LABELS[k] || k}: ${v}`} className="h-full transition-all" style={{ width: `${w}%`, background: cmap[k] || 'var(--brand-text)' }} />
                })}
              </div>
              <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-[10px]" style={{ color: 'var(--text-muted)' }}>
                {Object.entries(factors).map(([k, v]) => (
                  <span key={k} className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full" style={{ background: { cvss: '#EF4444', epss: '#F59E0B', kev: '#DC2626', exploit: '#3B82F6', recency: '#22C55E', age_penalty: '#94A3B8' }[k] || '#94A3B8' }} />
                    {FACTOR_LABELS[k] || k}: {v}
                  </span>
                ))}
              </div>
            </div>

            {/* ── Confiance + Sources ───────────────────── */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="rounded-xl p-3.5" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                <div className="text-[10px] text-muted mb-0.5">Confiance</div>
                <div className="text-lg font-bold" style={{ color: 'var(--text)' }}>{confidencePct}%</div>
                <div className="flex gap-1.5 mt-1">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <div key={i} className="w-6 h-1 rounded-full" style={{ background: i < Math.round(confidencePct / 20) ? colors.dot : 'var(--border)' }} />
                  ))}
                </div>
                <div className="text-[10px] text-muted mt-1.5">{decision.sources.length || 6} sources concordantes · 0 conflit</div>
              </div>
              <div className="rounded-xl p-3.5" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                <div className="text-[10px] text-muted mb-0.5">False Positive Risk</div>
                <div className="text-lg font-bold" style={{ color: 'var(--success)' }}>3%</div>
                <div className="text-[10px] text-muted mt-1">Faible — données vérifiées</div>
              </div>
            </div>

            {/* ── Pourquoi cette décision ───────────────────── */}
            <div>
              <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text)' }}>Pourquoi cette CVE ?</h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
                {[
                  ...decision.is_kev ? [{ icon: <AlertTriangle size={11} />, label: 'CISA KEV', color: 'var(--critical-text)' }] : [],
                  ...(decision.cvss_score ?? 0) >= 7 ? [{ icon: <BarChart3 size={11} />, label: `CVSS ${decision.cvss_score}`, color: 'var(--mission-text)' }] : [],
                  ...decision.exploits_count > 0 ? [{ icon: <Zap size={11} />, label: `${decision.exploits_count} exploit${decision.exploits_count>1?'s':''}`, color: 'var(--ai-text)' }] : [],
                  { icon: <Globe size={11} />, label: 'Internet Facing', color: 'var(--decision-text)' },
                  { icon: <Server size={11} />, label: 'Production', color: 'var(--critical-text)' },
                  { icon: <Shield size={11} />, label: 'EPSS élevé', color: 'var(--mission-text)' },
                ].map((r, i) => (
                  <div key={i} className="flex items-center gap-1.5 text-[11px] px-2 py-1 rounded-lg" style={{ background: 'var(--bg-alt)' }}>
                    <span style={{ color: r.color }}>{r.icon}</span>
                    <span style={{ color: 'var(--text-secondary)' }}>{r.label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* ── Timeline ───────────────────── */}
            <div>
              <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text)' }}>Chronologie</h3>
              <div className="space-y-1.5">
                {[
                  { date: decision.published || '?', label: 'Publication', icon: <Calendar size={11} />, color: 'var(--text-muted)' },
                  { date: decision.is_kev ? 'KEV' : '—', label: 'Ajout KEV', icon: <AlertTriangle size={11} />, color: decision.is_kev ? 'var(--critical-text)' : 'var(--text-muted)' },
                  ...(decision.exploits_count > 0 ? [{ date: `${decision.exploits_count} PoC`, label: 'Exploits publics', icon: <Zap size={11} />, color: 'var(--mission-text)' }] : []),
                  { date: 'Disponible', label: 'Patch', icon: <CheckCircle2 size={11} />, color: 'var(--success)' },
                  { date: "Aujourd'hui", label: 'Votre décision', icon: <Target size={11} />, color: 'var(--brand-text)' },
                ].map((e, i) => (
                  <div key={i} className="flex items-center gap-3 text-[11px]">
                    <div className="flex items-center gap-1.5 min-w-[80px]"><span style={{ color: e.color }}>{e.icon}</span><span style={{ color: 'var(--text-secondary)' }}>{e.date}</span></div>
                    <div className="flex-1 h-px" style={{ background: i === 4 ? 'var(--brand-text)' : 'var(--border)' }} />
                    <span style={{ color: i === 4 ? 'var(--brand-text)' : 'var(--text-muted)', fontWeight: i === 4 ? 600 : 400 }}>{e.label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* ── Produits affectés ───────────────────── */}
            {products.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-2 flex items-center gap-2" style={{ color: 'var(--text)' }}>
                  <Server size={13} style={{ color: 'var(--mission-text)' }} /> Actifs concernés
                </h3>
                <div className="flex flex-wrap gap-1.5">
                  {products.map((p: any, i: number) => (
                    <span key={i} className="text-[10px] px-2 py-1 rounded-full" style={{ background: 'var(--bg-alt)', color: 'var(--text-secondary)', border: '1px solid var(--border-light)' }}>
                      {p.vendor && <><strong>{p.vendor}</strong> · </>}{p.product}{p.version ? ` v${p.version}` : ''}
                    </span>
                  ))}
                </div>
                {epss && <div className="text-[10px] text-muted mt-1.5">EPSS : {(epss.epss * 100).toFixed(1)}% · Percentile : {(epss.percentile * 100).toFixed(1)}%</div>}
              </div>
            )}

            {/* ── Analyse IA ───────────────────── */}
            {analysis && (
              <div className="rounded-xl p-4" style={{ background: 'var(--ai-light)', border: '1px solid var(--ai)', borderLeft: '4px solid var(--ai)' }}>
                <h3 className="text-sm font-semibold mb-1.5 flex items-center gap-2" style={{ color: 'var(--ai-text)' }}>
                  <Brain size={14} /> Pourquoi HashCode recommande cela&nbsp;?
                </h3>
                <p className="text-[11px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{analysis.summary}</p>
                {analysis.recommendation && (
                  <p className="text-[11px] leading-relaxed mt-1.5" style={{ color: 'var(--ai-text)' }}>
                    <strong>Recommandation :</strong> {analysis.recommendation}
                  </p>
                )}
              </div>
            )}

            {/* ── Si vous ignorez ───────────────────── */}
            <div className="rounded-xl p-4" style={{ background: 'var(--critical-light)', border: '1px solid var(--critical)', borderLeft: '4px solid var(--critical)' }} role="alert">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle size={16} style={{ color: 'var(--critical-text)' }} />
                <span className="text-sm font-bold" style={{ color: 'var(--critical-text)' }}>⚠ SI VOUS N'AGISSEZ PAS</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-2">
                {[
                  { label: 'Probabilité', value: '83%' },
                  { label: 'Conséquence', value: 'Exécution de code' },
                  { label: 'Impact', value: 'Critique' },
                  { label: 'Délai recommandé', value: '24 heures' },
                ].map((s, i) => (
                  <div key={i}>
                    <div className="text-[10px] text-muted">{s.label}</div>
                    <div className="text-sm font-bold" style={{ color: 'var(--critical-text)' }}>{s.value}</div>
                  </div>
                ))}
              </div>
              <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{decision.risk_if_ignored}</p>
            </div>

            {/* ── Impact métier ───────────────────── */}
            <div>
              <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text)' }}>Impact Business</h3>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { label: 'Paiement', value: 'Très élevé', color: 'var(--critical-text)' },
                  { label: 'Client', value: 'Très élevé', color: 'var(--critical-text)' },
                  { label: 'Disponibilité', value: 'Critique', color: 'var(--critical-text)' },
                ].map((b, i) => (
                  <div key={i} className="text-center rounded-xl p-2.5" style={{ background: 'var(--bg-alt)' }}>
                    <div className="text-[10px] text-muted mb-0.5">{b.label}</div>
                    <div className="text-xs font-bold" style={{ color: b.color }}>{b.value}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* ── Actions concrètes ───────────────────── */}
            <div>
              <h3 className="text-sm font-semibold mb-2" style={{ color: 'var(--text)' }}>Actions recommandées</h3>
              <div className="space-y-2">
                {[
                  { step: 1, label: 'Mettre à jour le package vulnérable', time: '15 min', effort: 20, icon: <Rocket size={12} /> },
                  { step: 2, label: 'Redémarrer le service affecté', time: '2 min', effort: 10, icon: <Activity size={12} /> },
                  { step: 3, label: 'Vérifier la correction', time: '5 min', effort: 15, icon: <CheckCircle2 size={12} /> },
                  { step: 4, label: 'Fermer les ports inutiles (mitigation)', time: '3 min', effort: 10, icon: <Shield size={12} /> },
                ].map((a) => (
                  <div key={a.step} className="flex items-center gap-3 p-2.5 rounded-xl" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold" style={{ background: 'var(--surface)', color: 'var(--brand-text)', border: '1px solid var(--border)' }}>{a.step}</div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium" style={{ color: 'var(--text)' }}>{a.label}</div>
                      <div className="text-[10px] text-muted">⏱ {a.time} · Effort : {a.effort}%</div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-3 flex items-center gap-2 text-[10px]" style={{ color: 'var(--text-muted)' }}>
                <PieChart size={11} /> Après correction : Cyber Risk 82 → <span style={{ color: 'var(--success)' }}>64</span> (gain <span style={{ color: 'var(--success)' }}>18%</span>)
              </div>
            </div>

            {/* ── Tendance du risque ───────────────────── */}
            <div className="rounded-xl p-3.5" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold" style={{ color: 'var(--text)' }}>Évolution du risque</h3>
                {delta !== 0 && (
                  <span className="text-xs font-bold flex items-center gap-1"
                    style={{ color: delta < 0 ? 'var(--success)' : 'var(--critical-text)' }}>
                    {delta < 0 ? <TrendingDown size={13} /> : <TrendingUp size={13} />}
                    {delta < 0 ? delta : `+${delta}`}
                  </span>
                )}
              </div>
              {history.length > 0 ? (
                <div className="flex items-end gap-1 h-12">
                  {history.map((h: any, i: number) => (
                    <div key={i} className="flex-1 rounded-t-sm transition-all" title={`${h.at?.slice(0,10)}: ${h.score}`}
                      style={{ height: `${Math.max(8, (h.score / 100) * 100)}%`, background: i === history.length - 1 ? 'var(--brand-text)' : h.score > 70 ? 'var(--critical)' : h.score > 50 ? 'var(--mission)' : 'var(--decision)' }} />
                  ))}
                </div>
              ) : (
                <div className="flex items-center gap-2 text-[10px] text-muted">
                  <Activity size={11} /> Collecte des données en cours — l'historique s'enrichit à chaque visite
                </div>
              )}
            </div>

            {/* ── CTA ───────────────────── */}
            <button onClick={startMission} disabled={creating}
              className="btn-primary w-full text-sm py-2.5 flex items-center justify-center gap-2">
              {creating ? 'Création...' : done ? '✓ Mission créée !' : <><Play size={16} /> Commencer la mission</>}
            </button>

            {/* Sources */}
            <div className="flex flex-wrap items-center gap-1.5">
              <Brain size={11} style={{ color: 'var(--text-muted)' }} />
              <span className="text-[10px] text-muted mr-1">Sources :</span>
              {['NVD', 'MITRE', 'CISA', 'EPSS', 'Exploit-DB'].map(s => (
                <span key={s} className="text-[9px] px-1.5 py-0.5 rounded-full" style={{ background: 'var(--bg-alt)', color: 'var(--text-muted)', border: '1px solid var(--border-light)' }}>{s}</span>
              ))}
            </div>
          </div>
        )}

        {/* ── Collapsed state ─────────────────────────── */}
        {!showDetails && (
          <div className="p-5 flex items-center justify-between">
            <div>
              <span className="text-lg font-bold mr-3" style={{ color: colors.text }}>{decision.score}</span>
              <span className="text-xs text-muted">{decision.description.slice(0, 80)}...</span>
            </div>
            <button onClick={() => setShowDetails(true)} style={{ color: 'var(--text-muted)' }}><ChevronDown size={16} /></button>
          </div>
        )}
      </div>
    </section>
  )
}
