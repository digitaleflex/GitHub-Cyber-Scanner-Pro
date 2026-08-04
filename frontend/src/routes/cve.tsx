import { createRoute, useParams, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import { Shield, ExternalLink, AlertTriangle, Bug, Star, ArrowLeft, Brain, CheckCircle2, Target, Fingerprint, FileCode, Package, CalendarClock, FileDown, FileText } from 'lucide-react'
import { InstrumentPanel } from '../components/InstrumentPanel'
import { ScoreRing } from '../components/ScoreRing'
import Chip from '../components/Chip'

const LEVEL_LABEL: Record<string, string> = {
  CRITIQUE: 'Critique',
  ELEVE: 'Élevé',
  MOYEN: 'Moyen',
  BAS: 'Faible',
}

const LEVEL_ACCENT: Record<string, 'red' | 'amber' | 'cyan' | 'violet' | 'lime'> = {
  CRITIQUE: 'red',
  ELEVE: 'amber',
  MOYEN: 'cyan',
  BAS: 'violet',
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
      <div className="w-8 h-8 border-2 border-[var(--amber)] border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (!cve || cve.error) return (
    <div className="w-full py-24 text-center">
      <Shield size={40} className="mx-auto text-muted mb-4" />
      <p className="text-secondary">{cve?.error || 'CVE introuvable'}</p>
      <Link to="/" className="btn-secondary mt-3 text-xs">Retour</Link>
    </div>
  )

  const dec: DecisionData | null = decision && !decision.error ? decision : null
  const decisionLevel = dec?.level === 'CRITIQUE' ? 'CRITIQUE' : dec?.level === 'ELEVE' ? 'ELEVE' : dec?.level === 'MOYEN' ? 'MOYEN' : 'BAS'
  const accent = LEVEL_ACCENT[decisionLevel] || 'violet'

  return (
    <div className="w-full py-4 sm:py-8 animate-fade">
      <Link to="/" className="inline-flex items-center gap-1.5 text-xs text-secondary hover:underline transition mb-6">
        <ArrowLeft size={13} /> Aujourd'hui
      </Link>

      <InstrumentPanel title="Decision Center" icon={<Brain size={18} />} accent={accent} className="mb-6 text-center">
        <h1 className="h2 mb-2" style={{ color: 'var(--text)' }}>
          {cve.description?.slice(0, 150) || 'Aucune description'}
        </h1>
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <span className="mono font-semibold" style={{ color: 'var(--cyan)' }}>{cve.cve_id}</span>
          {cve.cvss_score != null && (
            <span style={{ color: 'var(--text-secondary)' }}>CVSS {cve.cvss_score}</span>
          )}
          <Chip variant="verdict" value={LEVEL_LABEL[decisionLevel] || decisionLevel} />
          {cve.is_kev && (
            <Chip variant="verdict" value="CISA KEV" icon={AlertTriangle} />
          )}
        </div>
      </InstrumentPanel>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main column */}
        <div className="lg:col-span-2 space-y-6">
          {dec && (
            <InstrumentPanel title="Pourquoi cette décision ?" icon={<Brain size={18} />} accent={accent}>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
                {[
                  { v: dec.score, l: 'Score' },
                  { v: dec.confidence, l: 'Confiance' },
                  { v: dec.exploits_count, l: 'Exploits' },
                  { v: dec.is_kev ? 'Oui' : 'Non', l: 'CISA KEV', c: dec.is_kev ? 'var(--amber)' : undefined },
                ].map((s, i) => (
                  <div key={i} className="rounded-xl p-3 text-center" style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border-light)' }}>
                    <div className="text-lg font-bold" style={{ color: s.c || 'var(--text)' }}>{s.v}</div>
                    <div className="text-xs text-muted">{s.l}</div>
                  </div>
                ))}
              </div>

              <div className="space-y-2.5 mb-5">
                {dec.reasons.map((r, i) => (
                  <div key={i} className="flex items-start gap-2.5 body-sm" style={{ color: 'var(--text)' }}>
                    <CheckCircle2 size={15} className="shrink-0 mt-0.5" style={{ color: 'var(--amber)' }} />
                    <span>{r}</span>
                  </div>
                ))}
              </div>

              <div className="rounded-xl p-4 mb-4" style={{ background: 'var(--amber-light)', borderLeft: '4px solid var(--amber)' }}>
                <p className="caption mb-1" style={{ color: 'var(--amber)' }}>Si vous ignorez</p>
                <p className="body-sm" style={{ color: 'var(--text)' }}>{dec.risk_if_ignored}</p>
              </div>

              <div className="flex items-center gap-1.5 text-xs text-muted">
                <Brain size={11} />
                <span>Sources : {dec.sources.join(', ')}</span>
              </div>
            </InstrumentPanel>
          )}

          <InstrumentPanel title="Contexte" icon={<FileText size={18} />} accent="cyan">
            <p className="body-sm" style={{ color: 'var(--text-secondary)' }}>{cve.description || 'Aucune description'}</p>
            {cve.weaknesses && (
              <div className="mt-4 pt-4" style={{ borderTop: '1px solid var(--border)' }}>
                <p className="text-xs text-muted">Faiblesses CWE : {String(cve.weaknesses).replace(/CISA_KEV[^,]*/g, '').slice(0, 300)}</p>
              </div>
            )}
          </InstrumentPanel>

          {cve.exploits?.length > 0 && (
            <InstrumentPanel title={`${cve.exploits.length} exploit${cve.exploits.length > 1 ? 's' : ''} public${cve.exploits.length > 1 ? 's' : ''}`} icon={<Bug size={18} />} accent="red">
              <div className="space-y-2">
                {cve.exploits.map((e: any, i: number) => (
                  <div key={i} className="rounded-xl p-3.5" style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border-light)' }}>
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
            </InstrumentPanel>
          )}

          {cve.tools?.length > 0 && (
            <InstrumentPanel title={`${cve.tools.length} outil${cve.tools.length > 1 ? 's' : ''} associé${cve.tools.length > 1 ? 's' : ''}`} icon={<Star size={18} />} accent="violet">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {cve.tools.map((t: any, i: number) => (
                  <Link key={i} to="/tool/$name" params={{ name: t.name }}
                    className="rounded-xl p-3 block transition-all hover:-translate-y-0.5"
                    style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border-light)', textDecoration: 'none' }}>
                    <div className="text-xs font-medium truncate" style={{ color: 'var(--text)' }}>{t.name}</div>
                    {t.desc && <div className="text-[10px] text-muted mt-0.5 line-clamp-1">{t.desc}</div>}
                    <div className="flex items-center gap-2 mt-1.5 text-[9px] text-muted">
                      {t.stars && <span className="flex items-center gap-0.5" style={{ color: 'var(--amber)' }}><Star size={9} /> {t.stars}</span>}
                      <span>{t.match_type}</span>
                    </div>
                  </Link>
                ))}
              </div>
            </InstrumentPanel>
          )}

          {cve.kev && (
            <InstrumentPanel title={`CISA KEV — ${cve.kev.vulnerability_name || 'Vulnérabilité exploitée'}`} icon={<CalendarClock size={18} />} accent="red">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="rounded-xl p-3" style={{ background: 'var(--red-light)', border: '1px solid var(--red)40' }}>
                  <div className="text-muted">Ajoutée au catalogue</div>
                  <div className="font-semibold mt-0.5" style={{ color: 'var(--text)' }}>{cve.kev.cisa_kev_date ? new Date(cve.kev.cisa_kev_date).toLocaleDateString('fr-FR') : '?'}</div>
                </div>
                <div className="rounded-xl p-3" style={{ background: 'var(--red-light)', border: '1px solid var(--red)40' }}>
                  <div className="text-muted">Échéance de remédiation</div>
                  <div className="font-semibold mt-0.5" style={{ color: 'var(--red)' }}>{cve.kev.due_date ? new Date(cve.kev.due_date).toLocaleDateString('fr-FR') : '?'}</div>
                </div>
                <div className="rounded-xl p-3 col-span-2" style={{ background: 'var(--red-light)', border: '1px solid var(--red)40' }}>
                  <div className="text-muted">Ransomware</div>
                  <div className="font-semibold mt-0.5" style={{ color: cve.kev.ransomware_campaign ? 'var(--red)' : 'var(--text-muted)' }}>
                    {cve.kev.ransomware_campaign || 'Non associé'}
                  </div>
                </div>
              </div>
              {cve.kev.required_action && (
                <p className="body-sm mt-3" style={{ color: 'var(--text-secondary)' }}>{cve.kev.required_action}</p>
              )}
            </InstrumentPanel>
          )}

          {cve.iocs?.length > 0 && (
            <InstrumentPanel title={`${cve.iocs.length} IOC${cve.iocs.length > 1 ? 's' : ''} associé${cve.iocs.length > 1 ? 's' : ''}`} icon={<Fingerprint size={18} />} accent="cyan">
              <div className="flex flex-wrap gap-1.5">
                {cve.iocs.map((i: any) => (
                  <button key={i.id}
                    onClick={() => navigator.clipboard?.writeText(i.value)}
                    title={`Source: ${i.source || '?'} — cliquer pour copier`}
                    className="mono text-[10px] px-2.5 py-1 rounded-full border transition-colors"
                    style={{ background: 'var(--surface-elevated)', color: 'var(--text-secondary)', borderColor: 'var(--border-light)' }}>
                    {i.value}
                  </button>
                ))}
              </div>
            </InstrumentPanel>
          )}

          {cve.attack_techniques?.length > 0 && (
            <InstrumentPanel title={`${cve.attack_techniques.length} technique${cve.attack_techniques.length > 1 ? 's' : ''} MITRE ATT&CK`} icon={<Target size={18} />} accent="amber">
              <div className="space-y-2">
                {cve.attack_techniques.map((t: any, i: number) => (
                  <div key={i} className="flex items-start justify-between gap-3 rounded-xl p-3" style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border-light)' }}>
                    <div className="min-w-0">
                      <div className="text-xs font-medium" style={{ color: 'var(--text)' }}>
                        <span className="mono mr-2" style={{ color: 'var(--amber)' }}>{t.technique_id}</span>{t.name}
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
            </InstrumentPanel>
          )}

          {cve.sigma_rules?.length + cve.yara_rules?.length + cve.ids_rules?.length > 0 && (
            <InstrumentPanel title="Règles de détection" icon={<FileCode size={18} />} accent="violet">
              <div className="flex flex-wrap gap-1.5">
                {cve.sigma_rules.map((r: any, i: number) => (
                  <span key={`s-${i}`} className="text-[10px] px-2.5 py-1 rounded-full border font-medium" style={{ background: 'var(--amber-light)', color: 'var(--amber)', borderColor: 'var(--border-light)' }}>
                    Sigma — {r.title}
                  </span>
                ))}
                {cve.yara_rules.map((r: any, i: number) => (
                  <span key={`y-${i}`} className="text-[10px] px-2.5 py-1 rounded-full border font-medium" style={{ background: 'var(--amber-light)', color: 'var(--amber)', borderColor: 'var(--border-light)' }}>
                    YARA — {r.rule_name}
                  </span>
                ))}
                {cve.ids_rules.map((r: any, i: number) => (
                  <span key={`i-${i}`} className="mono text-[10px] px-2.5 py-1 rounded-full border font-medium" style={{ background: 'var(--surface-elevated)', color: 'var(--text-secondary)', borderColor: 'var(--border-light)' }}>
                    {r.engine} {r.sid} — {r.message}
                  </span>
                ))}
              </div>
            </InstrumentPanel>
          )}

          {cve.patches?.length > 0 && (
            <InstrumentPanel title={`${cve.patches.length} correctif${cve.patches.length > 1 ? 's' : ''}`} icon={<Package size={18} />} accent="lime">
              <div className="space-y-2">
                {cve.patches.map((p: any, i: number) => (
                  <div key={i} className="flex items-start justify-between gap-3 rounded-xl p-3" style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border-light)' }}>
                    <div className="min-w-0">
                      <div className="text-xs font-medium" style={{ color: 'var(--text)' }}>
                        {p.patch_name || p.vendor || 'Correctif'}
                        {p.version_fixed && <span className="mono ml-2" style={{ color: 'var(--lime)' }}>fix {p.version_fixed}</span>}
                      </div>
                      {p.notes && <div className="text-[10px] text-muted mt-0.5 line-clamp-1">{p.notes}</div>}
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full border"
                        style={{ background: p.available ? 'var(--lime-light)' : 'var(--surface-elevated)', color: p.available ? 'var(--lime)' : 'var(--text-muted)', borderColor: 'var(--border-light)' }}>
                        {p.available ? 'DISPONIBLE' : 'ATTENTE'}
                      </span>
                      {p.url && <a href={p.url} target="_blank" rel="noopener" className="p-1 rounded" style={{ color: 'var(--text-muted)' }}><ExternalLink size={12} /></a>}
                    </div>
                  </div>
                ))}
              </div>
            </InstrumentPanel>
          )}

          {cve.affected_products?.length > 0 && (
            <InstrumentPanel title="Produits affectés" icon={<Package size={18} />} accent="violet">
              <div className="flex flex-wrap gap-1.5">
                {cve.affected_products.map((p: any, i: number) => (
                  <span key={i} className="text-[10px] px-2.5 py-1 rounded-full border" style={{ background: 'var(--surface-elevated)', color: 'var(--text-secondary)', borderColor: 'var(--border-light)' }}>
                    {[p.vendor, p.product, p.version].filter(Boolean).join(' ')}
                  </span>
                ))}
              </div>
            </InstrumentPanel>
          )}

          {cve.advisories?.length > 0 && (
            <InstrumentPanel title={`${cve.advisories.length} avis fournisseur${cve.advisories.length > 1 ? 's' : ''}`} icon={<FileText size={18} />} accent="cyan">
              <div className="space-y-2">
                {cve.advisories.map((a: any, i: number) => (
                  <div key={i} className="flex items-start justify-between gap-3 rounded-xl p-3" style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border-light)' }}>
                    <div className="min-w-0">
                      <div className="text-xs font-medium" style={{ color: 'var(--text)' }}>{a.vendor} — {a.title}</div>
                      {a.published && <div className="text-[10px] text-muted mt-0.5">{new Date(a.published).toLocaleDateString('fr-FR')}</div>}
                    </div>
                    {a.url && <a href={a.url} target="_blank" rel="noopener" className="shrink-0 p-1 rounded" style={{ color: 'var(--text-muted)' }}><ExternalLink size={13} /></a>}
                  </div>
                ))}
              </div>
            </InstrumentPanel>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {dec && (
            <InstrumentPanel accent={accent} className="text-center">
              <ScoreRing score={dec.score} color={`var(--${accent})`} size={160} />
              <div className="mt-3">
                <Chip variant="verdict" value={LEVEL_LABEL[decisionLevel] || decisionLevel} />
              </div>
            </InstrumentPanel>
          )}

          <InstrumentPanel title="Informations" icon={<Shield size={18} />} accent="cyan">
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
                <span className="font-semibold" style={{ color: cve.is_kev ? 'var(--red)' : 'var(--text-muted)' }}>
                  {cve.is_kev ? 'OUI' : 'NON'}
                </span>
              </div>
              {cve.kev?.due_date && (
                <div className="flex justify-between">
                  <span className="text-muted">Échéance KEV</span>
                  <span className="font-semibold" style={{ color: 'var(--amber)' }}>
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
                  <div className="h-1.5 rounded-full mt-1.5" style={{ background: 'var(--surface-elevated)' }}>
                    <div className="h-full rounded-full" style={{ width: `${Math.min(cve.epss.epss * 100, 100)}%`, background: cve.epss.epss >= 0.5 ? 'var(--red)' : cve.epss.epss >= 0.1 ? 'var(--amber)' : 'var(--lime)' }} />
                  </div>
                  <div className="text-right text-[9px] text-muted mt-0.5">P{Math.round((cve.epss.percentile || 0) * 100)} — {cve.epss.percentile != null ? `top ${Math.round((1 - (cve.epss.percentile || 0)) * 100)}%` : ''}</div>
                </div>
              )}
            </div>
          </InstrumentPanel>

          <a href={`https://nvd.nist.gov/vuln/detail/${cve.cve_id}`} target="_blank" rel="noopener"
            className="surface rounded-xl p-3 flex items-center justify-center gap-1.5 text-xs font-medium transition-all hover:-translate-y-0.5"
            style={{ color: 'var(--cyan)', border: '1px solid var(--border)', textDecoration: 'none' }}>
            Voir sur NVD <ExternalLink size={10} />
          </a>

          <a href={`https://www.exploit-db.com/search?cve=${cve.cve_id}`} target="_blank" rel="noopener"
            className="surface rounded-xl p-3 flex items-center justify-center gap-1.5 text-xs transition-all hover:-translate-y-0.5"
            style={{ color: 'var(--text-secondary)', border: '1px solid var(--border)', textDecoration: 'none' }}>
            Exploit-DB <ExternalLink size={10} />
          </a>

          <a href={`/api/cve/${encodeURIComponent(cve.cve_id)}/stix`} target="_blank" rel="noopener"
            className="surface rounded-xl p-3 flex items-center justify-center gap-1.5 text-xs font-medium transition-all hover:-translate-y-0.5"
            style={{ color: 'var(--amber)', border: '1px solid var(--border)', textDecoration: 'none', background: 'var(--amber-light)' }}>
            Export STIX 2.1 <FileDown size={11} />
          </a>
        </div>
      </div>
    </div>
  )
}
