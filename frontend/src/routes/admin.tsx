import { useState, useEffect } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Settings, RefreshCw, Shield, Database, FileText, Bug, Download, Play, CheckCircle2, XCircle, Brain, Lock, LogOut, Activity, LayoutDashboard, ArrowLeft } from 'lucide-react'

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
  const [section, setSection] = useState('dashboard')

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

  const sidebarItems = [
    { key: 'dashboard', label: 'Tableau de bord', icon: <LayoutDashboard size={13} /> },
    { key: 'operations', label: 'Operations', icon: <Play size={13} /> },
    { key: 'exports', label: 'Exports', icon: <Download size={13} /> },
    { key: 'status', label: 'Status systeme', icon: <Activity size={13} /> },
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
    <div className="flex gap-5 -mx-4 sm:-mx-6 lg:-mx-8 min-h-[calc(100vh-12rem)]">
      {/* Sidebar */}
      <aside className="hidden sm:flex flex-col w-48 shrink-0 glass border-r border-white/[0.03] px-3 py-4">
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-5 h-5 rounded-md bg-amber-500/20 flex items-center justify-center"><Settings size={11} className="text-amber-400" /></div>
            <span className="text-xs font-semibold text-white">Admin</span>
          </div>
          <p className="text-[9px] text-slate-500">Decision Engine</p>
        </div>

        <nav className="flex flex-col gap-0.5 flex-1">
          {sidebarItems.map(item => (
            <button key={item.key} onClick={() => setSection(item.key)}
              className={`flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs transition text-left ${
                section === item.key ? 'bg-amber-500/10 text-amber-400' : 'text-slate-400 hover:text-white hover:bg-white/5'
              }`}>
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>

        <div className="pt-3 border-t border-white/[0.04] space-y-1">
          <Link to="/" className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg text-xs text-slate-500 hover:text-white hover:bg-white/5 transition">
            <ArrowLeft size={11} /> Retour au site
          </Link>
          <button onClick={logout} className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg text-xs text-slate-500 hover:text-rose-400 hover:bg-rose-500/5 transition w-full text-left">
            <LogOut size={11} /> Deconnexion
          </button>
        </div>
      </aside>

      {/* Mobile section tabs */}
      <div className="sm:hidden w-full px-4 pt-4">
        <div className="flex gap-1 mb-4 overflow-x-auto pb-1">
          {sidebarItems.map(item => (
            <button key={item.key} onClick={() => setSection(item.key)}
              className={`shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                section === item.key ? 'bg-amber-500/10 text-amber-400' : 'glass text-slate-500'
              }`}>
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main content */}
      <main className="flex-1 min-w-0 py-4 pr-4 sm:pr-6 lg:pr-8 pl-4 sm:pl-0">
        <div className="sm:hidden mb-4">
          <Link to="/" className="text-xs text-slate-500 hover:text-white flex items-center gap-1"><ArrowLeft size={11} /> Retour</Link>
        </div>

        {section === 'dashboard' && (
          <>
            <h1 className="text-lg font-semibold text-white mb-4">Tableau de bord</h1>
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
                <span className="inline-block w-2 h-2 rounded-full mr-1.5" style={{ background: hfStatus?.available ? '#34d399' : '#f43f5e' }} />
                <span className="text-xs text-slate-300">{hfStatus?.available ? 'OK' : 'OFF'}</span>
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
          </>
        )}

        {section === 'operations' && (
          <>
            <h1 className="text-lg font-semibold text-white mb-4">Operations</h1>
            <div className="space-y-2">
              {ops.map(op => {
                const st = statuses[op.key]
                return (
                  <div key={op.key} className="glass-card rounded-xl p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <span className="text-slate-400 shrink-0">{op.icon}</span>
                        <div className="min-w-0">
                          <span className="text-sm text-slate-200 font-medium">{op.label}</span>
                          <p className="text-[10px] text-slate-500">{op.desc}</p>
                        </div>
                      </div>
                      <button onClick={() => run(op.key, op.url)} disabled={st?.running}
                        className="shrink-0 px-4 py-2 rounded-lg bg-amber-500/10 text-amber-400 text-xs font-medium hover:bg-amber-500/20 disabled:opacity-40 transition border border-amber-500/20">
                        {st?.running ? 'En cours...' : 'Executer'}
                      </button>
                    </div>
                    {st?.result && <div className="mt-2 flex items-start gap-2 text-[10px]"><CheckCircle2 size={10} className="text-emerald-400 mt-0.5 shrink-0" /><span className="text-emerald-400">{st.result}</span></div>}
                    {st?.error && <div className="mt-2 flex items-start gap-2 text-[10px]"><XCircle size={10} className="text-rose-400 mt-0.5 shrink-0" /><span className="text-rose-400">{st.error}</span></div>}
                  </div>
                )
              })}
            </div>
          </>
        )}

        {section === 'exports' && (
          <>
            <h1 className="text-lg font-semibold text-white mb-4">Exports</h1>
            <div className="glass-card rounded-2xl p-5">
              <a href="/api/download" className="inline-flex items-center gap-2 px-4 py-2 glass rounded-xl text-sm text-slate-400 hover:text-white transition">
                <Download size={14} /> Telecharger Excel
              </a>
            </div>
          </>
        )}

        {section === 'status' && (
          <>
            <h1 className="text-lg font-semibold text-white mb-4">Status systeme</h1>
            <div className="glass-card rounded-2xl p-5 space-y-3">
              <div className="flex justify-between text-sm"><span className="text-slate-500">Decision Engine</span><span className="text-emerald-400 flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Actif</span></div>
              <div className="flex justify-between text-sm"><span className="text-slate-500">NVD Backfill</span><span className={cveStatus?.running ? 'text-amber-400' : 'text-emerald-400'}>{cveStatus?.running ? 'En cours' : 'A jour'}</span></div>
              <div className="flex justify-between text-sm"><span className="text-slate-500">HF API</span><span className={hfStatus?.available ? 'text-emerald-400' : 'text-rose-400'}>{hfStatus?.available ? 'Connectee' : 'Absente'}</span></div>
              <div className="flex justify-between text-sm"><span className="text-slate-500">Exploit-DB</span><span className="text-slate-400">{exploitStats?.total_exploits?.toLocaleString() || '?'} exploits</span></div>
              <div className="flex justify-between text-sm"><span className="text-slate-500">PostgreSQL</span><span className="text-emerald-400 flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Connectee</span></div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
