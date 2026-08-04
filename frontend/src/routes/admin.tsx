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
    { key: 'backfill', label: 'Backfill Sévérité', desc: 'Remplir severity/CVSS', icon: <Shield size={14} />, url: '/api/cves/backfill-severity' },
    { key: 'exploit', label: 'Refresh Exploits', desc: 'MAJ Exploit-DB', icon: <Bug size={14} />, url: '/api/exploits/refresh' },
    { key: 'readme', label: 'Backfill README', desc: 'Chunks RAG', icon: <FileText size={14} />, url: '/api/tools/backfill-readmes?limit=50' },
    { key: 'vitality', label: 'Recalcul Vitalité', desc: 'Scores qualité repos', icon: <RefreshCw size={14} />, url: '/api/tools/recompute-vitality' },
    { key: 'guard', label: 'Content Safety', desc: 'Scan Granite Guardian', icon: <Brain size={14} />, url: '/api/hf/guard?limit=20' },
  ]

  const sidebarItems = [
    { key: 'dashboard', label: 'Tableau de bord', icon: <LayoutDashboard size={13} /> },
    { key: 'operations', label: 'Opérations', icon: <Play size={13} /> },
    { key: 'exports', label: 'Exports', icon: <Download size={13} /> },
    { key: 'status', label: 'Statut système', icon: <Activity size={13} /> },
  ]

  if (!authenticated) return (
    <div className="max-w-sm mx-auto py-24 animate-fade text-center">
      <div className="w-14 h-14 mx-auto mb-4 rounded-2xl flex items-center justify-center" style={{ background: 'var(--mission-light)', border: '1px solid var(--mission)' }}>
        <Lock size={24} style={{ color: 'var(--mission)' }} />
      </div>
      <h1 className="h2 mb-1" style={{ color: 'var(--text)' }}>Administration</h1>
      <p className="body-sm text-secondary mb-5">Mot de passe administrateur.</p>
      <input type="password" value={password} onChange={e => { setPassword(e.target.value); setAuthError(false) }}
        onKeyDown={e => e.key === 'Enter' && login()}
        placeholder="Mot de passe..."
        className="w-full rounded-xl px-4 py-3 text-sm mb-3 ring-brand"
        style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }} />
      {authError && <p className="text-xs mb-3" style={{ color: 'var(--critical-text)' }}>Mot de passe incorrect.</p>}
      <button onClick={login} disabled={!password} className="btn-primary w-full justify-center">
        Connexion
      </button>
    </div>
  )

  return (
    <div className="flex gap-5 -mx-4 sm:-mx-6 lg:-mx-8 min-h-[calc(100vh-12rem)]">
      {/* Sidebar */}
      <aside className="hidden sm:flex flex-col w-48 shrink-0 px-3 py-4" style={{ background: 'var(--surface)', borderRight: '1px solid var(--border)' }}>
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-5 h-5 rounded-md flex items-center justify-center" style={{ background: 'var(--mission-light)' }}>
              <Settings size={11} style={{ color: 'var(--mission)' }} />
            </div>
            <span className="text-xs font-semibold" style={{ color: 'var(--text)' }}>Admin</span>
          </div>
          <p className="text-[9px] text-muted">Decision Engine</p>
        </div>

        <nav className="flex flex-col gap-0.5 flex-1">
          {sidebarItems.map(item => (
            <button key={item.key} onClick={() => setSection(item.key)}
              className="flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs transition-all text-left"
              style={{
                color: section === item.key ? 'var(--mission-text)' : 'var(--text-secondary)',
                background: section === item.key ? 'var(--mission-light)' : 'transparent',
                border: section === item.key ? '1px solid var(--mission)' : '1px solid transparent',
              }}>
              {item.icon}
              {item.label}
            </button>
          ))}
        </nav>

        <div className="pt-3 space-y-1" style={{ borderTop: '1px solid var(--border)' }}>
          <Link to="/" className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg text-xs transition-colors" style={{ color: 'var(--text-muted)' }}>
            <ArrowLeft size={11} /> Retour au site
          </Link>
          <button onClick={logout} className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg text-xs transition-colors w-full text-left" style={{ color: 'var(--text-muted)' }}>
            <LogOut size={11} /> Déconnexion
          </button>
        </div>
      </aside>

      {/* Mobile section tabs */}
      <div className="sm:hidden w-full px-4 pt-4">
        <div className="flex gap-1 mb-4 overflow-x-auto pb-1">
          {sidebarItems.map(item => (
            <button key={item.key} onClick={() => setSection(item.key)}
              className="shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all"
              style={{
                background: section === item.key ? 'var(--mission-light)' : 'var(--surface)',
                color: section === item.key ? 'var(--mission-text)' : 'var(--text-muted)',
                borderColor: section === item.key ? 'var(--mission)' : 'var(--border)',
              }}>
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main content */}
      <main className="flex-1 min-w-0 py-4 pr-4 sm:pr-6 lg:pr-8 pl-4 sm:pl-0">
        <div className="sm:hidden mb-4">
          <Link to="/" className="text-xs flex items-center gap-1" style={{ color: 'var(--text-muted)' }}><ArrowLeft size={11} /> Retour</Link>
        </div>

        {section === 'dashboard' && (
          <>
            <h1 className="h2 mb-4" style={{ color: 'var(--text)' }}>Tableau de bord</h1>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
              <div className="surface rounded-xl p-4" style={{ border: '1px solid var(--border)' }}>
                <p className="caption mb-1" style={{ color: 'var(--brand-text)' }}>CVE Import</p>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ background: cveStatus?.running ? 'var(--mission)' : 'var(--success)' }} />
                  <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{cveStatus?.running ? 'En cours' : 'Prêt'}</span>
                </div>
                {cveStatus?.imported > 0 && <p className="text-[10px] text-muted mt-1">{cveStatus.imported.toLocaleString()} CVEs</p>}
              </div>
              <div className="surface rounded-xl p-4" style={{ border: '1px solid var(--border)' }}>
                <p className="caption mb-1" style={{ color: 'var(--brand-text)' }}>HF API</p>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ background: hfStatus?.available ? 'var(--success)' : 'var(--critical)' }} />
                  <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{hfStatus?.available ? 'OK' : 'OFF'}</span>
                </div>
              </div>
              <div className="surface rounded-xl p-4" style={{ border: '1px solid var(--border)' }}>
                <p className="caption mb-1" style={{ color: 'var(--brand-text)' }}>Exploit-DB</p>
                <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{exploitStats?.total_exploits?.toLocaleString() || '?'} exploits</p>
              </div>
              <div className="surface rounded-xl p-4" style={{ border: '1px solid var(--border)' }}>
                <p className="caption mb-1" style={{ color: 'var(--brand-text)' }}>Base</p>
                <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>{dbStats?.total_repos?.toLocaleString() || '?'} repos</p>
                <p className="text-[10px] text-muted">{dbStats?.total_cves?.toLocaleString() || '?'} CVEs</p>
              </div>
            </div>
          </>
        )}

        {section === 'operations' && (
          <>
            <h1 className="h2 mb-4" style={{ color: 'var(--text)' }}>Opérations</h1>
            <div className="space-y-2">
              {ops.map(op => {
                const st = statuses[op.key]
                return (
                  <div key={op.key} className="surface rounded-xl p-4" style={{ border: '1px solid var(--border)' }}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <span style={{ color: 'var(--text-secondary)' }} className="shrink-0">{op.icon}</span>
                        <div className="min-w-0">
                          <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>{op.label}</span>
                          <p className="text-[10px] text-muted">{op.desc}</p>
                        </div>
                      </div>
                      <button onClick={() => run(op.key, op.url)} disabled={st?.running}
                        className="shrink-0 px-4 py-2 rounded-lg text-xs font-medium border transition-all disabled:opacity-40"
                        style={{
                          background: 'var(--mission-light)',
                          color: 'var(--mission-text)',
                          borderColor: 'var(--mission)',
                        }}>
                        {st?.running ? 'En cours...' : 'Exécuter'}
                      </button>
                    </div>
                    {st?.result && <div className="mt-2 flex items-start gap-2 text-[10px]"><CheckCircle2 size={10} className="mt-0.5 shrink-0" style={{ color: '#166534' }} /><span style={{ color: '#166534' }}>{st.result}</span></div>}
                    {st?.error && <div className="mt-2 flex items-start gap-2 text-[10px]"><XCircle size={10} className="mt-0.5 shrink-0" style={{ color: 'var(--critical-text)' }} /><span style={{ color: 'var(--critical-text)' }}>{st.error}</span></div>}
                  </div>
                )
              })}
            </div>
          </>
        )}

        {section === 'exports' && (
          <>
            <h1 className="h2 mb-4" style={{ color: 'var(--text)' }}>Exports</h1>
            <div className="surface rounded-2xl p-5" style={{ border: '1px solid var(--border)' }}>
              <a href="/api/download" className="btn-secondary inline-flex text-sm">
                <Download size={14} /> Télécharger Excel
              </a>
            </div>
          </>
        )}

        {section === 'status' && (
          <>
            <h1 className="h2 mb-4" style={{ color: 'var(--text)' }}>Statut système</h1>
            <div className="surface rounded-2xl p-5 space-y-3" style={{ border: '1px solid var(--border)' }}>
              <div className="flex justify-between text-sm">
                <span className="text-muted">Decision Engine</span>
                <span style={{ color: '#166534' }} className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--success)' }} /> Actif</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted">NVD Backfill</span>
                <span style={{ color: cveStatus?.running ? 'var(--mission-text)' : '#166534' }}>{cveStatus?.running ? 'En cours' : 'À jour'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted">HF API</span>
                <span style={{ color: hfStatus?.available ? '#166534' : 'var(--critical-text)' }}>{hfStatus?.available ? 'Connectée' : 'Absente'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted">Exploit-DB</span>
                <span style={{ color: 'var(--text-secondary)' }}>{exploitStats?.total_exploits?.toLocaleString() || '?'} exploits</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted">PostgreSQL</span>
                <span style={{ color: '#166534' }} className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--success)' }} /> Connectée</span>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
