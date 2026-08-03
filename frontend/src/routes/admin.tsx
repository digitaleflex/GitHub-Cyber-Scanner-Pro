import { useState } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import AdminGuard from '../components/AdminGuard'
import AdminSidebar from '../components/AdminSidebar'
import CyberRadar from '../components/CyberRadar'
import ActivityFeed from '../components/ActivityFeed'
import { useStats, useScanStatus } from '../lib/api'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Play, Zap, Download, Brain, Shield, GitBranch, Search, Bug, Globe, RefreshCw, Loader2, TrendingUp, AlertTriangle, Activity } from 'lucide-react'
import { getAuthHeaders, clearAuthToken } from './login'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/admin',
  component: () => <AdminGuard><AdminDashboard /></AdminGuard>,
})

async function adminPost(url: string): Promise<any> {
  const res = await fetch(url, { method: 'POST', headers: getAuthHeaders() })
  return res.json()
}

function StatusBadge({ status }: { status?: string }) {
  if (!status || status.includes('Prêt') || status.includes('sommeil')) return <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-500/10 text-slate-400 border border-slate-500/20">Idle</span>
  if (status.includes('en cours')) return <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1"><Loader2 size={9} className="animate-spin" /> Actif</span>
  return <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-500/10 text-slate-400 border border-slate-500/20">{status}</span>
}

function ActionBtn({ icon, label, endpoint, disabled, variant = 'default' }: { icon: React.ReactNode; label: string; endpoint: string; disabled?: boolean; variant?: 'default' | 'danger' | 'success' | 'highlight' }) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<string | null>(null)
  const qc = useQueryClient()

  const colors = {
    default: 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400 hover:bg-indigo-500/20',
    danger: 'bg-rose-500/10 border-rose-500/20 text-rose-400 hover:bg-rose-500/20',
    success: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20',
    highlight: 'bg-amber-500/10 border-amber-500/20 text-amber-400 hover:bg-amber-500/20',
  }

  const run = async () => {
    setLoading(true); setResult(null)
    try {
      const r = await adminPost(endpoint)
      setResult(r.message || r.discovered || r.audited || r.saved ? 'OK' : JSON.stringify(r).slice(0, 60))
      setTimeout(() => { qc.invalidateQueries(); setResult(null) }, 2000)
    } catch { setResult('Erreur') }
    setLoading(false)
  }

  return (
    <button onClick={run} disabled={disabled || loading}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition border disabled:opacity-30 ${colors[variant]}`}>
      {loading ? <Loader2 size={13} className="animate-spin" /> : <>{icon}</>}
      <span className="flex-1 text-left">{label}</span>
      {result && <span className="text-[9px] ml-1 opacity-70">{result}</span>}
    </button>
  )
}

function AdminDashboard() {
  const { data: stats } = useStats()
  const { data: scanStatus } = useScanStatus()

  const { data: tokenStatus } = useQuery({ queryKey: ['token-status'], queryFn: () => fetch('/api/token-status').then(r => r.json()), staleTime: 60_000 })
  const { data: dataPoints } = useQuery({ queryKey: ['data-points'], queryFn: () => fetch('/api/data-points').then(r => r.json()), staleTime: 60_000 })
  const { data: hfStatus } = useQuery({ queryKey: ['hf-status'], queryFn: () => fetch('/api/hf/status').then(r => r.json()).catch(() => ({})), staleTime: 120_000 })
  const { data: embStatus } = useQuery({ queryKey: ['emb-status'], queryFn: () => fetch('/api/embeddings/status').then(r => r.json()).catch(() => ({})), staleTime: 60_000 })

  return (
    <div className="flex gap-6 items-start">
      <AdminSidebar />
      <div className="flex-1 min-w-0 space-y-4 animate-fade">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-white">Dashboard Admin</h1>
            <p className="text-xs text-slate-500">Contrôles opérationnels</p>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={scanStatus?.status} />
            <button onClick={() => { clearAuthToken(); window.location.href = '/' }} className="text-xs text-slate-500 hover:text-rose-400 transition">Déconnexion</button>
          </div>
        </div>

        {/* Status Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2">
          <div className="glass-card rounded-xl p-3 text-center">
            <div className="text-lg font-bold text-white">{tokenStatus?.token_count || 0}</div>
            <div className="text-[9px] text-slate-500">Tokens GitHub</div>
          </div>
          <div className="glass-card rounded-xl p-3 text-center">
            <div className="text-lg font-bold text-white">{dataPoints?.total?.toLocaleString() || '?'}</div>
            <div className="text-[9px] text-slate-500">Data Points</div>
          </div>
          <div className="glass-card rounded-xl p-3 text-center">
            <div className="text-lg font-bold text-white">{stats?.total_cves?.toLocaleString() || '?'}</div>
            <div className="text-[9px] text-slate-500">CVE Importés</div>
          </div>
          <div className="glass-card rounded-xl p-3 text-center">
            <div className="text-lg font-bold text-white">{stats?.pending_keywords || 0}</div>
            <div className="text-[9px] text-slate-500">KW en attente</div>
          </div>
          <div className="glass-card rounded-xl p-3 text-center">
            <div className={`text-lg font-bold ${hfStatus?.models_loaded ? 'text-emerald-400' : 'text-rose-400'}`}>{hfStatus?.models_loaded || '?'}</div>
            <div className="text-[9px] text-slate-500">Modèles HF</div>
          </div>
          <div className="glass-card rounded-xl p-3 text-center">
            <div className="text-lg font-bold text-white">{embStatus?.embedded || 0}/{embStatus?.total || 0}</div>
            <div className="text-[9px] text-slate-500">Embeddings</div>
          </div>
        </div>

        {/* Actions Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Scan */}
          <div className="glass-card rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2"><Play size={14} className="text-indigo-400" /> Scanner GitHub</h3>
            <div className="space-y-2">
              <ActionBtn icon={<Play size={13} />} label="Scan manuel" endpoint="/api/scan" />
              <ActionBtn icon={<Zap size={13} />} label="Bulk Seed (massif)" endpoint="/api/bulk-seed" variant="highlight" />
              <ActionBtn icon={<Search size={13} />} label="GitHub Slicer" endpoint="/api/slicer/scan" />
              <ActionBtn icon={<Globe size={13} />} label="Dorking Code Search" endpoint="/api/dorking/scan" />
            </div>
          </div>

          {/* AI & Enrichment */}
          <div className="glass-card rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2"><Brain size={14} className="text-violet-400" /> Intelligence Artificielle</h3>
            <div className="space-y-2">
              <ActionBtn icon={<Brain size={13} />} label="Audit IA (verdict)" endpoint="/api/ai-verdict?limit=30" />
              <ActionBtn icon={<TrendingUp size={13} />} label="Découvrir mots-clés IA" endpoint="/api/ai-keywords?limit=25" />
              <ActionBtn icon={<Activity size={13} />} label="Catégoriser repos (IA)" endpoint="/api/agents/github/categorize" />
              <ActionBtn icon={<Shield size={13} />} label="Content Safety Scan (HF)" endpoint="/api/hf/guard" />
            </div>
          </div>

          {/* Data Import */}
          <div className="glass-card rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2"><Download size={14} className="text-amber-400" /> Import & Données</h3>
            <div className="space-y-2">
              <ActionBtn icon={<Shield size={13} />} label="Importer CVE (NVD)" endpoint="/api/import-cve" variant="danger" />
              <ActionBtn icon={<Bug size={13} />} label="Importer Exploit-DB" endpoint="/api/dorking/exploitdb" />
              <ActionBtn icon={<GitBranch size={13} />} label="Enrichir Ontologie (MITRE)" endpoint="/api/enrich-ontology" />
              <ActionBtn icon={<RefreshCw size={13} />} label="Enrichir Mots-clés" endpoint="/api/enrich-keywords" />
            </div>
          </div>

          {/* Harvest & Others */}
          <div className="glass-card rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2"><GitBranch size={14} className="text-emerald-400" /> Harvest & OSINT</h3>
            <div className="space-y-2">
              <ActionBtn icon={<GitBranch size={13} />} label="Récolter Issues/Commits" endpoint="/api/harvest" />
              <ActionBtn icon={<Globe size={13} />} label="Scan Reddit" endpoint="/api/social/reddit" />
              <ActionBtn icon={<Globe size={13} />} label="Enrichissement OSINT" endpoint="/api/osint/enrich" />
              <ActionBtn icon={<Shield size={13} />} label="Enrichissement IOC" endpoint="/api/ioc/enrich" />
            </div>
          </div>
        </div>

        {/* Security Stats */}
        <div className="glass-card rounded-2xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2"><AlertTriangle size={14} className="text-rose-400" /> Sécurité des repos</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="text-center p-2 glass rounded-xl">
              <div className="text-xl font-bold text-rose-400">{stats?.security_critique || 0}</div>
              <div className="text-[9px] text-slate-500">Critiques</div>
            </div>
            <div className="text-center p-2 glass rounded-xl">
              <div className="text-xl font-bold text-amber-400">{stats?.security_suspect || 0}</div>
              <div className="text-[9px] text-slate-500">Suspects</div>
            </div>
            <div className="text-center p-2 glass rounded-xl">
              <div className="text-xl font-bold text-emerald-400">{(stats?.total_repos || 0) - (stats?.security_critique || 0) - (stats?.security_suspect || 0) - (stats?.security_unscanned || 0)}</div>
              <div className="text-[9px] text-slate-500">Sains</div>
            </div>
            <div className="text-center p-2 glass rounded-xl">
              <div className="text-xl font-bold text-slate-400">{stats?.security_unscanned || 0}</div>
              <div className="text-[9px] text-slate-500">Non audités</div>
            </div>
          </div>
          <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-2 text-[10px] text-slate-500">
            <span>Vitalité moyenne: <b className="text-white">{stats?.avg_vitality || '?'}</b></span>
            <span>Vitalité max: <b className="text-white">{stats?.top_vitality || '?'}</b></span>
            <span>Repos morts: <b className="text-rose-400">{stats?.dead_vitality || 0}</b></span>
          </div>
        </div>

        {/* Cyber Radar */}
        <CyberRadar />

        {/* Activity Feed */}
        <ActivityFeed />

      </div>
    </div>
  )
}
