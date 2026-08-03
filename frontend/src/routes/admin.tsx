import { useState } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import AdminGuard from '../components/AdminGuard'
import CyberRadar from '../components/CyberRadar'
import ActivityFeed from '../components/ActivityFeed'
import { useStats, useScanStatus } from '../lib/api'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Play, Zap, Download, Brain, Shield, GitBranch, Search, Bug, Globe, RefreshCw, Loader2, TrendingUp, AlertTriangle, Activity, Database, HardDrive, CloudLightning, ShieldCheck, MapPin, Radio } from 'lucide-react'
import { getAuthHeaders, clearAuthToken } from './login'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/admin',
  component: AdminDashboardRoute,
})

function AdminDashboardRoute() {
  return (
    <AdminGuard>
      <AdminDashboard />
    </AdminGuard>
  )
}

async function adminPost(url: string): Promise<any> {
  const res = await fetch(url, { method: 'POST', headers: getAuthHeaders() })
  return res.json()
}

function ActionBtn({ icon, label, endpoint, disabled, variant = 'default', hint }: { icon: React.ReactNode; label: string; endpoint: string; disabled?: boolean; variant?: 'default' | 'danger' | 'success' | 'highlight'; hint?: string }) {
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
      await adminPost(endpoint)
      setResult('OK')
      setTimeout(() => { qc.invalidateQueries(); setResult(null) }, 2000)
    } catch { setResult('Erreur') }
    setLoading(false)
  }

  return (
    <button onClick={run} disabled={disabled || loading}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition border disabled:opacity-30 ${colors[variant]}`}>
      {loading ? <Loader2 size={13} className="animate-spin" /> : <>{icon}</>}
      <span className="flex-1 text-left">{label}</span>
      {hint && !result && <span className="text-[9px] text-slate-500">{hint}</span>}
      {result && <span className="text-[9px] ml-1">{result}</span>}
    </button>
  )
}

function StatusDot({ ok, label }: { ok: boolean | null; label: string }) {
  const color = ok === true ? 'bg-emerald-400' : ok === false ? 'bg-rose-400' : 'bg-slate-600'
  return (
    <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
      <span className={`w-2 h-2 rounded-full ${color} ${ok === true ? 'shadow-[0_0_6px_rgba(52,211,153,0.5)]' : ''}`} />
      {label}
    </div>
  )
}

function AdminDashboard() {
  const { data: stats } = useStats()
  const { data: scanStatus } = useScanStatus()

  const { data: tokenStatus } = useQuery({ queryKey: ['token-status'], queryFn: () => fetch('/api/token-status').then(r => r.json()), staleTime: 60_000 })
  const { data: dataPoints } = useQuery({ queryKey: ['data-points'], queryFn: () => fetch('/api/data-points').then(r => r.json()), staleTime: 60_000 })
  const { data: hfStatus } = useQuery({ queryKey: ['hf-status'], queryFn: () => fetch('/api/hf/status').then(r => r.json()).catch(() => ({})), staleTime: 120_000 })
  const { data: embStatus } = useQuery({ queryKey: ['emb-status'], queryFn: () => fetch('/api/embeddings/status').then(r => r.json()).catch(() => ({})), staleTime: 60_000 })
  const { data: bulkStatus } = useQuery({ queryKey: ['bulk-status'], queryFn: () => fetch('/api/bulk-status').then(r => r.json()).catch(() => ({})), staleTime: 30_000 })
  const { data: harvestStatus } = useQuery({ queryKey: ['harvest-status'], queryFn: () => fetch('/api/harvest-status').then(r => r.json()).catch(() => ({})), staleTime: 30_000 })
  const { data: iocStats } = useQuery({ queryKey: ['ioc-stats'], queryFn: () => fetch('/api/ingest/stats').then(r => r.json()).catch(() => ({})), staleTime: 30_000 })

  const isScanning = scanStatus?.status?.includes('en cours') || false
  const isBulk = bulkStatus?.in_progress || false
  const isHarvest = harvestStatus?.in_progress || false

  return (
    <div className="flex-1 min-w-0 space-y-4 animate-fade">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-white">Cockpit Admin</h1>
            <p className="text-xs text-slate-500">Controles operationnels CyberScan Pro v3.1</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <StatusDot ok={tokenStatus?.has_tokens} label={`${tokenStatus?.token_count || 0} tokens`} />
              <StatusDot ok={hfStatus?.models_loaded ? true : null} label={`${hfStatus?.models_loaded || '?'} modeles HF`} />
              <StatusDot ok={isScanning} label={isScanning ? 'Scan actif' : 'Scanner idle'} />
            </div>
            <button onClick={() => { clearAuthToken(); window.location.href = '/' }} className="text-xs text-slate-500 hover:text-rose-400 transition">Logout</button>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2">
          {[
            { value: tokenStatus?.token_count || 0, label: 'Tokens', icon: <Database size={13} className="text-indigo-400" /> },
            { value: dataPoints?.total?.toLocaleString() || '?', label: 'Data Points', icon: <HardDrive size={13} className="text-cyan-400" /> },
            { value: stats?.total_repos?.toLocaleString() || '?', label: 'Outils', icon: <GitBranch size={13} className="text-amber-400" /> },
            { value: stats?.total_cves?.toLocaleString() || '?', label: 'CVE', icon: <Shield size={13} className="text-rose-400" /> },
            { value: stats?.pending_keywords || 0, label: 'KW en attente', icon: <AlertTriangle size={13} className="text-violet-400" /> },
            { value: `${embStatus?.embedded || 0}/${embStatus?.total || 0}`, label: 'Embeddings', icon: <Activity size={13} className="text-emerald-400" /> },
            { value: iocStats?.total_iocs?.toLocaleString() || '0', label: 'IOCs', icon: <CloudLightning size={13} className="text-cyan-400" /> },
            { value: iocStats?.iocs_24h?.toLocaleString() || '0', label: 'IOCs 24h', icon: <TrendingUp size={13} className="text-violet-400" /> },
          ].map((x, i) => (
            <div key={i} className="glass-card rounded-xl p-3 text-center">
              <div className="flex justify-center mb-1">{x.icon}</div>
              <div className="text-lg font-bold text-white">{x.value}</div>
              <div className="text-[9px] text-slate-500">{x.label}</div>
            </div>
          ))}
        </div>

        {/* Alerts row */}
        {(isScanning || isBulk || isHarvest) && (
          <div className="glass-card rounded-xl p-3 flex items-center gap-3 text-xs animate-pulse">
            <Loader2 size={14} className="text-amber-400 animate-spin shrink-0" />
            <span className="text-amber-400 font-medium">Tâches en cours:</span>
            <span className="text-slate-400">{isScanning && 'Scanner '}{isBulk && 'Bulk Seed '}{isHarvest && 'Harvest'}</span>
          </div>
        )}

        {/* Workflows */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Scan GitHub */}
          <div className="glass-card rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-indigo-500/10 flex items-center justify-center"><Play size={12} className="text-indigo-400" /></span>
              Scanner GitHub
            </h3>
            <p className="text-[10px] text-slate-500 mb-3">Decouverte de nouveaux outils cyber</p>
            <div className="space-y-1.5">
              <ActionBtn icon={<Play size={12} />} label="Scan manuel" endpoint="/api/scan" hint="~500 repos" />
              <ActionBtn icon={<Zap size={12} />} label="Bulk Seed" endpoint="/api/bulk-seed" variant="highlight" hint="~1M repos" />
              <ActionBtn icon={<Search size={12} />} label="Slicer (tranches)" endpoint="/api/slicer/scan" hint="Temporel" />
              <ActionBtn icon={<Globe size={12} />} label="Dorking" endpoint="/api/dorking/scan" hint="Code Search" />
            </div>
          </div>

          {/* IA */}
          <div className="glass-card rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-violet-500/10 flex items-center justify-center"><Brain size={12} className="text-violet-400" /></span>
              Intelligence Artificielle
            </h3>
            <p className="text-[10px] text-slate-500 mb-3">Analyse, classification, decouverte</p>
            <div className="space-y-1.5">
              <ActionBtn icon={<Brain size={12} />} label="Audit IA (verdict)" endpoint="/api/ai-verdict?limit=30" hint="30 repos" />
              <ActionBtn icon={<TrendingUp size={12} />} label="IA Keywords" endpoint="/api/ai-keywords?limit=25" hint="25 termes" />
              <ActionBtn icon={<Activity size={12} />} label="Categoriser repos" endpoint="/api/agents/github/categorize" hint="15 repos" />
              <ActionBtn icon={<Shield size={12} />} label="HF Guard scan" endpoint="/api/hf/guard" hint="Content safety" />
            </div>
          </div>

          {/* Import */}
          <div className="glass-card rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-amber-500/10 flex items-center justify-center"><Download size={12} className="text-amber-400" /></span>
              Import & Donnees
            </h3>
            <p className="text-[10px] text-slate-500 mb-3">Chargement de donnees externes</p>
            <div className="space-y-1.5">
              <ActionBtn icon={<Shield size={12} />} label="Importer CVE (NVD)" endpoint="/api/import-cve" variant="danger" hint="300K vulns" />
              <ActionBtn icon={<Bug size={12} />} label="Importer Exploit-DB" endpoint="/api/dorking/exploitdb" hint="46K exploits" />
              <ActionBtn icon={<GitBranch size={12} />} label="Ontologie MITRE" endpoint="/api/enrich-ontology" hint="ATT&CK" />
              <ActionBtn icon={<RefreshCw size={12} />} label="Enrichir Mots-cles" endpoint="/api/enrich-keywords" hint="Externes" />
            </div>
          </div>

          {/* Harvest & OSINT */}
          <div className="glass-card rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center"><GitBranch size={12} className="text-emerald-400" /></span>
              Harvest & OSINT
            </h3>
            <p className="text-[10px] text-slate-500 mb-3">Recolte et enrichissement</p>
            <div className="space-y-1.5">
              <ActionBtn icon={<GitBranch size={12} />} label="Harvest Issues/Commits" endpoint="/api/harvest" hint="50 repos" />
              <ActionBtn icon={<Globe size={12} />} label="Scan Reddit" endpoint="/api/social/reddit" hint="Outils" />
              <ActionBtn icon={<Globe size={12} />} label="Enrichissement OSINT" endpoint="/api/osint/enrich" hint="KEV" />
              <ActionBtn icon={<Shield size={12} />} label="Enrichissement IOC" endpoint="/api/ioc/enrich" hint="abuse.ch" />
              <ActionBtn icon={<Download size={12} />} label="IOC Feed STIX" endpoint="/api/stix/ioc-feed" hint="IPs/domains" variant="success" />
            </div>
          </div>
        </div>

        {/* Premium Threat Intel */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="glass-card rounded-2xl p-4 border border-indigo-500/10">
            <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-indigo-500/10 flex items-center justify-center"><ShieldCheck size={12} className="text-indigo-400" /></span>
              Premium Intel
            </h3>
            <p className="text-[10px] text-slate-500 mb-3">VirusTotal + SecurityTrails + Shodan</p>
            <div className="space-y-1.5">
              <ActionBtn icon={<ShieldCheck size={12} />} label="Enrich via VirusTotal" endpoint="/api/intel/enrich-all?limit=20" hint="2B+ files" variant="default" />
              <ActionBtn icon={<MapPin size={12} />} label="Enrich via SecurityTrails" endpoint="/api/ingest/run" hint="4B+ DNS" variant="default" />
              <ActionBtn icon={<Radio size={12} />} label="Enrich via Shodan" endpoint="/api/intel/shodan" hint="5B+ devices" variant="default" />
            </div>
          </div>
          <div className="glass-card rounded-2xl p-4 border border-amber-500/10">
            <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-amber-500/10 flex items-center justify-center"><Activity size={12} className="text-amber-400" /></span>
              Status Premium APIs
            </h3>
            <p className="text-[10px] text-slate-500 mb-3">Verifier les cles API configurees</p>
            <PremiumStatus />
          </div>
        </div>

        {/* Ingestion Massive IOC */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="glass-card rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-cyan-500/10 flex items-center justify-center"><CloudLightning size={12} className="text-cyan-400" /></span>
              Ingestion massive IOC
            </h3>
            <p className="text-[10px] text-slate-500 mb-3">Millions de data points temps reel</p>
            <div className="space-y-1.5">
              <ActionBtn icon={<Globe size={12} />} label="URLhaus (3M+ URLs)" endpoint="/api/ingest/urlhaus?limit=5000" hint="Malware" />
              <ActionBtn icon={<Bug size={12} />} label="MalwareBazaar (1.5M)" endpoint="/api/ingest/malwarebazaar?limit=2000" hint="Hashes" />
              <ActionBtn icon={<Activity size={12} />} label="ThreatFox (1M+)" endpoint="/api/ingest/threatfox?limit=5000" hint="IOCs" />
              <ActionBtn icon={<TrendingUp size={12} />} label="EPSS Scores" endpoint="/api/ingest/epss" hint="200K" variant="success" />
            </div>
          </div>
          <div className="glass-card rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-rose-500/10 flex items-center justify-center"><CloudLightning size={12} className="text-rose-400" /></span>
              Threat Intel Externe
            </h3>
            <p className="text-[10px] text-slate-500 mb-3">OTX, OpenCVE, FeodoTracker</p>
            <div className="space-y-1.5">
              <ActionBtn icon={<Globe size={12} />} label="OTX Pulses (20M+)" endpoint="/api/ingest/otx?limit=500" hint="AlienVault" variant="highlight" />
              <ActionBtn icon={<Shield size={12} />} label="OpenCVE (200K+)" endpoint="/api/ingest/opencve?limit=1000" hint="CVEs" />
              <ActionBtn icon={<Activity size={12} />} label="FeodoTracker C2" endpoint="/api/ingest/feodotracker" hint="IPs" />
              <ActionBtn icon={<Zap size={12} />} label="Pipeline complet" endpoint="/api/ingest/run?full=false" hint="Tout" variant="danger" />
            </div>
          </div>

          {/* Sources gratuites */}
          <div className="glass-card rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-emerald-500/10 flex items-center justify-center"><Globe size={12} className="text-emerald-400" /></span>
              Sources gratuites (illimite)
            </h3>
            <p className="text-[10px] text-slate-500 mb-3">SSLBL, GHSA, OSV, SigmaHQ, YARAify, Ransomware, D3FEND, Packages</p>
            <div className="space-y-1.5">
              <ActionBtn icon={<Globe size={12} />} label="Pipeline gratuit complet" endpoint="/api/sources/run" hint="8 sources" variant="success" />
              <ActionBtn icon={<Shield size={12} />} label="GitHub Advisories (GHSA)" endpoint="/api/sources/ghsa" hint="Open Source" />
              <ActionBtn icon={<Bug size={12} />} label="OSV.dev (Google)" endpoint="/api/sources/osv?limit=200" hint="20+ ecosystems" />
              <ActionBtn icon={<Activity size={12} />} label="Ransomware.live" endpoint="/api/sources/ransomware" hint="Victims" variant="danger" />
            </div>
          </div>

          {/* Detection Rules */}
          <div className="glass-card rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-white mb-1 flex items-center gap-2">
              <span className="w-6 h-6 rounded-lg bg-violet-500/10 flex items-center justify-center"><Search size={12} className="text-violet-400" /></span>
              Regles de detection
            </h3>
            <p className="text-[10px] text-slate-500 mb-3">SigmaHQ, YARAify, SSLBL, Packages</p>
            <div className="space-y-1.5">
              <ActionBtn icon={<Search size={12} />} label="SigmaHQ Rules" endpoint="/api/sources/sigmahq" hint="SIEM/EDR" />
              <ActionBtn icon={<Bug size={12} />} label="YARAify Rules" endpoint="/api/sources/yaraify" hint="YARA" />
              <ActionBtn icon={<Shield size={12} />} label="SSLBL Certificats" endpoint="/api/sources/sslbl" hint="SSL malveillant" />
              <ActionBtn icon={<Download size={12} />} label="Package Advisories" endpoint="/api/sources/packages" hint="npm/PyPI/Maven" />
            </div>
          </div>
        </div>

        {/* Security Dashboard */}
        <div className="glass-card rounded-2xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2"><AlertTriangle size={14} className="text-rose-400" /> Securite des repos</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { value: stats?.security_critique || 0, label: 'Critiques', color: 'text-rose-400' },
              { value: stats?.security_suspect || 0, label: 'Suspects', color: 'text-amber-400' },
              { value: (stats?.total_repos || 0) - (stats?.security_critique || 0) - (stats?.security_suspect || 0) - (stats?.security_unscanned || 0), label: 'Sains', color: 'text-emerald-400' },
              { value: stats?.security_unscanned || 0, label: 'Non audites', color: 'text-slate-400' },
            ].map((x, i) => (
              <div key={i} className="text-center p-3 glass rounded-xl">
                <div className={`text-xl font-bold ${x.color}`}>{Math.max(0, x.value)}</div>
                <div className="text-[9px] text-slate-500">{x.label}</div>
              </div>
            ))}
          </div>
          <div className="mt-3 grid grid-cols-3 gap-2 text-[10px] text-slate-500">
            <span>Vitalite moyenne: <b className="text-white">{stats?.avg_vitality || '?'}</b></span>
            <span>Vitalite max: <b className="text-white">{stats?.top_vitality || '?'}</b></span>
            <span>Morts: <b className="text-rose-400">{stats?.dead_vitality || 0}</b></span>
          </div>
        </div>

        <CyberRadar />
        <ActivityFeed />
    </div>
  )
}

function PremiumStatus() {
  const { data, isLoading } = useQuery({
    queryKey: ['intel-status'],
    queryFn: () => fetch('/api/intel/status').then(r => r.json()),
    staleTime: 300_000,
  })
  if (isLoading) return <div className="h-16 bg-slate-800/50 rounded animate-pulse" />
  if (!data) return <p className="text-xs text-slate-500">Verification...</p>
  return (
    <div className="space-y-2">
      {[
        { label: 'VirusTotal', ok: data.virustotal, desc: '2B+ files, 70 AV engines', icon: <ShieldCheck size={12} /> },
        { label: 'SecurityTrails', ok: data.securitytrails, desc: '4B+ DNS, 1B+ domaines', icon: <MapPin size={12} /> },
        { label: 'Shodan', ok: data.shodan, desc: '5B+ devices, banners, vulns', icon: <Radio size={12} /> },
      ].map((x, i) => (
        <div key={i} className="flex items-center gap-2 text-xs">
          <span className={`w-2 h-2 rounded-full ${x.ok ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.5)]' : 'bg-slate-600'}`} />
          <span className="text-slate-300">{x.label}</span>
          <span className="text-slate-500 ml-auto text-[10px]">{x.ok ? 'Configure' : 'Non configure'}</span>
        </div>
      ))}
      <p className="text-[9px] text-slate-500 mt-2">Configurer via variables d'environnement: VIRUSTOTAL_API_KEY, SECURITYTRAILS_API_KEY, SHODAN_API_KEY</p>
    </div>
  )
}
