import { useState, useEffect } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Settings, RefreshCw, Shield, Database, FileText, Bug, Download, Play, CheckCircle2, XCircle, Brain, Lock, LogOut } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/admin', component: AdminPage })

interface OpStatus { running: boolean; result: string | null; error: string | null }

function getAuthHeaders(): Record<string, string> {
  const pwd = sessionStorage.getItem('admin_password') || ''
  if (!pwd) return {}
  return { 'Authorization': `Basic ${btoa(`admin:${pwd}`)}` }
}

function AdminPage() {
  const qc = useQueryClient()
  const [authenticated, setAuthenticated] = useState(false)
  const [password, setPassword] = useState('')
  const [authError, setAuthError] = useState(false)
  const [statuses, setStatuses] = useState<Record<string, OpStatus>>({})

  useEffect(() => {
    const stored = sessionStorage.getItem('admin_password')
    if (stored) { setPassword(stored); setAuthenticated(true) }
  }, [])

  const login = async () => {
    const token = btoa(`admin:${password}`)
    try {
      const r = await fetch('/api/scan', { method: 'POST', headers: { 'Authorization': `Basic ${token}` } })
      if (r.ok || r.status === 409) { sessionStorage.setItem('admin_password', password); setAuthenticated(true); setAuthError(false) }
      else setAuthError(true)
    } catch { setAuthError(true) }
  }

  const logout = () => { sessionStorage.removeItem('admin_password'); setAuthenticated(false); setPassword('') }

  const { data: cveStatus, refetch: refetchCve } = useQuery({
    queryKey: ['cve-status'], queryFn: () => fetch('/api/cve-status').then(r => r.json()), staleTime: 10_000, enabled: authenticated,
  })
  const { data: hfStatus } = useQuery({
    queryKey: ['hf-status'], queryFn: () => fetch('/api/hf/status').then(r => r.json()), staleTime: 30_000, enabled: authenticated,
  })
  const { data: exploitStats } = useQuery({
    queryKey: ['exploit-stats'], queryFn: () => fetch('/api/exploits/stats').then(r => r.json()), staleTime: 60_000, enabled: authenticated,
  })
  const { data: dbStats } = useQuery({
    queryKey: ['db-stats'], queryFn: () => fetch('/api/stats').then(r => r.json()), staleTime: 30_000, enabled: authenticated,
  })

  const run = async (key: string, url: string) => {
    setStatuses(prev => ({ ...prev, [key]: { running: true, result: null, error: null } }))
    try {
      const headers = getAuthHeaders()
      const r = await fetch(url, { method: 'POST', headers })
      const text = await r.text()
      let d: any = {}
      try { d = JSON.parse(text) } catch { d = { message: text.slice(0, 100) } }
      if (r.ok) {
        setStatuses(prev => ({ ...prev, [key]: { running: false, result: JSON.stringify(d).slice(0, 150), error: null } }))
        qc.invalidateQueries(); refetchCve()
      } else {
        setStatuses(prev => ({ ...prev, [key]: { running: false, result: null, error: `HTTP ${r.status}` } }))
      }
    } catch (e: any) {
      setStatuses(prev => ({ ...prev, [key]: { running: false, result: null, error: e.message } }))
    }
  }

  const ops = [
    { key: 'scan', label: 'Scan GitHub', desc: 'Scan manuel des repos', icon: <Play size={14} />, url: '/api/scan' },
    { key: 'cve', label: 'Import CVE NVD', desc: 'Import complet depuis NVD', icon: <Database size={14} />, url: '/api/import-cve' },
    { key: 'backfill', label: 'Backfill Severite', desc: 'Remplir severity/CVSS', icon: <Shield size={14} />, url: '/api/cves/backfill-severity' },
    { key: 'exploit', label: 'Refresh Exploits', desc: 'MAJ Exploit-DB', icon: <Bug size={14} />, url: '/api/exploits/refresh' },
    { key: 'readme', label: 'Backfill README', desc: 'Chunks RAG', icon: <FileText size={14} />, url: '/api/tools/backfill-readmes?limit=50' },
    { key: 'vitality', label: 'Recalcul Vitalite', desc: 'Scores qualite repos', icon: <RefreshCw size={14} />, url: '/api/tools/recompute-vitality' },
    { key: 'guard', label: 'Content Safety', desc: 'Scan Granite Guardian', icon: <Brain size={14} />, url: '/api/hf/guard?limit=20' },
  ]

  if (!authenticated) return (
    <div className="max-w-sm mx-auto py-24 animate-fade text-center">
      <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
        <Lock size={24} className="text-amber-400" />
      </div>
      <h1 className="text-lg font-semibold text-white mb-1">Administration</h1>
      <p className="text-sm text-slate-500 mb-5">Mot de passe administrateur.</p>
      <input type="password" value={password} onChange={e => { setPassword(e.target.value); setAuthError(false) }}
        onKeyDown={e => e.key === 'Enter' && login()}
        placeholder="Mot de passe..."
        className="w-full glass rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-amber-500/30 mb-3" />
      {authError && <p className="text-xs text-rose-400 mb-3">Mot de passe incorrect.</p>}
      <button onClick={login} disabled={!password}
        className="w-full px-4 py-3 rounded-xl bg-amber-500 text-white text-sm font-medium hover:bg-amber-400 disabled:opacity-40 transition">
        Connexion
      </button>
    </div>
  )

  return (
    <div className="max-w-3xl mx-auto py-4 sm:py-8 animate-fade">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <Settings size={18} className="text-amber-400" />
          <h1 className="text-xl sm:text-2xl font-semibold text-white">Administration</h1>
        </div>
        <button onClick={logout} className="text-[10px] text-slate-500 hover:text-rose-400 transition flex items-center gap-1">
          <LogOut size={11} /> Deconnexion
        </button>
      </div>
      <p className="text-sm text-slate-500 mb-6">Controles, imports, maintenance du Decision Engine.</p>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div className="glass-card rounded-xl p-4">
          <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">CVE Import</p>
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${cveStatus?.running ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400'}`} />
            <span className="text-xs text-slate-300">{cveStatus?.running ? 'En cours' : 'Pret'}</span>
          </div>
          {cveStatus?.imported > 0 && <p className="text-[10px] text-slate-500 mt-1">{cveStatus.imported.toLocaleString()} CVEs</p>}
        </div>
        <div className="glass-card rounded-xl p-4">
          <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">HF API</p>
          <span className={`inline-block w-2 h-2 rounded-full ${hfStatus?.available ? 'bg-emerald-400' : 'bg-rose-400'}`} />
          <span className="text-xs text-slate-300 ml-1.5">{hfStatus?.available ? 'OK' : 'OFF'}</span>
        </div>
        <div className="glass-card rounded-xl p-4">
          <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">Exploit-DB</p>
          <p className="text-xs text-slate-300">{exploitStats?.total_exploits?.toLocaleString() || '?'} exploits</p>
        </div>
        <div className="glass-card rounded-xl p-4">
          <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">Base</p>
          <p className="text-xs text-slate-300">{dbStats?.total_repos?.toLocaleString() || '?'} repos</p>
          <p className="text-[10px] text-slate-500">{dbStats?.total_cves?.toLocaleString() || '?'} CVEs</p>
        </div>
      </div>

      <div className="glass-card rounded-2xl p-5">
        <h2 className="text-sm font-semibold text-white mb-4">Operations</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {ops.map(op => {
            const st = statuses[op.key]
            return (
              <div key={op.key} className="glass rounded-xl p-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-slate-400 shrink-0">{op.icon}</span>
                    <div className="min-w-0">
                      <span className="text-xs text-slate-200 font-medium">{op.label}</span>
                      <p className="text-[10px] text-slate-500 line-clamp-1">{op.desc}</p>
                    </div>
                  </div>
                  <button onClick={() => run(op.key, op.url)} disabled={st?.running}
                    className="shrink-0 px-3 py-1.5 glass rounded-lg text-[10px] text-slate-400 hover:text-white disabled:opacity-40 transition">
                    {st?.running ? '...' : 'Executer'}
                  </button>
                </div>
                {st?.result && <div className="mt-1.5 flex items-start gap-1.5 text-[10px]"><CheckCircle2 size={10} className="text-emerald-400 mt-0.5 shrink-0" /><span className="text-emerald-400">{st.result}</span></div>}
                {st?.error && <div className="mt-1.5 flex items-start gap-1.5 text-[10px]"><XCircle size={10} className="text-rose-400 mt-0.5 shrink-0" /><span className="text-rose-400">{st.error}</span></div>}
              </div>
            )
          })}
        </div>
      </div>

      <div className="glass-card rounded-2xl p-5 mt-4">
        <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2"><Download size={14} className="text-slate-500" /> Exports</h2>
        <div className="flex flex-wrap gap-2">
          <a href="/api/download" className="px-4 py-2 glass rounded-xl text-xs text-slate-400 hover:text-white transition">Excel</a>
        </div>
      </div>
    </div>
  )
}
