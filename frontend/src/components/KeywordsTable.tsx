import { useState } from 'react'
import { useKeywords, approveKeyword, rejectKeyword, type Keyword } from '../lib/api'
import { useQueryClient } from '@tanstack/react-query'

const TABS = [
  { key: 'pending', label: 'En attente' },
  { key: 'approved', label: 'Approuvés' },
  { key: 'rejected', label: 'Rejetés' },
  { key: 'all', label: 'Tous' },
]

const STATUS_CLASSES: Record<string, string> = {
  pending: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  approved: 'bg-neon-green/10 text-neon-green border-neon-green/20',
  rejected: 'bg-neon-red/10 text-neon-red border-neon-red/20',
}

export default function KeywordsTable() {
  const [tab, setTab] = useState('pending')
  const [categoryInput, setCategoryInput] = useState<Record<string, string>>({})

  const qc = useQueryClient()
  const { data, isLoading, error } = useKeywords(tab)

  const keywords = data?.keywords ?? []

  const handleApprove = async (term: string) => {
    const cat = categoryInput[term] || undefined
    await approveKeyword(term, cat)
    qc.invalidateQueries({ queryKey: ['keywords'] })
  }

  const handleReject = async (term: string) => {
    await rejectKeyword(term)
    qc.invalidateQueries({ queryKey: ['keywords'] })
  }

  return (
    <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan hover:neon-glow-cyan transition-all duration-300">
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider font-cyber">
          Mots-clés & Ontologie
        </h2>
        {data && (
          <span className="text-xs text-gray-600 font-mono">
            {keywords.length} mots-clés
          </span>
        )}
      </div>

      <div className="flex items-center gap-2 mb-4 flex-wrap">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`text-xs px-3 py-1 rounded-full border transition-colors font-mono ${
              tab === t.key
                ? 'bg-white/[0.06] text-white border-white/20'
                : 'text-gray-600 border-white/[0.06] hover:text-gray-400'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3" role="status">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-10 bg-white/5 rounded animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <p className="text-neon-red text-sm py-4 text-center font-mono">Erreur de chargement</p>
      ) : keywords.length === 0 ? (
        <p className="text-gray-600 text-sm py-8 text-center font-mono">Aucun mot-clé</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm" role="table">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <th className="text-left py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider">Terme</th>
                <th className="text-center py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider w-20">Score</th>
                <th className="text-center py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider w-20">Sources</th>
                <th className="text-center py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider w-28">Statut</th>
                <th className="text-left py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider max-md:hidden">Catégorie</th>
                {tab === 'pending' && (
                  <th className="text-center py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider w-48">Actions</th>
                )}
              </tr>
            </thead>
            <tbody>
              {keywords.map((kw: Keyword) => (
                <tr
                  key={kw.term}
                  className="border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"
                >
                  <td className="py-2.5 px-2 font-medium text-white/80 font-mono text-xs">{kw.term}</td>
                  <td className="py-2.5 px-2 text-center text-white/70 font-mono text-xs">{kw.score.toFixed(2)}</td>
                  <td className="py-2.5 px-2 text-center text-gray-500 font-mono text-xs">{kw.sources}</td>
                  <td className="py-2.5 px-2 text-center">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium border font-mono ${STATUS_CLASSES[kw.status] ?? 'bg-gray-500/10 text-gray-400 border-gray-500/20'}`}>
                      {kw.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-2 max-md:hidden">
                    {kw.category_guess ? (
                      <span className="text-gray-400 font-mono text-xs">{kw.category_guess}</span>
                    ) : (
                      <span className="text-gray-700">-</span>
                    )}
                  </td>
                  {tab === 'pending' && (
                    <td className="py-2.5 px-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <input
                          type="text"
                          placeholder="Catégorie..."
                          value={categoryInput[kw.term] ?? kw.category_guess ?? ''}
                          onChange={(e) => setCategoryInput(prev => ({ ...prev, [kw.term]: e.target.value }))}
                          className="w-24 px-2 py-1 bg-white/[0.05] border border-white/[0.1] rounded text-xs text-white placeholder-gray-700 focus:outline-none focus-visible:ring-1 focus-visible:ring-neon-cyan/50 font-mono"
                        />
                        <button
                          onClick={() => handleApprove(kw.term)}
                          className="px-2 py-1 rounded text-xs font-mono bg-neon-green/10 text-neon-green border border-neon-green/20 hover:bg-neon-green/20 transition-colors"
                        >
                          ✓
                        </button>
                        <button
                          onClick={() => handleReject(kw.term)}
                          className="px-2 py-1 rounded text-xs font-mono bg-neon-red/10 text-neon-red border border-neon-red/20 hover:bg-neon-red/20 transition-colors"
                        >
                          ✗
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
