import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import { Clock, Shield, Bug, Target, Box } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/timeline', component: TimelinePage })

const TYPE_CONFIG: Record<string, { icon: React.ReactNode; color: string }> = {
  cve: { icon: <Shield size={13} />, color: 'var(--critical)' },
  mission: { icon: <Target size={13} />, color: 'var(--brand-text)' },
  asset: { icon: <Box size={13} />, color: 'var(--mission)' },
  exploit: { icon: <Bug size={13} />, color: 'var(--decision)' },
}

function TimelinePage() {
  const { data, isLoading } = useQuery({
    queryKey: ['timeline'],
    queryFn: () => fetch('/api/timeline?limit=40').then(r => r.json()),
    staleTime: 60_000,
  })

  if (isLoading) return <div className="flex justify-center py-24"><div className="w-8 h-8 border-2 border-[var(--brand)] border-t-transparent rounded-full animate-spin" /></div>

  return (
    <div className="max-w-2xl mx-auto py-4 sm:py-8 animate-fade">
      <h1 className="h1 mb-1" style={{ color: 'var(--text)' }}>Timeline</h1>
      <p className="body-sm text-secondary mb-6">Que s'est-il passé ? Toute l'histoire de votre sécurité.</p>

      <div className="relative">
        <div className="absolute left-4 top-2 bottom-2 w-px" style={{ background: 'var(--border)' }} />
        <div className="space-y-1">
          {data?.events?.map((e: any, i: number) => {
            const cfg = TYPE_CONFIG[e.type]
            return (
              <div key={i} className="relative pl-10 py-2 group">
                <div className="absolute left-2 top-3 w-4 h-4 rounded-full border-2 flex items-center justify-center"
                  style={{ background: 'var(--bg)', borderColor: cfg?.color || 'var(--border)' }}>
                  {cfg?.icon || <Clock size={10} style={{ color: 'var(--text-muted)' }} />}
                </div>
                <div className="rounded-xl p-3 transition-all hover:-translate-y-0.5" style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}>
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-medium" style={{ color: 'var(--text)' }}>{e.title}</span>
                    {e.severity && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded-full border font-medium" style={{
                        background: e.severity === 'CRITICAL' ? 'var(--critical-light)' : e.severity === 'HIGH' ? 'var(--mission-light)' : 'var(--bg-alt)',
                        color: e.severity === 'CRITICAL' ? 'var(--critical-text)' : e.severity === 'HIGH' ? 'var(--mission-text)' : 'var(--text-muted)',
                        borderColor: e.severity === 'CRITICAL' ? 'var(--critical)' : e.severity === 'HIGH' ? 'var(--mission)' : 'var(--border)',
                      }}>
                        {e.severity}
                      </span>
                    )}
                    {e.status && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded-full border font-medium" style={{
                        background: e.status === 'completed' ? 'var(--success-light)' : 'var(--decision-light)',
                        color: e.status === 'completed' ? '#166534' : 'var(--decision-text)',
                        borderColor: e.status === 'completed' ? 'var(--success)' : 'var(--decision)',
                      }}>
                        {e.status}
                      </span>
                    )}
                  </div>
                  {e.desc && <p className="text-[10px] text-secondary line-clamp-1">{e.desc}</p>}
                  <span className="text-[9px] text-muted mt-1 block">{e.ts?.slice(0, 10)}</span>
                </div>
              </div>
            )
          })}
        </div>
        {!data?.events?.length && (
          <p className="text-center body-sm text-secondary py-12">Aucun événement. La timeline se remplit au fur et à mesure.</p>
        )}
      </div>
    </div>
  )
}
