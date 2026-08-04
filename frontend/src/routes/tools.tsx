import { useState } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Star, ExternalLink, Zap, TrendingUp, Target, ShieldCheck, Bug, Globe, Wifi, Search, X, LayoutGrid, List, Cpu } from 'lucide-react'
import DataTable, { type DataTableColumn } from '../components/DataTable'
import Chip from '../components/Chip'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/tools', component: ToolsPage })

const CATS = [
  { id: 'all', label: 'Tous', icon: <Star size={12} /> },
  { id: 'red-team', label: 'Red Team', icon: <Target size={12} /> },
  { id: 'blue-team', label: 'Blue Team', icon: <ShieldCheck size={12} /> },
  { id: 'exploit', label: 'Exploits', icon: <Bug size={12} /> },
  { id: 'malware', label: 'Malware', icon: <Zap size={12} /> },
  { id: 'osint', label: 'OSINT', icon: <Globe size={12} /> },
  { id: 'network', label: 'Réseau', icon: <Wifi size={12} /> },
]

type ToolRow = { name: string; desc: string | null; stars: number; lang: string | null; url: string; security_verdict: string | null; vitality_score: number | null }

function ToolsPage() {
  const [tab, setTab] = useState<'featured'|'ready'|'category'|'best'>('featured')
  const [category, setCategory] = useState('all')
  const [page, setPage] = useState(1)
  const [sortKey, setSortKey] = useState('stars')
  const [sortDir, setSortDir] = useState<'asc'|'desc'>('desc')
  const [view, setView] = useState<'table'|'grid'>('table')
  const [drawer, setDrawer] = useState<ToolRow | null>(null)
  const qc = useQueryClient()

  const { data: featured, isLoading: fl, error: featErr } = useQuery({
    queryKey: ['featured-tools'], queryFn: async () => { const r = await fetch('/api/tools/featured'); if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() }, staleTime: 120_000
  })
  const { data: ready, isLoading: rl, error: readyErr } = useQuery({
    queryKey: ['ready-tools'], queryFn: async () => { const r = await fetch('/api/tools/readytouse'); if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() }, staleTime: 120_000, enabled: tab === 'ready'
  })
  const { data: byCat, isLoading: cl, error: catErr } = useQuery({
    queryKey: ['tools-cat', category], queryFn: async () => { const r = await fetch(`/api/tools/by-category?category=${category}&limit=200`); if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() }, staleTime: 60_000, enabled: tab === 'category'
  })
  const { data: best, isLoading: bl, error: bestErr } = useQuery({
    queryKey: ['best-tools', category], queryFn: async () => { const r = await fetch(`/api/tools/best?category=${category}&limit=200`); if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() }, staleTime: 60_000, enabled: tab === 'best'
  })

  const raw = tab === 'featured' ? featured?.tools : tab === 'ready' ? ready?.tools : tab === 'best' ? best?.tools : byCat?.tools
  const total = raw?.length || 0
  const loading = tab === 'featured' ? fl : tab === 'ready' ? rl : tab === 'best' ? bl : cl
  const error = tab === 'featured' ? featErr : tab === 'ready' ? readyErr : tab === 'best' ? bestErr : catErr
  const retry = () => {
    const key = tab === 'featured' ? ['featured-tools'] : tab === 'ready' ? ['ready-tools'] : tab === 'best' ? ['best-tools', category] : ['tools-cat', category]
    qc.invalidateQueries({ queryKey: key })
  }

  const perPage = tab === 'category' || tab === 'best' ? 30 : 20
  const isBestTab = tab === 'best'
  const showCats = tab === 'category' || isBestTab
  const sorted = [...(raw || [])].sort((a: ToolRow, b: ToolRow) => {
    const av = sortKey === 'stars' ? a.stars : sortKey === 'vitality_score' ? (a.vitality_score || 0) : a.name
    const bv = sortKey === 'stars' ? b.stars : sortKey === 'vitality_score' ? (b.vitality_score || 0) : b.name
    const cmp = av < bv ? -1 : av > bv ? 1 : 0
    return sortDir === 'asc' ? cmp : -cmp
  })
  const paged = sorted.slice((page - 1) * perPage, page * perPage)

  const columns: DataTableColumn<ToolRow>[] = [
    {
      key: 'name', label: 'Outil', sortable: true,
      render: (t) => (
        <button onClick={() => setDrawer(t)} className="text-left truncate max-w-[200px] block font-medium hover:underline" style={{ color: 'var(--decision-text)' }}>
          {t.name}
        </button>
      ),
    },
    {
      key: 'stars', label: 'Stars', sortable: true,
      render: (t) => <span className="mono" style={{ color: 'var(--mission)' }}>{t.stars?.toLocaleString()}</span>,
    },
    {
      key: 'security_verdict', label: 'Verdict', sortable: true,
      render: (t) => t.security_verdict ? <Chip variant="verdict" value={t.security_verdict} /> : <span className="text-[10px] text-muted">-</span>,
    },
    {
      key: 'vitality_score', label: 'Vitalité', sortable: true,
      render: (t) => t.vitality_score != null ? (
        <span className="mono text-[10px]" style={{ color: t.vitality_score >= 70 ? 'var(--brand-text)' : t.vitality_score >= 40 ? 'var(--mission-text)' : 'var(--text-muted)' }}>
          {t.vitality_score}/100
        </span>
      ) : <span className="text-muted">-</span>,
    },
    {
      key: 'lang', label: 'Langage', sortable: true,
      render: (t) => <span className="text-xs text-muted">{t.lang || '-'}</span>,
      className: 'hidden md:table-cell',
    },
  ]

  const getTabStyle = (t: string) => {
    const active = tab === t
    return {
      background: active ? 'var(--surface-elevated)' : 'var(--surface)',
      color: active ? 'var(--text)' : 'var(--text-secondary)',
      borderColor: active ? 'var(--brand)' : 'var(--border)',
      boxShadow: active ? 'var(--shadow-md)' : 'none',
    }
  }

  return (
    <div className="max-w-6xl mx-auto py-4 sm:py-8 animate-fade">
      {/* Tabs */}
      <div className="flex items-center gap-1 mb-4 flex-wrap">
        {[
          { id: 'featured' as const, icon: <TrendingUp size={13} />, label: 'Incontournables' },
          { id: 'ready' as const, icon: <Zap size={13} />, label: "Prêts à l'emploi" },
          { id: 'category' as const, icon: <Search size={13} />, label: 'Par catégorie' },
          { id: 'best' as const, icon: <Cpu size={13} />, label: 'Outils pro' },
        ].map(t => (
          <button key={t.id} onClick={() => { setTab(t.id); setPage(1) }}
            className="px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all flex items-center gap-1.5 border hover:-translate-y-0.5"
            style={getTabStyle(t.id)}>
            {t.icon} {t.label}
          </button>
        ))}
        <div className="ml-auto flex gap-1">
          <button onClick={() => setView('table')} className="p-2 rounded-lg text-xs transition-colors"
            style={{ color: view === 'table' ? 'var(--text)' : 'var(--text-muted)', background: view === 'table' ? 'var(--surface)' : 'transparent', border: view === 'table' ? '1px solid var(--border)' : '1px solid transparent' }}>
            <List size={13} />
          </button>
          <button onClick={() => setView('grid')} className="p-2 rounded-lg text-xs transition-colors"
            style={{ color: view === 'grid' ? 'var(--text)' : 'var(--text-muted)', background: view === 'grid' ? 'var(--surface)' : 'transparent', border: view === 'grid' ? '1px solid var(--border)' : '1px solid transparent' }}>
            <LayoutGrid size={13} />
          </button>
        </div>
      </div>

      {showCats && (
        <div className="flex flex-wrap gap-1 mb-4">
          {CATS.map(c => (
            <button key={c.id} onClick={() => { setCategory(c.id); setPage(1) }}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] sm:text-xs font-medium border transition-all hover:-translate-y-0.5"
              style={{
                background: category === c.id ? 'var(--surface-elevated)' : 'var(--surface)',
                color: category === c.id ? 'var(--text)' : 'var(--text-muted)',
                borderColor: category === c.id ? 'var(--brand)' : 'var(--border)',
              }}>
              {c.icon} {c.label}
            </button>
          ))}
        </div>
      )}

      {/* View: Table */}
      {view === 'table' ? (
        <DataTable<ToolRow>
          columns={columns}
          data={paged}
          total={total}
          page={page}
          perPage={perPage}
          onPageChange={setPage}
          onSort={(k, d) => { setSortKey(k); setSortDir(d); setPage(1) }}
          sortKey={sortKey}
          sortDir={sortDir}
          loading={loading}
          emptyMessage="Aucun outil trouvé"
          error={error ? String(error instanceof Error ? error.message : error) : null}
          onRetry={retry}
          exportCSV={showCats ? () => {
            const csv = ['Nom,Stars,Verdict,Vitalite,Langage,URL'].concat(sorted.map(t => `"${t.name}",${t.stars},${t.security_verdict || ''},${t.vitality_score || ''},${t.lang || ''},${t.url}`)).join('\n')
            const blob = new Blob([csv], { type: 'text/csv' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a'); a.href = url; a.download = 'cyberscan-outils.csv'; a.click()
          } : undefined}
        />
      ) : (
        /* Grid view */
        <div>
          <p className="text-xs text-muted mb-3">{total} outils</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3">
            {paged.map((t, i) => (
              <button key={i} onClick={() => setDrawer(t)}
                className="surface rounded-xl p-3 sm:p-4 text-left cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-md w-full"
                style={{ border: '1px solid var(--border)' }}>
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <div className="flex-1 min-w-0">
                    <span className="text-xs sm:text-sm font-medium truncate block" style={{ color: 'var(--text)' }}>{t.name}</span>
                  </div>
                  <span className="flex items-center gap-0.5 text-[10px] sm:text-xs shrink-0" style={{ color: 'var(--mission)' }}><Star size={10} />{t.stars?.toLocaleString()}</span>
                </div>
                {t.desc && <p className="text-[10px] sm:text-xs leading-relaxed line-clamp-2 mb-2 text-secondary">{t.desc}</p>}
                <div className="flex items-center gap-2 text-[9px] sm:text-[10px] text-muted">
                  {t.security_verdict && <Chip variant="verdict" value={t.security_verdict} />}
                  {t.lang && <span>{t.lang}</span>}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Drawer */}
      {drawer && (
        <div className="fixed inset-0 z-50 flex justify-end" onClick={() => setDrawer(null)} style={{ background: 'var(--overlay)' }}>
          <div className="relative w-full max-w-md overflow-y-auto animate-fade p-6"
            style={{ background: 'var(--surface-elevated)', borderLeft: '1px solid var(--border)' }}
            onClick={e => e.stopPropagation()}>
            <button onClick={() => setDrawer(null)} className="absolute top-4 right-4 p-1 rounded-lg transition-colors" style={{ color: 'var(--text-muted)' }}><X size={18} /></button>
            <h2 className="h2 mb-1" style={{ color: 'var(--text)' }}>{drawer.name}</h2>
            {drawer.desc && <p className="text-xs text-secondary mb-4">{drawer.desc}</p>}
            <div className="flex flex-wrap gap-2 mb-4">
              {drawer.security_verdict && <Chip variant="verdict" value={drawer.security_verdict} />}
              {drawer.lang && <span className="text-xs px-2 py-1 rounded-lg" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}>{drawer.lang}</span>}
              <span className="text-xs px-2 py-1 rounded-lg flex items-center gap-1" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border)', color: 'var(--mission)' }}>
                <Star size={9} />{drawer.stars?.toLocaleString()}
              </span>
            </div>
            {drawer.vitality_score != null && (
              <div className="rounded-xl p-3 mb-4" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border)' }}>
                <span className="text-xs text-muted block mb-1">Score de vitalité</span>
                <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'var(--border)' }}>
                  <div className="h-full rounded-full" style={{
                    width: `${drawer.vitality_score}%`,
                    background: drawer.vitality_score >= 70 ? 'var(--success)' : drawer.vitality_score >= 40 ? 'var(--mission)' : 'var(--critical)',
                  }} />
                </div>
              </div>
            )}
            <div className="space-y-2">
              <Link to="/tool/$name" params={{ name: drawer.name }}
                className="block w-full text-center rounded-xl p-3 text-xs font-medium transition-all hover:-translate-y-0.5"
                style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--decision-text)', textDecoration: 'none' }}>
                Fiche complète
              </Link>
              <a href={drawer.url} target="_blank" rel="noopener"
                className="block w-full text-center rounded-xl p-3 text-xs font-medium transition-all hover:-translate-y-0.5 flex items-center justify-center gap-1.5"
                style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-secondary)', textDecoration: 'none' }}>
                <ExternalLink size={11} /> GitHub
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
