import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import { Shield, AlertTriangle, TrendingUp, Bug, Globe, Target, Zap, Brain } from 'lucide-react'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/threats',
  component: ThreatIntelPage,
})

function KpiCard({ icon, value, label, iconColor }: { icon: React.ReactNode; value: string; label: string; iconColor: string }) {
  return (
    <div className="surface rounded-xl p-4 text-center" style={{ border: '1px solid var(--border)' }}>
      <div className="flex justify-center mb-1" style={{ color: iconColor }}>{icon}</div>
      <div className="text-xl font-bold" style={{ color: 'var(--text)' }}>{value}</div>
      <div className="text-[10px] text-muted mt-0.5">{label}</div>
    </div>
  )
}

function ThreatIntelPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['threat-intel'],
    queryFn: () => fetch('/api/threat-intel').then(r => r.json()),
    staleTime: 120_000,
  })

  if (isLoading) return <div className="flex justify-center py-24"><div className="w-8 h-8 border-2 border-[var(--danger)] border-t-transparent rounded-full animate-spin" /></div>

  const kev = data?.kev
  const epss = data?.epss
  const recent = data?.recent_criticals
  const platforms = data?.exploit_platforms

  return (
    <div className="max-w-4xl mx-auto py-4 sm:py-8 animate-fade">
      <h1 className="h1 mb-1" style={{ color: 'var(--text)' }}>Threat Intelligence</h1>
      <p className="body-sm text-secondary mb-6">Que se passe-t-il dans le monde ? Les campagnes actives, les tendances et les menaces émergentes.</p>

      {/* KPI row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <KpiCard icon={<AlertTriangle size={18} />} value={kev?.total?.toLocaleString() || '0'} label="CISA KEV actives" iconColor="var(--danger)" />
        <KpiCard icon={<Bug size={18} />} value={platforms?.total_exploits?.toLocaleString() || '0'} label="Exploits publics" iconColor="var(--warning)" />
        <KpiCard icon={<Zap size={18} />} value={(epss?.top?.length || 0).toString()} label="Top EPSS" iconColor="var(--info)" />
        <KpiCard icon={<Shield size={18} />} value={(recent?.total || 0).toString()} label="Critiques 30j" iconColor="var(--brand)" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Active campaigns (KEV) */}
        <div className="surface p-4 sm:p-5 lg:col-span-2" style={{ border: '1px solid var(--border)' }}>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: 'var(--danger-light)' }}>
              <AlertTriangle size={14} style={{ color: 'var(--danger-text)' }} />
            </div>
            <h2 className="h3" style={{ color: 'var(--text)' }}>Campagnes actives (CISA KEV)</h2>
            <span className="text-xs text-muted ml-auto">{kev?.total} CVEs</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {kev?.top?.slice(0, 8).map((c: any, i: number) => (
              <Link key={i} to="/cve/$id" params={{ id: c.cve_id }}
                className="rounded-xl p-3 block transition-all hover:-translate-y-0.5"
                style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)', textDecoration: 'none' }}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="mono font-semibold" style={{ color: 'var(--info-text)' }}>{c.cve_id}</span>
                  {c.cvss_score && <span className="text-xs font-medium" style={{ color: 'var(--danger-text)' }}>CVSS {c.cvss_score}</span>}
                </div>
                <p className="text-xs text-secondary line-clamp-2">{c.description}</p>
              </Link>
            ))}
          </div>
        </div>

        {/* Recent criticals */}
        <div className="surface p-4 sm:p-5" style={{ border: '1px solid var(--border)' }}>
          <div className="flex items-center gap-2 mb-3">
            <Shield size={15} style={{ color: 'var(--brand)' }} />
            <h2 className="h3" style={{ color: 'var(--text)' }}>Critiques récentes</h2>
          </div>
          <div className="space-y-1.5">
            {recent?.cves?.slice(0, 8).map((c: any, i: number) => (
              <Link key={i} to="/cve/$id" params={{ id: c.cve_id }}
                className="rounded-lg p-2.5 flex items-center gap-2 transition-all hover:-translate-y-0.5"
                style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)', textDecoration: 'none' }}>
                <span className="w-2 h-2 rounded-full shrink-0" style={{ background: c.severity === 'CRITICAL' ? 'var(--danger)' : 'var(--warning)' }} />
                <span className="mono font-semibold shrink-0" style={{ color: 'var(--info-text)' }}>{c.cve_id}</span>
                <span className="text-xs text-secondary line-clamp-1 flex-1">{c.description?.slice(0, 80)}</span>
                {c.cvss_score && <span className="text-xs text-muted shrink-0">{c.cvss_score}</span>}
              </Link>
            ))}
          </div>
        </div>

        {/* Top EPSS */}
        <div className="surface p-4 sm:p-5" style={{ border: '1px solid var(--border)' }}>
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp size={15} style={{ color: 'var(--info)' }} />
            <h2 className="h3" style={{ color: 'var(--text)' }}>Probables exploits (EPSS)</h2>
          </div>
          <div className="space-y-1.5">
            {epss?.top?.slice(0, 8).map((e: any, i: number) => (
              <Link key={i} to="/cve/$id" params={{ id: e.cve_id }}
                className="rounded-lg p-2.5 flex items-center gap-2 transition-all hover:-translate-y-0.5"
                style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)', textDecoration: 'none' }}>
                <Brain size={12} style={{ color: 'var(--ai)' }} />
                <span className="mono font-semibold" style={{ color: 'var(--info-text)' }}>{e.cve_id}</span>
                <div className="ml-auto flex items-center gap-2 shrink-0">
                  <div className="h-1.5 w-20 rounded-full overflow-hidden" style={{ background: 'var(--border)' }}>
                    <div className="h-full rounded-full" style={{ width: `${Math.min(e.epss * 100, 100)}%`, background: 'var(--info)' }} />
                  </div>
                  <span className="text-xs font-medium" style={{ color: 'var(--text-secondary)' }}>{(e.epss * 100).toFixed(0)}%</span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Platforms & Languages */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6 mt-6">
        <div className="surface p-4 sm:p-5" style={{ border: '1px solid var(--border)' }}>
          <div className="flex items-center gap-2 mb-3">
            <Globe size={15} style={{ color: 'var(--warning)' }} />
            <h2 className="h3" style={{ color: 'var(--text)' }}>Plateformes ciblées</h2>
          </div>
          <div className="space-y-1.5">
            {platforms?.top_platforms?.map((p: any, i: number) => (
              <div key={i} className="flex items-center justify-between rounded-lg p-2.5" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                <span className="text-xs capitalize" style={{ color: 'var(--text-secondary)' }}>{p.platform}</span>
                <span className="mono" style={{ color: 'var(--text-muted)' }}>{p.count.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="surface p-4 sm:p-5" style={{ border: '1px solid var(--border)' }}>
          <div className="flex items-center gap-2 mb-3">
            <Target size={15} style={{ color: 'var(--info)' }} />
            <h2 className="h3" style={{ color: 'var(--text)' }}>Langages les plus actifs</h2>
          </div>
          <div className="space-y-1.5">
            {data?.stack_languages?.map((l: any, i: number) => (
              <div key={i} className="flex items-center justify-between rounded-lg p-2.5" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>{l.language}</span>
                <span className="mono" style={{ color: 'var(--text-muted)' }}>{l.count.toLocaleString()} outils</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
