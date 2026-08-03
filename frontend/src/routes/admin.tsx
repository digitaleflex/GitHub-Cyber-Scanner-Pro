import { useState } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Settings, RefreshCw, Shield, Database, FileText, Bug, Download, Play, CheckCircle2, XCircle, Brain } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/admin', component: AdminPage })

interface OpStatus { running: boolean; result: string | null; error: string | null }

function AdminPage() {
  const qc = useQueryClient()
  const [statuses, setStatuses] = useState<Record<string, OpStatus>>({})

  const { data: cveStatus, refetch: refetchCve } = useQuery({
    queryKey: ['cve-status'], queryFn: () => fetch('/api/cve-status').then(r => r.json()), staleTime: 10_000,
  })

  const { data: hfStatus } = useQuery({
    queryKey: ['hf-status'], queryFn: () => fetch('/api/hf/status').then(r => r.json()), staleTime: 30_000,
  })

  const { data: exploitStats } = useQuery({
    queryKey: ['exploit-stats'], queryFn: () => fetch('/api/exploits/stats').then(r => r.json()), staleTime: 60_000,
  })

  const run = async (key: string, url: string, method = 'POST') => {
    setStatuses(prev => ({ ...prev, [key]: { running: true, result: null, error: null } }))
    try {
      const r = await fetch(url, { method })
      const d = await r.json()
      setStatuses(prev => ({ ...prev, [key]: { running: false, result: JSON.stringify(d).slice(0, 120), error: null } }))
      if (r.ok) { qc.invalidateQueries(); refetchCve() }
    } catch (e: any) {
      setStatuses(prev => ({ ...prev, [key]: { running: false, result: null, error: e.message } }))
    }
  }

  const ops = [
    { key: 'scan', label: 'Scan GitHub', desc: 'Lancer un scan manuel', icon: <Play size={14} />, url: '/api/scan', method: 'POST' },
    { key: 'cve', label: 'Import CVE', desc: 'Importer depuis NVD', icon: <Database size={14} />, url: '/api/import-cve', method: 'POST' },
    { key: 'backfill', label: 'Backfill Sévérité', desc: 'Remplir severity/CVSS', icon: <Shield size={14} />, url: '/api/cves/backfill-severity', method: 'POST' },
    { key: 'exploit', label: 'Refresh Exploits', desc: 'Màj Exploit-DB', icon: <Bug size={14} />, url: '/api/exploits/refresh', method: 'POST' },
    { key: 'readme', label: 'Backfill README', desc: 'RAG chunks', icon: <FileText size={14} />, url: '/api/tools/backfill-readmes?limit=50', method: 'POST' },
    { key: 'vitality', label: 'Recalcul Vitalité', desc: 'Scores qualité outils', icon: <RefreshCw size={14} />, url: '/api/tools/recompute-vitality', method: 'POST' },
    { key: 'guard', label: 'Content Safety', desc: 'Scan Granite Guardian', icon: <Brain size={14} />, url: '/api/hf/guard?limit=20', method: 'POST' },
    { key: 'export', label: 'Télécharger Excel', desc: 'Export données', icon: <Download size={14} />, url: '/api/download', method: 'GET' },
  ]

  return (
    <div className="max-w-3xl mx-auto py-4 sm:py-8 animate-fade">
      <div className="flex items-center gap-2 mb-1">
        <Settings size={18} className="text-amber-400" />
        <h1 className="text-xl sm:text-2xl font-semibold text-white">Administration</h1>
      </div>
      <p className="text-sm text-slate-500 mb-6">Controles, imports, et maintenance du Decision Engine.</p>

      {/* Status cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        <div className="glass-card rounded-xl p-4">
          <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">CVE Import</p>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${cveStatus?.running ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400'}`} />
            <span className="text-xs text-slate-300">{cveStatus?.running ? 'En cours' : 'Pret'}</span>
          </div>
          {cveStatus?.imported > 0 && <p className="text-[10px] text-slate-500 mt-1">{cveStatus.imported.toLocaleString()} CVEs traitees</p>}
        </div>
        <div className="glass-card rounded-xl p-4">
          <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">HF API</p>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${hfStatus?.available ? 'bg-emerald-400' : 'bg-rose-400'}`} />
            <span className="text-xs text-slate-300">{hfStatus?.available ? 'Connectee' : 'Absente'}</span>
          </div>
          {hfStatus?.models_available && <p className="text-[10px] text-slate-500 mt-1">{hfStatus.models_available} modeles</p>}
        </div>
        <div className="glass-card rounded-xl p-4">
          <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">Exploit-DB</p>
          <p className="text-xs text-slate-300">{exploitStats?.total_exploits?.toLocaleString() || '?'} exploits</p>
          <p className="text-[10px] text-slate-500">{exploitStats?.cves_mapped?.toLocaleString() || '?'} CVEs liees</p>
        </div>
      </div>

      {/* Operation buttons */}
      <div className="glass-card rounded-2xl p-5">
        <h2 className="text-sm font-semibold text-white mb-4">Operations</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {ops.map(op => {
            const st = statuses[op.key]
            return (
              <div key={op.key} className="glass rounded-xl p-3">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400">{op.icon}</span>
                    <div>
                      <span className="text-xs text-slate-200 font-medium">{op.label}</span>
                      <p className="text-[10px] text-slate-500">{op.desc}</p>
                    </div>
                  </div>
                  {op.key === 'export' ? (
                    <a href={op.url} className="shrink-0 px-3 py-1.5 glass rounded-lg text-[10px] text-slate-400 hover:text-white transition">
                      Telecharger
                    </a>
                  ) : (
                    <button onClick={() => run(op.key, op.url, op.method)} disabled={st?.running}
                      className="shrink-0 px-3 py-1.5 glass rounded-lg text-[10px] text-slate-400 hover:text-white disabled:opacity-40 transition">
                      {st?.running ? '...' : 'Executer'}
                    </button>
                  )}
                </div>
                {st?.result && (
                  <div className="mt-1.5 flex items-start gap-1.5 text-[10px]">
                    <CheckCircle2 size={10} className="text-emerald-400 mt-0.5 shrink-0" />
                    <span className="text-emerald-400">{st.result}</span>
                  </div>
                )}
                {st?.error && (
                  <div className="mt-1.5 flex items-start gap-1.5 text-[10px]">
                    <XCircle size={10} className="text-rose-400 mt-0.5 shrink-0" />
                    <span className="text-rose-400">{st.error}</span>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
