import { useState, useEffect } from 'react'
import { useRepos, type Repo } from '../lib/api'

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

function exportCSV(repos: Repo[]) {
  const headers = ['Nom', 'Stars', 'Langage', 'Description', 'Mis à jour']
  const rows = repos.map((r) => [
    r.name,
    r.stars,
    r.lang ?? '',
    `"${(r.desc ?? '').replace(/"/g, '""')}"`,
    r.updated?.slice(0, 10) ?? '',
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

export default function ReposTable() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const debouncedSearch = useDebounce(search, 300)

  const { data, isLoading, error } = useRepos(debouncedSearch || undefined, page)

  useEffect(() => setPage(1), [debouncedSearch])

  const repos = data?.repos ?? []
  const pages = data?.pages ?? 1

  return (
    <div
      className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-5 hover:bg-white/[0.06] hover:-translate-y-0.5 transition-all duration-300"
      role="region"
      aria-label="Liste des outils"
    >
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <h2 className="text-gray-400 text-sm font-semibold uppercase tracking-wider">
          Tous les outils
        </h2>
        {data && data.total > 0 && (
          <button
            onClick={() => exportCSV(repos)}
            className="ml-auto text-xs text-gray-500 hover:text-indigo-400 transition-colors px-3 py-1.5 border border-white/[0.08] rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50"
            aria-label="Exporter les résultats en CSV"
          >
            Export CSV
          </button>
        )}
      </div>

      <input
        type="text"
        placeholder="Rechercher par nom, description, langage..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full px-4 py-2.5 bg-white/[0.05] border border-white/[0.1] rounded-lg text-white text-sm placeholder-gray-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 transition-colors mb-4"
        aria-label="Rechercher un outil"
      />

      {isLoading ? (
        <div className="space-y-3" role="status" aria-label="Chargement">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-10 bg-white/5 rounded animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <p className="text-red-400 text-sm py-4 text-center" role="alert">Erreur de chargement</p>
      ) : repos.length === 0 ? (
        <p className="text-gray-600 text-sm py-8 text-center">
          {debouncedSearch ? 'Aucun résultat' : 'Aucune donnée disponible'}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm" role="table">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <th className="text-left py-3 px-2 text-gray-500 font-medium">Nom</th>
                <th className="text-right py-3 px-2 text-gray-500 font-medium w-24">Stars</th>
                <th className="text-center py-3 px-2 text-gray-500 font-medium w-28">Langage</th>
                <th className="text-left py-3 px-2 text-gray-500 font-medium max-md:hidden">Description</th>
                <th className="text-right py-3 px-2 text-gray-500 font-medium w-28 max-sm:hidden">Mis à jour</th>
              </tr>
            </thead>
            <tbody>
              {repos.map((repo) => (
                <tr
                  key={repo.name}
                  className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors"
                >
                  <td className="py-2.5 px-2">
                    <a
                      href={repo.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-400 hover:text-indigo-300 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 rounded"
                    >
                      {repo.name}
                    </a>
                  </td>
                  <td className="py-2.5 px-2 text-right text-amber-400 font-semibold">
                    ★ {repo.stars.toLocaleString()}
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    <span className="inline-block px-2 py-0.5 rounded text-xs bg-indigo-500/10 text-indigo-300">
                      {repo.lang || '?'}
                    </span>
                  </td>
                  <td className="py-2.5 px-2 text-gray-500 truncate max-w-xs max-md:hidden">
                    {repo.desc}
                  </td>
                  <td className="py-2.5 px-2 text-right text-gray-600 text-xs max-sm:hidden">
                    {repo.updated?.slice(0, 10)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {!isLoading && !error && pages > 1 && (
        <nav className="flex items-center justify-center gap-2 mt-6" aria-label="Pagination">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="px-3 py-1.5 text-sm rounded-lg border border-white/[0.08] text-gray-400 hover:text-white hover:border-white/[0.15] disabled:opacity-30 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50"
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
                className={`px-3 py-1.5 text-sm rounded-lg transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 ${
                  p === page
                    ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
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
            className="px-3 py-1.5 text-sm rounded-lg border border-white/[0.08] text-gray-400 hover:text-white hover:border-white/[0.15] disabled:opacity-30 disabled:cursor-not-allowed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50"
            aria-label="Page suivante"
          >
            →
          </button>
        </nav>
      )}

      {data && (
        <p className="text-gray-700 text-xs mt-4 text-center" role="status">
          {data.total} outil{data.total !== 1 ? 's' : ''} trouvé{data.total !== 1 ? 's' : ''}
          {debouncedSearch ? ` pour "${debouncedSearch}"` : ''}
          {' · Page '}{data.page}/{data.pages}
        </p>
      )}
    </div>
  )
}
