import { useState } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Star, ExternalLink, Zap, TrendingUp, Target, ShieldCheck, Bug, Globe, Wifi, Search, X, LayoutGrid, List } from 'lucide-react'
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
  { id: 'network', label: 'Reseau', icon: <Wifi size={12} /> },
]

type ToolRow = { name: string; desc: string | null; stars: number; lang: string | null; url: string; security_verdict: string | null; vitality_score: number | null }

function ToolsPage() {
  const [tab, setTab] = useState<'featured'|'ready'|'category'>('featured')
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

  const raw = tab === 'featured' ? featured?.tools : tab === 'ready' ? ready?.tools : byCat?.tools
  const total = raw?.length || 0
  const loading = tab === 'featured' ? fl : tab === 'ready' ? rl : cl
  const error = tab === 'featured' ? featErr : tab === 'ready' ? readyErr : catErr
  const retry = () => {
    const key = tab === 'featured' ? ['featured-tools'] : tab === 'ready' ? ['ready-tools'] : ['tools-cat', category]
    qc.invalidateQueries({ queryKey: key })
  }

  const perPage = tab === 'category' ? 30 : 20
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
        <button onClick={() => setDrawer(t)} className="text-indigo-400 hover:text-indigo-300 truncate max-w-[200px] block text-left">
          {t.name}
        </button>
      ),
    },
    {
      key: 'stars', label: 'Stars', sortable: true,
      render: (t) => <span className="text-amber-400 font-mono">{t.stars?.toLocaleString()}</span>,
    },
    {
      key: 'security_verdict', label: 'Verdict', sortable: true,
      render: (t) => t.security_verdict ? <Chip variant="verdict" value={t.security_verdict} /> : <span className="text-slate-500 text-[10px]">-</span>,
    },
    {
      key: 'vitality_score', label: 'Vitalite', sortable: true,
      render: (t) => t.vitality_score != null ? (
        <span className={`font-mono text-[10px] ${t.vitality_score >= 70 ? 'text-emerald-400' : t.vitality_score >= 40 ? 'text-amber-400' : 'text-slate-500'}`}>
          {t.vitality_score}/100
        </span>
      ) : <span className="text-slate-500">-</span>,
    },
    {
      key: 'lang', label: 'Langage', sortable: true,
      render: (t) => <span className="text-slate-500 text-[10px]">{t.lang || '-'}</span>,
      className: 'hidden md:table-cell',
    },
  ]

  return (
    <div className="max-w-6xl mx-auto py-4 sm:py-8 animate-fade">
      {/* Tabs */}
      <div className="flex items-center gap-1 mb-4 flex-wrap">
        <button onClick={() => { setTab('featured'); setPage(1) }} className={`px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition flex items-center gap-1.5 ${tab === 'featured' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'glass text-slate-400 hover:text-white'}`}><TrendingUp size={13} /> Incontournables</button>
        <button onClick={() => { setTab('ready'); setPage(1) }} className={`px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition flex items-center gap-1.5 ${tab === 'ready' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'glass text-slate-400 hover:text-white'}`}><Zap size={13} /> Prets a l'emploi</button>
        <button onClick={() => { setTab('category'); setPage(1) }} className={`px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition flex items-center gap-1.5 ${tab === 'category' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'glass text-slate-400 hover:text-white'}`}><Search size={13} /> Par categorie</button>
        <div className="ml-auto flex gap-1">
          <button onClick={() => setView('table')} className={`p-2 rounded-lg text-xs ${view === 'table' ? 'glass text-white' : 'text-slate-500 hover:text-white'}`}><List size={13} /></button>
          <button onClick={() => setView('grid')} className={`p-2 rounded-lg text-xs ${view === 'grid' ? 'glass text-white' : 'text-slate-500 hover:text-white'}`}><LayoutGrid size={13} /></button>
        </div>
      </div>

      {tab === 'category' && (
        <div className="flex flex-wrap gap-1 mb-4">
          {CATS.map(c => (
            <button key={c.id} onClick={() => { setCategory(c.id); setPage(1) }}
              className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] sm:text-xs font-medium transition border ${category === c.id ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' : 'glass text-slate-500 hover:text-slate-300'}`}>
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
          emptyMessage="Aucun outil trouve"
          error={error ? String(error instanceof Error ? error.message : error) : null}
          onRetry={retry}
          exportCSV={tab === 'category' ? () => {
            const csv = ['Nom,Stars,Verdict,Vitalite,Langage,URL'].concat(sorted.map(t => `"${t.name}",${t.stars},${t.security_verdict || ''},${t.vitality_score || ''},${t.lang || ''},${t.url}`)).join('\n')
            const blob = new Blob([csv], { type: 'text/csv' })
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a'); a.href = url; a.download = 'cyberscan-outils.csv'; a.click()
          } : undefined}
        />
      ) : (
        /* Grid view */
        <div>
          <p className="text-xs text-slate-500 mb-3">{total} outils</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3">
            {paged.map((t, i) => (
              <button key={i} onClick={() => setDrawer(t)} className="glass-card rounded-xl p-3 sm:p-4 text-left group w-full">
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <div className="flex-1 min-w-0">
                    <span className="text-xs sm:text-sm font-medium text-slate-200 group-hover:text-indigo-400 transition truncate block">{t.name}</span>
                  </div>
                  <span className="flex items-center gap-0.5 text-[10px] sm:text-xs text-amber-400 shrink-0"><Star size={10} />{t.stars?.toLocaleString()}</span>
                </div>
                {t.desc && <p className="text-[10px] sm:text-xs text-slate-500 leading-relaxed line-clamp-2 mb-2">{t.desc}</p>}
                <div className="flex items-center gap-2 text-[9px] sm:text-[10px] text-slate-500">
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
        <div className="fixed inset-0 z-50 flex justify-end" onClick={() => setDrawer(null)}>
          <div className="absolute inset-0 bg-black/50" />
          <div className="relative w-full max-w-md bg-slate-950 border-l border-white/[0.08] overflow-y-auto animate-fade p-6" onClick={e => e.stopPropagation()}>
            <button onClick={() => setDrawer(null)} className="absolute top-4 right-4 text-slate-500 hover:text-white"><X size={18} /></button>
            <h2 className="text-base font-bold text-white mb-1">{drawer.name}</h2>
            {drawer.desc && <p className="text-xs text-slate-400 mb-4">{drawer.desc}</p>}
            <div className="flex flex-wrap gap-2 mb-4">
              {drawer.security_verdict && <Chip variant="verdict" value={drawer.security_verdict} />}
              {drawer.lang && <span className="glass px-2 py-1 rounded-lg text-[10px] text-slate-300">{drawer.lang}</span>}
              <span className="glass px-2 py-1 rounded-lg text-[10px] text-amber-400 flex items-center gap-1"><Star size={9} />{drawer.stars?.toLocaleString()}</span>
            </div>
            {drawer.vitality_score != null && (
              <div className="glass rounded-xl p-3 mb-4">
                <span className="text-[10px] text-slate-500 block mb-1">Score de vitalite</span>
                <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${drawer.vitality_score >= 70 ? 'bg-emerald-400' : drawer.vitality_score >= 40 ? 'bg-amber-400' : 'bg-rose-400'}`} style={{ width: `${drawer.vitality_score}%` }} />
                </div>
              </div>
            )}
            <div className="space-y-2">
              <Link to="/tool/$name" params={{ name: drawer.name }} className="block w-full text-center glass-card rounded-xl p-3 text-xs font-medium text-indigo-400 hover:text-white hover:bg-indigo-500/10 transition">
                Fiche complete
              </Link>
              <a href={drawer.url} target="_blank" rel="noopener" className="block w-full text-center glass-card rounded-xl p-3 text-xs font-medium text-slate-400 hover:text-white transition flex items-center justify-center gap-1.5">
                <ExternalLink size={11} /> GitHub
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
