import { useState } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Star, ExternalLink, Zap, TrendingUp, Target, ShieldCheck, Bug, Globe, Wifi, X, LayoutGrid, List, Wrench, Radar } from 'lucide-react'
import DataTable, { type DataTableColumn } from '../components/DataTable'
import Chip from '../components/Chip'
import { InstrumentPanel } from '../components/InstrumentPanel'

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
        <button onClick={() => setDrawer(t)} className="text-left truncate max-w-[200px] block font-medium hover:underline" style={{ color: 'var(--cyan)' }}>
          {t.name}
        </button>
      ),
    },
    {
      key: 'stars', label: 'Stars', sortable: true,
      render: (t) => <span className="mono" style={{ color: 'var(--amber)' }}>{t.stars?.toLocaleString()}</span>,
    },
    {
      key: 'security_verdict', label: 'Verdict', sortable: true,
      render: (t) => t.security_verdict ? <Chip variant="verdict" value={t.security_verdict} /> : <span className="text-caption t-m" style={{ textTransform: 'none' }}>-</span>,
    },
    {
      key: 'vitality_score', label: 'Vitalité', sortable: true,
      render: (t) => t.vitality_score != null ? (
        <span className="mono" style={{ color: t.vitality_score >= 70 ? 'var(--lime)' : t.vitality_score >= 40 ? 'var(--amber)' : 'var(--text-muted)' }}>
          {t.vitality_score}/100
        </span>
      ) : <span className="t-m">-</span>,
    },
    {
      key: 'lang', label: 'Langage', sortable: true,
      render: (t) => <span className="text-caption t-s" style={{ textTransform: 'none' }}>{t.lang || '-'}</span>,
      className: 'hidden md:table-cell',
    },
  ]

  const tabs = [
    { id: 'featured' as const, icon: <TrendingUp size={13} />, label: 'Incontournables' },
    { id: 'ready' as const, icon: <Zap size={13} />, label: "Prêts à l'emploi" },
    { id: 'category' as const, icon: <Radar size={13} />, label: 'Catégories' },
    { id: 'best' as const, icon: <Target size={13} />, label: 'Pro' },
  ]

  return (
    <div className="w-full py-4 sm:py-8 animate-fade">
      <InstrumentPanel
        className="max-w-6xl mx-auto"
        icon={<Wrench size={18} />}
        title="Outils"
        accent="amber"
      >
        {/* Tabs */}
        <div className="flex items-center gap-1 mb-4 flex-wrap">
          {tabs.map(t => (
            <button key={t.id} onClick={() => { setTab(t.id); setPage(1) }}
              className="px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all flex items-center gap-1.5 border"
              style={{
                background: tab === t.id ? 'var(--surface-elevated)' : 'var(--surface)',
                color: tab === t.id ? 'var(--text)' : 'var(--text-secondary)',
                borderColor: tab === t.id ? 'var(--amber)' : 'var(--border)',
                boxShadow: tab === t.id ? '0 0 12px rgba(245, 158, 11, 0.15)' : 'none',
              }}>
              {t.icon} {t.label}
            </button>
          ))}
          <div className="ml-auto flex gap-1">
            <button onClick={() => setView('table')} className="p-2 rounded-lg transition-all"
              style={{
                color: view === 'table' ? 'var(--text)' : 'var(--text-muted)',
                background: view === 'table' ? 'var(--surface-elevated)' : 'transparent',
                border: view === 'table' ? '1px solid var(--amber)' : '1px solid transparent',
              }}>
              <List size={13} />
            </button>
            <button onClick={() => setView('grid')} className="p-2 rounded-lg transition-all"
              style={{
                color: view === 'grid' ? 'var(--text)' : 'var(--text-muted)',
                background: view === 'grid' ? 'var(--surface-elevated)' : 'transparent',
                border: view === 'grid' ? '1px solid var(--amber)' : '1px solid transparent',
              }}>
              <LayoutGrid size={13} />
            </button>
          </div>
        </div>

        {showCats && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {CATS.map(c => (
              <button key={c.id} onClick={() => { setCategory(c.id); setPage(1) }}
                className="transition-all rounded-full"
                style={{
                  outline: 'none',
                  background: 'transparent',
                  border: 'none',
                  padding: 0,
                  opacity: category === c.id ? 1 : 0.55,
                  filter: category === c.id ? 'brightness(1.2)' : 'none',
                }}>
                <Chip variant="category" value={`${c.icon ? '' : ''}${c.label}`} />
              </button>
            ))}
          </div>
        )}

        {/* Table / Grid */}
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
          <div>
            <p className="text-caption t-m mb-3" style={{ textTransform: 'none' }}>{total.toLocaleString()} outils</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3">
              {paged.map((t, i) => (
                <button key={i} onClick={() => setDrawer(t)}
                  className="surface rounded-xl p-3 sm:p-4 text-left cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-md w-full"
                  style={{ border: '1px solid var(--border)' }}>
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <div className="flex-1 min-w-0">
                      <span className="text-xs sm:text-sm font-semibold truncate block t-p">{t.name}</span>
                    </div>
                    <span className="flex items-center gap-0.5 text-[10px] sm:text-xs shrink-0 mono" style={{ color: 'var(--amber)' }}><Star size={10} />{t.stars?.toLocaleString()}</span>
                  </div>
                  {t.desc && <p className="text-[10px] sm:text-xs leading-relaxed line-clamp-2 mb-2 t-s">{t.desc}</p>}
                  <div className="flex items-center gap-2 text-[9px] sm:text-[10px]">
                    {t.security_verdict && <Chip variant="verdict" value={t.security_verdict} />}
                    {t.lang && <span className="text-caption t-m" style={{ textTransform: 'none' }}>{t.lang}</span>}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </InstrumentPanel>

      {/* Drawer */}
      {drawer && (
        <div className="fixed inset-0 z-50 flex justify-end animate-fade" onClick={() => setDrawer(null)} style={{ background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }}>
          <div className="relative w-full max-w-md overflow-y-auto p-6"
            style={{ background: 'var(--surface-elevated)', borderLeft: '1px solid var(--border)', boxShadow: '-8px 0 24px rgba(0,0,0,0.4)' }}
            onClick={e => e.stopPropagation()}>
            <button onClick={() => setDrawer(null)} aria-label="Fermer le panneau" className="absolute top-4 right-4 p-1.5 rounded-lg transition-colors hover:bg-[var(--surface-hover)]" style={{ color: 'var(--text-muted)' }}><X size={18} /></button>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'var(--amber-light)' }}>
                <Wrench size={14} style={{ color: 'var(--amber)' }} />
              </div>
              <h2 className="h2 t-p flex-1">{drawer.name}</h2>
            </div>
            {drawer.desc && <p className="text-xs t-s mb-4 leading-relaxed">{drawer.desc}</p>}
            <div className="flex flex-wrap gap-2 mb-4">
              {drawer.security_verdict && <Chip variant="verdict" value={drawer.security_verdict} />}
              {drawer.lang && (
                <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-caption border"
                  style={{ background: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text-secondary)' }}>
                  {drawer.lang}
                </span>
              )}
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-caption border mono"
                style={{ background: 'var(--amber-light)', borderColor: 'var(--amber)', color: 'var(--amber)' }}>
                <Star size={10} />{drawer.stars?.toLocaleString()}
              </span>
            </div>
            {drawer.vitality_score != null && (
              <div className="rounded-xl p-3 mb-4" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
                <span className="text-caption t-m block mb-2" style={{ textTransform: 'none' }}>Score de vitalité</span>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: 'var(--border)' }}>
                    <div className="h-full rounded-full transition-all duration-500" style={{
                      width: `${drawer.vitality_score}%`,
                      background: drawer.vitality_score >= 70 ? 'var(--lime)' : drawer.vitality_score >= 40 ? 'var(--amber)' : 'var(--red)',
                    }} />
                  </div>
                  <span className="text-caption mono font-semibold" style={{ color: drawer.vitality_score >= 70 ? 'var(--lime)' : drawer.vitality_score >= 40 ? 'var(--amber)' : 'var(--red)' }}>
                    {drawer.vitality_score}/100
                  </span>
                </div>
              </div>
            )}
            <div className="space-y-2">
              <Link to="/tool/$name" params={{ name: drawer.name }}
                className="block w-full text-center rounded-xl p-3 text-xs font-medium transition-all hover:-translate-y-0.5"
                style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--cyan)', textDecoration: 'none' }}>
                Fiche complète
              </Link>
              <a href={drawer.url} target="_blank" rel="noopener noreferrer"
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
