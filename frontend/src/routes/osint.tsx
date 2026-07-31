import { useState } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { ExternalLink, Loader2, MapPin, User, Hash, Brain } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/osint', component: OsintPage })

function OsintPage() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const search = async () => {
    if (!text.trim()) return
    setLoading(true); setResult(null)
    try {
      const r = await fetch(`/api/osint/investigate?free_text=${encodeURIComponent(text)}`, { method: 'POST' }).then(r => r.json())
      setResult(r)
    } catch {}
    setLoading(false)
  }

  return (
    <div className="max-w-4xl mx-auto py-4 sm:py-8 animate-fade">
      <h2 className="text-lg font-semibold text-white mb-2">OSINT Lab</h2>
      <p className="text-xs sm:text-sm text-slate-400 mb-4 sm:mb-6">
        Recherche de personnes par IA — décrivez qui vous cherchez, l'IA extrait les paramètres, les outils OSINT enquêtent.
      </p>

      <div className="glass-card rounded-2xl p-4 sm:p-6 mb-6">
        <div className="flex flex-col sm:flex-row gap-3">
          <textarea value={text} onChange={e => setText(e.target.value)}
            placeholder="Ex: un chercheur en securite allemand qui travaille sur la detection de malwares avec YARA et Sigma..."
            className="flex-1 px-4 py-3 glass rounded-xl text-sm text-white placeholder-slate-500 min-h-[80px] focus:ring-2 focus:ring-cyan-500/40"
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); search() } }} />
          <button onClick={search} disabled={loading || !text.trim()}
            className="px-6 py-3 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 rounded-xl text-sm font-medium hover:bg-cyan-500/20 disabled:opacity-30 transition self-end">
            {loading ? <Loader2 size={16} className="animate-spin" /> : 'Enqueter'}
          </button>
        </div>
      </div>

      {result && (
        <div className="space-y-4 sm:space-y-6 animate-fade">
          {/* AI Extraction */}
          {result.ai_extracted?.name && (
            <div className="glass-card rounded-2xl p-4 sm:p-6">
              <div className="flex items-center gap-2 mb-3">
                <Brain size={15} className="text-violet-400" />
                <h3 className="text-sm font-semibold text-white">Parametres extraits par l'IA</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {result.ai_extracted.name && (
                  <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 text-xs"><User size={11} /> {result.ai_extracted.name}</span>
                )}
                {result.ai_extracted.location && (
                  <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 text-xs"><MapPin size={11} /> {result.ai_extracted.location}</span>
                )}
                {result.ai_extracted.keywords?.map((k: string, i: number) => (
                  <span key={i} className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-500/10 text-slate-300 text-xs"><Hash size={11} /> {k}</span>
                ))}
              </div>
              {result.ai_extracted.strategy && (
                <p className="text-xs text-slate-500 mt-3 italic">Strategie: {result.ai_extracted.strategy}</p>
              )}
            </div>
          )}

          {/* Summary */}
          <p className="text-sm text-slate-400">{result.summary}</p>

          {/* GitHub Profiles */}
          {result.findings?.github_profiles?.length > 0 && (
            <div className="glass-card rounded-2xl p-4 sm:p-6">
              <h3 className="text-sm font-semibold text-white mb-3">Profils GitHub ({result.findings.github_profiles.length})</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {result.findings.github_profiles.map((p: any, i: number) => (
                  <a key={i} href={p.url} target="_blank" rel="noopener"
                    className="glass-card rounded-xl p-3 flex items-start gap-3 group">
                    <img src={p.avatar} className="w-10 h-10 rounded-full" alt="" />
                    <div className="min-w-0">
                      <div className="text-xs font-medium text-slate-200 group-hover:text-indigo-400">{p.username}</div>
                      {p.name && <div className="text-[10px] text-slate-400">{p.name}</div>}
                      {p.location && <div className="text-[9px] text-slate-600">{p.location}</div>}
                      {p.bio && <div className="text-[10px] text-slate-500 mt-1 line-clamp-2">{p.bio}</div>}
                      <div className="flex items-center gap-2 mt-1 text-[9px] text-slate-600">
                        {p.company && <span>{p.company}</span>}
                        {p.twitter && <span>@{p.twitter}</span>}
                        <span>{p.followers} followers</span>
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Social Presence */}
          {result.findings?.social_presence?.length > 0 && (
            <div className="glass-card rounded-2xl p-4 sm:p-6">
              <h3 className="text-sm font-semibold text-white mb-3">Presence sociale</h3>
              <div className="flex flex-wrap gap-2">
                {result.findings.social_presence.filter((s: any) => s.present).map((s: any, i: number) => (
                  <a key={i} href={s.url} target="_blank" rel="noopener"
                    className="px-3 py-1.5 glass rounded-lg text-xs text-emerald-400 hover:bg-emerald-500/10 transition flex items-center gap-1.5">
                    {s.platform} <ExternalLink size={10} />
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
