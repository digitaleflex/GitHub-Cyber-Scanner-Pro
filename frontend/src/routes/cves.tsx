import { useState } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useCves } from '../lib/api'
import AdminGuard from '../components/AdminGuard'
import { Search, Shield, ChevronLeft, ChevronRight } from 'lucide-react'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/cves',
  component: () => <AdminGuard><CvesPage /></AdminGuard>,
})

function CvesPage() {
  const [q, setQ] = useState('')
  const [severity, setSeverity] = useState('')
  const [page, setPage] = useState(1)
  const { data, isLoading } = useCves(q, severity, page)

  return (
    <div className="max-w-5xl mx-auto">
      <h2 className="text-lg font-semibold text-white mb-4">Base CVE</h2>
      <div className="flex gap-2 mb-4">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input value={q} onChange={e => { setQ(e.target.value); setPage(1) }}
            placeholder="CVE-2024-..." className="w-full pl-9 pr-3 py-2 bg-slate-900/80 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:ring-1 focus:ring-indigo-500/50" />
        </div>
        <select value={severity} onChange={e => { setSeverity(e.target.value); setPage(1) }}
          className="px-3 py-2 bg-slate-900/80 border border-slate-700 rounded-lg text-xs text-white">
          <option value="">Toutes</option>
          {['CRITICAL','HIGH','MEDIUM','LOW'].map(s => <option key={s}>{s}</option>)}
        </select>
      </div>

      {isLoading ? <p className="text-slate-500 text-sm">Chargement...</p> : data ? (
        <div className="space-y-2">
          {data.cves?.map((cve, i) => (
            <div key={i} className="bg-slate-900/60 border border-slate-800 rounded-lg p-3 hover:border-slate-700 transition">
              <div className="flex items-center gap-2 mb-1">
                <Shield size={13} className={
                  cve.severity === 'CRITICAL' ? 'text-rose-400' :
                  cve.severity === 'HIGH' ? 'text-amber-400' : 'text-slate-500'
                } />
                <span className="text-xs font-mono text-indigo-400">{cve.cve_id}</span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                  cve.severity === 'CRITICAL' ? 'bg-rose-500/10 text-rose-400' :
                  cve.severity === 'HIGH' ? 'bg-amber-500/10 text-amber-400' :
                  'bg-slate-700/50 text-slate-400'
                }`}>{cve.severity}</span>
                {cve.cvss_score && <span className="text-[10px] text-slate-500">CVSS {cve.cvss_score}</span>}
              </div>
              <p className="text-xs text-slate-400 leading-relaxed line-clamp-2">{cve.description}</p>
            </div>
          ))}
          {data.pages > 1 && (
            <div className="flex items-center justify-center gap-3 mt-4">
              <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page===1}
                className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-slate-300 disabled:opacity-30"><ChevronLeft size={14} /></button>
              <span className="text-xs text-slate-500">{page}/{data.pages}</span>
              <button onClick={() => setPage(p => Math.min(data.pages, p+1))} disabled={page>=data.pages}
                className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-slate-300 disabled:opacity-30"><ChevronRight size={14} /></button>
            </div>
          )}
        </div>
      ) : null}
    </div>
  )
}
