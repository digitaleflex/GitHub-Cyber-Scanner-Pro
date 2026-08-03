import { useState, useCallback } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useCves, useStats, type CveEntry } from '../lib/api'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import AdminGuard from '../components/AdminGuard'
import DataTable, { type DataTableColumn } from '../components/DataTable'
import Chip from '../components/Chip'
import { Search, Shield, AlertTriangle, TrendingUp, Bug, Download } from 'lucide-react'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/cves',
  component: () => <AdminGuard><CvesPage /></AdminGuard>,
})

function CvesPage() {
  const [q, setQ] = useState('')
  const [severity, setSeverity] = useState('')
  const [page, setPage] = useState(1)
  const [sortKey, setSortKey] = useState('')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const { data, isLoading, error } = useCves(q, severity, page)
  const { data: stats } = useStats()
  const queryClient = useQueryClient()

  const { data: cveStats } = useQuery({
    queryKey: ['cve-stats'],
    queryFn: () => fetch('/api/cves?q=&severity=&page=1&per_page=1').then(r => r.json()),
    staleTime: 120_000,
  })

  const handleSort = useCallback((key: string, dir: 'asc' | 'desc') => {
    setSortKey(key)
    setSortDir(dir)
  }, [])

  const sorted = data?.cves ? [...data.cves].sort((a, b) => {
    if (!sortKey) return 0
    const av = a[sortKey as keyof CveEntry]
    const bv = b[sortKey as keyof CveEntry]
    if (av == null && bv == null) return 0
    if (av == null) return 1
    if (bv == null) return -1
    const cmp = av < bv ? -1 : av > bv ? 1 : 0
    return sortDir === 'asc' ? cmp : -cmp
  }) : []

  const columns: DataTableColumn<CveEntry>[] = [
    {
      key: 'cve_id', label: 'CVE ID', sortable: true,
      render: (cve) => (
        <Link to="/cve/$id" params={{ id: cve.cve_id }} className="text-indigo-400 hover:text-indigo-300 font-mono">
          {cve.cve_id}
        </Link>
      ),
    },
    {
      key: 'severity', label: 'Sévérité', sortable: true,
      render: (cve) => <Chip variant="severity" value={cve.severity} />,
    },
    {
      key: 'cvss_score', label: 'CVSS', sortable: true,
      render: (cve) => cve.cvss_score ? (
        <span className={`font-mono font-bold ${cve.cvss_score >= 9 ? 'text-rose-400' : cve.cvss_score >= 7 ? 'text-amber-400' : 'text-slate-400'}`}>
          {cve.cvss_score.toFixed(1)}
        </span>
      ) : <span className="text-slate-500">-</span>,
    },
    {
      key: 'published', label: 'Publiée', sortable: true,
      render: (cve) => cve.published ? (
        <span className="text-slate-500">{new Date(cve.published).toLocaleDateString('fr-FR')}</span>
      ) : <span className="text-slate-500">-</span>,
    },
    {
      key: 'description', label: 'Description',
      render: (cve) => <span className="line-clamp-1 text-slate-400">{cve.description?.slice(0, 120)}</span>,
      className: 'hidden md:table-cell',
    },
  ]

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-lg font-semibold text-white">Base CVE</h1>
        <a href="/api/stix/download?what=cves&limit=100"
          className="flex items-center gap-1.5 px-3 py-1.5 glass rounded-lg text-[10px] text-indigo-400 hover:text-white transition">
          <Download size={11} /> STIX 2.1
        </a>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3 mb-4">
        <div className="glass-card rounded-xl p-3 text-center">
          <Shield size={14} className="text-rose-400 mx-auto mb-1" />
          <div className="text-lg font-bold text-white">{cveStats?.total?.toLocaleString() || '?'}</div>
          <div className="text-[9px] text-slate-500">Total CVEs</div>
        </div>
        <div className="glass-card rounded-xl p-3 text-center">
          <Bug size={14} className="text-indigo-400 mx-auto mb-1" />
          <div className="text-lg font-bold text-white">{stats?.pending_keywords || '?'}</div>
          <div className="text-[9px] text-slate-500">Mots-clés</div>
        </div>
        <div className="glass-card rounded-xl p-3 text-center">
          <AlertTriangle size={14} className="text-amber-400 mx-auto mb-1" />
          <div className="text-lg font-bold text-white">{stats?.security_critique || '?'}</div>
          <div className="text-[9px] text-slate-500">Outils critiques</div>
        </div>
        <div className="glass-card rounded-xl p-3 text-center">
          <TrendingUp size={14} className="text-emerald-400 mx-auto mb-1" />
          <div className="text-lg font-bold text-white">{stats?.new_repos_24h || '?'}</div>
          <div className="text-[9px] text-slate-500">Nouveaux 24h</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-4">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input value={q} onChange={e => { setQ(e.target.value); setPage(1) }}
            placeholder="CVE-2024-... (appuyez / pour chercher)"
            className="w-full pl-9 pr-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500/40" />
        </div>
        <select value={severity} onChange={e => { setSeverity(e.target.value); setPage(1) }}
          className="px-3 py-2 glass rounded-lg text-xs text-white">
          <option value="">Toutes sévérités</option>
          {['CRITICAL','HIGH','MEDIUM','LOW'].map(s => <option key={s}>{s}</option>)}
        </select>
      </div>

      <DataTable<CveEntry>
        columns={columns}
        data={sorted}
        total={data?.total || 0}
        page={page}
        perPage={20}
        onPageChange={setPage}
        onSort={handleSort}
        sortKey={sortKey}
        sortDir={sortDir}
        loading={isLoading}
        emptyMessage="Aucune CVE trouvée"
        error={error ? String(error instanceof Error ? error.message : error) : null}
        onRetry={() => queryClient.invalidateQueries({ queryKey: ['cves'] })}
      />
    </div>
  )
}
