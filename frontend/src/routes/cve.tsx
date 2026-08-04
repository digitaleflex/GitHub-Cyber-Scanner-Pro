import { createRoute, useParams, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import { Shield, ExternalLink, AlertTriangle, Bug, Star, ArrowLeft, Brain, CheckCircle2, Target, Fingerprint, FileCode, Package, CalendarClock, FileDown, FileText } from 'lucide-react'

const LEVEL_LABEL: Record<string, string> = {
  CRITIQUE: 'Critique',
  ELEVE: 'Élevé',
  MOYEN: 'Moyen',
  BAS: 'Faible',
}

const LEVEL_COLORS: Record<string, { bg: string; text: string; border: string; stroke: string }> = {
  CRITIQUE: { bg: 'var(--critical-light)', text: 'var(--critical-text)', border: 'var(--critical)', stroke: '#DC2626' },
  ELEVE: { bg: 'var(--mission-light)', text: 'var(--mission-text)', border: 'var(--mission)', stroke: '#D97706' },
  MOYEN: { bg: 'var(--decision-light)', text: 'var(--decision-text)', border: 'var(--decision)', stroke: '#2563EB' },
  BAS: { bg: 'var(--surface-hover)', text: 'var(--text-muted)', border: 'var(--border)', stroke: '#94A3B8' },
}

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/cve/$id',
  component: DecisionCenter,
})

interface DecisionData {
  cve_id: string
  score: number
  level: string
  severity: string
  cvss_score: number | null
  published: string | null
  description: string
  is_kev: boolean
  exploits_count: number
  factors: Record<string, number>
  reasons: string[]
  risk_if_ignored: string
  confidence: string
  sources: string[]
}

function ScoreRing({ score, level }: { score: number; level: string; maxScore: number }) {
  const r = 45
  const circ = 2 * Math.PI * r
  const pct = Math.min(score / 100, 1)
  const colors = LEVEL_COLORS[level] || LEVEL_COLORS.BAS
  return (
    <div className="relative w-28 h-28 mx-auto">
      <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
        <circle cx="50" cy="50" r={r} fill="none" stroke="var(--border)" strokeWidth="4" />
        <circle cx="50" cy="50" r={r} fill="none" stroke={colors.stroke} strokeWidth="4" strokeLinecap="round"
          strokeDasharray={`${pct * circ} ${circ}`} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold" style={{ color: 'var(--text)' }}>{score}</span>
        <span className="text-[10px] text-muted">/ 100</span>
      </div>
    </div>
  )
}

function DecisionCenter() {
  const { id } = useParams({ from: '/cve/$id' })
  const { data: cve, isLoading } = useQuery({
    queryKey: ['cve', id],
    queryFn: () => fetch(`/api/cve/${encodeURIComponent(id)}`).then(r => r.json()),
    staleTime: 300_000,
  })
  const { data: decision, isLoading: dl } = useQuery({
    queryKey: ['cve-decision', id],
    queryFn: () => fetch(`/api/cve/${encodeURIComponent(id)}/decision`).then(r => r.json()),
    staleTime: 300_000,
  })

  if (isLoading || dl) return (
    <div className="flex items-center justify-center py-24">
      <div className="w-8 h-8 border-2 border-[var(--brand)] border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (!cve || cve.error) return (
    <div className="max-w-4xl mx-auto py-24 text-center">
      <Shield size={40} className="mx-auto text-muted mb-4" />
      <p className="text-secondary">{cve?.error || 'CVE introuvable'}</p>
      <Link to="/" className="btn-secondary mt-3 text-xs">Retour</Link>
    </div>
  )

  const dec: DecisionData | null = decision && !decision.error ? decision : null
  const decisionLevel = dec?.level === 'CRITIQUE' ? 'CRITIQUE' : dec?.level === 'ELEVE' ? 'ELEVE' : dec?.level === 'MOYEN' ? 'MOYEN' : 'BAS'
  const colors = LEVEL_COLORS[decisionLevel] || LEVEL_COLORS.BAS

  return (
    <div className="max-w-4xl mx-auto py-4 sm:py-8 animate-fade">
      <Link to="/" className="inline-flex items-center gap-1.5 text-xs text-secondary hover:underline transition mb-6">
        <ArrowLeft size={13} /> Aujourd'hui
      </Link>

      {/* Header */}
      <div className="surface p-5 sm:p-7 mb-5 text-center" style={{ border: '1px solid var(--border)' }}>
        <p className="caption mb-2" style={{ color: 'var(--brand-text)' }}>Decision Center</p>
        <h1 className="h2 mb-2" style={{ color: 'var(--text)' }}>
          {cve.description?.slice(0, 150) || 'Aucune description'}
        </h1>
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <span className="mono font-semibold" style={{ color: 'var(--decision-text)' }}>{cve.cve_id}</span>
          {cve.cvss_score != null && (
            <span style={{ color: 'var(--text-secondary)' }}>CVSS {cve.cvss_score}</span>
          )}
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full border" style={{ background: colors.bg, color: colors.text, borderColor: colors.border }}>
            {LEVEL_LABEL[decisionLevel] || decisionLevel}
          </span>
          {cve.is_kev && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border" style={{ background: 'var(--critical-light)', color: 'var(--critical-text)', borderColor: 'var(--critical)' }}>
              <AlertTriangle size={9} /> CISA KEV
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Main column */}
        <div className="lg:col-span-2 space-y-5">
          {dec && (
            <div className="surface p-5 sm:p-6" style={{ border: '1px solid var(--border)' }}>
              <p className="caption mb-4" style={{ color: 'var(--brand-text)' }}>Pourquoi cette décision ?</p>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
                {[
                  { v: dec.score, l: 'Score' },
                  { v: dec.confidence, l: 'Confiance' },
                  { v: dec.exploits_count, l: 'Exploits' },
                  { v: dec.is_kev ? 'Oui' : 'Non', l: 'CISA KEV', c: dec.is_kev ? 'var(--mission-text)' : undefined },
                ].map((s, i) => (
                  <div key={i} className="rounded-xl p-3 text-center" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                    <div className="text-lg font-bold" style={{ color: s.c || 'var(--text)' }}>{s.v}</div>
                    <div className="text-xs text-muted">{s.l}</div>
                  </div>
                ))}
              </div>

              <div className="space-y-2.5 mb-5">
                {dec.reasons.map((r, i) => (
                  <div key={i} className="flex items-start gap-2.5 body-sm" style={{ color: 'var(--text)' }}>
                    <CheckCircle2 size={15} className="shrink-0 mt-0.5" style={{ color: 'var(--brand-text)' }} />
                    <span>{r}</span>
                  </div>
                ))}
              </div>

              <div className="rounded-xl p-4 mb-4" style={{ background: 'var(--mission-light)', borderLeft: '4px solid var(--mission)' }}>
                <p className="caption mb-1" style={{ color: 'var(--mission-text)' }}>Si vous ignorez</p>
                <p className="body-sm" style={{ color: 'var(--text)' }}>{dec.risk_if_ignored}</p>
              </div>

              <div className="flex items-center gap-1.5 text-xs text-muted">
                <Brain size={11} />
                <span>Sources : {dec.sources.join(', ')}</span>
              </div>
            </div>
          )}

          {/* Description */}
          <div className="surface p-5 sm:p-6" style={{ border: '1px solid var(--border)' }}>
            <p className="caption mb-3" style={{ color: 'var(--brand-text)' }}>Contexte</p>
            <p className="body-sm" style={{ color: 'var(--text-secondary)' }}>{cve.description || 'Aucune description'}</p>
            {cve.weaknesses && (
              <div className="mt-4 pt-4" style={{ borderTop: '1px solid var(--border)' }}>
                <p className="text-xs text-muted">Faiblesses CWE : {String(cve.weaknesses).replace(/CISA_KEV[^,]*/g, '').slice(0, 300)}</p>
              </div>
            )}
          </div>

          {/* Exploits */}
          {cve.exploits?.length > 0 && (
            <div className="surface p-5 sm:p-6" style={{ border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-2 mb-3">
                <Bug size={15} style={{ color: 'var(--mission)' }} />
                <h2 className="h3" style={{ color: 'var(--text)' }}>{cve.exploits.length} exploit{cve.exploits.length > 1 ? 's' : ''} public{cve.exploits.length > 1 ? 's' : ''}</h2>
              </div>
              <div className="space-y-2">
                {cve.exploits.map((e: any, i: number) => (
                  <div key={i} className="rounded-xl p-3.5" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <div className="text-xs" style={{ color: 'var(--text)' }}>{e.description}</div>
                        <div className="flex items-center gap-2 mt-1.5 text-[10px] text-muted">
                          {e.platform && <span>{e.platform}</span>}
                          {e.type && <span>{e.type}</span>}
                          {e.author && <span>{e.author}</span>}
                          {e.date && <span>{e.date}</span>}
                        </div>
                      </div>
                      <a href={`https://www.exploit-db.com/exploits/${e.id}`} target="_blank" rel="noopener"
                        className="shrink-0 p-1 rounded transition-colors" style={{ color: 'var(--text-muted)' }}>
                        <ExternalLink size={13} />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tools */}
          {cve.tools?.length > 0 && (
            <div className="surface p-5 sm:p-6" style={{ border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-2 mb-3">
                <Star size={15} style={{ color: 'var(--decision)' }} />
                <h2 className="h3" style={{ color: 'var(--text)' }}>{cve.tools.length} outil{cve.tools.length > 1 ? 's' : ''} associé{cve.tools.length > 1 ? 's' : ''}</h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {cve.tools.map((t: any, i: number) => (
                  <Link key={i} to="/tool/$name" params={{ name: t.name }}
                    className="rounded-xl p-3 block transition-all hover:-translate-y-0.5"
                    style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)', textDecoration: 'none' }}>
                    <div className="text-xs font-medium truncate" style={{ color: 'var(--text)' }}>{t.name}</div>
                    {t.desc && <div className="text-[10px] text-muted mt-0.5 line-clamp-1">{t.desc}</div>}
                    <div className="flex items-center gap-2 mt-1.5 text-[9px] text-muted">
                      {t.stars && <span className="flex items-center gap-0.5" style={{ color: 'var(--mission)' }}><Star size={9} /> {t.stars}</span>}
                      <span>{t.match_type}</span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* KEV */}
          {cve.kev && (
            <div className="surface p-5 sm:p-6" style={{ border: '1px solid var(--critical)' }}>
              <div className="flex items-center gap-2 mb-3">
                <CalendarClock size={15} style={{ color: 'var(--critical)' }} />
                <h2 className="h3" style={{ color: 'var(--text)' }}>CISA KEV — {cve.kev.vulnerability_name || 'Vulnérabilité exploitée'}</h2>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="rounded-xl p-3" style={{ background: 'var(--critical-light)' }}>
                  <div className="text-muted">Ajoutée au catalogue</div>
                  <div className="font-semibold mt-0.5" style={{ color: 'var(--text)' }}>{cve.kev.cisa_kev_date ? new Date(cve.kev.cisa_kev_date).toLocaleDateString('fr-FR') : '?'}</div>
                </div>
                <div className="rounded-xl p-3" style={{ background: 'var(--critical-light)' }}>
                  <div className="text-muted">Échéance de remédiation</div>
                  <div className="font-semibold mt-0.5" style={{ color: 'var(--critical-text)' }}>{cve.kev.due_date ? new Date(cve.kev.due_date).toLocaleDateString('fr-FR') : '?'}</div>
                </div>
                <div className="rounded-xl p-3 col-span-2" style={{ background: 'var(--critical-light)' }}>
                  <div className="text-muted">Ransomware</div>
                  <div className="font-semibold mt-0.5" style={{ color: cve.kev.ransomware_campaign ? 'var(--critical-text)' : 'var(--text-muted)' }}>
                    {cve.kev.ransomware_campaign || 'Non associé'}
                  </div>
                </div>
              </div>
              {cve.kev.required_action && (
                <p className="body-sm mt-3" style={{ color: 'var(--text-secondary)' }}>{cve.kev.required_action}</p>
              )}
            </div>
          )}

          {/* IOCs */}
          {cve.iocs?.length > 0 && (
            <div className="surface p-5 sm:p-6" style={{ border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-2 mb-3">
                <Fingerprint size={15} style={{ color: 'var(--decision)' }} />
                <h2 className="h3" style={{ color: 'var(--text)' }}>{cve.iocs.length} IOC{cve.iocs.length > 1 ? 's' : ''} associé{cve.iocs.length > 1 ? 's' : ''}</h2>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {cve.iocs.map((i: any) => (
                  <button key={i.id}
                    onClick={() => navigator.clipboard?.writeText(i.value)}
                    title={`Source: ${i.source || '?'} — cliquer pour copier`}
                    className="mono text-[10px] px-2.5 py-1 rounded-full border transition-colors"
                    style={{ background: 'var(--bg-alt)', color: 'var(--text-secondary)', borderColor: 'var(--border-light)' }}>
                    {i.value}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* ATT&CK */}
          {cve.attack_techniques?.length > 0 && (
            <div className="surface p-5 sm:p-6" style={{ border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-2 mb-3">
                <Target size={15} style={{ color: 'var(--mission)' }} />
                <h2 className="h3" style={{ color: 'var(--text)' }}>{cve.attack_techniques.length} technique{cve.attack_techniques.length > 1 ? 's' : ''} MITRE ATT&CK</h2>
              </div>
              <div className="space-y-2">
                {cve.attack_techniques.map((t: any, i: number) => (
                  <div key={i} className="flex items-start justify-between gap-3 rounded-xl p-3" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                    <div className="min-w-0">
                      <div className="text-xs font-medium" style={{ color: 'var(--text)' }}>
                        <span className="mono mr-2" style={{ color: 'var(--mission-text)' }}>{t.technique_id}</span>{t.name}
                      </div>
                      {t.tactic && <div className="text-[10px] text-muted mt-0.5">{t.tactic}</div>}
                    </div>
                    <a href={`https://attack.mitre.org/techniques/${t.technique_id}`} target="_blank" rel="noopener"
                      className="shrink-0 p-1 rounded transition-colors" style={{ color: 'var(--text-muted)' }}>
                      <ExternalLink size={13} />
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Detection rules */}
          {cve.sigma_rules?.length + cve.yara_rules?.length + cve.ids_rules?.length > 0 && (
            <div className="surface p-5 sm:p-6" style={{ border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-2 mb-3">
                <FileCode size={15} style={{ color: 'var(--brand-text)' }} />
                <h2 className="h3" style={{ color: 'var(--text)' }}>Règles de détection</h2>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {cve.sigma_rules.map((r: any, i: number) => (
                  <span key={`s-${i}`} className="text-[10px] px-2.5 py-1 rounded-full border font-medium" style={{ background: 'var(--brand-bg)', color: 'var(--brand-text)', borderColor: 'var(--border-light)' }}>
                    Sigma — {r.title}
                  </span>
                ))}
                {cve.yara_rules.map((r: any, i: number) => (
                  <span key={`y-${i}`} className="text-[10px] px-2.5 py-1 rounded-full border font-medium" style={{ background: 'var(--mission-light)', color: 'var(--mission-text)', borderColor: 'var(--border-light)' }}>
                    YARA — {r.rule_name}
                  </span>
                ))}
                {cve.ids_rules.map((r: any, i: number) => (
                  <span key={`i-${i}`} className="mono text-[10px] px-2.5 py-1 rounded-full border font-medium" style={{ background: 'var(--bg-alt)', color: 'var(--text-secondary)', borderColor: 'var(--border-light)' }}>
                    {r.engine} {r.sid} — {r.message}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Patches & produits */}
          {cve.patches?.length > 0 && (
            <div className="surface p-5 sm:p-6" style={{ border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-2 mb-3">
                <Package size={15} style={{ color: 'var(--success)' }} />
                <h2 className="h3" style={{ color: 'var(--text)' }}>{cve.patches.length} correctif{cve.patches.length > 1 ? 's' : ''}</h2>
              </div>
              <div className="space-y-2">
                {cve.patches.map((p: any, i: number) => (
                  <div key={i} className="flex items-start justify-between gap-3 rounded-xl p-3" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                    <div className="min-w-0">
                      <div className="text-xs font-medium" style={{ color: 'var(--text)' }}>
                        {p.patch_name || p.vendor || 'Correctif'}
                        {p.version_fixed && <span className="mono ml-2" style={{ color: 'var(--success)' }}>fix {p.version_fixed}</span>}
                      </div>
                      {p.notes && <div className="text-[10px] text-muted mt-0.5 line-clamp-1">{p.notes}</div>}
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full border"
                        style={{ background: p.available ? 'var(--success-light)' : 'var(--bg-alt)', color: p.available ? '#166534' : 'var(--text-muted)', borderColor: 'var(--border-light)' }}>
                        {p.available ? 'DISPONIBLE' : 'ATTENTE'}
                      </span>
                      {p.url && <a href={p.url} target="_blank" rel="noopener" className="p-1 rounded" style={{ color: 'var(--text-muted)' }}><ExternalLink size={12} /></a>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Produits affectes */}
          {cve.affected_products?.length > 0 && (
            <div className="surface p-5 sm:p-6" style={{ border: '1px solid var(--border)' }}>
              <p className="caption mb-3" style={{ color: 'var(--brand-text)' }}>Produits affectés</p>
              <div className="flex flex-wrap gap-1.5">
                {cve.affected_products.map((p: any, i: number) => (
                  <span key={i} className="text-[10px] px-2.5 py-1 rounded-full border" style={{ background: 'var(--bg-alt)', color: 'var(--text-secondary)', borderColor: 'var(--border-light)' }}>
                    {[p.vendor, p.product, p.version].filter(Boolean).join(' ')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Advisories */}
          {cve.advisories?.length > 0 && (
            <div className="surface p-5 sm:p-6" style={{ border: '1px solid var(--border)' }}>
              <div className="flex items-center gap-2 mb-3">
                <FileText size={15} style={{ color: 'var(--decision)' }} />
                <h2 className="h3" style={{ color: 'var(--text)' }}>{cve.advisories.length} avis fournisseur{cve.advisories.length > 1 ? 's' : ''}</h2>
              </div>
              <div className="space-y-2">
                {cve.advisories.map((a: any, i: number) => (
                  <div key={i} className="flex items-start justify-between gap-3 rounded-xl p-3" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                    <div className="min-w-0">
                      <div className="text-xs font-medium" style={{ color: 'var(--text)' }}>{a.vendor} — {a.title}</div>
                      {a.published && <div className="text-[10px] text-muted mt-0.5">{new Date(a.published).toLocaleDateString('fr-FR')}</div>}
                    </div>
                    {a.url && <a href={a.url} target="_blank" rel="noopener" className="shrink-0 p-1 rounded" style={{ color: 'var(--text-muted)' }}><ExternalLink size={13} /></a>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {dec && (
            <div className="surface p-5 text-center" style={{ border: '1px solid var(--border)' }}>
              <ScoreRing score={dec.score} level={dec.level} maxScore={100} />
              <div className="mt-3">
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full border" style={{ background: colors.bg, color: colors.text, borderColor: colors.border }}>
                  {LEVEL_LABEL[decisionLevel] || decisionLevel}
                </span>
              </div>
            </div>
          )}

          <div className="surface p-5" style={{ border: '1px solid var(--border)' }}>
            <p className="caption mb-3" style={{ color: 'var(--brand-text)' }}>Informations</p>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between">
                <span className="text-muted">Score CVSS</span>
                <span className="font-medium" style={{ color: 'var(--text)' }}>{cve.cvss_score || '?'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Sévérité</span>
                <span className="font-medium" style={{ color: 'var(--text)' }}>{cve.severity || '?'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Publiée</span>
                <span className="font-medium" style={{ color: 'var(--text)' }}>{cve.published ? new Date(cve.published).toLocaleDateString('fr-FR') : '?'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Exploits</span>
                <span className="font-medium" style={{ color: 'var(--text)' }}>{cve.exploits?.length || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">Outils</span>
                <span className="font-medium" style={{ color: 'var(--text)' }}>{cve.tools?.length || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted">CISA KEV</span>
                <span className="font-semibold" style={{ color: cve.is_kev ? 'var(--critical-text)' : 'var(--text-muted)' }}>
                  {cve.is_kev ? 'OUI' : 'NON'}
                </span>
              </div>
              {cve.kev?.due_date && (
                <div className="flex justify-between">
                  <span className="text-muted">Échéance KEV</span>
                  <span className="font-semibold" style={{ color: 'var(--mission-text)' }}>
                    {new Date(cve.kev.due_date).toLocaleDateString('fr-FR')}
                  </span>
                </div>
              )}
              {cve.epss?.epss != null && (
                <div>
                  <div className="flex justify-between">
                    <span className="text-muted">EPSS (prob. exploitation)</span>
                    <span className="font-semibold" style={{ color: 'var(--text)' }}>{(cve.epss.epss * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-1.5 rounded-full mt-1.5" style={{ background: 'var(--bg-alt)' }}>
                    <div className="h-full rounded-full" style={{ width: `${Math.min(cve.epss.epss * 100, 100)}%`, background: cve.epss.epss >= 0.5 ? 'var(--critical)' : cve.epss.epss >= 0.1 ? 'var(--mission)' : 'var(--success)' }} />
                  </div>
                  <div className="text-right text-[9px] text-muted mt-0.5">P{Math.round((cve.epss.percentile || 0) * 100)} — {cve.epss.percentile != null ? `top ${Math.round((1 - (cve.epss.percentile || 0)) * 100)}%` : ''}</div>
                </div>
              )}
            </div>
          </div>

          <a href={`https://nvd.nist.gov/vuln/detail/${cve.cve_id}`} target="_blank" rel="noopener"
            className="surface rounded-xl p-3 flex items-center justify-center gap-1.5 text-xs font-medium transition-all hover:-translate-y-0.5"
            style={{ color: 'var(--decision-text)', border: '1px solid var(--border)', textDecoration: 'none' }}>
            Voir sur NVD <ExternalLink size={10} />
          </a>

          <a href={`https://www.exploit-db.com/search?cve=${cve.cve_id}`} target="_blank" rel="noopener"
            className="surface rounded-xl p-3 flex items-center justify-center gap-1.5 text-xs transition-all hover:-translate-y-0.5"
            style={{ color: 'var(--text-secondary)', border: '1px solid var(--border)', textDecoration: 'none' }}>
            Exploit-DB <ExternalLink size={10} />
          </a>

          <a href={`/api/cve/${encodeURIComponent(cve.cve_id)}/stix`} target="_blank" rel="noopener"
            className="surface rounded-xl p-3 flex items-center justify-center gap-1.5 text-xs font-medium transition-all hover:-translate-y-0.5"
            style={{ color: 'var(--brand-text)', border: '1px solid var(--border)', textDecoration: 'none', background: 'var(--brand-bg)' }}>
            Export STIX 2.1 <FileDown size={11} />
          </a>
        </div>
      </div>
    </div>
  )
}
