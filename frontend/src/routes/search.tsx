import { useState, useEffect, useRef } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useSearch, type SearchResultType, type SearchParams } from '../lib/api'
import { Search, Star, Shield, BookOpen, Hash, ExternalLink, SlidersHorizontal, Brain, Sparkles } from 'lucide-react'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/search', component: SearchPage })

const TYPE_META: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  repo: { label: 'Outils', icon: <Star size={12} />, color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' },
  cve: { label: 'CVE', icon: <Shield size={12} />, color: 'bg-rose-500/10 text-rose-400 border-rose-500/20' },
  book: { label: 'Ressources', icon: <BookOpen size={12} />, color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
  keyword: { label: 'Mots-clés', icon: <Hash size={12} />, color: 'bg-violet-500/10 text-violet-400 border-violet-500/20' },
}

const SORTS: { value: NonNullable<SearchParams['sort']>; label: string }[] = [
  { value: 'relevance', label: 'Pertinence' }, { value: 'stars', label: 'Stars' }, { value: 'updated', label: 'Recent' },
]

function SearchPage() {
  const [query, setQuery] = useState('')
  const [debounced, setDebounced] = useState('')
  const [types, setTypes] = useState<SearchResultType[]>(['repo', 'cve'])
  const [severity, setSeverity] = useState('')
  const [verdict, setVerdict] = useState('')
  const [sort, setSort] = useState<NonNullable<SearchParams['sort']>>('relevance')
  const [page, setPage] = useState(1)
  const [showFilters, setShowFilters] = useState(false)
  const [mode, setMode] = useState<'classic' | 'ai' | 'semantic'>('classic')
  const [aiResults, setAiResults] = useState<any>(null)
  const [aiLoading, setAiLoading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { const t = setTimeout(() => setDebounced(query), 300); return () => clearTimeout(t) }, [query])

  const sp: SearchParams = { q: debounced, page, per_page: 20, types, severity: severity || undefined, security_verdict: verdict || undefined, sort }
  const { data: results, error: classicError, refetch: refetchClassic } = useSearch(mode === 'classic' && debounced.length >= 2 ? sp : { ...sp, q: '' })
  const hasFilters = !!(severity || verdict)

  // AI/Semantic search
  useEffect(() => {
    if (debounced.length < 2 || mode === 'classic') { setAiResults(null); return }
    setAiLoading(true)
    const endpoint = mode === 'ai' ? '/api/search/ai' : '/api/search/semantic'
    fetch(`${endpoint}?q=${encodeURIComponent(debounced)}&limit=20`)
      .then(r => r.json())
      .then(data => { setAiResults(data); setAiLoading(false) })
      .catch(() => setAiLoading(false))
  }, [debounced, mode])

  return (
    <div className="max-w-4xl mx-auto py-4 sm:py-8 animate-fade">
      <h1 className="text-lg font-semibold text-white mb-4">Recherche avancée</h1>

      <div className="flex gap-2 mb-4">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input ref={inputRef} type="text" value={query} onChange={e => { setQuery(e.target.value); setPage(1) }}
            placeholder="Recherche multi-source..." className="w-full pl-10 pr-4 py-3 glass rounded-xl text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500/40" />
        </div>
        <button onClick={() => setShowFilters(!showFilters)}
          className={`glass px-4 py-3 rounded-xl text-sm transition flex items-center gap-2 ${showFilters || hasFilters ? 'text-indigo-400 border-indigo-500/40' : 'text-slate-400 hover:text-white'}`}>
          <SlidersHorizontal size={14} /> Filtres
        </button>
      </div>

      {/* Search mode */}
      <div className="flex flex-wrap items-center gap-1.5 mb-3">
        <button onClick={() => setMode('classic')}
          className={`px-3 py-1.5 rounded-lg text-[10px] sm:text-xs font-medium transition border ${mode === 'classic' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' : 'glass text-slate-500'}`}>
          <Search size={11} className="inline mr-1" /> Classique
        </button>
        <button onClick={() => setMode('ai')}
          className={`px-3 py-1.5 rounded-lg text-[10px] sm:text-xs font-medium transition border ${mode === 'ai' ? 'bg-violet-500/10 text-violet-400 border-violet-500/20' : 'glass text-slate-500'}`}>
          <Brain size={11} className="inline mr-1" /> IA (Groq)
        </button>
        <button onClick={() => setMode('semantic')}
          className={`px-3 py-1.5 rounded-lg text-[10px] sm:text-xs font-medium transition border ${mode === 'semantic' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'glass text-slate-500'}`}>
          <Sparkles size={11} className="inline mr-1" /> Sémantique
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-1.5 mb-3">
        {(['repo','cve','book','keyword'] as const).map(t => (
          <button key={t} onClick={() => setTypes(p => p.includes(t)?p.filter(x=>x!==t):[...p,t])}
            className={`px-3 py-1 rounded-lg text-[10px] sm:text-xs font-medium transition border ${types.includes(t) ? TYPE_META[t].color : 'glass text-slate-500'}`}>{TYPE_META[t].label}</button>
        ))}
      </div>

      {showFilters && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
          <select value={severity} onChange={e => setSeverity(e.target.value)} className="glass px-3 py-2 rounded-lg text-xs text-white"><option value="">Severite</option>{['CRITICAL','HIGH','MEDIUM','LOW'].map(s=><option key={s}>{s}</option>)}</select>
          <select value={verdict} onChange={e => setVerdict(e.target.value)} className="glass px-3 py-2 rounded-lg text-xs text-white"><option value="">Verdict</option>{['Critique','Suspect','Sain'].map(v=><option key={v}>{v}</option>)}</select>
          <select value={sort} onChange={e => setSort(e.target.value as any)} className="glass px-3 py-2 rounded-lg text-xs text-white">{SORTS.map(s=><option key={s.value} value={s.value}>{s.label}</option>)}</select>
        </div>
      )}

      {debounced.length >= 2 ? (
        mode === 'classic' ? (
          classicError ? (
            <div className="glass-card rounded-2xl">
              <ErrorState title="Erreur de recherche" onRetry={() => refetchClassic()} />
            </div>
          ) : results && results.results.length === 0 ? (
            <div className="glass-card rounded-2xl">
              <EmptyState title="Aucun resultat" description={`Aucun element ne correspond a "${debounced}". Essayez d'autres termes ou types.`} />
            </div>
          ) : results ? (
            <div>
              <p className="text-xs text-slate-500 mb-3">{results.total} résultats</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {results.results.map((r,i) => (
                  <div key={i} className="glass-card rounded-xl p-3 group">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] border ${TYPE_META[r.result_type]?.color}`}>{TYPE_META[r.result_type]?.icon}</span>
                      {r.stars != null && <span className="text-[10px] text-amber-400 ml-auto">★ {r.stars.toLocaleString()}</span>}
                    </div>
                    <Link to="/tool/$name" params={{ name: r.name }} className="text-xs font-medium text-slate-200 hover:text-indigo-400 transition block truncate">{r.name}</Link>
                    {r.desc && <p className="text-[10px] text-slate-500 line-clamp-2 mt-0.5">{r.desc.slice(0,120)}</p>}
                    <div className="flex items-center gap-2 mt-1.5 text-[9px] text-slate-500">
                      {r.lang && <span>{r.lang}</span>}
                      <a href={r.url||'#'} target="_blank" rel="noopener" className="hover:text-indigo-400 ml-auto"><ExternalLink size={9} /></a>
                    </div>
                  </div>
                ))}
              </div>
              {results.pages > 1 && (
                <div className="flex items-center justify-center gap-3 mt-6">
                  <button onClick={() => setPage(p=>Math.max(1,p-1))} disabled={page===1} className="glass px-4 py-2 rounded-full text-xs disabled:opacity-30">Prec</button>
                  <span className="text-xs text-slate-500">{page}/{results.pages}</span>
                  <button onClick={() => setPage(p=>Math.min(results.pages,p+1))} disabled={page>=results.pages} className="glass px-4 py-2 rounded-full text-xs disabled:opacity-30">Suiv</button>
                </div>
              )}
            </div>
          ) : null
        ) : (
          <div>
            {aiLoading ? (
              <div className="text-center py-16">
                <Brain size={24} className="mx-auto text-violet-400 animate-pulse mb-3" />
                <p className="text-slate-500 text-sm">Recherche {mode === 'ai' ? 'IA' : 'sémantique'} en cours...</p>
              </div>
            ) : aiResults ? (
              <div>
                <p className="text-xs text-slate-500 mb-3">
                  {aiResults.total || aiResults.results?.length || 0} résultats
                  {aiResults.ai_explanation && <span className="ml-2 text-violet-400 italic">{aiResults.ai_explanation}</span>}
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {(aiResults.results || []).slice(0, 20).map((r: any, i: number) => (
                    <div key={i} className="glass-card rounded-xl p-3 group">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] border ${TYPE_META[r.result_type || 'repo']?.color}`}>
                          {TYPE_META[r.result_type || 'repo']?.icon}
                        </span>
                        {r.stars != null && <span className="text-[10px] text-amber-400 ml-auto">★ {r.stars.toLocaleString()}</span>}
                        {r.score != null && <span className="text-[10px] text-violet-400 ml-auto">{(r.score * 100).toFixed(0)}%</span>}
                      </div>
                      <Link to="/tool/$name" params={{ name: r.name }} className="text-xs font-medium text-slate-200 hover:text-indigo-400 transition block truncate">{r.name}</Link>
                      {r.desc && <p className="text-[10px] text-slate-500 line-clamp-2 mt-0.5">{r.desc.slice(0,120)}</p>}
                      <div className="flex items-center gap-2 mt-1.5 text-[9px] text-slate-500">
                        {r.lang && <span>{r.lang}</span>}
                        <a href={r.url||'#'} target="_blank" rel="noopener" className="hover:text-indigo-400 ml-auto"><ExternalLink size={9} /></a>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        )
      ) : (
        <div className="text-center py-16 glass-card rounded-2xl">
          <Search size={32} className="mx-auto text-slate-500 mb-3" />
          <p className="text-slate-400 text-sm">Tapez au moins 2 caractères pour chercher</p>
          <p className="text-slate-500 text-xs mt-1">
            {mode === 'ai' ? 'Recherche IA avec re-ranking Groq (Llama 3.3)' :
             mode === 'semantic' ? 'Recherche sémantique par similarité cosine' :
             'Recherche classique multi-source'}
          </p>
        </div>
      )}
    </div>
  )
}
