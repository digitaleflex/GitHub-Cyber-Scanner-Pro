import { useState, useEffect, useRef } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useSearch, type SearchResult, type SearchResultType, type SearchParams } from '../lib/api'
import { useQuery } from '@tanstack/react-query'
import { Search, Star, Shield, BookOpen, Hash, ExternalLink, AlertTriangle, TrendingUp, Newspaper, Brain, ChevronDown, Loader2, MapPin, User, Target, MessageSquare, Bug, Activity } from 'lucide-react'
import { useStats } from '../lib/api'

function useCountUp(target: number, duration = 1500) {
  const [count, setCount] = useState(0)
  useEffect(() => {
    if (!target) return
    let start = 0; const step = Math.ceil(target / (duration / 16))
    const timer = setInterval(() => { start += step; if (start >= target) { setCount(target); clearInterval(timer) } else setCount(start) }, 16)
    return () => clearInterval(timer)
  }, [target, duration])
  return count
}

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
  const [showSections, setShowSections] = useState(true)
  const inputRef = useRef<HTMLInputElement>(null)
  useEffect(() => { const t = setTimeout(() => setDebounced(query), 300); return () => clearTimeout(t) }, [query])
  const sp: SearchParams = { q: debounced, page, per_page: 12, types, sort: 'stars' }
  const { data: results, isLoading } = useSearch(debounced.length >= 2 ? sp : { ...sp, q: '' })
  const hasResults = debounced.length >= 2 && results && results.results.length > 0

  const { data: stats } = useStats()
  const { data: digest } = useQuery({ queryKey: ['digest-hero'], queryFn: () => fetch('/api/digest').then(r => r.json()), staleTime: 300_000 })
  const repos = useCountUp(stats?.total_repos || 0, 2000)
  const stars_c = useCountUp(stats?.total_stars || 0, 2500)
  const cves = stats?.total_cves ? (stats.total_cves >= 1000 ? `${(stats.total_cves / 1000).toFixed(0)}K` : stats.total_cves.toLocaleString()) : '0'
  const criticalThreats = digest?.top_threats?.filter((t: any) => t.severity === 'CRITIQUE').length || 0

  return (
    <div className="max-w-5xl mx-auto w-full">
      {/* Hero section */}
      <section className="py-6 sm:py-12 text-center animate-fade">
        <div className="flex items-center justify-center gap-2 mb-4 flex-wrap">
          <span className="glass px-2.5 py-1 rounded-full text-[10px] sm:text-xs text-slate-400 flex items-center gap-1.5">
            <Shield size={10} className="text-indigo-400" /> Groq AI
          </span>
          <span className="glass px-2.5 py-1 rounded-full text-[10px] sm:text-xs text-slate-400 flex items-center gap-1.5">
            <Star size={10} className="text-amber-400" /> GitHub API
          </span>
          <span className="glass px-2.5 py-1 rounded-full text-[10px] sm:text-xs text-slate-400 flex items-center gap-1.5">
            <Shield size={10} className="text-rose-400" /> NVD CVE
          </span>
        </div>

        <h1 className="text-2xl sm:text-4xl lg:text-5xl font-bold tracking-tight mb-3 sm:mb-4">
          <span className="bg-gradient-to-r from-indigo-400 via-white to-violet-400 bg-clip-text text-transparent">
            Veille Cyber Intelligence
          </span>
        </h1>
        <p className="text-sm sm:text-base text-slate-400 max-w-xl mx-auto mb-6 sm:mb-8 leading-relaxed">
          {repos.toLocaleString()}+ outils de securite audites par IA. Decouvrez les menaces du jour, explorez la base de connaissances cyber.
        </p>

        {criticalThreats > 0 && (
          <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full mb-6 sm:mb-8 pulse-ring">
            <AlertTriangle size={14} className="text-rose-400" />
            <span className="text-xs sm:text-sm font-medium text-rose-300">
              {criticalThreats} menace{criticalThreats > 1 ? 's' : ''} critique{criticalThreats > 1 ? 's' : ''} aujourd'hui
            </span>
          </div>
        )}

        <div className="grid grid-cols-3 gap-3 sm:gap-6 max-w-lg mx-auto mb-6 sm:mb-8">
          {[
            { label: 'Outils', value: repos.toLocaleString(), icon: <Star size={14} className="text-amber-400" />, delay: '0s' },
            { label: 'Stars', value: stars_c.toLocaleString(), icon: <TrendingUp size={14} className="text-indigo-400" />, delay: '0.2s' },
            { label: 'CVE', value: cves.toLocaleString(), icon: <Shield size={14} className="text-rose-400" />, delay: '0.4s' },
          ].map((c, i) => (
            <div key={i} className="glass-card rounded-xl p-3 sm:p-4 text-center animate-slide" style={{ animationDelay: c.delay }}>
              <div className="flex justify-center mb-1">{c.icon}</div>
              <div className="text-lg sm:text-2xl font-bold text-white tabular-nums">{c.value}</div>
              <div className="text-[10px] sm:text-xs text-slate-500 mt-0.5">{c.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* KPI Dashboard */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3 mb-4 animate-fade">
        <div className="glass-card rounded-xl p-3 text-center">
          <AlertTriangle size={16} className="text-rose-400 mx-auto mb-1" />
          <div className="text-lg sm:text-xl font-bold text-white">{criticalThreats}</div>
          <div className="text-[9px] text-slate-500">Menaces critiques</div>
        </div>
        <div className="glass-card rounded-xl p-3 text-center">
          <TrendingUp size={16} className="text-amber-400 mx-auto mb-1" />
          <div className="text-lg sm:text-xl font-bold text-white">{stats?.new_repos_24h || 0}</div>
          <div className="text-[9px] text-slate-500">Nouveaux 24h</div>
        </div>
        <div className="glass-card rounded-xl p-3 text-center">
          <Shield size={16} className="text-indigo-400 mx-auto mb-1" />
          <div className="text-lg sm:text-xl font-bold text-white">{stats?.security_critique || 0}</div>
          <div className="text-[9px] text-slate-500">Repos critiques</div>
        </div>
        <div className="glass-card rounded-xl p-3 text-center">
          <Activity size={16} className="text-emerald-400 mx-auto mb-1" />
          <div className="text-lg sm:text-xl font-bold text-white">{stats?.pending_keywords || 0}</div>
          <div className="text-[9px] text-slate-500">Mots-cles a valider</div>
        </div>
      </div>

      {/* Search bar */}
      <div className="relative mb-3">
        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
        <input ref={inputRef} type="text" value={query} onChange={e => { setQuery(e.target.value); setPage(1) }}
          placeholder="Rechercher un outil, une CVE, une technique, une personne..."
          className="w-full pl-11 pr-4 py-3.5 sm:py-4 glass rounded-2xl text-sm sm:text-base text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500/40" />
        {isLoading && <div className="absolute right-4 top-1/2 -translate-y-1/2"><div className="w-5 h-5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" /></div>}
      </div>
      <div className="flex items-center justify-between mb-4 sm:mb-6">
        <div className="flex items-center gap-1.5 flex-wrap">
          {(['repo','cve','book','keyword'] as const).map(t => (
            <button key={t} onClick={() => setTypes(p => p.includes(t) ? p.filter(x => x!==t) : [...p,t])}
              className={`px-2.5 sm:px-3 py-1 rounded-full text-[10px] sm:text-xs font-medium transition border ${types.includes(t) ? TYPE_META[t].color : 'glass text-slate-500 hover:text-slate-300'}`}>
              {TYPE_META[t].label}
            </button>
          ))}
        </div>
        {!hasResults && (
          <button onClick={() => setShowSections(!showSections)} className="text-[10px] text-slate-600 hover:text-slate-400 flex items-center gap-1">
            <ChevronDown size={12} className={`transition ${showSections ? '' : 'rotate-180'}`} />
            {showSections ? 'Masquer' : 'Afficher'} les sections
          </button>
        )}
      </div>

      {hasResults ? (
        <div className="animate-fade">
          <p className="text-[10px] sm:text-xs text-slate-500 mb-3">{results!.total.toLocaleString()} resultats</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3">
            {results!.results.map((r,i) => <ResultCard key={i} result={r} />)}
          </div>
          {results!.pages > 1 && (
            <div className="flex items-center justify-center gap-3 mt-6">
              <button onClick={() => setPage(p => Math.max(1,p-1))} disabled={page===1} className="glass px-4 py-2 rounded-full text-xs text-slate-300 disabled:opacity-30">Prec</button>
              <span className="text-xs text-slate-500">{page}/{results!.pages}</span>
              <button onClick={() => setPage(p => Math.min(results!.pages,p+1))} disabled={page>=results!.pages} className="glass px-4 py-2 rounded-full text-xs text-slate-300 disabled:opacity-30">Suiv</button>
            </div>
          )}
        </div>
      ) : showSections && (
        <div className="space-y-4 animate-fade">
          <StatsRow />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="space-y-4">
              <DigestSection />
              <ThreatSection />
            </div>
            <div className="space-y-4">
              <TrendingSection />
              <BlogSection />
              <OsintSection />
            </div>
          </div>
          <AiLabSection />
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
        <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] border ${meta.color}`}>{meta.icon}</span>
        {result.stars != null && <span className="flex items-center gap-1 text-[10px] text-slate-500 shrink-0"><Star size={10} className="text-amber-500" />{result.stars.toLocaleString()}</span>}
      </div>
      <Link to="/tool/$name" params={{ name: result.name }} className="text-xs sm:text-sm font-medium text-slate-200 hover:text-indigo-400 transition line-clamp-1 block mb-1">{result.name}</Link>
      {desc && <p className="text-[10px] text-slate-500 line-clamp-2">{desc}</p>}
      <div className="flex items-center gap-2 mt-2 text-[9px] text-slate-600">
        {result.security_verdict && <span className={`px-1.5 py-0.5 rounded ${vc}`}>{result.security_verdict}</span>}
        {result.lang && <span>{result.lang}</span>}
        <a href={result.url||'#'} target="_blank" rel="noopener" className="flex items-center gap-0.5 hover:text-indigo-400 ml-auto"><ExternalLink size={9} /></a>
      </div>
    </div>
  )
}

// ── SECTIONS ─────────────────────────────────────────────────────────────

function StatsRow() {
  const { data: s } = useQuery({ queryKey: ['stats-bar'], queryFn: () => fetch('/api/stats').then(r=>r.json()), staleTime: 120_000 })
  if (!s) return null
  return (
    <div className="glass-card rounded-2xl p-3 sm:p-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4 text-center">
        {[
          { label: 'Outils indexés', value: (s.total_repos||0).toLocaleString(), icon: <Star size={13} className="text-amber-400" /> },
          { label: 'CVE', value: '356K+', icon: <Shield size={13} className="text-rose-400" /> },
          { label: 'Modèles IA', value: '22', icon: <Brain size={13} className="text-violet-400" /> },
          { label: 'Blogs', value: '30+', icon: <Newspaper size={13} className="text-emerald-400" /> },
        ].map((x, i) => (
          <div key={i} className="flex flex-col items-center gap-1">
            {x.icon}
            <div className="text-sm sm:text-lg font-bold text-white">{x.value}</div>
            <div className="text-[9px] sm:text-[10px] text-slate-500">{x.label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function DigestSection() {
  const { data: d } = useQuery({ queryKey: ['digest-home'], queryFn: () => fetch('/api/digest').then(r => r.json()), staleTime: 600_000 })
  if (!d || d.error) return null
  return (
    <div className="glass-card rounded-2xl p-4 sm:p-6">
      <div className="flex items-center gap-2 mb-3"><AlertTriangle size={15} className="text-rose-400" /><h3 className="text-sm sm:text-base font-semibold text-white">{d.title || 'Analyse du jour'}</h3></div>
      {d.summary && <p className="text-xs sm:text-sm text-slate-400 mb-3">{d.summary}</p>}
      {d.top_threats?.slice(0,3).map((t: any, i: number) => (
        <div key={i} className="flex items-start gap-3 glass-card rounded-xl p-3 mb-2">
          <span className={`shrink-0 w-2 h-2 rounded-full mt-1.5 ${t.severity==='CRITIQUE'?'bg-rose-400':t.severity==='ELEVE'?'bg-amber-400':'bg-slate-500'}`} />
          <div className="min-w-0"><div className="text-xs sm:text-sm font-medium text-slate-200">{t.name}</div><div className="text-[10px] text-slate-500 mt-0.5">{t.description?.slice(0,120)}</div></div>
        </div>
      ))}
      {d.key_insight && <div className="bg-gradient-to-r from-indigo-500/5 to-violet-500/5 border border-indigo-500/10 rounded-xl p-3 mt-3"><p className="text-[9px] uppercase tracking-widest text-indigo-400 mb-1">Insight</p><p className="text-xs text-slate-300">{d.key_insight}</p></div>}
    </div>
  )
}

function ThreatSection() {
  const { data: d } = useQuery({ queryKey: ['threats-home'], queryFn: () => fetch('/api/threats/top?limit=5').then(r => r.json()), staleTime: 300_000 })
  if (!d || d.threats?.length === 0) return null
  return (
    <div>
      <div className="flex items-center gap-2 mb-3"><Shield size={14} className="text-rose-400" /><h3 className="text-sm font-semibold text-white">Menaces Prioritaires</h3></div>
      <div className="space-y-2">
        {d.threats.slice(0,5).map((t: any, i: number) => (
          <Link key={i} to="/cve/$id" params={{ id: t.cve_id }} className="flex items-center gap-3 glass-card rounded-xl p-3 group">
            <span className={`shrink-0 w-2 h-2 rounded-full ${t.priority?.label==='CRITIQUE'?'bg-rose-400':t.priority?.label==='ELEVE'?'bg-amber-400':'bg-slate-500'}`} />
            <div className="flex-1 min-w-0"><div className="text-xs font-mono text-indigo-400">{t.cve_id}</div><div className="text-[10px] text-slate-400 line-clamp-1">{t.description?.slice(0,120)}</div></div>
            <div className="text-right shrink-0"><div className="text-xs font-bold text-white">{t.priority?.score||'?'}</div><div className="text-[9px] text-slate-600">{t.priority?.label||'?'}</div></div>
          </Link>
        ))}
      </div>
    </div>
  )
}

function OsintSection() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const search = async () => {
    if (!text.trim()) return
    setLoading(true); setResult(null)
    try { const r = await fetch(`/api/osint/investigate?free_text=${encodeURIComponent(text)}`, { method: 'POST' }).then(r => r.json()); setResult(r) } catch {}
    setLoading(false)
  }
  return (
    <div className="glass-card rounded-2xl p-4 sm:p-6">
      <div className="flex items-center gap-2 mb-3"><Target size={15} className="text-cyan-400" /><h3 className="text-sm sm:text-base font-semibold text-white">OSINT Lab</h3><span className="text-[10px] text-cyan-400/70 ml-auto">7 outils</span></div>
      <div className="flex flex-col sm:flex-row gap-2 mb-3">
        <textarea value={text} onChange={e => setText(e.target.value)} placeholder="Ex: un chercheur en securite allemand qui a cree des regles YARA..."
          className="flex-1 px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500 min-h-[60px]" />
        <button onClick={search} disabled={loading || !text.trim()}
          className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded-lg text-xs font-medium hover:bg-cyan-500/20 disabled:opacity-30 self-end">{loading ? <Loader2 size={12} className="animate-spin" /> : 'Enqueter'}</button>
      </div>
      {result && (
        <div className="text-xs space-y-2">
          <p className="text-slate-400">{result.summary}</p>
          {result.ai_extracted?.name && (
            <div className="flex flex-wrap gap-1">
              {result.ai_extracted.name && <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 text-[10px]"><User size={10} className="inline mr-1"/>{result.ai_extracted.name}</span>}
              {result.ai_extracted.location && <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px]"><MapPin size={10} className="inline mr-1"/>{result.ai_extracted.location}</span>}
              {result.ai_extracted.keywords?.slice(0,3).map((k: string, i: number) => <span key={i} className="px-2 py-0.5 rounded bg-slate-500/10 text-slate-400 text-[10px]">{k}</span>)}
            </div>
          )}
          {result.findings?.github_profiles?.slice(0,3).map((p: any, i: number) => (
            <a key={i} href={p.url} target="_blank" rel="noopener" className="block glass-card rounded-lg p-2 text-[11px]">
              <span className="text-indigo-400">{p.username}</span> {p.name && <span className="text-slate-400">({p.name})</span>} {p.location && <span className="text-slate-600">- {p.location}</span>}
            </a>
          ))}
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
      <div className="flex items-center gap-2 mb-3"><Newspaper size={14} className="text-emerald-400" /><h3 className="text-sm font-semibold text-white">Veille Blogs</h3></div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {posts.slice(0,6).map((p: any, i: number) => (
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
      <div className="flex items-center gap-2 mb-3"><TrendingUp size={14} className="text-amber-400" /><h3 className="text-sm font-semibold text-white">Tendances de la semaine</h3></div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {d.tools.slice(0,8).map((t: any, i: number) => (
          <Link key={i} to="/tool/$name" params={{ name: t.name }} className="glass-card rounded-xl p-3 group text-center">
            <div className="text-xs font-medium text-slate-200 group-hover:text-indigo-400 truncate">{t.name.split('/').pop()}</div>
            <div className="flex items-center justify-center gap-1.5 mt-1 text-[10px] text-slate-500"><Star size={9} className="text-amber-500" />{t.stars?.toLocaleString()}</div>
          </Link>
        ))}
      </div>
    </div>
  )
}

function AiLabSection() {
  const [tab, setTab] = useState<'classify' | 'qa' | 'vuln'>('classify')

  return (
    <div className="glass-card rounded-2xl p-4 sm:p-6">
      <div className="flex items-center gap-2 mb-3"><Brain size={15} className="text-violet-400" /><h3 className="text-sm font-semibold text-white">AI Lab — Testez nos 22 modèles</h3></div>

      <div className="flex gap-1 mb-3 flex-wrap">
        <button onClick={() => setTab('classify')}
          className={`px-3 py-1 rounded-full text-[10px] font-medium transition border ${tab === 'classify' ? 'bg-violet-500/10 text-violet-400 border-violet-500/20' : 'glass text-slate-500'}`}>
          Classification
        </button>
        <button onClick={() => setTab('qa')}
          className={`px-3 py-1 rounded-full text-[10px] font-medium transition border ${tab === 'qa' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' : 'glass text-slate-500'}`}>
          <MessageSquare size={10} className="inline mr-1" /> Q&A
        </button>
        <button onClick={() => setTab('vuln')}
          className={`px-3 py-1 rounded-full text-[10px] font-medium transition border ${tab === 'vuln' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' : 'glass text-slate-500'}`}>
          <Bug size={10} className="inline mr-1" /> Vulnérabilité
        </button>
      </div>

      {tab === 'classify' && <ClassifyTab />}
      {tab === 'qa' && <QATab />}
      {tab === 'vuln' && <VulnTab />}
    </div>
  )
}

function ClassifyTab() {
  const [q, setQ] = useState('')
  const [result, setResult] = useState<any>(null)
  const test = async () => {
    const r = await fetch(`/api/hf/classify?text=${encodeURIComponent(q)}`).then(r => r.json())
    setResult(r)
  }
  return (
    <div>
      <div className="flex gap-2">
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Ex: outil de scan réseau pour pentest..."
          className="flex-1 px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500" />
        <button onClick={test} className="px-4 py-2 bg-violet-500/10 border border-violet-500/20 text-violet-400 rounded-lg text-xs font-medium hover:bg-violet-500/20">Classifier</button>
      </div>
      {result?.all && (
        <div className="text-xs space-y-1 mt-3">
          {Object.entries(result.all as Record<string,number>).slice(0,4).map(([k,v]) => (
            <div key={k} className="flex items-center gap-2"><span className="text-slate-400 w-24">{k}</span><div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden"><div className="h-full bg-violet-500/50 rounded-full" style={{width:`${(v as number)*100}%`}} /></div><span className="text-slate-500 w-10 text-right">{((v as number)*100).toFixed(0)}%</span></div>
          ))}
        </div>
      )}
    </div>
  )
}

function QATab() {
  const [question, setQuestion] = useState('')
  const [context, setContext] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const ask = async () => {
    setLoading(true)
    try {
      const r = await fetch(`/api/hf/qa?question=${encodeURIComponent(question)}&context=${encodeURIComponent(context)}`).then(r => r.json())
      setAnswer(r.answer || r.error || JSON.stringify(r))
    } catch {}
    setLoading(false)
  }
  return (
    <div className="space-y-2">
      <input value={question} onChange={e => setQuestion(e.target.value)} placeholder="Question..."
        className="w-full px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500" />
      <textarea value={context} onChange={e => setContext(e.target.value)} placeholder="Contexte (description, rapport...)"
        className="w-full px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500 min-h-[50px]" />
      <div className="flex items-center gap-2">
        <button onClick={ask} disabled={loading || !question.trim() || !context.trim()}
          className="px-4 py-2 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-lg text-xs font-medium hover:bg-indigo-500/20 disabled:opacity-30">
          {loading ? <Loader2 size={12} className="animate-spin" /> : 'Demander'}
        </button>
        {answer && <span className="text-xs text-indigo-400 font-medium">{answer}</span>}
      </div>
    </div>
  )
}

function VulnTab() {
  const [text, setText] = useState('')
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)
  const detect = async () => {
    setLoading(true)
    try {
      const r = await fetch(`/api/hf/vuln-type?text=${encodeURIComponent(text)}`).then(r => r.json())
      setResult(r.type || r.error || JSON.stringify(r))
    } catch {}
    setLoading(false)
  }
  return (
    <div className="space-y-2">
      <textarea value={text} onChange={e => setText(e.target.value)} placeholder="Description d'une vulnérabilité à analyser..."
        className="w-full px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500 min-h-[50px]" />
      <div className="flex items-center gap-2">
        <button onClick={detect} disabled={loading || !text.trim()}
          className="px-4 py-2 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-lg text-xs font-medium hover:bg-rose-500/20 disabled:opacity-30">
          {loading ? <Loader2 size={12} className="animate-spin" /> : 'Détecter (SecBERT)'}
        </button>
        {result && <span className="text-xs text-rose-400 font-mono">{result}</span>}
      </div>
    </div>
  )
}
