import { useState, useEffect, useRef } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useSearch, type SearchResult, type SearchResultType, type SearchParams } from '../lib/api'
import { useQuery } from '@tanstack/react-query'
import { Search, Star, Shield, BookOpen, Hash, ExternalLink, AlertTriangle, TrendingUp, Newspaper } from 'lucide-react'

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
  const [page, setPage] = useState(1)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => { const t = setTimeout(() => setDebounced(query), 300); return () => clearTimeout(t) }, [query])

  const sp: SearchParams = { q: debounced, page, per_page: 12, types, sort: 'stars' }
  const { data: results, isLoading } = useSearch(debounced.length >= 2 ? sp : { ...sp, q: '' })
  const hasResults = debounced.length >= 2 && results && results.results.length > 0

  return (
    <div className="max-w-5xl mx-auto w-full">
      {/* Search bar */}
      <div className="relative mb-3">
        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
        <input ref={inputRef} type="text" value={query} onChange={e => { setQuery(e.target.value); setPage(1) }}
          placeholder="Rechercher un outil, une CVE, une technique..."
          className="w-full pl-11 pr-4 py-3.5 sm:py-4 glass rounded-2xl text-sm sm:text-base text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 transition" />
        {isLoading && <div className="absolute right-4 top-1/2 -translate-y-1/2"><div className="w-5 h-5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" /></div>}
      </div>

      {/* Type toggles */}
      <div className="flex items-center justify-center gap-1.5 mb-4 sm:mb-6 flex-wrap">
        {(['repo','cve','book','keyword'] as const).map(t => (
          <button key={t} onClick={() => setTypes(p => p.includes(t) ? p.filter(x => x!==t) : [...p,t])}
            className={`px-2.5 sm:px-3 py-1 rounded-full text-[10px] sm:text-xs font-medium transition border ${types.includes(t) ? TYPE_META[t].color + ' border-current/30' : 'glass text-slate-500 hover:text-slate-300'}`}>
            {TYPE_META[t].label}
          </button>
        ))}
      </div>

      {/* Search Results */}
      {hasResults && (
        <div className="animate-fade">
          <p className="text-[10px] sm:text-xs text-slate-500 mb-3">{results!.total.toLocaleString()} resultats</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3">
            {results!.results.map((r,i) => <ResultCard key={i} result={r} />)}
          </div>
          {results!.pages > 1 && (
            <div className="flex items-center justify-center gap-3 mt-6">
              <button onClick={() => setPage(p => Math.max(1,p-1))} disabled={page===1} className="glass px-4 py-2 rounded-full text-xs text-slate-300 disabled:opacity-30">Precedent</button>
              <span className="text-xs text-slate-500">{page}/{results!.pages}</span>
              <button onClick={() => setPage(p => Math.min(results!.pages,p+1))} disabled={page>=results!.pages} className="glass px-4 py-2 rounded-full text-xs text-slate-300 disabled:opacity-30">Suivant</button>
            </div>
          )}
        </div>
      )}

      {/* Home sections (when no search) */}
      {!hasResults && !isLoading && (
        <div className="space-y-4 sm:space-y-6 animate-fade">
          <StatsBar />
          <DigestSection />
          <ThreatSection />
          <OsintSection />
          <AiLabSection />
          <BlogSection />
          <TrendingSection />
        </div>
      )}
    </div>
  )
}

function ResultCard({ result }: { result: SearchResult }) {
  const meta = TYPE_META[result.result_type] || TYPE_META.repo
  const desc = result.desc ? (result.desc.length > 100 ? result.desc.slice(0,100)+'...' : result.desc) : null
  const vc = result.security_verdict === 'Critique' ? 'text-rose-400 bg-rose-500/10' : result.security_verdict === 'Suspect' ? 'text-amber-400 bg-amber-500/10' : result.security_verdict ? 'text-emerald-400 bg-emerald-500/10' : ''
  return (
    <div className="glass-card rounded-xl p-3 sm:p-4 group">
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
  const { data: d } = useQuery({ queryKey: ['digest-home'], queryFn: () => fetch('/api/digest').then(r => r.json()), staleTime: 600_000 })
  if (!d || d.error) return null
  return (
    <div className="glass-card rounded-2xl p-4 sm:p-6">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-6 h-6 rounded-lg bg-rose-500/10 flex items-center justify-center"><AlertTriangle size={13} className="text-rose-400" /></div>
        <h3 className="text-sm sm:text-base font-semibold text-white">{d.title || 'Analyse du jour'}</h3>
      </div>
      {d.summary && <p className="text-xs sm:text-sm text-slate-400 leading-relaxed mb-4">{d.summary}</p>}
      {d.top_threats?.slice(0,3).map((t: any, i: number) => (
        <div key={i} className="flex items-start gap-3 glass-card rounded-xl p-3 mb-2">
          <span className={`shrink-0 w-2 h-2 rounded-full mt-1.5 ${t.severity==='CRITIQUE'?'bg-rose-400':t.severity==='ELEVE'?'bg-amber-400':'bg-slate-500'}`} />
          <div className="min-w-0">
            <div className="text-xs sm:text-sm font-medium text-slate-200">{t.name}</div>
            <div className="text-[10px] sm:text-xs text-slate-500 mt-0.5">{t.description?.slice(0,120)}</div>
          </div>
        </div>
      ))}
      {d.key_insight && (
        <div className="bg-gradient-to-r from-indigo-500/5 to-violet-500/5 border border-indigo-500/10 rounded-xl p-3 mt-3">
          <p className="text-[9px] uppercase tracking-widest text-indigo-400 mb-1">Insight cle</p>
          <p className="text-xs text-slate-300">{d.key_insight}</p>
        </div>
      )}
    </div>
  )
}

function BlogSection() {
  const { data: posts } = useQuery({ queryKey: ['blog-posts'], queryFn: () => fetch('/api/blog/posts?limit=6').then(r => r.json()), staleTime: 300_000 })
  if (!posts || posts.length === 0) return null
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <Newspaper size={15} className="text-emerald-400" />
        <h3 className="text-sm sm:text-base font-semibold text-white">Veille Blogs</h3>
        <span className="text-[10px] text-slate-600">{posts.length}+ articles</span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {posts.slice(0, 6).map((p: any, i: number) => (
          <a key={i} href={p.link} target="_blank" rel="noopener" className="glass-card rounded-xl p-3 group block">
            <div className="text-[10px] text-slate-500 mb-0.5">{p.source_name}</div>
            <div className="text-xs font-medium text-slate-200 group-hover:text-indigo-400 transition line-clamp-1">{p.title}</div>
            {p.summary && <div className="text-[10px] text-slate-500 mt-1 line-clamp-2">{p.summary}</div>}
          </a>
        ))}
      </div>
    </div>
  )
}

function TrendingSection() {
  const { data: d } = useQuery({ queryKey: ['trending-home'], queryFn: () => fetch('/api/trending?days=7&limit=8').then(r => r.json()), staleTime: 300_000 })
  if (!d || d.tools?.length === 0) return null
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <TrendingUp size={15} className="text-amber-400" />
        <h3 className="text-sm sm:text-base font-semibold text-white">Tendances de la semaine</h3>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {d.tools.slice(0, 8).map((t: any, i: number) => (
          <Link key={i} to="/tool/$name" params={{ name: t.name }} className="glass-card rounded-xl p-3 group text-center">
            <div className="text-xs font-medium text-slate-200 group-hover:text-indigo-400 truncate">{t.name.split('/').pop()}</div>
            <div className="flex items-center justify-center gap-1.5 mt-1 text-[10px] text-slate-500">
              <Star size={9} className="text-amber-500" />{t.stars?.toLocaleString()}
              {t.verdict && <span className={t.verdict==='Critique'?'text-rose-400':t.verdict==='Suspect'?'text-amber-400':'text-emerald-400'}>{t.verdict}</span>}
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
function ThreatSection() {
  const { data: d } = useQuery({ queryKey: ['threats-home'], queryFn: () => fetch('/api/threats/top?limit=5').then(r => r.json()), staleTime: 300_000 })
  if (!d || d.threats?.length === 0) return null
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <Shield size={15} className="text-rose-400" />
        <h3 className="text-sm sm:text-base font-semibold text-white">Menaces Prioritaires</h3>
      </div>
      <div className="space-y-2">
        {d.threats.slice(0, 5).map((t: any, i: number) => (
          <Link key={i} to="/cve/$id" params={{ id: t.cve_id }} className="flex items-center gap-3 glass-card rounded-xl p-3 group">
            <span className={`shrink-0 w-2 h-2 rounded-full ${t.priority?.label==='CRITIQUE'?'bg-rose-400':t.priority?.label==='ELEVE'?'bg-amber-400':'bg-slate-500'}`} />
            <div className="flex-1 min-w-0">
              <div className="text-xs font-mono text-indigo-400">{t.cve_id}</div>
              <div className="text-[10px] text-slate-400 line-clamp-1">{t.description?.slice(0, 120)}</div>
            </div>
            <div className="text-right shrink-0">
              <div className="text-xs font-bold text-white">{t.priority?.score || '?'}</div>
              <div className="text-[9px] text-slate-600">{t.priority?.label || '?'}</div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

function AiLabSection() {
  const [q, setQ] = useState('')
  const [result, setResult] = useState<any>(null)
  const testClassify = async () => {
    const r = await fetch(`/api/hf/classify?text=${encodeURIComponent(q)}`).then(r => r.json())
    setResult(r)
  }
  return (
    <div className="glass-card rounded-2xl p-4 sm:p-6">
      <div className="flex items-center gap-2 mb-3">
        <span className="w-6 h-6 rounded-lg bg-violet-500/10 flex items-center justify-center text-violet-400 text-xs">AI</span>
        <h3 className="text-sm sm:text-base font-semibold text-white">Lab IA — Testez nos modeles</h3>
        <span className="text-[10px] text-slate-600 ml-auto">22 modeles</span>
      </div>
      <div className="flex gap-2 mb-3">
        <input value={q} onChange={e => setQ(e.target.value)}
          placeholder="Ex: outil de scan reseau pour pentest..."
          className="flex-1 px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500" />
        <button onClick={testClassify} className="px-4 py-2 bg-violet-500/10 border border-violet-500/20 text-violet-400 rounded-lg text-xs font-medium hover:bg-violet-500/20">Classifier</button>
      </div>
      {result && result.all && (
        <div className="text-xs space-y-1">
          <p className="text-slate-400">Classification IA (zero-shot multilingue):</p>
          {Object.entries(result.all as Record<string,number>).slice(0,4).map(([k,v]) => (
            <div key={k} className="flex items-center gap-2">
              <span className="text-slate-300 w-24">{k}</span>
              <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                <div className="h-full bg-violet-500/50 rounded-full" style={{width: `${(v as number)*100}%`}} />
              </div>
              <span className="text-slate-500 w-10 text-right">{(v as number*100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function StatsBar() {
  const { data: s } = useQuery({ queryKey: ['stats-bar'], queryFn: () => Promise.all([
    fetch('/api/stats').then(r=>r.json()),
    fetch('/api/blog/sources').then(r=>r.json()),
  ]).then(([stats, sources]) => ({...stats, blogSources: sources?.length || 0})), staleTime: 120_000 })
  if (!s) return null
  return (
    <div className="glass-card rounded-2xl p-3 sm:p-4">
      <div className="grid grid-cols-4 gap-2 text-center">
        {[
          { label: 'Outils', value: s.total_repos?.toLocaleString() || '0' },
          { label: 'CVE', value: (s.total_cves || 0).toLocaleString() },
          { label: 'Blogs', value: `${s.blogSources || 0} sources` },
          { label: 'IA', value: '22 modeles' },
        ].map((x, i) => (
          <div key={i}>
            <div className="text-sm sm:text-base font-bold text-white">{x.value}</div>
            <div className="text-[9px] sm:text-[10px] text-slate-500">{x.label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Replace the empty-state return in ExplorePage to include new sections
// Actually, just add the sections to the home layout

function OsintSection() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const search = async () => {
    if (!text.trim()) return
    setLoading(true)
    try {
      const r = await fetch(`/api/osint/investigate?free_text=${encodeURIComponent(text)}`, { method: 'POST' }).then(r => r.json())
      setResult(r)
    } catch {}
    setLoading(false)
  }
  return (
    <div className="glass-card rounded-2xl p-4 sm:p-6">
      <div className="flex items-center gap-2 mb-3">
        <span className="w-6 h-6 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-400 text-xs">OS</span>
        <h3 className="text-sm sm:text-base font-semibold text-white">OSINT Lab — Recherche IA</h3>
        <span className="text-[10px] text-slate-600">Decrivez, l'IA trouve</span>
      </div>
      <div className="flex flex-col sm:flex-row gap-2 mb-3">
        <textarea value={text} onChange={e => setText(e.target.value)}
          placeholder="Ex: un chercheur en securite francais qui travaille sur les malwares Android..."
          className="flex-1 px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500 min-h-[60px]" />
        <button onClick={search} disabled={loading || !text.trim()}
          className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded-lg text-xs font-medium hover:bg-cyan-500/20 disabled:opacity-30 self-end">
          {loading ? 'Recherche...' : 'Enqueter'}
        </button>
      </div>
      {result && (
        <div className="text-xs space-y-2">
          <p className="text-slate-400 font-medium">{result.summary}</p>
          {result.ai_extracted?.name && (
            <div className="flex flex-wrap gap-1">
              {result.ai_extracted.name && <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 text-[10px]">Nom: {result.ai_extracted.name}</span>}
              {result.ai_extracted.location && <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px]">Ville: {result.ai_extracted.location}</span>}
              {result.ai_extracted.keywords?.map((k: string, i: number) => (
                <span key={i} className="px-2 py-0.5 rounded bg-slate-500/10 text-slate-400 text-[10px]">{k}</span>
              ))}
            </div>
          )}
          {result.ai_extracted?.strategy && (
            <p className="text-[10px] text-slate-500 italic">{result.ai_extracted.strategy}</p>
          )}
          {result.findings?.github_profiles && (
            <div>
              <p className="text-slate-500 text-[10px] mb-1">Profils GitHub:</p>
              {result.findings.github_profiles.slice(0,3).map((p: any, i: number) => (
                <a key={i} href={p.url} target="_blank" rel="noopener" className="block text-indigo-400 hover:underline text-[11px]">
                  {p.username} {p.name ? `(${p.name})` : ''} {p.location ? `- ${p.location}` : ''}
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
