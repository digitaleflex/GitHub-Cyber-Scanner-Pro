import { useState, useEffect } from 'react'
import { useRepos, useStats, type Repo } from '../lib/api'
import FicheFlashModal from './FicheFlashModal'

const SECURITY_COLORS: Record<string, string> = {
  Critique: 'bg-neon-red/15 text-neon-red border-neon-red/30 shadow-[0_0_6px_rgba(255,0,68,0.15)]',
  Suspect: 'bg-neon-amber/15 text-neon-amber border-neon-amber/30 shadow-[0_0_6px_rgba(255,187,0,0.15)]',
  Sain: 'bg-neon-green/15 text-neon-green border-neon-green/30 shadow-[0_0_6px_rgba(0,255,102,0.15)]',
}

function SecurityBadge({ verdict }: { verdict: string | null }) {
  if (!verdict) return <span className="text-gray-700 text-xs font-mono">—</span>
  const cls = SECURITY_COLORS[verdict] ?? 'bg-gray-500/20 text-gray-400 border-gray-500/30'
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium border font-mono ${cls}`}>
      {verdict}
    </span>
  )
}

function VitalityBadge({ score }: { score: number | null }) {
  if (score == null || score === 0) return <span className="text-gray-700 text-xs font-mono">—</span>
  const color = score >= 70
    ? 'bg-neon-green/15 text-neon-green border-neon-green/30'
    : score >= 40
      ? 'bg-neon-amber/15 text-neon-amber border-neon-amber/30'
      : 'bg-neon-red/15 text-neon-red border-neon-red/30'
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium border font-mono ${color}`}>
      {score}
    </span>
  )
}

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

function exportCSV(repos: Repo[]) {
  const headers = ['Nom', 'Stars', 'Langage', 'Description', 'Mis à jour', 'Vitalité', 'Sécurité']
  const rows = repos.map((r) => [
    r.name,
    r.stars,
    r.lang ?? '',
    `"${(r.desc ?? '').replace(/"/g, '""')}"`,
    r.updated?.slice(0, 10) ?? '',
    r.vitality_score ?? 0,
    r.security_verdict ?? '',
  ])
  const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `cyberscan_repos_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

const SORT_OPTIONS = [
  { key: 'stars', label: 'Stars ↓' },
  { key: 'vitality', label: 'Vitalité ↓' },
  { key: 'updated', label: 'Récents ↑' },
  { key: 'name', label: 'Nom A-Z' },
]

export default function ReposTable() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState('stars')
  const [vitalityMin, setVitalityMin] = useState(0)
  const [verdictFilter, setVerdictFilter] = useState<string | null>(null)
  const [selectedRepo, setSelectedRepo] = useState<Repo | null>(null)
  const debouncedSearch = useDebounce(search, 300)

  const { data, isLoading, error } = useRepos(debouncedSearch || undefined, page, sortBy, vitalityMin, verdictFilter)
  const { data: stats } = useStats()

  useEffect(() => setPage(1), [debouncedSearch, sortBy, vitalityMin, verdictFilter])

  const repos = data?.repos ?? []
  const pages = data?.pages ?? 1

  return (
    <div
      className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan hover:neon-glow-cyan transition-all duration-300"
      role="region"
      aria-label="Liste des outils"
    >
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider font-cyber">
          Tous les outils
        </h2>
        <div className="flex items-center gap-2 ml-auto">
          {stats && (stats.security_critique > 0 || stats.security_suspect > 0) && (
            <div className="flex items-center gap-1 mr-2">
              {[
                { key: null, label: 'Tous' },
                { key: 'Critique', label: `Critique ${stats.security_critique}`, cls: 'text-neon-red border-neon-red/30' },
                { key: 'Suspect', label: `Suspect ${stats.security_suspect}`, cls: 'text-neon-amber border-neon-amber/30' },
                { key: 'Sain', label: 'Sain', cls: 'text-neon-green border-neon-green/30' },
              ].map((opt) => (
                <button
                  key={opt.key ?? 'all'}
                  onClick={() => setVerdictFilter(opt.key)}
                  className={`text-xs px-2.5 py-1 rounded-lg border transition-colors font-mono ${
                    verdictFilter === opt.key
                      ? `${opt.cls} bg-white/[0.06]`
                      : 'text-gray-600 border-white/[0.06] hover:text-gray-400'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <input
          type="text"
          placeholder="Rechercher par nom, description, langage..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1 min-w-[200px] px-4 py-2.5 bg-white/[0.05] border border-white/[0.1] rounded-lg text-white text-sm placeholder-gray-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50 transition-colors font-mono"
          aria-label="Rechercher un outil"
        />

        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
          className="px-3 py-2.5 bg-white/[0.05] border border-white/[0.1] rounded-lg text-gray-300 text-sm font-mono focus:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50 transition-colors cursor-pointer"
          aria-label="Trier par"
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.key} value={opt.key} className="bg-cyber-bg text-gray-300">
              {opt.label}
            </option>
          ))}
        </select>

        <select
          value={vitalityMin}
          onChange={(e) => setVitalityMin(Number(e.target.value))}
          className="px-3 py-2.5 bg-white/[0.05] border border-white/[0.1] rounded-lg text-gray-300 text-sm font-mono focus:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50 transition-colors cursor-pointer"
          aria-label="Filtrer par vitalité minimale"
        >
          <option value={0} className="bg-cyber-bg text-gray-300">Toute vitalité</option>
          <option value={30} className="bg-cyber-bg text-gray-300">≥ 30</option>
          <option value={50} className="bg-cyber-bg text-gray-300">≥ 50</option>
          <option value={70} className="bg-cyber-bg text-gray-300">≥ 70</option>
        </select>

        {data && data.total > 0 && (
          <button
            onClick={() => exportCSV(repos)}
            className="text-xs text-gray-500 hover:text-neon-cyan transition-colors px-3 py-2 border border-white/[0.08] rounded-lg font-mono focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50"
            aria-label="Exporter les résultats en CSV"
          >
            Export CSV
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-3" role="status" aria-label="Chargement">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-10 bg-white/5 rounded animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <p className="text-neon-red text-sm py-4 text-center font-mono" role="alert">Erreur de chargement</p>
      ) : repos.length === 0 ? (
        <p className="text-gray-600 text-sm py-8 text-center font-mono">
          {debouncedSearch ? 'Aucun résultat' : 'Aucune donnée disponible'}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm" role="table">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <th className="text-left py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider">Nom</th>
                <th className="text-right py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider w-24">Stars</th>
                <th className="text-center py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider w-20">Sécurité</th>
                <th className="text-center py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider w-20">Vitalité</th>
                <th className="text-center py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider w-28">Langage</th>
                <th className="text-left py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider max-md:hidden">Description</th>
                <th className="text-right py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider w-28 max-sm:hidden">Mis à jour</th>
              </tr>
            </thead>
            <tbody>
              {repos.map((repo) => (
                <tr
                  key={repo.name}
                  className="border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"
                >
                  <td className="py-2.5 px-2">
                    <button
                      onClick={() => setSelectedRepo(repo)}
                      className="text-indigo-400 hover:text-neon-cyan transition-colors text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50 rounded"
                    >
                      {repo.name}
                    </button>
                  </td>
                  <td className="py-2.5 px-2 text-right text-neon-amber font-semibold font-mono">
                    ★ {repo.stars.toLocaleString()}
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    <SecurityBadge verdict={repo.security_verdict} />
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    <VitalityBadge score={repo.vitality_score ?? null} />
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    <span className="inline-block px-2 py-0.5 rounded text-xs bg-neon-cyan/10 text-neon-cyan font-mono border border-neon-cyan/20">
                      {repo.lang || '?'}
                    </span>
                  </td>
                  <td className="py-2.5 px-2 text-gray-500 truncate max-w-xs max-md:hidden font-mono text-xs">
                    {repo.desc}
                  </td>
                  <td className="py-2.5 px-2 text-right text-gray-600 text-xs max-sm:hidden font-mono">
                    {repo.updated?.slice(0, 10)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!isLoading && !error && pages > 1 && (
        <nav className="flex items-center justify-center gap-2 mt-6" aria-label="Pagination">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="px-3 py-1.5 text-sm rounded-lg border border-white/[0.08] text-gray-400 hover:text-neon-cyan hover:border-neon-cyan/30 disabled:opacity-30 disabled:cursor-not-allowed transition-colors font-mono focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50"
            aria-label="Page précédente"
          >
            ←
          </button>
          {Array.from({ length: Math.min(7, pages) }, (_, i) => {
            const start = Math.max(1, Math.min(page - 3, pages - 6))
            const p = start + i
            if (p > pages) return null
            return (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors font-mono focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50 ${
                  p === page
                    ? 'bg-neon-cyan/15 text-neon-cyan border border-neon-cyan/30 shadow-[0_0_10px_rgba(0,240,255,0.1)]'
                    : 'text-gray-500 hover:text-white border border-white/[0.06] hover:border-white/[0.15]'
                }`}
                aria-label={`Page ${p}`}
                aria-current={p === page ? 'page' : undefined}
              >
                {p}
              </button>
            )
          })}
          <button
            onClick={() => setPage((p) => Math.min(pages, p + 1))}
            disabled={page >= pages}
            className="px-3 py-1.5 text-sm rounded-lg border border-white/[0.08] text-gray-400 hover:text-neon-cyan hover:border-neon-cyan/30 disabled:opacity-30 disabled:cursor-not-allowed transition-colors font-mono focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50"
            aria-label="Page suivante"
          >
            →
          </button>
        </nav>
      )}

      {data && (
        <p className="text-gray-700 text-xs mt-4 text-center font-mono" role="status">
          <span className="text-neon-cyan/60">{data.total}</span> outil{data.total !== 1 ? 's' : ''} trouvé{data.total !== 1 ? 's' : ''}
          {debouncedSearch ? <span className="text-gray-600"> pour "<span className="text-neon-cyan/40">{debouncedSearch}</span>"</span> : ''}
          <span className="text-gray-700"> · Page {data.page}/{data.pages}</span>
          <span className="text-gray-700"> · Tri: <span className="text-neon-cyan/40">{sortBy}</span></span>
        </p>
      )}

      {selectedRepo && (
        <FicheFlashModal repo={selectedRepo} onClose={() => setSelectedRepo(null)} />
      )}
    </div>
  )
}
