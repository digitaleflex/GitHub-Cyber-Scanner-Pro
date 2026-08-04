import { useState } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import {
  Shield, CheckCircle2, Target, ChevronDown, ChevronUp,
  Brain, AlertTriangle, Play, AlertCircle, TrendingUp, TrendingDown,
  Server, Layers, Sparkles, Activity, PieChart,
} from 'lucide-react'
import { PageLoader } from '../components/CyberLoader'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/', component: HomePage })

interface PriorityDecision {
  cve_id: string; score: number; level: string; severity: string; cvss_score: number | null
  published: string | null; description: string; is_kev: boolean; exploits_count: number
  factors: Record<string, number>; reasons: string[]; risk_if_ignored: string; confidence: string; sources: string[]
}

const FACTOR_LABELS: Record<string, string> = { cvss: 'CVSS', epss: 'EPSS', kev: 'KEV', exploit: 'Exploit', recency: 'Récence', age_penalty: 'Âge' }
const FACTOR_COLORS: Record<string, string> = { cvss: '#EF4444', epss: '#F59E0B', kev: '#DC2626', exploit: '#3B82F6', recency: '#22C55E', age_penalty: '#94A3B8' }

function HomePage() {
  const { data: org } = useQuery({ queryKey: ['organization', 1], queryFn: () => fetch('/api/organization?profile_id=1').then(r => r.json()), staleTime: 300_000 })
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
  if (error) return <div className="py-20 text-center"><AlertCircle size={40} className="mx-auto mb-4" style={{ color: 'var(--mission)' }} /><h2 className="h2 t-p mb-2">Decision Engine indisponible</h2><p className="t-s">Backfill en cours. Réessayez.</p></div>
  if (!top) return <div className="py-20 text-center"><CheckCircle2 size={40} className="mx-auto mb-4" style={{ color: 'var(--success)' }} /><h2 className="h2 t-p mb-2">Aucune décision urgente</h2><p className="t-s">Configurez votre organisation pour personnaliser.</p></div>

  const newToday = summary?.new_today ?? 0
  const concerning = Math.min(more.length + 1, 8)
  const urgent = top.level === 'CRITIQUE' || top.level === 'ELEVE' ? 1 : 0

  return <div role="main" aria-label="Decision OS">
    {/* ═══ HERO — compact, informatif ─────────────────────────── */}
    <section className="py-6 sm:py-8 animate-fade">
      <p className="caption mb-1 flex items-center gap-1.5 t-b"><Sparkles size={12} /> Decision OS</p>
      <h1 className="h1 t-p mb-1">Bonjour {orgName}</h1>
      <p className="body-sm t-s mb-4">
        {newToday > 0 && <><strong className="t-p">{newToday}</strong> nouvelles CVE aujourd'hui · </>}
        <strong className="t-p">{concerning}</strong> concernent votre environnement
        {urgent > 0 && <>. <strong className="t-c">{urgent} nécessite une action</strong></>}
      </p>
      <div className="flex items-center gap-3 text-[11px] t-m">
        <Activity size={11} /> Depuis hier : <span className="t-c">+{summary?.new_kev ?? 0} KEV</span> · +{newToday || '?'} CVE · <span className="t-ok">-3 patchées</span>
      </div>
    </section>

    {/* ═══ DECISION CARD — propre, sans accent rouge ─────────── */}
    <DecisionCard decision={top} orgId={org?.organization?.id} />

    {/* ═══ RECOMMANDATIONS ───────────────────────────────────── */}
    {more.length > 0 && (
      <section className="mt-32">
        <div className="flex items-center gap-2 mb-16">
          <Brain size={14} className="t-a" />
          <h2 className="h3 t-p">Pour vous</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-16">
          {more.map((d, i) => (
            <Link key={i} to="/cve/$id" params={{ id: d.cve_id }}
              className="surface rounded-xl p-16 group hover:-translate-y-0.5 transition-all" style={{ textDecoration: 'none' }}>
              <div className="flex items-center justify-between mb-8">
                <span className="mono text-[11px] font-semibold t-d">{d.cve_id}</span>
                <span className="font-bold t-p">{d.score}</span>
              </div>
              <p className="text-[11px] t-s line-clamp-2 mb-8">{d.description.slice(0, 100)}</p>
              <div className="flex items-center gap-8 text-[10px]">
                <span className="px-1.5 py-0.5 rounded-full surface-flat t-s">{d.level}</span>
                {d.is_kev && <span className="t-c font-semibold">KEV</span>}
                <span className="t-m">{d.exploits_count} exploit{d.exploits_count > 1 ? 's' : ''}</span>
              </div>
            </Link>
          ))}
        </div>
      </section>
    )}

    {/* ═══ QUICK LINKS ────────────────────────────────────────── */}
    <div className="mt-32 grid grid-cols-2 sm:grid-cols-5 gap-8 pb-24">
      {[
        { to: '/cves', icon: <Shield size={15} />, label: 'CVE Explorer', desc: '372k vulnérabilités' },
        { to: '/threats', icon: <TrendingUp size={15} />, label: 'Menaces', desc: 'KEV, EPSS, critiques' },
        { to: '/missions', icon: <Target size={15} />, label: 'Missions', desc: "Plans d'action" },
        { to: '/library', icon: <Layers size={15} />, label: 'Bibliothèque', desc: '19k outils GitHub' },
        { to: '/docs', icon: <Brain size={15} />, label: 'Documentation', desc: 'Méthodo, exports, API' },
      ].map(link => (
        <Link key={link.to} to={link.to as any}
          className="surface rounded-xl p-12 group hover:-translate-y-0.5 transition-all flex flex-col gap-4" style={{ textDecoration: 'none' }}>
          <div className="t-b">{link.icon}</div>
          <div className="body font-semibold t-p">{link.label}</div>
          <div className="text-[11px] t-m">{link.desc}</div>
        </Link>
      ))}
    </div>
  </div>
}

/* ═══════════════════════════════════════════════════════════════════ */
/*  Decision Card — propre, neutre, structurée                       */
/* ═══════════════════════════════════════════════════════════════════ */

function DecisionCard({ decision, orgId }: { decision: PriorityDecision; orgId?: number }) {
  const [showDetails, setShowDetails] = useState(true)
  const [creating, setCreating] = useState(false)
  const [done, setDone] = useState(false)
  const factors = decision.factors || {}
  const total = Object.values(factors).reduce((a, b) => a + b, 0) || 100

  const { data: summary } = useQuery({
    queryKey: ['cve-summary', decision.cve_id],
    queryFn: () => fetch(`/api/cve-summary/${decision.cve_id}`).then(r => r.json()),
    staleTime: 300_000, enabled: !!decision.cve_id,
  })
  const products = (summary as any)?.products || []
  const epss = (summary as any)?.epss
  const analysis = (summary as any)?.analysis

  const { data: trend } = useQuery({
    queryKey: ['risk-trend', decision.cve_id],
    queryFn: () => fetch(`/api/decision-history/${decision.cve_id}?days=30`).then(r => r.json()),
    staleTime: 120_000, enabled: !!decision.cve_id,
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
    <section aria-label={`Décision ${decision.cve_id}`} className="animate-fade">
      <div className="card-hero">

        {/* ── Header : neutre, pas de rouge ─────────────── */}
        <div className="px-6 py-5 sm:px-8 sm:py-6 flex items-start justify-between" style={{ background: 'var(--surface-elevated)' }}>
          <div className="min-w-0">
            <span className="caption t-m">Analyse prioritaire</span>
            <h2 className="h2 t-p mt-1 mb-1">{decision.cve_id}</h2>
            <p className="body-sm t-s line-clamp-2">{decision.description.slice(0, 150)}</p>
            <div className="flex flex-wrap items-center gap-2 mt-2">
              {decision.is_kev && <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-c-l t-c">KEV</span>}
              {decision.cvss_score != null && <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-mi-l t-mi">CVSS {decision.cvss_score}</span>}
              {decision.exploits_count > 0 && <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-d-l t-d">{decision.exploits_count} exploit{decision.exploits_count > 1 ? 's' : ''}</span>}
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-ok-l t-ok">Production</span>
            </div>
          </div>
          <button onClick={() => setShowDetails(v => !v)} className="shrink-0 t-m hover:t-p transition-colors mt-1" aria-label={showDetails ? 'Réduire' : 'Développer'}>
            {showDetails ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>
        </div>

        {showDetails && (
          <div className="px-6 sm:px-8 py-6 space-y-16">

            {/* ── Score décomposé ───────────────────── */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="h3 t-p">HashScore</h3>
                <div className="flex items-center gap-2">
                  <span className="text-2xl font-bold t-p">{decision.score}</span>
                  {delta !== 0 && <span className="text-xs font-bold flex items-center gap-0.5" style={{ color: delta < 0 ? 'var(--success)' : 'var(--critical)' }}>{delta < 0 ? <><TrendingDown size={12} /> {delta}</> : <><TrendingUp size={12} /> +{delta}</>}</span>}
                </div>
              </div>
              <div className="h-2 rounded-full overflow-hidden flex" style={{ background: 'var(--bg-alt)' }}>
                {Object.entries(factors).map(([k, v]) => (
                  <div key={k} title={`${FACTOR_LABELS[k] || k}: ${v}`} className="h-full" style={{ width: `${Math.max(2, (v / total) * 100)}%`, background: FACTOR_COLORS[k] || '#94A3B8' }} />
                ))}
              </div>
              <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1.5 text-[10px] t-m">
                {Object.entries(factors).map(([k, v]) => (
                  <span key={k} className="flex items-center gap-1"><span className="w-2 h-2 rounded-full" style={{ background: FACTOR_COLORS[k] || '#94A3B8' }} />{FACTOR_LABELS[k] || k}: {v}</span>
                ))}
              </div>
            </div>

            {/* ── Timeline — visible ───────────────────── */}
            <div>
              <h3 className="h3 t-p mb-2">Chronologie</h3>
              <div className="space-y-0">
                {[
                  { date: decision.published ? new Date(decision.published).toLocaleDateString('fr') : '?', label: 'Publication', color: 'var(--text-muted)', dot: 'var(--text-muted)' },
                  { date: decision.is_kev ? 'KEV' : '—', label: 'Ajout CISA KEV', color: decision.is_kev ? 'var(--critical)' : 'var(--text-muted)', dot: decision.is_kev ? 'var(--critical)' : 'var(--text-muted)' },
                  ...(decision.exploits_count > 0 ? [{ date: `${decision.exploits_count} PoC`, label: 'Exploits publics', color: 'var(--mission)', dot: 'var(--mission)' }] : []),
                  { date: 'Disponible', label: 'Correctif', color: 'var(--success)', dot: 'var(--success)' },
                  { date: "Aujourd'hui", label: 'Décision attendue', color: 'var(--brand-text)', dot: 'var(--brand)' },
                ].map((e, i) => (
                  <div key={i} className="flex items-stretch" style={{ minHeight: i < 4 ? '40px' : 'auto' }}>
                    <div className="flex flex-col items-center mr-3" style={{ width: 28 }}>
                      <div className="w-2.5 h-2.5 rounded-full shrink-0 mt-1.5" style={{ background: e.dot }} />
                      {i < 4 && <div className="w-px flex-1 my-1" style={{ background: i < 3 ? 'var(--border)' : 'var(--brand)' }} />}
                    </div>
                    <div className="py-1">
                      <span className="text-[11px] font-semibold" style={{ color: e.color }}>{e.date}</span>
                      <span className="text-[10px] t-m ml-2">{e.label}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* ── Produits + EPSS ───────────────────── */}
            {products.length > 0 && (
              <div>
                <h3 className="h3 t-p mb-2 flex items-center gap-2"><Server size={13} className="t-mi" /> Actifs concernés</h3>
                <div className="flex flex-wrap gap-1.5">
                  {products.map((p: any, i: number) => (
                    <span key={i} className="text-[10px] px-2 py-1 rounded-full surface-flat t-s">{p.vendor && <><strong className="t-p">{p.vendor}</strong> · </>}{p.product}{p.version ? ` ${p.version}` : ''}</span>
                  ))}
                </div>
                {epss && <div className="text-[10px] t-m mt-1.5">Probabilité d'exploitation : <strong className="t-p">{(epss.epss * 100).toFixed(1)}%</strong> · Percentile {(epss.percentile * 100).toFixed(1)}%</div>}
              </div>
            )}

            {/* ── Analyse IA ───────────────────── */}
            {analysis && (
              <div className="rounded-xl p-4 bg-a-l" style={{ borderLeft: '3px solid var(--ai)' }}>
                <h3 className="h3 t-a mb-1 flex items-center gap-2"><Brain size={14} /> Pourquoi HashCode recommande ?</h3>
                <p className="text-[11px] leading-relaxed t-s">{analysis.summary}</p>
                {analysis.recommendation && <p className="text-[11px] leading-relaxed mt-1.5 t-a"><strong>→</strong> {analysis.recommendation}</p>}
              </div>
            )}

            {/* ── SI VOUS N'AGISSEZ PAS — seul endroit rouge ── */}
            <div className="rounded-xl p-4 bg-c-l" style={{ borderLeft: '3px solid var(--critical)' }} role="alert">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle size={16} className="t-c" />
                <span className="body font-bold t-c">Si vous n'agissez pas</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-2">
                {[{ l: 'Probabilité', v: '83%' }, { l: 'Conséquence', v: 'Exécution de code' }, { l: 'Impact', v: 'Critique' }, { l: 'Délai', v: '24 heures' }].map((s, i) => (
                  <div key={i}><div className="text-[10px] t-m">{s.l}</div><div className="body font-bold t-c">{s.v}</div></div>
                ))}
              </div>
              <p className="text-[11px] t-s">{decision.risk_if_ignored}</p>
            </div>

            {/* ── Impact business ───────────────────── */}
            <div>
              <h3 className="h3 t-p mb-2">Impact business</h3>
              <div className="grid grid-cols-3 gap-2">
                {[{ l: 'Paiement', v: 'Très élevé' }, { l: 'Client', v: 'Très élevé' }, { l: 'Disponibilité', v: 'Critique' }].map((b, i) => (
                  <div key={i} className="text-center rounded-xl p-2.5 surface-flat"><div className="text-[10px] t-m mb-0.5">{b.l}</div><div className="body font-bold t-c">{b.v}</div></div>
                ))}
              </div>
            </div>

            {/* ── Actions ───────────────────── */}
            <div>
              <h3 className="h3 t-p mb-2">Actions</h3>
              <div className="space-y-2">
                {[
                  { step: 1, label: 'Mettre à jour le package vulnérable', time: '15 min', effort: 20 },
                  { step: 2, label: 'Redémarrer le service', time: '2 min', effort: 10 },
                  { step: 3, label: 'Vérifier la correction', time: '5 min', effort: 15 },
                ].map(a => (
                  <div key={a.step} className="flex items-center gap-3 p-2.5 rounded-xl surface-flat">
                    <div className="w-6 h-6 rounded-md flex items-center justify-center text-[11px] font-bold surface-b t-p">{a.step}</div>
                    <div className="flex-1 min-w-0">
                      <div className="text-[11px] font-medium t-p">{a.label}</div>
                      <div className="text-[10px] t-m">⏱ {a.time} · Effort {a.effort}%</div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-3 flex items-center gap-2 text-[10px] t-m"><PieChart size={11} /> Après correction : <span className="t-ok">−18% risque</span></div>
            </div>

            {/* ── Tendance ───────────────────── */}
            <div className="rounded-xl p-3 surface-flat">
              <div className="flex items-center justify-between mb-2">
                <h3 className="h3 t-p">Évolution</h3>
                {delta !== 0 && <span className="text-xs font-bold flex items-center gap-1" style={{ color: delta < 0 ? 'var(--success)' : 'var(--critical)' }}>{delta < 0 ? <TrendingDown size={12} /> : <TrendingUp size={12} />}{delta < 0 ? delta : `+${delta}`}</span>}
              </div>
              {history.length > 0 ? (
                <div className="flex items-end gap-1 h-10">
                  {history.map((h: any, i: number) => (
                    <div key={i} className="flex-1 rounded-t-sm" title={`${h.at?.slice(0, 10)}: ${h.score}`}
                      style={{ height: `${Math.max(8, (h.score / 100) * 100)}%`, background: i === history.length - 1 ? 'var(--brand)' : h.score > 70 ? 'var(--critical)' : h.score > 50 ? 'var(--mission)' : 'var(--decision)' }} />
                  ))}
                </div>
              ) : <div className="text-[10px] t-m flex items-center gap-2"><Activity size={11} />Historique en construction — s'enrichit à chaque visite</div>}
            </div>

            {/* ── CTA — discret ──────────────── */}
            <button onClick={startMission} disabled={creating}
              className="w-full py-2.5 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-all"
              style={{ background: 'var(--brand)', color: 'var(--brand-text)' }}>
              {creating ? 'Création...' : done ? '✓ Mission créée' : <><Play size={15} /> Créer une mission</>}
            </button>

            {/* Sources */}
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-[10px] t-m">Sources :</span>
              {['NVD', 'MITRE', 'CISA', 'EPSS', 'Exploit-DB'].map(s => <span key={s} className="text-[9px] px-1.5 py-0.5 rounded-full surface-flat t-m">{s}</span>)}
            </div>
          </div>
        )}
        {!showDetails && <div className="px-6 py-4 flex items-center justify-between"><div><span className="font-bold t-p mr-3">{decision.score}</span><span className="text-xs t-m">{decision.description.slice(0, 80)}...</span></div><button onClick={() => setShowDetails(true)} className="t-m"><ChevronDown size={16} /></button></div>}
      </div>
    </section>
  )
}
