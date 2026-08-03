import { createRoute, useParams, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import { Shield, ExternalLink, AlertTriangle, Bug, Star, ArrowLeft, Brain, CheckCircle2 } from 'lucide-react'

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

function ScoreRing({ score, level, maxScore }: { score: number; level: string; maxScore: number }) {
  const r = 45
  const circ = 2 * Math.PI * r
  const pct = Math.min(score / maxScore, 1)
  const color = level === 'CRITIQUE' ? 'stroke-rose-400' : level === 'ELEVE' ? 'stroke-amber-400' : 'stroke-slate-400'
  return (
    <div className="relative w-28 h-28 mx-auto">
      <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
        <circle cx="50" cy="50" r={r} fill="none" stroke="currentColor" strokeWidth="4" className="text-slate-800" />
        <circle cx="50" cy="50" r={r} fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" className={color}
          strokeDasharray={`${pct * circ} ${circ}`} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-white">{score}</span>
        <span className="text-[10px] text-slate-500">/ {maxScore}</span>
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
      <div className="w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  if (!cve || cve.error) return (
    <div className="max-w-4xl mx-auto py-24 text-center">
      <Shield size={40} className="mx-auto text-slate-600 mb-4" />
      <p className="text-slate-400">{cve?.error || 'CVE introuvable'}</p>
      <Link to="/" className="text-emerald-400 text-sm mt-3 inline-block">Retour</Link>
    </div>
  )

  const dec: DecisionData | null = decision && !decision.error ? decision : null
  const levelColor = dec?.level === 'CRITIQUE' ? 'rose' : dec?.level === 'ELEVE' ? 'amber' : 'slate'

  return (
    <div className="max-w-4xl mx-auto py-4 sm:py-8 animate-fade">
      <Link to="/" className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 transition mb-6">
        <ArrowLeft size={13} /> Aujourd'hui
      </Link>

      {/* Header */}
      <div className="glass-card rounded-2xl p-5 sm:p-7 mb-5 text-center">
        <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-2">Decision Center</p>
        <h1 className="text-lg sm:text-xl font-semibold text-white mb-2">
          {cve.description?.slice(0, 150) || 'Aucune description'}
        </h1>
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <span className="text-xs font-mono text-indigo-400">{cve.cve_id}</span>
          {cve.cvss_score != null && (
            <span className="text-xs text-slate-400">CVSS {cve.cvss_score}</span>
          )}
          <span className={`px-2 py-0.5 rounded text-[10px] font-medium bg-${levelColor}-500/10 text-${levelColor}-400 border border-${levelColor}-500/20`}>
            {dec?.level || cve.severity || '?'}
          </span>
          {cve.is_kev && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-rose-500/20 text-rose-300 border border-rose-500/30">
              <AlertTriangle size={9} /> CISA KEV
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Main column */}
        <div className="lg:col-span-2 space-y-5">
          {/* Score & metrics */}
          {dec && (
            <div className="glass-card rounded-2xl p-5 sm:p-6">
              <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-4">Pourquoi cette décision ?</p>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
                <div className="glass rounded-xl p-3 text-center">
                  <div className="text-lg font-bold text-white">{dec.score}</div>
                  <div className="text-[10px] text-slate-500">Score</div>
                </div>
                <div className="glass rounded-xl p-3 text-center">
                  <div className="text-lg font-bold text-white">{dec.confidence}</div>
                  <div className="text-[10px] text-slate-500">Confiance</div>
                </div>
                <div className="glass rounded-xl p-3 text-center">
                  <div className="text-lg font-bold text-white">{dec.exploits_count}</div>
                  <div className="text-[10px] text-slate-500">Exploits</div>
                </div>
                <div className="glass rounded-xl p-3 text-center">
                  <div className="text-lg font-bold text-amber-400">{dec.is_kev ? 'Oui' : 'Non'}</div>
                  <div className="text-[10px] text-slate-500">CISA KEV</div>
                </div>
              </div>

              <div className="space-y-2.5 mb-5">
                {dec.reasons.map((r, i) => (
                  <div key={i} className="flex items-start gap-2.5 text-sm text-slate-300">
                    <CheckCircle2 size={15} className="shrink-0 mt-0.5 text-emerald-500" />
                    <span>{r}</span>
                  </div>
                ))}
              </div>

              <div className="glass rounded-xl p-4 mb-4 border-amber-500/10">
                <p className="text-[10px] uppercase tracking-widest text-amber-400 mb-1.5">Si vous ignorez</p>
                <p className="text-sm text-slate-300 leading-relaxed">{dec.risk_if_ignored}</p>
              </div>

              <div className="text-[10px] text-slate-500 flex items-center gap-1.5">
                <Brain size={11} />
                <span>Sources : {dec.sources.join(', ')}</span>
              </div>
            </div>
          )}

          {/* Description */}
          <div className="glass-card rounded-2xl p-5 sm:p-6">
            <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-3">Contexte</p>
            <p className="text-sm text-slate-300 leading-relaxed">{cve.description || 'Aucune description'}</p>
            {cve.weaknesses && (
              <div className="mt-4 pt-4 border-t border-white/[0.04]">
                <p className="text-xs text-slate-500">Faiblesses CWE : {String(cve.weaknesses).replace(/CISA_KEV[^,]*/g, '').slice(0, 300)}</p>
              </div>
            )}
          </div>

          {/* Exploits */}
          {cve.exploits?.length > 0 && (
            <div className="glass-card rounded-2xl p-5 sm:p-6">
              <div className="flex items-center gap-2 mb-3">
                <Bug size={15} className="text-amber-400" />
                <h2 className="text-sm font-semibold text-white">{cve.exploits.length} exploit{cve.exploits.length > 1 ? 's' : ''} public{cve.exploits.length > 1 ? 's' : ''}</h2>
              </div>
              <div className="space-y-2">
                {cve.exploits.map((e: any, i: number) => (
                  <div key={i} className="glass rounded-xl p-3.5">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <div className="text-xs text-slate-200">{e.description}</div>
                        <div className="flex items-center gap-2 mt-1.5 text-[10px] text-slate-500">
                          {e.platform && <span>{e.platform}</span>}
                          {e.type && <span>{e.type}</span>}
                          {e.author && <span>{e.author}</span>}
                          {e.date && <span>{e.date}</span>}
                        </div>
                      </div>
                      <a href={`https://www.exploit-db.com/exploits/${e.id}`} target="_blank" rel="noopener"
                        className="shrink-0 text-slate-500 hover:text-indigo-400"><ExternalLink size={13} /></a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tools */}
          {cve.tools?.length > 0 && (
            <div className="glass-card rounded-2xl p-5 sm:p-6">
              <div className="flex items-center gap-2 mb-3">
                <Star size={15} className="text-indigo-400" />
                <h2 className="text-sm font-semibold text-white">{cve.tools.length} outil{cve.tools.length > 1 ? 's' : ''} associé{cve.tools.length > 1 ? 's' : ''}</h2>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {cve.tools.map((t: any, i: number) => (
                  <Link key={i} to="/tool/$name" params={{ name: t.name }}
                    className="glass rounded-xl p-3 block hover:bg-white/5 transition group">
                    <div className="text-xs font-medium text-slate-200 group-hover:text-indigo-400 truncate">{t.name}</div>
                    {t.desc && <div className="text-[10px] text-slate-500 mt-0.5 line-clamp-1">{t.desc}</div>}
                    <div className="flex items-center gap-2 mt-1.5 text-[9px] text-slate-500">
                      {t.stars && <span className="flex items-center gap-0.5"><Star size={9} className="text-amber-500" /> {t.stars}</span>}
                      <span className="text-indigo-500">{t.match_type}</span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {dec && (
            <div className="glass-card rounded-2xl p-5">
              <ScoreRing score={dec.score} level={dec.level} maxScore={100} />
              <div className="text-center mt-3">
                <span className={`text-xs font-medium px-2.5 py-1 rounded bg-${levelColor}-500/10 text-${levelColor}-400`}>
                  {dec.level}
                </span>
              </div>
            </div>
          )}

          <div className="glass-card rounded-2xl p-5">
            <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-3">Informations</p>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-500">Score CVSS</span>
                <span className="text-white font-medium">{cve.cvss_score || '?'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Sévérité</span>
                <span className="text-white">{cve.severity || '?'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Publiée</span>
                <span className="text-white">{cve.published ? new Date(cve.published).toLocaleDateString('fr-FR') : '?'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Exploits</span>
                <span className="text-white">{cve.exploits?.length || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Outils</span>
                <span className="text-white">{cve.tools?.length || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">CISA KEV</span>
                <span className={cve.is_kev ? 'text-rose-400 font-medium' : 'text-slate-500'}>
                  {cve.is_kev ? 'OUI' : 'NON'}
                </span>
              </div>
            </div>
          </div>

          <a href={`https://nvd.nist.gov/vuln/detail/${cve.cve_id}`} target="_blank" rel="noopener"
            className="glass-card rounded-xl p-3 text-xs text-center text-indigo-400 hover:text-white hover:bg-indigo-500/10 transition flex items-center justify-center gap-1.5">
            Voir sur NVD <ExternalLink size={10} />
          </a>

          <a href={`https://www.exploit-db.com/search?cve=${cve.cve_id}`} target="_blank" rel="noopener"
            className="glass-card rounded-xl p-3 text-xs text-center text-slate-500 hover:text-white hover:bg-slate-500/10 transition">
            Exploit-DB <ExternalLink size={10} className="inline ml-1" />
          </a>
        </div>
      </div>
    </div>
  )
}
