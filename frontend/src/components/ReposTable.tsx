import { useState, useMemo } from 'react'
import { useRepos } from '../lib/api'

export default function ReposTable() {
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<'stars' | 'name' | 'lang' | 'updated'>('stars')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  const { data, isLoading, error } = useRepos(search || undefined)

  const repos = useMemo(() => {
    if (!data?.repos) return []
    return [...data.repos].sort((a, b) => {
      let cmp = 0
      if (sortKey === 'stars') cmp = a.stars - b.stars
      else if (sortKey === 'name') cmp = a.name.localeCompare(b.name)
      else if (sortKey === 'lang') cmp = (a.lang ?? '').localeCompare(b.lang ?? '')
      else cmp = a.updated.localeCompare(b.updated)
      return sortDir === 'desc' ? -cmp : cmp
    })
  }, [data, sortKey, sortDir])

  const handleSort = (key: typeof sortKey) => {
    if (sortKey === key) setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'))
    else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const SortIcon = ({ col }: { col: typeof sortKey }) => {
    if (sortKey !== col) return <span className="text-gray-700 ml-1">↕</span>
    return <span className="text-indigo-400 ml-1">{sortDir === 'desc' ? '↓' : '↑'}</span>
  }

  return (
    <div className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-5">
      <h2 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-4">
        Tous les outils
      </h2>

      <input
        type="text"
        placeholder="Rechercher par nom, description, langage..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full px-4 py-2.5 bg-white/[0.05] border border-white/[0.1] rounded-lg text-white text-sm placeholder-gray-600 focus:outline-none focus:border-indigo-500/50 transition-colors mb-4"
      />

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-10 bg-white/5 rounded animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <p className="text-red-400 text-sm py-4 text-center">Erreur de chargement</p>
      ) : repos.length === 0 ? (
        <p className="text-gray-600 text-sm py-8 text-center">
          {search ? 'Aucun résultat' : 'Aucune donnée disponible'}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <th
                  className="text-left py-3 px-2 text-gray-500 font-medium cursor-pointer hover:text-gray-300 select-none"
                  onClick={() => handleSort('name')}
                >
                  Nom <SortIcon col="name" />
                </th>
                <th
                  className="text-right py-3 px-2 text-gray-500 font-medium cursor-pointer hover:text-gray-300 select-none w-24"
                  onClick={() => handleSort('stars')}
                >
                  Stars <SortIcon col="stars" />
                </th>
                <th
                  className="text-center py-3 px-2 text-gray-500 font-medium cursor-pointer hover:text-gray-300 select-none w-28"
                  onClick={() => handleSort('lang')}
                >
                  Langage <SortIcon col="lang" />
                </th>
                <th className="text-left py-3 px-2 text-gray-500 font-medium max-md:hidden">
                  Description
                </th>
                <th
                  className="text-right py-3 px-2 text-gray-500 font-medium cursor-pointer hover:text-gray-300 select-none w-28 max-sm:hidden"
                  onClick={() => handleSort('updated')}
                >
                  Mis à jour <SortIcon col="updated" />
                </th>
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
                      className="text-indigo-400 hover:text-indigo-300 transition-colors"
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

      {data && (
        <p className="text-gray-700 text-xs mt-4 text-center">
          {data.total} outil{data.total !== 1 ? 's' : ''} trouvé{data.total !== 1 ? 's' : ''}
          {search ? ` pour "${search}"` : ''}
        </p>
      )}
    </div>
  )
}
