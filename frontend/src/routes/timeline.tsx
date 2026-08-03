import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import { Clock, Shield, Bug, Target, Box } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/timeline', component: TimelinePage })

const TYPE_ICONS: Record<string, React.ReactNode> = {
  cve: <Shield size={13} className="text-rose-400" />,
  mission: <Target size={13} className="text-emerald-400" />,
  asset: <Box size={13} className="text-amber-400" />,
  exploit: <Bug size={13} className="text-indigo-400" />,
}

function TimelinePage() {
  const { data, isLoading } = useQuery({
    queryKey: ['timeline'],
    queryFn: () => fetch('/api/timeline?limit=40').then(r => r.json()),
    staleTime: 60_000,
  })

  if (isLoading) return <div className="flex justify-center py-24"><div className="w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" /></div>

  return (
    <div className="max-w-2xl mx-auto py-4 sm:py-8 animate-fade">
      <h1 className="text-xl sm:text-2xl font-semibold text-white mb-1">Timeline</h1>
      <p className="text-sm text-slate-500 mb-6">Que s'est-il passe ? Toute l'histoire de votre securite.</p>

      <div className="relative">
        <div className="absolute left-4 top-2 bottom-2 w-px bg-slate-800" />
        <div className="space-y-1">
          {data?.events?.map((e: any, i: number) => (
            <div key={i} className="relative pl-10 py-2 group">
              <div className="absolute left-2 top-3 w-4 h-4 rounded-full bg-slate-900 border-2 border-slate-700 flex items-center justify-center">
                {TYPE_ICONS[e.type] || <Clock size={10} className="text-slate-500" />}
              </div>
              <div className="glass rounded-xl p-3 hover:bg-white/[0.02] transition">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-xs font-medium text-slate-200">{e.title}</span>
                  {e.severity && (
                    <span className={`text-[9px] px-1.5 py-0.5 rounded ${e.severity === 'CRITICAL' ? 'bg-rose-500/10 text-rose-400' : e.severity === 'HIGH' ? 'bg-amber-500/10 text-amber-400' : 'bg-slate-500/10 text-slate-400'}`}>
                      {e.severity}
                    </span>
                  )}
                  {e.status && (
                    <span className={`text-[9px] px-1.5 py-0.5 rounded ${e.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-indigo-500/10 text-indigo-400'}`}>
                      {e.status}
                    </span>
                  )}
                </div>
                {e.desc && <p className="text-[10px] text-slate-500 line-clamp-1">{e.desc}</p>}
                <span className="text-[9px] text-slate-600 mt-1 block">{e.ts?.slice(0, 10)}</span>
              </div>
            </div>
          ))}
        </div>
        {!data?.events?.length && (
          <p className="text-center text-sm text-slate-500 py-12">Aucun evenement. La timeline se remplit au fur et a mesure.</p>
        )}
      </div>
    </div>
  )
}
