import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import { Shield, AlertTriangle, TrendingUp, Bug, Globe, Target, Zap, Brain } from 'lucide-react'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/threats',
  component: ThreatIntelPage,
})

function ThreatIntelPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['threat-intel'],
    queryFn: () => fetch('/api/threat-intel').then(r => r.json()),
    staleTime: 120_000,
  })

  if (isLoading) return <div className="flex justify-center py-24"><div className="w-8 h-8 border-2 border-rose-400 border-t-transparent rounded-full animate-spin" /></div>

  const kev = data?.kev
  const epss = data?.epss
  const recent = data?.recent_criticals
  const platforms = data?.exploit_platforms

  return (
    <div className="max-w-4xl mx-auto py-4 sm:py-8 animate-fade">
      <h1 className="text-xl sm:text-2xl font-semibold text-white mb-1">Threat Intelligence</h1>
      <p className="text-sm text-slate-500 mb-6">Que se passe-t-il dans le monde ? Les campagnes actives, les tendances et les menaces emergentes.</p>

      {/* KPI row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div className="glass-card rounded-xl p-4 text-center">
          <div className="flex justify-center mb-1"><AlertTriangle size={18} className="text-rose-400" /></div>
          <div className="text-xl font-bold text-white">{kev?.total?.toLocaleString() || '0'}</div>
          <div className="text-[10px] text-slate-500">CISA KEV actives</div>
        </div>
        <div className="glass-card rounded-xl p-4 text-center">
          <div className="flex justify-center mb-1"><Bug size={18} className="text-amber-400" /></div>
          <div className="text-xl font-bold text-white">{platforms?.total_exploits?.toLocaleString() || '0'}</div>
          <div className="text-[10px] text-slate-500">Exploits publics</div>
        </div>
        <div className="glass-card rounded-xl p-4 text-center">
          <div className="flex justify-center mb-1"><Zap size={18} className="text-indigo-400" /></div>
          <div className="text-xl font-bold text-white">{epss?.top?.length || 0}</div>
          <div className="text-[10px] text-slate-500">Top EPSS</div>
        </div>
        <div className="glass-card rounded-xl p-4 text-center">
          <div className="flex justify-center mb-1"><Shield size={18} className="text-emerald-400" /></div>
          <div className="text-xl font-bold text-white">{recent?.total || 0}</div>
          <div className="text-[10px] text-slate-500">Critiques 30j</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Active campaigns (KEV) */}
        <div className="glass-card rounded-2xl p-4 sm:p-5 lg:col-span-2">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-7 h-7 rounded-lg bg-rose-500/20 flex items-center justify-center"><AlertTriangle size={14} className="text-rose-400" /></div>
            <h2 className="text-sm font-semibold text-white">Campagnes actives (CISA KEV)</h2>
            <span className="text-[10px] text-slate-500 ml-auto">{kev?.total} CVEs</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {kev?.top?.slice(0, 8).map((c: any, i: number) => (
              <Link key={i} to="/cve/$id" params={{ id: c.cve_id }}
                className="glass rounded-xl p-3 hover:bg-white/5 transition group">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono text-indigo-400">{c.cve_id}</span>
                  {c.cvss_score && <span className="text-[10px] text-rose-400 font-medium">CVSS {c.cvss_score}</span>}
                </div>
                <p className="text-xs text-slate-400 line-clamp-2">{c.description}</p>
              </Link>
            ))}
          </div>
        </div>

        {/* Recent criticals */}
        <div className="glass-card rounded-2xl p-4 sm:p-5">
          <div className="flex items-center gap-2 mb-3">
            <Shield size={15} className="text-emerald-400" />
            <h2 className="text-sm font-semibold text-white">Critiques recentes</h2>
          </div>
          <div className="space-y-1.5">
            {recent?.cves?.slice(0, 8).map((c: any, i: number) => (
              <Link key={i} to="/cve/$id" params={{ id: c.cve_id }}
                className="glass rounded-lg p-2.5 flex items-center gap-2 hover:bg-white/5 transition group">
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${c.severity === 'CRITICAL' ? 'bg-rose-400' : 'bg-amber-400'}`} />
                <span className="text-xs font-mono text-indigo-400 shrink-0">{c.cve_id}</span>
                <span className="text-xs text-slate-400 line-clamp-1 flex-1">{c.description?.slice(0, 80)}</span>
                {c.cvss_score && <span className="text-[10px] text-slate-500 shrink-0">{c.cvss_score}</span>}
              </Link>
            ))}
          </div>
        </div>

        {/* Top EPSS */}
        <div className="glass-card rounded-2xl p-4 sm:p-5">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp size={15} className="text-indigo-400" />
            <h2 className="text-sm font-semibold text-white">Probables exploits (EPSS)</h2>
          </div>
          <div className="space-y-1.5">
            {epss?.top?.slice(0, 8).map((e: any, i: number) => (
              <Link key={i} to="/cve/$id" params={{ id: e.cve_id }}
                className="glass rounded-lg p-2.5 flex items-center gap-2 hover:bg-white/5 transition group">
                <Brain size={12} className="text-indigo-400 shrink-0" />
                <span className="text-xs font-mono text-indigo-400">{e.cve_id}</span>
                <div className="ml-auto flex items-center gap-2 shrink-0">
                  <div className="h-1.5 w-20 rounded-full bg-slate-800 overflow-hidden">
                    <div className="h-full rounded-full bg-indigo-500" style={{ width: `${Math.min(e.epss * 100, 100)}%` }} />
                  </div>
                  <span className="text-[10px] text-slate-300 font-medium">{(e.epss * 100).toFixed(0)}%</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Platforms & Languages */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6 mt-6">
        <div className="glass-card rounded-2xl p-4 sm:p-5">
          <div className="flex items-center gap-2 mb-3">
            <Globe size={15} className="text-amber-400" />
            <h2 className="text-sm font-semibold text-white">Plateformes ciblees</h2>
          </div>
          <div className="space-y-1.5">
            {platforms?.top_platforms?.map((p: any, i: number) => (
              <div key={i} className="glass rounded-lg p-2.5 flex items-center justify-between">
                <span className="text-xs text-slate-300 capitalize">{p.platform}</span>
                <span className="text-xs text-slate-500 font-mono">{p.count.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="glass-card rounded-2xl p-4 sm:p-5">
          <div className="flex items-center gap-2 mb-3">
            <Target size={15} className="text-indigo-400" />
            <h2 className="text-sm font-semibold text-white">Langages les plus actifs</h2>
          </div>
          <div className="space-y-1.5">
            {data?.stack_languages?.map((l: any, i: number) => (
              <div key={i} className="glass rounded-lg p-2.5 flex items-center justify-between">
                <span className="text-xs text-slate-300">{l.language}</span>
                <span className="text-xs text-slate-500 font-mono">{l.count.toLocaleString()} outils</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
