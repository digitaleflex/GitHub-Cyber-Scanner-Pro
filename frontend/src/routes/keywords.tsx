import { useState, useMemo } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useKeywords, approveKeyword, rejectKeyword, enrichKeywords, enrichOntology, type Keyword } from '../lib/api'
import AdminGuard from '../components/AdminGuard'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import { Check, X, Search, Hash } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/keywords',
  component: () => <AdminGuard><KeywordsPage /></AdminGuard>,
})

const STATUS_LABELS: Record<string, string> = {
  approved: 'Approuvés',
  pending: 'En attente',
  rejected: 'Rejetés',
  all: 'Tous',
}

function KeywordsPage() {
  const [status, setStatus] = useState('approved')
  const [search, setSearch] = useState('')
  const { data, isLoading, error, refetch } = useKeywords(status, 200)
  const qc = useQueryClient()
  const keywords = data?.keywords || []

  const filtered = useMemo(() => {
    if (!search.trim()) return keywords
    const q = search.trim().toLowerCase()
    return keywords.filter(kw =>
      kw.term.toLowerCase().includes(q) ||
      (kw.category_guess || '').toLowerCase().includes(q)
    )
  }, [keywords, search])

  const handleApprove = async (term: string, category?: string) => {
    await approveKeyword(term, category)
    qc.invalidateQueries({ queryKey: ['keywords'] })
  }

  const handleReject = async (term: string) => {
    await rejectKeyword(term)
    qc.invalidateQueries({ queryKey: ['keywords'] })
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
        <h1 className="text-lg font-semibold text-white">Mots-clés découverts</h1>
        {data && (
          <span className="text-xs text-slate-500">
            {keywords.length} mots-clés
          </span>
        )}
      </div>

      <div className="flex flex-wrap gap-2 mb-4 items-center">
        <div className="flex gap-1">
          {Object.entries(STATUS_LABELS).map(([key, label]) => (
            <button key={key} onClick={() => setStatus(key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${status === key ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30' : 'bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:text-white'}`}>
              {label}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <button
            onClick={async () => { await enrichKeywords(); qc.invalidateQueries({ queryKey: ['keywords'] }) }}
            className="text-xs px-3 py-1.5 rounded border border-white/[0.12] text-gray-400 hover:text-white hover:border-white/30 transition-colors font-mono"
            title="Découvrir de nouveaux mots-clés depuis des sources externes"
          >
            + Sources externes
          </button>
          <button
            onClick={async () => { await enrichOntology(); qc.invalidateQueries({ queryKey: ['keywords'] }) }}
            className="text-xs px-3 py-1.5 rounded border border-white/[0.12] text-gray-400 hover:text-white hover:border-white/30 transition-colors font-mono"
            title="Enrichir l'ontologie MITRE ATT&CK / CAPEC"
          >
            + MITRE/CAPEC
          </button>
        </div>
        <div className="relative flex-1 min-w-[180px]">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Filtrer par terme ou categorie..."
            aria-label="Filtrer les mots-clés"
            className="w-full pl-8 pr-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500/40" />
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2" role="status">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-16 bg-white/5 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <div className="glass-card rounded-2xl">
          <ErrorState onRetry={() => refetch()} />
        </div>
      ) : filtered.length === 0 ? (
        <div className="glass-card rounded-2xl">
          <EmptyState
            icon={Hash}
            title={search ? 'Aucun résultat' : 'Aucun mot-clé'}
            description={search ? `Aucun mot-clé ne correspond à "${search}".` : 'Lancez un enrichissement pour découvrir de nouveaux mots-clés.'}
          />
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
          {filtered.map((kw: Keyword) => (
            <div key={kw.term} className="bg-slate-900/60 border border-slate-800 rounded-lg p-3 hover:border-slate-700 transition flex items-center justify-between">
              <div className="min-w-0">
                <span className="text-xs text-white truncate block">{kw.term}</span>
                <span className="text-[10px] text-slate-500">{kw.category_guess || 'Non catégorisé'}</span>
              </div>
              {status === 'pending' && (
                <div className="flex gap-1 ml-2 shrink-0">
                  <button onClick={() => handleApprove(kw.term, kw.category_guess || undefined)} title="Approuver"
                    className="p-1 rounded hover:bg-emerald-500/20 text-slate-500 hover:text-emerald-400 transition"><Check size={12} /></button>
                  <button onClick={() => handleReject(kw.term)} title="Rejeter"
                    className="p-1 rounded hover:bg-rose-500/20 text-slate-500 hover:text-rose-400 transition"><X size={12} /></button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
