import { useState, useEffect, useCallback, useRef } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useSearch, type SearchResult, type SearchResultType, type SearchParams } from '../lib/api'
import { Search, ExternalLink, Star, Shield, BookOpen, Hash, ChevronLeft, ChevronRight, SlidersHorizontal, X } from 'lucide-react'

const TYPE_ORDER: SearchResultType[] = ['repo', 'cve', 'book', 'keyword']

const TYPE_META: Record<SearchResultType, { label: string; icon: React.ReactNode; badge: string; color: string }> = {
  repo: { label: 'Dépôts', icon: <Star size={14} className="text-neon-cyan" />, badge: 'bg-neon-cyan/10 text-neon-cyan border-neon-cyan/20', color: 'text-neon-cyan' },
  cve: { label: 'CVEs', icon: <Shield size={14} className="text-neon-red" />, badge: 'bg-neon-red/10 text-neon-red border-neon-red/20', color: 'text-neon-red' },
  book: { label: 'Ressources', icon: <BookOpen size={14} className="text-amber-400" />, badge: 'bg-amber-500/10 text-amber-400 border-amber-500/20', color: 'text-amber-400' },
  keyword: { label: 'Mots-clés', icon: <Hash size={14} className="text-neon-magenta" />, badge: 'bg-neon-magenta/10 text-neon-magenta border-neon-magenta/20', color: 'text-neon-magenta' },
}

const SEVERITIES = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
const VERDICTS = ['Critique', 'Suspect', 'Sain']
const SORTS: { value: NonNullable<SearchParams['sort']>; label: string }[] = [
  { value: 'relevance', label: 'Pertinence' },
  { value: 'stars', label: 'Stars' },
  { value: 'cvss', label: 'CVSS' },
  { value: 'published', label: 'Publié' },
  { value: 'updated', label: 'Mis à jour' },
]

const PER_PAGE = 20

function SearchPage() {
  const [query, setQuery] = useState('')
  const [debounced, setDebounced] = useState('')
  const [page, setPage] = useState(1)
  const [types, setTypes] = useState<SearchResultType[]>([])
  const [language, setLanguage] = useState('')
  const [severity, setSeverity] = useState('')
  const [securityVerdict, setSecurityVerdict] = useState('')
  const [category, setCategory] = useState('')
  const [sort, setSort] = useState<NonNullable<SearchParams['sort']>>('relevance')
  const [showFilters, setShowFilters] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const { data, isLoading, isFetching } = useSearch({
    q: debounced,
    page,
    per_page: PER_PAGE,
    types: types.length ? types : undefined,
    language: language || undefined,
    severity: severity || undefined,
    security_verdict: securityVerdict || undefined,
    category: category || undefined,
    sort,
  })

  useEffect(() => {
    const t = setTimeout(() => { setDebounced(query); setPage(1) }, 300)
    return () => clearTimeout(t)
  }, [query])

  const toggleType = useCallback((t: SearchResultType) => {
    setTypes((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]))
    setPage(1)
  }, [])

  const resetFilters = useCallback(() => {
    setTypes([]); setLanguage(''); setSeverity(''); setSecurityVerdict(''); setCategory(''); setSort('relevance'); setPage(1)
  }, [])

  const hasFilters = types.length > 0 || language || severity || securityVerdict || category || sort !== 'relevance'
  const hasQuery = debounced.length >= 2
  const results = data?.results ?? []
  const facets = data?.facets
  const activeCount = types.length
  const allTypesActive = activeCount === 0 || activeCount === TYPE_ORDER.length

  return (
    <div>
      {/* Barre de recherche principale */}
      <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 mb-6 neon-border-cyan">
        <div className="flex items-center gap-3 mb-4">
          <Search size={18} className="text-neon-cyan" />
          <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider font-cyber">
            Recherche unifiée
          </h2>
          {data && hasQuery && (
            <span className="text-xs text-gray-500 font-mono ml-auto">
              {data.total.toLocaleString('fr-FR')} résultat{data.total > 1 ? 's' : ''}
            </span>
          )}
        </div>
        <div className="flex gap-3">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Rechercher dans repos, CVEs, ressources, mots-clés..."
            autoFocus
            className="flex-1 px-4 py-3 bg-white/[0.05] border border-white/[0.1] rounded-lg text-sm text-white placeholder-gray-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50 font-mono"
          />
          <button
            onClick={() => setShowFilters((s) => !s)}
            className={`flex items-center gap-2 px-4 py-2.5 border rounded-lg text-sm font-mono transition-colors ${showFilters || hasFilters ? 'bg-neon-cyan/10 border-neon-cyan/40 text-neon-cyan' : 'bg-white/[0.03] border-white/[0.1] text-gray-400 hover:text-white'}`}
          >
            <SlidersHorizontal size={14} />
            Filtres
            {hasFilters && <span className="w-1.5 h-1.5 rounded-full bg-neon-cyan animate-pulse" />}
          </button>
        </div>
        {hasFilters && (
          <div className="flex items-center gap-2 mt-3 flex-wrap">
            {types.map((t) => (
              <span key={t} className={`text-[10px] px-2 py-0.5 rounded border font-mono ${TYPE_META[t].badge}`}>
                {TYPE_META[t].label}
              </span>
            ))}
            {language && <span className="text-[10px] px-2 py-0.5 rounded border font-mono bg-indigo-500/10 text-indigo-300 border-indigo-500/20">lang:{language}</span>}
            {severity && <span className="text-[10px] px-2 py-0.5 rounded border font-mono bg-neon-red/10 text-neon-red border-neon-red/20">sev:{severity}</span>}
            {securityVerdict && <span className="text-[10px] px-2 py-0.5 rounded border font-mono bg-amber-500/10 text-amber-400 border-amber-500/20">verdict:{securityVerdict}</span>}
            {category && <span className="text-[10px] px-2 py-0.5 rounded border font-mono bg-neon-green/10 text-neon-green border-neon-green/20">cat:{category}</span>}
            <button onClick={resetFilters} className="flex items-center gap-1 text-[10px] text-gray-600 hover:text-neon-red transition-colors font-mono ml-1">
              <X size={11} /> Effacer
            </button>
          </div>
        )}
      </div>

      {!hasQuery ? (
        <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-10 text-center">
          <p className="text-gray-600 text-sm font-mono">Tapez au moins 2 caractères pour lancer la recherche</p>
          <p className="text-gray-800 text-xs font-mono mt-2">Indexation : dépôts GitHub, CVEs NVD, ressources, mots-clés</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-6 items-start">
          {/* Panneau de filtres */}
          <aside className={`bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan ${showFilters ? '' : 'hidden lg:block'}`}>
            <h3 className="text-xs font-mono uppercase tracking-wider text-gray-500 mb-3">Types de résultats</h3>
            <div className="space-y-1.5 mb-5">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-mono text-gray-300 hover:text-white transition-colors py-1">
                <input
                  type="checkbox"
                  checked={allTypesActive}
                  onChange={() => setTypes(allTypesActive ? TYPE_ORDER : [])}
                  className="accent-neon-cyan"
                />
                Tous
              </label>
              {TYPE_ORDER.map((t) => {
                const count = facets?.types[t] ?? 0
                const active = types.includes(t)
                return (
                  <label key={t} className="flex items-center gap-2 cursor-pointer text-xs font-mono text-gray-300 hover:text-white transition-colors py-1">
                    <input
                      type="checkbox"
                      checked={types.length === 0 || active}
                      onChange={() => toggleType(t)}
                      className="accent-neon-cyan"
                    />
                    {TYPE_META[t].icon}
                    <span className="flex-1">{TYPE_META[t].label}</span>
                    <span className="text-gray-600 tabular-nums">{count.toLocaleString('fr-FR')}</span>
                  </label>
                )
              })}
            </div>

            <div className="space-y-4">
              <div>
                <h4 className="text-[10px] font-mono uppercase tracking-wider text-gray-600 mb-1.5">Langage (dépôts)</h4>
                <input
                  list="lang-options"
                  value={language}
                  onChange={(e) => { setLanguage(e.target.value); setPage(1) }}
                  placeholder="ex: Python"
                  className="w-full px-3 py-2 bg-white/[0.05] border border-white/[0.1] rounded-md text-xs font-mono text-white placeholder-gray-700 focus:outline-none focus-visible:ring-1 focus-visible:ring-neon-cyan/50"
                />
                <datalist id="lang-options">
                  {facets?.languages.map((l) => <option key={l.lang ?? ''} value={l.lang ?? ''} />)}
                </datalist>
              </div>

              <div>
                <h4 className="text-[10px] font-mono uppercase tracking-wider text-gray-600 mb-1.5">Sévérité (CVEs)</h4>
                <select
                  value={severity}
                  onChange={(e) => { setSeverity(e.target.value); setPage(1) }}
                  className="w-full px-3 py-2 bg-white/[0.05] border border-white/[0.1] rounded-md text-xs font-mono text-white focus:outline-none focus-visible:ring-1 focus-visible:ring-neon-cyan/50 [&>option]:bg-gray-900"
                >
                  <option value="">Toutes</option>
                  {SEVERITIES.map((s) => (
                    <option key={s} value={s}>
                      {s} {facets?.severities[s] != null ? `(${facets.severities[s]})` : ''}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <h4 className="text-[10px] font-mono uppercase tracking-wider text-gray-600 mb-1.5">Verdict sécurité</h4>
                <select
                  value={securityVerdict}
                  onChange={(e) => { setSecurityVerdict(e.target.value); setPage(1) }}
                  className="w-full px-3 py-2 bg-white/[0.05] border border-white/[0.1] rounded-md text-xs font-mono text-white focus:outline-none focus-visible:ring-1 focus-visible:ring-neon-cyan/50 [&>option]:bg-gray-900"
                >
                  <option value="">Tous</option>
                  {VERDICTS.map((v) => <option key={v} value={v}>{v}</option>)}
                </select>
              </div>

              <div className="mt-2">
                <h4 className="text-[10px] font-mono uppercase tracking-wider text-gray-600 mb-1.5">Catégorie</h4>
                <input
                  list="cat-options"
                  value={category}
                  onChange={(e) => { setCategory(e.target.value); setPage(1) }}
                  placeholder="ex: threat-intel"
                  className="w-full px-3 py-2 bg-white/[0.05] border border-white/[0.1] rounded-md text-xs font-mono text-white placeholder-gray-700 focus:outline-none focus-visible:ring-1 focus-visible:ring-neon-cyan/50"
                />
                <datalist id="cat-options">
                  {facets?.categories.map((c) => <option key={c.category ?? ''} value={c.category ?? ''} />)}
                </datalist>
              </div>

              <div>
                <h4 className="text-[10px] font-mono uppercase tracking-wider text-gray-600 mb-1.5">Tri</h4>
                <select
                  value={sort}
                  onChange={(e) => { setSort(e.target.value as NonNullable<SearchParams['sort']>); setPage(1) }}
                  className="w-full px-3 py-2 bg-white/[0.05] border border-white/[0.1] rounded-md text-xs font-mono text-white focus:outline-none focus-visible:ring-1 focus-visible:ring-neon-cyan/50 [&>option]:bg-gray-900"
                >
                  {SORTS.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}
                </select>
              </div>
            </div>
          </aside>

          {/* Résultats */}
          <section>
            <div className="flex items-center gap-3 mb-3">
              <h3 className="text-sm font-mono text-gray-400">
                {isLoading ? 'Recherche en cours...' : `${data?.total.toLocaleString('fr-FR') ?? 0} résultat(s) pour "${debounced}"`}
              </h3>
              {isFetching && !isLoading && <span className="text-xs text-gray-600 font-mono animate-pulse">mise à jour...</span>}
            </div>

            {isLoading ? (
              <div className="space-y-3">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="h-16 bg-white/5 rounded animate-pulse" />
                ))}
              </div>
            ) : results.length === 0 ? (
              <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-10 text-center">
                <p className="text-gray-600 text-sm font-mono">Aucun résultat</p>
                {hasFilters && (
                  <button onClick={resetFilters} className="mt-3 text-xs text-neon-cyan hover:underline font-mono">Effacer les filtres</button>
                )}
              </div>
            ) : (
              <>
                <div className="space-y-2">
                  {results.map((r, i) => (
                    <SearchResultRow key={`${r.result_type}-${r.name}-${i}`} result={r} />
                  ))}
                </div>

                {(data?.pages ?? 1) > 1 && (
                  <div className="flex items-center justify-center gap-4 mt-6">
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page <= 1}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-md border border-white/[0.1] text-xs font-mono text-gray-400 hover:text-white hover:border-white/30 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      <ChevronLeft size={14} /> Précédent
                    </button>
                    <span className="text-xs font-mono text-gray-500">
                      {page} / {data?.pages}
                    </span>
                    <button
                      onClick={() => setPage((p) => Math.min(data?.pages ?? 1, p + 1))}
                      disabled={page >= (data?.pages ?? 1)}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-md border border-white/[0.1] text-xs font-mono text-gray-400 hover:text-white hover:border-white/30 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      Suivant <ChevronRight size={14} />
                    </button>
                  </div>
                )}
              </>
            )}
          </section>
        </div>
      )}
    </div>
  )
}

function SearchResultRow({ result }: { result: SearchResult }) {
  const meta = TYPE_META[result.result_type]
  const desc = result.desc
    ? (result.desc.length > 160 ? result.desc.slice(0, 160) + '...' : result.desc)
    : null

  const href = result.result_type === 'cve' ? '/cves'
    : result.result_type === 'repo' ? '/'
    : result.result_type === 'book' ? '/'
    : '/keywords'

  return (
    <div className="flex items-start gap-3 p-3 rounded-lg border border-white/[0.04] hover:bg-white/[0.03] hover:border-neon-cyan/20 transition-colors">
      <div className="mt-0.5 shrink-0">{meta.icon}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-xs px-1.5 py-0.5 rounded border font-mono ${meta.badge}`}>
            {meta.label}
          </span>
          <Link to={href} className="text-sm font-medium text-white/80 hover:text-neon-cyan transition-colors font-mono truncate">
            {result.name}
          </Link>
          {result.stars != null && (
            <span className="text-xs text-gray-600 font-mono">★ {result.stars.toLocaleString('fr-FR')}</span>
          )}
          {result.lang && <span className="text-[10px] text-indigo-300/70 font-mono">{result.lang}</span>}
          {result.cvss_score != null && (
            <span className={`text-xs font-mono ${(result.cvss_score ?? 0) >= 9 ? 'text-neon-red' : (result.cvss_score ?? 0) >= 7 ? 'text-amber-400' : 'text-gray-500'}`}>
              CVSS {result.cvss_score?.toFixed(1)}
            </span>
          )}
          {result.severity && (
            <span className={`text-xs font-mono ${
              result.severity === 'CRITICAL' ? 'text-neon-red' : result.severity === 'HIGH' ? 'text-amber-400' : 'text-gray-500'
            }`}>
              {result.severity}
            </span>
          )}
          {result.security_verdict && (
            <span className={`text-xs font-mono ${result.security_verdict === 'Critique' ? 'text-neon-red' : result.security_verdict === 'Suspect' ? 'text-amber-400' : 'text-green-500'}`}>
              {result.security_verdict}
            </span>
          )}
          {result.status && (
            <span className="text-xs text-gray-500 font-mono">{result.status}</span>
          )}
          {result.published && (
            <span className="text-[10px] text-gray-700 font-mono">{result.published.slice(0, 10)}</span>
          )}
        </div>
        {desc && (
          <p className="text-xs text-gray-600 mt-1 font-mono leading-relaxed line-clamp-2">{desc}</p>
        )}
        {(result.category || result.repo_name) && (
          <p className="text-[10px] text-gray-700 mt-0.5 font-mono">
            {[result.category, result.repo_name].filter(Boolean).join(' · ')}
          </p>
        )}
      </div>
      {result.url && (
        <a href={result.url} target="_blank" rel="noopener noreferrer" className="shrink-0 text-gray-600 hover:text-neon-cyan transition-colors mt-1">
          <ExternalLink size={14} />
        </a>
      )}
    </div>
  )
}

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/search',
  component: SearchPage,
})
