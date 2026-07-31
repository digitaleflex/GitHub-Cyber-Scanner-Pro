import { createRoute, useParams, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import { Shield, ExternalLink, AlertTriangle, Bug, Star, ArrowLeft, Clock, Target, Brain, Wrench, ShieldCheck } from 'lucide-react'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/cve/$id',
  component: CveDetail,
})

function ThreatMeter({ score, kev }: { score?: number | null; kev?: boolean }) {
  const s = score || 0
  const color = kev ? 'from-rose-600 to-red-500' : s >= 9 ? 'from-rose-500 to-red-400' : s >= 7 ? 'from-amber-500 to-orange-400' : 'from-slate-500 to-slate-400'
  const label = kev ? 'Exploitee activement (CISA KEV)' : s >= 9 ? 'Critique' : s >= 7 ? 'Elevee' : s >= 4 ? 'Moyenne' : 'Faible'
  const bg = kev ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' : s >= 9 ? 'bg-rose-500/10 text-rose-400' : s >= 7 ? 'bg-amber-500/10 text-amber-400' : 'bg-slate-500/10 text-slate-400'
  return (
    <div className="glass-card rounded-2xl p-4 sm:p-5">
      <p className="text-[9px] uppercase tracking-widest text-slate-600 mb-2">Niveau de menace</p>
      <div className="flex items-center gap-3">
        <div className="relative w-14 h-14 sm:w-16 sm:h-16 shrink-0">
          <svg className="w-full h-full -rotate-90"><circle cx="50%" cy="50%" r="45%" fill="none" stroke="currentColor" strokeWidth="3" className="text-slate-800" /><circle cx="50%" cy="50%" r="45%" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" className={color} strokeDasharray={`${s * 10} 100`} /></svg>
          <span className="absolute inset-0 flex items-center justify-center text-lg sm:text-xl font-bold text-white">{s.toFixed(1)}</span>
        </div>
        <div>
          <div className={`inline-block text-xs sm:text-sm px-2 py-0.5 rounded font-medium border ${bg}`}>{label}</div>
          {kev && <div className="text-[10px] sm:text-xs text-rose-300 mt-1 flex items-center gap-1"><AlertTriangle size={10} /> Priorite immediate</div>}
        </div>
      </div>
    </div>
  )
}

function CveDetail() {
  const { id } = useParams({ from: '/cve/$id' })
  const { data: cve, isLoading } = useQuery({
    queryKey: ['cve', id],
    queryFn: () => fetch(`/api/cve/${encodeURIComponent(id)}`).then(r => r.json()),
    staleTime: 300_000,
  })
  const { data: analysis } = useQuery({
    queryKey: ['cve-analysis', id],
    queryFn: () => fetch(`/api/cve/${encodeURIComponent(id)}/analysis`).then(r => r.json()).catch(() => ({})),
    staleTime: 3_600_000,
  })
  const hasAnalysis = analysis && analysis.summary && !String(analysis.summary).includes('indisponible')

  if (isLoading) return <div className="text-center py-16 text-slate-500">Chargement...</div>
  if (!cve || cve.error) return (
    <div className="text-center py-16">
      <Shield size={32} className="mx-auto text-slate-600 mb-3" />
      <p className="text-slate-400">{cve?.error || 'CVE introuvable'}</p>
      <Link to="/" className="text-indigo-400 text-xs mt-2 inline-block">← Retour</Link>
    </div>
  )

  return (
    <div className="max-w-4xl mx-auto py-4 sm:py-8 animate-fade">
      <Link to="/" className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-white mb-4 sm:mb-6 transition">
        <ArrowLeft size={12} /> Retour
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Main */}
        <div className="lg:col-span-2 space-y-3 sm:space-y-4">
          <div className="glass-card rounded-2xl p-4 sm:p-6">
            <div className="flex items-start gap-2 mb-2 flex-wrap">
              <h1 className="text-lg sm:text-xl font-bold text-white font-mono">{cve.cve_id}</h1>
              {cve.is_kev && <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] sm:text-xs font-medium bg-rose-500/20 text-rose-300 border border-rose-500/30"><AlertTriangle size={10} /> CISA KEV</span>}
            </div>

            <p className="text-sm text-slate-400 leading-relaxed mb-4">{cve.description || 'Aucune description disponible'}</p>

            <div className="flex flex-wrap items-center gap-2 mb-4">
              {cve.severity && <span className={`glass px-2 py-1 rounded-lg text-[10px] sm:text-xs font-medium ${cve.severity === 'CRITICAL' ? 'text-rose-400 bg-rose-500/10' : cve.severity === 'HIGH' ? 'text-amber-400 bg-amber-500/10' : 'text-slate-400'}`}>{cve.severity}</span>}
              {cve.cvss_score && <span className="glass px-2 py-1 rounded-lg text-[10px] sm:text-xs text-slate-300">CVSS {cve.cvss_score}</span>}
              {cve.published && <span className="glass px-2 py-1 rounded-lg text-[10px] sm:text-xs text-slate-500 flex items-center gap-1"><Clock size={10} /> {new Date(cve.published).toLocaleDateString('fr-FR')}</span>}
            </div>

            {cve.weaknesses && <div className="glass rounded-xl p-3 text-xs text-slate-500"><span className="text-slate-600">Faiblesses :</span> {String(cve.weaknesses).slice(0, 300)}</div>}
          </div>

          {/* Analyse IA */}
          {hasAnalysis && (
            <div className="glass-card rounded-2xl p-4 sm:p-6 border border-indigo-500/20">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-7 h-7 rounded-lg bg-indigo-500/20 flex items-center justify-center"><Brain size={14} className="text-indigo-400" /></div>
                <h2 className="text-sm font-semibold text-white">Analyse IA</h2>
                {analysis.exploitation_likelihood && (
                  <span className={`ml-auto text-[10px] sm:text-xs px-2 py-0.5 rounded font-medium ${
                    analysis.exploitation_likelihood === 'CRITIQUE' ? 'bg-rose-500/20 text-rose-300' :
                    analysis.exploitation_likelihood === 'MOYEN' ? 'bg-amber-500/20 text-amber-300' :
                    'bg-emerald-500/20 text-emerald-300'
                  }`}>Exploitation: {analysis.exploitation_likelihood}</span>
                )}
              </div>

              {analysis.summary && <p className="text-sm text-slate-200 leading-relaxed mb-3">{analysis.summary}</p>}

              <div className="space-y-2">
                {analysis.impact && (
                  <div className="flex items-start gap-2 text-xs">
                    <Target size={12} className="text-rose-400 mt-0.5 shrink-0" />
                    <div><span className="text-slate-500">Impact :</span> <span className="text-slate-300">{analysis.impact}</span></div>
                  </div>
                )}
                {analysis.recommendation && (
                  <div className="flex items-start gap-2 text-xs">
                    <ShieldCheck size={12} className="text-emerald-400 mt-0.5 shrink-0" />
                    <div><span className="text-slate-500">Recommandation :</span> <span className="text-slate-300">{analysis.recommendation}</span></div>
                  </div>
                )}
                {analysis.audience && (
                  <div className="flex items-start gap-2 text-xs">
                    <Wrench size={12} className="text-amber-400 mt-0.5 shrink-0" />
                    <div><span className="text-slate-500">Public :</span> <span className="text-slate-300">{analysis.audience}</span></div>
                  </div>
                )}
                {analysis.patched_in && (
                  <div className="text-xs"><span className="text-slate-500">Corrigee en :</span> <span className="text-emerald-400 font-mono">{analysis.patched_in}</span></div>
                )}
              </div>
            </div>
          )}

          {/* Exploits */}
          {cve.exploits?.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Bug size={14} className="text-amber-400" /> Exploits connus ({cve.exploits.length})
              </h2>
              <div className="space-y-2">
                {cve.exploits.map((e: any, i: number) => (
                  <div key={i} className="glass-card rounded-xl p-3">
                    <div className="flex items-start gap-2">
                      <span className="text-xs text-amber-400 font-medium shrink-0 mt-0.5">#{e.id}</span>
                      <div className="min-w-0">
                        <div className="text-xs text-slate-200">{e.description}</div>
                        <div className="flex items-center gap-2 mt-1 text-[9px] sm:text-[10px] text-slate-600">
                          {e.platform && <span>{e.platform}</span>}
                          {e.type && <span>{e.type}</span>}
                          {e.author && <span>{e.author}</span>}
                          {e.date && <span>{e.date}</span>}
                        </div>
                      </div>
                      <a href={e.file ? `https://www.exploit-db.com/exploits/${e.id}` : '#'} target="_blank" rel="noopener"
                        className="shrink-0 text-slate-600 hover:text-indigo-400"><ExternalLink size={12} /></a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tools */}
          {cve.tools?.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Target size={14} className="text-indigo-400" /> Outils associes ({cve.tools.length})
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {cve.tools.map((t: any, i: number) => (
                  <Link key={i} to="/tool/$name" params={{ name: t.name }}
                    className="glass-card rounded-xl p-3 block group">
                    <div className="text-xs font-medium text-slate-200 group-hover:text-indigo-400 truncate">{t.name}</div>
                    {t.desc && <div className="text-[10px] text-slate-500 mt-0.5 line-clamp-1">{t.desc}</div>}
                    <div className="flex items-center gap-2 mt-1.5 text-[9px] text-slate-600">
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
        <div className="space-y-3 sm:space-y-4">
          <ThreatMeter score={cve.cvss_score} kev={cve.is_kev} />

          <div className="glass-card rounded-2xl p-4 sm:p-5">
            <p className="text-[9px] uppercase tracking-widest text-slate-600 mb-3">Stats</p>
            <div className="space-y-2 text-xs sm:text-sm">
              <div className="flex justify-between"><span className="text-slate-500">Score CVSS</span><span className="text-white font-medium">{cve.cvss_score || '?'}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Severite</span><span className="text-white">{cve.severity || '?'}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Exploits</span><span className="text-white">{cve.exploits?.length || 0}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Outils</span><span className="text-white">{cve.tools?.length || 0}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">KEV</span><span className={cve.is_kev ? 'text-rose-400' : 'text-slate-500'}>{cve.is_kev ? 'OUI' : 'NON'}</span></div>
            </div>
          </div>

          <a href={`https://nvd.nist.gov/vuln/detail/${cve.cve_id}`} target="_blank" rel="noopener"
            className="block w-full text-center glass-card rounded-xl p-3 text-xs font-medium text-indigo-400 hover:text-white hover:bg-indigo-500/10 transition">
            Voir sur NVD <ExternalLink size={10} className="inline ml-1" />
          </a>
        </div>
      </div>
    </div>
  )
}
