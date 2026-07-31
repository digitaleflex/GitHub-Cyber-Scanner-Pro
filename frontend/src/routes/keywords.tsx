import { useState } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useKeywords, approveKeyword, rejectKeyword } from '../lib/api'
import AdminGuard from '../components/AdminGuard'
import { Check, X } from 'lucide-react'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/keywords',
  component: () => <AdminGuard><KeywordsPage /></AdminGuard>,
})

function KeywordsPage() {
  const [status, setStatus] = useState('approved')
  const { data, isLoading, refetch } = useKeywords(status, 200)
  const keywords = data?.keywords || []

  const handleApprove = async (term: string) => {
    await approveKeyword(term)
    refetch()
  }

  const handleReject = async (term: string) => {
    await rejectKeyword(term)
    refetch()
  }

  return (
    <div className="max-w-5xl mx-auto">
      <h2 className="text-lg font-semibold text-white mb-4">Mots-clés découverts</h2>
      <div className="flex gap-1 mb-4">
        {['approved', 'pending'].map(s => (
          <button key={s} onClick={() => setStatus(s)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${status === s ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30' : 'bg-slate-800/50 text-slate-400 border border-slate-700/50 hover:text-white'}`}>
            {s === 'approved' ? 'Approuvés' : 'En attente'}
          </button>
        ))}
      </div>

      {isLoading ? <p className="text-slate-500 text-sm">Chargement...</p> : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
          {keywords.map((kw, i) => (
            <div key={i} className="bg-slate-900/60 border border-slate-800 rounded-lg p-3 hover:border-slate-700 transition flex items-center justify-between">
              <div className="min-w-0">
                <span className="text-xs text-white truncate block">{kw.term}</span>
                <span className="text-[10px] text-slate-500">{kw.category_guess}</span>
              </div>
              {status === 'pending' && (
                <div className="flex gap-1 ml-2 shrink-0">
                  <button onClick={() => handleApprove(kw.term)}
                    className="p-1 rounded hover:bg-emerald-500/20 text-slate-500 hover:text-emerald-400 transition"><Check size={12} /></button>
                  <button onClick={() => handleReject(kw.term)}
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
