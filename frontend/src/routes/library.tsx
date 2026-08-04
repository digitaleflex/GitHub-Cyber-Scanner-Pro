import { useState } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import { Search, ExternalLink, Star, BookOpen, X, Shield, Library } from 'lucide-react'
import { PageLoader } from '../components/CyberLoader'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/library', component: LibraryPage })

const SORT_OPTIONS = [
  { value: 'stars', label: 'Stars' },
  { value: 'vitality', label: 'Vitalité' },
  { value: 'name', label: 'Nom' },
  { value: 'updated', label: 'Mise à jour' },
]
const VERDICTS = ['', 'legitimate', 'malicious', 'suspicious', 'neutral', 'unknown']

function LibraryPage() {
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState('stars')
  const [verdict, setVerdict] = useState('')
  const perPage = 30

  const { data, isLoading } = useQuery({
    queryKey: ['library', q, page, sort, verdict],
    queryFn: async () => {
      const p = new URLSearchParams({ q, page: String(page), per_page: String(perPage), sort_by: sort, vitality_min: '0' })
      if (verdict) p.set('security_verdict', verdict)
      const r = await fetch(`/api/repos?${p}`)
      return r.json()
    },
    placeholderData: (prev: any) => prev,
  })

  const repos = (data as any)?.repos ?? []
  const total = (data as any)?.total ?? 0
  const pages = (data as any)?.pages ?? 1

  return (
    <div className="w-full py-8 animate-fade">
      <div className="flex items-center gap-3 mb-6">
        <Library size={24} style={{ color: 'var(--amber)' }} />
        <div>
          <h1 className="h1" style={{ color: 'var(--text)' }}>Bibliothèque</h1>
          <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
            {total.toLocaleString()} outils et dépôts GitHub — recherche manuelle indépendante du pipeline
          </p>
        </div>
      </div>

      {/* Recherche + filtres */}
      <div className="flex flex-col sm:flex-row gap-2 mb-4">
        <div className="flex-1 relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} />
          <input type="text" value={q} onChange={e => { setQ(e.target.value); setPage(1) }}
            placeholder="Rechercher par nom, description, langage..."
            className="w-full pl-9 pr-8 py-2 rounded-xl text-sm"
            style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border)', color: 'var(--text)', outline: 'none' }} />
          {q && <button onClick={() => { setQ(''); setPage(1) }} className="absolute right-2 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }}><X size={14} /></button>}
        </div>
        <select value={sort} onChange={e => { setSort(e.target.value); setPage(1) }}
          className="px-3 py-2 rounded-xl text-sm" style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border)', color: 'var(--text)' }}>
          {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>Trier: {o.label}</option>)}
        </select>
        <select value={verdict} onChange={e => { setVerdict(e.target.value); setPage(1) }}
          className="px-3 py-2 rounded-xl text-sm" style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border)', color: 'var(--text)' }}>
          <option value="">Tous les verdicts</option>
          {VERDICTS.filter(Boolean).map(v => <option key={v} value={v}>{v}</option>)}
        </select>
      </div>

      {/* Résultats */}
      {isLoading ? (
        <PageLoader text="Recherche des outils..." />
      ) : repos.length === 0 ? (
        <div className="surface rounded-xl p-8 text-center" style={{ border: '1px solid var(--border)' }}>
          <BookOpen size={32} className="mx-auto mb-3" style={{ color: 'var(--text-muted)' }} />
          <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>Aucun dépôt trouvé.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {repos.map((r: any, i: number) => (
            <a key={r.name || i} href={r.url || r.html_url || '#'} target="_blank" rel="noopener noreferrer"
              className="surface rounded-xl p-4 hover:border transition-colors flex flex-col gap-2" style={{ border: '1px solid var(--border)' }}>
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <BookOpen size={14} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                  <span className="text-sm font-semibold truncate" style={{ color: 'var(--text)' }}>{r.name || r.full_name}</span>
                </div>
                <ExternalLink size={12} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
              </div>
              {r.description && (
                <p className="text-[11px] leading-relaxed line-clamp-2" style={{ color: 'var(--text-secondary)' }}>{r.description}</p>
              )}
              <div className="flex items-center gap-3 text-[10px] mt-auto pt-1" style={{ color: 'var(--text-muted)' }}>
                <span className="flex items-center gap-1"><Star size={10} />{r.stars ?? '—'}</span>
                {r.language && <span className="px-1.5 py-0.5 rounded-full" style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border-light)' }}>{r.language}</span>}
                {r.security_verdict && (
                  <span className="flex items-center gap-0.5">
                    <Shield size={10} style={{ color: r.security_verdict === 'legitimate' ? '#22c55e' : r.security_verdict === 'malicious' ? '#ef4444' : 'var(--text-muted)' }} />
                    {r.security_verdict}
                  </span>
                )}
              </div>
            </a>
          ))}
        </div>
      )}

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-center gap-1.5 mt-6">
          {Array.from({ length: Math.min(pages, 15) }, (_, i) => {
            const start = page <= 7 ? 1 : page > pages - 7 ? pages - 14 : page - 7
            const p = Math.max(1, start + i)
            if (p > pages) return null
            return (
              <button key={p} onClick={() => setPage(p)}
                className="w-8 h-8 rounded-lg text-xs font-medium transition-colors"
                style={{ background: p === page ? 'var(--amber)' : 'var(--surface-elevated)', color: p === page ? '#fff' : 'var(--text-secondary)', border: p === page ? 'none' : '1px solid var(--border)' }}>
                {p}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
