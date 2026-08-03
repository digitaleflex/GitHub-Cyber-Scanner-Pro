import { createRoute, useParams } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import { Star, ExternalLink, Shield, Clock, TrendingUp, ArrowLeft } from 'lucide-react'
import { Link } from '@tanstack/react-router'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/tool/$name',
  component: ToolDetail,
})

function TrustMeter({ score }: { score: number }) {
  const color = score >= 70 ? 'stroke-emerald-400' : score >= 40 ? 'stroke-amber-400' : 'stroke-rose-400'
  const label = score >= 70 ? 'Confiance elevee' : score >= 40 ? 'A surveiller' : 'Risque eleve'
  const bg = score >= 70 ? 'bg-emerald-500/10 text-emerald-400' : score >= 40 ? 'bg-amber-500/10 text-amber-400' : 'bg-rose-500/10 text-rose-400'
  const r = 28; const circ = 2 * Math.PI * r
  return (
    <div className="glass-card rounded-2xl p-4 sm:p-5">
      <p className="text-[9px] uppercase tracking-widest text-slate-600 mb-2">Score de confiance</p>
      <div className="flex items-center gap-3">
        <div className="relative w-16 h-16 shrink-0">
          <svg viewBox="0 0 64 64" className="w-full h-full -rotate-90">
            <circle cx="32" cy="32" r={r} fill="none" stroke="currentColor" strokeWidth="3" className="text-slate-700" />
            <circle cx="32" cy="32" r={r} fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" className={color}
              strokeDasharray={`${(score / 100) * circ} ${circ}`} />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-lg sm:text-xl font-bold text-white">{score}</span>
        </div>
        <div>
          <div className={`text-xs sm:text-sm font-medium ${bg.split(' ')[1]}`}>{label}</div>
          <p className="text-[10px] sm:text-xs text-slate-500 mt-0.5">Base sur stars, activite et verdict IA</p>
        </div>
      </div>
    </div>
  )
}

function ToolDetail() {
  const { name } = useParams({ from: '/tool/$name' })
  const { data: tool, isLoading } = useQuery({
    queryKey: ['tool', name],
    queryFn: () => fetch(`/api/tool/${encodeURIComponent(name)}`).then(r => r.json()),
    staleTime: 120_000,
  })

  if (isLoading) return <div className="text-center py-16 text-slate-500">Chargement...</div>
  if (!tool || tool.error) return (
    <div className="text-center py-16">
      <Shield size={32} className="mx-auto text-slate-600 mb-3" />
      <p className="text-slate-400">Outil introuvable</p>
      <Link to="/" className="text-indigo-400 text-xs mt-2 inline-block">← Retour</Link>
    </div>
  )

  const verdictColor = tool.security_verdict === 'Critique' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
    tool.security_verdict === 'Suspect' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
    'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'

  return (
    <div className="max-w-4xl mx-auto py-4 sm:py-8 animate-fade">
      <Link to="/" className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-white mb-4 sm:mb-6 transition">
        <ArrowLeft size={12} /> Retour
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Main */}
        <div className="lg:col-span-2 space-y-3 sm:space-y-4">
          <div className="glass-card rounded-2xl p-4 sm:p-6">
            <div className="flex items-start gap-2 mb-2">
              <h1 className="text-lg sm:text-xl font-bold text-white flex-1">{tool.full_name}</h1>
              <a href={tool.html_url} target="_blank" rel="noopener"
                className="glass px-3 py-1.5 rounded-full text-xs text-slate-400 hover:text-indigo-400 transition flex items-center gap-1 shrink-0">
                <ExternalLink size={11} /> GitHub
              </a>
            </div>

            <p className="text-sm text-slate-400 leading-relaxed mb-4">{tool.description || 'Aucune description'}</p>

            <div className="flex flex-wrap items-center gap-2 mb-4">
              {tool.language && <span className="glass px-2 py-1 rounded-lg text-[10px] sm:text-xs text-slate-300">{tool.language}</span>}
              {tool.stars != null && <span className="glass px-2 py-1 rounded-lg text-[10px] sm:text-xs text-amber-400 flex items-center gap-1"><Star size={10} /> {tool.stars.toLocaleString()} stars</span>}
              {tool.security_verdict && <span className={`px-2 py-1 rounded-lg text-[10px] sm:text-xs font-medium border ${verdictColor}`}>{tool.security_verdict}</span>}
              {tool.updated_at && <span className="glass px-2 py-1 rounded-lg text-[10px] sm:text-xs text-slate-500 flex items-center gap-1"><Clock size={10} /> {new Date(tool.updated_at).toLocaleDateString('fr-FR')}</span>}
            </div>

            {tool.security_details && (
              <div className="glass rounded-xl p-3 text-xs text-slate-400">
                <span className="text-slate-600">Analyse IA :</span> {tool.security_details}
              </div>
            )}
          </div>

          {/* Similar tools */}
          {tool.similar?.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <TrendingUp size={14} className="text-indigo-400" /> Outils similaires
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {tool.similar.map((s: any, i: number) => (
                  <Link key={i} to="/tool/$name" params={{ name: s.name }}
                    className="glass-card rounded-xl p-3 block group">
                    <div className="text-xs font-medium text-slate-200 group-hover:text-indigo-400 transition truncate">{s.name}</div>
                    <div className="text-[10px] text-slate-600 mt-0.5 truncate">{s.desc?.slice(0, 80)}</div>
                    <div className="flex items-center gap-2 mt-1.5 text-[9px] text-slate-600">
                      {s.stars && <span>★ {s.stars.toLocaleString()}</span>}
                      <span>sim {(s.similarity * 100).toFixed(0)}%</span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-3 sm:space-y-4">
          {tool.trust_score != null && <TrustMeter score={tool.trust_score} />}

          <div className="glass-card rounded-2xl p-4 sm:p-5">
            <p className="text-[9px] uppercase tracking-widest text-slate-600 mb-3">Statistiques</p>
            <div className="space-y-2 text-xs sm:text-sm">
              <div className="flex justify-between"><span className="text-slate-500">Stars</span><span className="text-white font-medium">{tool.stars?.toLocaleString() || '0'}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Langage</span><span className="text-white">{tool.language || '?'}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Vitalite</span><span className="text-white">{tool.vitality_score || '0'}/100</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Decouvert</span><span className="text-white text-[11px]">{tool.discovered_at ? new Date(tool.discovered_at).toLocaleDateString('fr-FR') : '?'}</span></div>
            </div>
          </div>

          <a href={tool.html_url} target="_blank" rel="noopener"
            className="block w-full text-center glass-card rounded-xl p-3 text-xs font-medium text-indigo-400 hover:text-white hover:bg-indigo-500/10 transition">
            Voir sur GitHub <ExternalLink size={10} className="inline ml-1" />
          </a>
        </div>
      </div>
    </div>
  )
}
