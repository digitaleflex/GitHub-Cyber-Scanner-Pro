import { useState, useEffect, useRef } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useSearch, type SearchResult, type SearchResultType, type SearchParams } from '../lib/api'
import { useQuery } from '@tanstack/react-query'
import { Search, Star, Shield, BookOpen, Hash, ExternalLink, ArrowRight, AlertTriangle } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/', component: ExplorePage })

const TYPE_META: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  repo: { label: 'Outil', icon: <Star size={12} />, color: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' },
  cve: { label: 'CVE', icon: <Shield size={12} />, color: 'bg-rose-500/10 text-rose-400 border-rose-500/20' },
  book: { label: 'Ressource', icon: <BookOpen size={12} />, color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
  keyword: { label: 'Mot-cle', icon: <Hash size={12} />, color: 'bg-violet-500/10 text-violet-400 border-violet-500/20' },
}

function ExplorePage() {
  const [query, setQuery] = useState('')
  const [debounced, setDebounced] = useState('')
  const [types, setTypes] = useState<SearchResultType[]>(['repo'])
  const [severity, setSeverity] = useState('')
  const [sort, setSort] = useState<NonNullable<SearchParams['sort']>>('stars')
  const [page, setPage] = useState(1)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { const t = setTimeout(() => setDebounced(query), 300); return () => clearTimeout(t) }, [query])

  const sp: SearchParams = { q: debounced, page, per_page: 12, types, severity: severity || undefined, sort, security_verdict: undefined, category: undefined }
  const { data: results, isLoading } = useSearch(debounced.length >= 2 ? sp : { ...sp, q: '' })
  const hasResults = debounced.length >= 2 && results && results.results.length > 0

  return (
    <div className="max-w-3xl mx-auto w-full">
      {/* Search input */}
      <div className="relative mb-3 sm:mb-4">
        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
        <input ref={inputRef} type="text" value={query} onChange={e => { setQuery(e.target.value); setPage(1) }}
          placeholder="Rechercher un outil, une CVE, une technique..."
          className="w-full pl-11 pr-4 py-3.5 sm:py-4 glass rounded-2xl text-sm sm:text-base text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 transition" />
        {isLoading && <div className="absolute right-4 top-1/2 -translate-y-1/2"><div className="w-5 h-5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" /></div>}
      </div>

      {/* Type filters */}
      <div className="flex items-center justify-center gap-1.5 mb-4 sm:mb-6 flex-wrap">
        {(['repo','cve','book','keyword'] as const).map(t => (
          <button key={t} onClick={() => setTypes(p => p.includes(t) ? p.filter(x => x!==t) : [...p,t])}
            className={`px-2.5 sm:px-3 py-1 rounded-full text-[10px] sm:text-xs font-medium transition border ${types.includes(t) ? TYPE_META[t].color + ' border-current/30' : 'glass text-slate-500 hover:text-slate-300'}`}>
            {TYPE_META[t].label}
          </button>
        ))}
        <select value={severity} onChange={e => setSeverity(e.target.value)}
          className="glass px-2.5 py-1 rounded-full text-[10px] sm:text-xs text-slate-400 focus:outline-none">
          <option value="" className="bg-slate-900">Severite</option>
          {['CRITICAL','HIGH','MEDIUM','LOW'].map(s => <option key={s} className="bg-slate-900">{s}</option>)}
        </select>
        <select value={sort} onChange={e => setSort(e.target.value as any)}
          className="glass px-2.5 py-1 rounded-full text-[10px] sm:text-xs text-slate-400 focus:outline-none">
          <option value="stars" className="bg-slate-900">Stars</option>
          <option value="relevance" className="bg-slate-900">Pertinence</option>
          <option value="updated" className="bg-slate-900">Recents</option>
        </select>
      </div>

      {/* Results */}
      {hasResults && (
        <div className="animate-fade">
          <p className="text-[10px] sm:text-xs text-slate-500 mb-3">{results!.total.toLocaleString()} resultats</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3">
            {results!.results.map((r,i) => <ResultCard key={i} result={r} />)}
          </div>
          {results!.pages > 1 && (
            <div className="flex items-center justify-center gap-3 mt-6">
              <button onClick={() => setPage(p => Math.max(1,p-1))} disabled={page===1} className="glass px-4 py-2 rounded-full text-xs text-slate-300 disabled:opacity-30 hover:border-indigo-500/30">Precedent</button>
              <span className="text-xs text-slate-500">{page}/{results!.pages}</span>
              <button onClick={() => setPage(p => Math.min(results!.pages,p+1))} disabled={page>=results!.pages} className="glass px-4 py-2 rounded-full text-xs text-slate-300 disabled:opacity-30 hover:border-indigo-500/30">Suivant</button>
            </div>
          )}
        </div>
      )}

      {/* Digest section (when no search) */}
      {!hasResults && !isLoading && <DigestSection />}
    </div>
  )
}

function ResultCard({ result }: { result: SearchResult }) {
  const meta = TYPE_META[result.result_type] || TYPE_META.repo
  const desc = result.desc ? (result.desc.length > 100 ? result.desc.slice(0,100)+'...' : result.desc) : null
  const vc = result.security_verdict === 'Critique' ? 'text-rose-400 bg-rose-500/10' : result.security_verdict === 'Suspect' ? 'text-amber-400 bg-amber-500/10' : result.security_verdict ? 'text-emerald-400 bg-emerald-500/10' : ''
  return (
    <div className="glass-card rounded-xl p-3 sm:p-4 group cursor-pointer">
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] sm:text-[10px] font-medium border ${meta.color}`}>{meta.icon}</span>
        {result.stars != null && <span className="flex items-center gap-1 text-[10px] sm:text-xs text-slate-500 shrink-0"><Star size={10} className="text-amber-500" />{result.stars.toLocaleString()}</span>}
      </div>
      <Link to="/tool/$name" params={{ name: result.name }} className="text-xs sm:text-sm font-medium text-slate-200 hover:text-indigo-400 transition line-clamp-1 block mb-1">{result.name}</Link>
      {desc && <p className="text-[10px] sm:text-xs text-slate-500 leading-relaxed line-clamp-2">{desc}</p>}
      <div className="flex items-center gap-2 mt-2 text-[9px] sm:text-[10px] text-slate-600">
        {result.security_verdict && <span className={`px-1.5 py-0.5 rounded ${vc}`}>{result.security_verdict}</span>}
        {result.lang && <span>{result.lang}</span>}
        <a href={result.url||'#'} target="_blank" rel="noopener" className="flex items-center gap-0.5 hover:text-indigo-400 ml-auto"><ExternalLink size={9} /></a>
      </div>
    </div>
  )
}

function DigestSection() {
  const { data: d, isLoading } = useQuery({ queryKey: ['digest-home'], queryFn: () => fetch('/api/digest').then(r => r.json()), staleTime: 600_000 })

  if (isLoading || !d || d.error) return (
    <div className="glass-card rounded-2xl p-6 sm:p-8 text-center max-w-lg mx-auto">
      <Search size={28} className="mx-auto text-slate-600 mb-3" />
      <p className="text-slate-500 text-sm">Commencez a taper pour rechercher</p>
      <p className="text-slate-700 text-xs mt-1">Recherche semantique IA disponible</p>
    </div>
  )

  return (
    <div className="max-w-2xl mx-auto space-y-3 sm:space-y-4 animate-slide">
      {/* Digest header */}
      <div className="glass-card rounded-2xl p-4 sm:p-6">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-6 h-6 rounded-lg bg-rose-500/10 flex items-center justify-center"><AlertTriangle size={13} className="text-rose-400" /></div>
          <h3 className="text-sm sm:text-base font-semibold text-white">{d.title || 'Analyse du jour'}</h3>
          {d.date && <span className="text-[10px] text-slate-600 ml-auto">{d.date}</span>}
        </div>
        {d.summary && <p className="text-xs sm:text-sm text-slate-400 leading-relaxed mb-4">{d.summary}</p>}
        
        {d.top_threats?.length > 0 && (
          <div className="space-y-2 mb-4">
            <h4 className="text-[10px] uppercase tracking-widest text-slate-600">Menaces detectees</h4>
            {d.top_threats.slice(0, 3).map((t: any, i: number) => (
              <div key={i} className="flex items-start gap-3 glass-card rounded-xl p-3">
                <span className={`shrink-0 w-2 h-2 rounded-full mt-1.5 ${t.severity==='CRITIQUE'?'bg-rose-400':t.severity==='ELEVE'?'bg-amber-400':'bg-slate-500'}`} />
                <div className="min-w-0">
                  <div className="text-xs sm:text-sm font-medium text-slate-200">{t.name}</div>
                  <div className="text-[10px] sm:text-xs text-slate-500 mt-0.5">{t.description?.slice(0, 120)}</div>
                </div>
                <span className={`shrink-0 text-[9px] px-1.5 py-0.5 rounded ${t.severity==='CRITIQUE'?'bg-rose-500/10 text-rose-400':t.severity==='ELEVE'?'bg-amber-500/10 text-amber-400':'bg-slate-500/10 text-slate-400'}`}>{t.severity}</span>
              </div>
            ))}
          </div>
        )}

        {d.key_insight && (
          <div className="bg-gradient-to-r from-indigo-500/5 to-violet-500/5 border border-indigo-500/10 rounded-xl p-3 sm:p-4">
            <p className="text-[9px] uppercase tracking-widest text-indigo-400 mb-1">Insight cle</p>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">{d.key_insight}</p>
          </div>
        )}

        {/* CTA */}
        {d.trending_tools?.length > 0 && (
          <div className="mt-4 pt-4 border-t border-white/[0.04]">
            <h4 className="text-[10px] uppercase tracking-widest text-slate-600 mb-2">Outils en tendance</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {d.trending_tools.slice(0, 4).map((t: any, i: number) => (
                <div key={i} className="flex items-center gap-2 text-xs text-slate-400">
                  <ArrowRight size={10} className="text-slate-600 shrink-0" />
                  <span className="truncate">{t.name}</span>
                  <span className="text-[9px] text-slate-600 shrink-0">{t.category}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Trust badges */}
      <div className="text-center">
        <p className="text-[9px] sm:text-[10px] text-slate-600 mb-1">
          <span className="text-indigo-400">{d.stats?.new_repos || '...'}</span> nouveaux outils &middot;{' '}
          <span className="text-rose-400">{d.stats?.new_cves || '...'}</span> nouvelles CVE analysees aujourd'hui
        </p>
      </div>
    </div>
  )
}
