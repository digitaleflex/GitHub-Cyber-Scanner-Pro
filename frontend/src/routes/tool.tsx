import { createRoute, useParams, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import { Star, ExternalLink, Shield, Clock, TrendingUp, ArrowLeft } from 'lucide-react'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/tool/$name',
  component: ToolDetail,
})

function TrustMeter({ score }: { score: number }) {
  const strokeColor = score >= 70 ? '#16A34A' : score >= 40 ? '#D97706' : '#DC2626'
  const label = score >= 70 ? 'Confiance élevée' : score >= 40 ? 'À surveiller' : 'Risque élevé'
  const labelColor = score >= 70 ? 'var(--lime)' : score >= 40 ? 'var(--amber)' : 'var(--red)'
  const labelBg = score >= 70 ? 'var(--lime-light)' : score >= 40 ? 'var(--amber-light)' : 'var(--red-light)'
  const labelBorder = score >= 70 ? 'var(--lime)' : score >= 40 ? 'var(--amber)' : 'var(--red)'
  const r = 28; const circ = 2 * Math.PI * r
  return (
    <div className="surface rounded-2xl p-4 sm:p-5" style={{ border: '1px solid var(--border)' }}>
      <p className="caption mb-2" style={{ color: 'var(--amber)' }}>Score de confiance</p>
      <div className="flex items-center gap-3">
        <div className="relative w-16 h-16 shrink-0">
          <svg viewBox="0 0 64 64" className="w-full h-full -rotate-90">
            <circle cx="32" cy="32" r={r} fill="none" stroke="var(--border)" strokeWidth="3" />
            <circle cx="32" cy="32" r={r} fill="none" stroke={strokeColor} strokeWidth="3" strokeLinecap="round"
              strokeDasharray={`${(score / 100) * circ} ${circ}`} />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-lg sm:text-xl font-bold" style={{ color: 'var(--text)' }}>{score}</span>
        </div>
        <div>
          <div className="text-xs sm:text-sm font-medium px-2 py-0.5 rounded-full border inline-block"
            style={{ background: labelBg, color: labelColor, borderColor: labelBorder }}>{label}</div>
          <p className="text-[10px] sm:text-xs text-muted mt-0.5">Basé sur stars, activité et verdict IA</p>
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

  if (isLoading) return <div className="text-center py-16 text-muted">Chargement...</div>
  if (!tool || tool.error) return (
    <div className="text-center py-16">
      <Shield size={32} className="mx-auto text-muted mb-3" />
      <p className="text-secondary">Outil introuvable</p>
      <Link to="/" className="text-xs mt-2 inline-block" style={{ color: 'var(--cyan)' }}>← Retour</Link>
    </div>
  )

  const verdictStyle = () => {
    if (tool.security_verdict === 'Critique') return { bg: 'var(--red-light)', text: 'var(--red)', border: 'var(--red)' }
    if (tool.security_verdict === 'Suspect') return { bg: 'var(--amber-light)', text: 'var(--amber)', border: 'var(--amber)' }
    return { bg: 'var(--lime-light)', text: 'var(--lime)', border: 'var(--lime)' }
  }
  const vs = verdictStyle()

  return (
    <div className="max-w-4xl mx-auto py-4 sm:py-8 animate-fade">
      <Link to="/" className="inline-flex items-center gap-1 text-xs text-secondary hover:underline transition mb-4 sm:mb-6">
        <ArrowLeft size={12} /> Retour
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Main */}
        <div className="lg:col-span-2 space-y-3 sm:space-y-4">
          <div className="surface rounded-2xl p-4 sm:p-6" style={{ border: '1px solid var(--border)' }}>
            <div className="flex items-start gap-2 mb-2">
              <h1 className="h2 flex-1" style={{ color: 'var(--text)' }}>{tool.full_name}</h1>
              <a href={tool.html_url} target="_blank" rel="noopener"
                className="text-xs px-3 py-1.5 rounded-full flex items-center gap-1 shrink-0 font-medium transition-all hover:-translate-y-0.5"
                style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-secondary)', textDecoration: 'none' }}>
                <ExternalLink size={11} /> GitHub
              </a>
            </div>

            <p className="body-sm mb-4" style={{ color: 'var(--text-secondary)' }}>{tool.description || 'Aucune description'}</p>

            <div className="flex flex-wrap items-center gap-2 mb-4">
              {tool.language && <span className="text-xs px-2 py-1 rounded-lg" style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}>{tool.language}</span>}
              {tool.stars != null && <span className="text-xs px-2 py-1 rounded-lg flex items-center gap-1" style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border)', color: 'var(--amber)' }}><Star size={10} /> {tool.stars.toLocaleString()} stars</span>}
              {tool.security_verdict && <span className="text-xs px-2 py-1 rounded-lg font-medium border" style={{ background: vs.bg, color: vs.text, borderColor: vs.border }}>{tool.security_verdict}</span>}
              {tool.updated_at && <span className="text-xs px-2 py-1 rounded-lg flex items-center gap-1" style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}><Clock size={10} /> {new Date(tool.updated_at).toLocaleDateString('fr-FR')}</span>}
            </div>

            {tool.security_details && (
              <div className="rounded-xl p-3 text-xs" style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                <span className="text-muted">Analyse IA :</span> {tool.security_details}
              </div>
            )}
          </div>

          {/* Similar tools */}
          {tool.similar?.length > 0 && (
            <div>
              <h2 className="h3 mb-3 flex items-center gap-2" style={{ color: 'var(--text)' }}>
                <TrendingUp size={14} style={{ color: 'var(--cyan)' }} /> Outils similaires
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {tool.similar.map((s: any, i: number) => (
                  <Link key={i} to="/tool/$name" params={{ name: s.name }}
                    className="rounded-xl p-3 block transition-all hover:-translate-y-0.5"
                    style={{ background: 'var(--surface)', border: '1px solid var(--border)', textDecoration: 'none' }}>
                    <div className="text-xs font-medium truncate" style={{ color: 'var(--text)' }}>{s.name}</div>
                    <div className="text-[10px] text-muted mt-0.5 truncate">{s.desc?.slice(0, 80)}</div>
                    <div className="flex items-center gap-2 mt-1.5 text-[9px] text-muted">
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

          <div className="surface rounded-2xl p-4 sm:p-5" style={{ border: '1px solid var(--border)' }}>
            <p className="caption mb-3" style={{ color: 'var(--amber)' }}>Statistiques</p>
            <div className="space-y-2 text-xs sm:text-sm">
              <div className="flex justify-between"><span className="text-muted">Stars</span><span className="font-medium" style={{ color: 'var(--text)' }}>{tool.stars?.toLocaleString() || '0'}</span></div>
              <div className="flex justify-between"><span className="text-muted">Langage</span><span style={{ color: 'var(--text)' }}>{tool.language || '?'}</span></div>
              <div className="flex justify-between"><span className="text-muted">Vitalité</span><span style={{ color: 'var(--text)' }}>{tool.vitality_score || '0'}/100</span></div>
              <div className="flex justify-between"><span className="text-muted">Découvert</span><span className="text-[11px]" style={{ color: 'var(--text)' }}>{tool.discovered_at ? new Date(tool.discovered_at).toLocaleDateString('fr-FR') : '?'}</span></div>
            </div>
          </div>

          <a href={tool.html_url} target="_blank" rel="noopener"
            className="block w-full text-center surface rounded-xl p-3 text-xs font-medium transition-all hover:-translate-y-0.5"
            style={{ border: '1px solid var(--border)', color: 'var(--cyan)', textDecoration: 'none' }}>
            Voir sur GitHub <ExternalLink size={10} />
          </a>
        </div>
      </div>
    </div>
  )
}
