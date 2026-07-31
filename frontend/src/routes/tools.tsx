import { useState } from 'react'
import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import { Star, ExternalLink, Zap, TrendingUp, Target, ShieldCheck, Bug, Globe, Wifi, Search } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/tools', component: ToolsPage })

const CATS = [
  { id: 'all', label: 'Tous', icon: <Star size={12} /> },
  { id: 'red-team', label: 'Red Team', icon: <Target size={12} /> },
  { id: 'blue-team', label: 'Blue Team', icon: <ShieldCheck size={12} /> },
  { id: 'exploit', label: 'Exploits', icon: <Bug size={12} /> },
  { id: 'malware', label: 'Malware', icon: <Zap size={12} /> },
  { id: 'osint', label: 'OSINT', icon: <Globe size={12} /> },
  { id: 'network', label: 'Reseau', icon: <Wifi size={12} /> },
]

function ToolsPage() {
  const [tab, setTab] = useState<'featured'|'ready'|'category'>('featured')
  const [category, setCategory] = useState('all')

  const { data: featured } = useQuery({
    queryKey: ['featured-tools'], queryFn: () => fetch('/api/tools/featured').then(r => r.json()), staleTime: 120_000
  })
  const { data: ready } = useQuery({
    queryKey: ['ready-tools'], queryFn: () => fetch('/api/tools/readytouse').then(r => r.json()), staleTime: 120_000, enabled: tab === 'ready'
  })
  const { data: byCat } = useQuery({
    queryKey: ['tools-cat', category], queryFn: () => fetch(`/api/tools/by-category?category=${category}&limit=30`).then(r => r.json()), staleTime: 60_000, enabled: tab === 'category'
  })

  const tools = tab === 'featured' ? featured?.tools : tab === 'ready' ? ready?.tools : byCat?.tools

  return (
    <div className="max-w-6xl mx-auto py-4 sm:py-8 animate-fade">
      {/* Tabs */}
      <div className="flex items-center gap-1 mb-4 sm:mb-6 flex-wrap">
        <button onClick={() => setTab('featured')} className={`px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition flex items-center gap-1.5 ${tab === 'featured' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'glass text-slate-400 hover:text-white'}`}><TrendingUp size={13} /> Incontournables</button>
        <button onClick={() => setTab('ready')} className={`px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition flex items-center gap-1.5 ${tab === 'ready' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'glass text-slate-400 hover:text-white'}`}><Zap size={13} /> Prets a l'emploi</button>
        <button onClick={() => setTab('category')} className={`px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition flex items-center gap-1.5 ${tab === 'category' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'glass text-slate-400 hover:text-white'}`}><Search size={13} /> Par categorie</button>
      </div>

      {/* Category filters (only for category tab) */}
      {tab === 'category' && (
        <div className="flex flex-wrap gap-1 mb-4">
          {CATS.map(c => (
            <button key={c.id} onClick={() => setCategory(c.id)}
              className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] sm:text-xs font-medium transition border ${category === c.id ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' : 'glass text-slate-500 hover:text-slate-300'}`}>
              {c.icon} {c.label}
            </button>
          ))}
        </div>
      )}

      {/* Tool cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3">
        {tools?.slice(0, tab === 'featured' ? undefined : 30).map((t: any, i: number) => (
          <div key={i} className="glass-card rounded-xl p-3 sm:p-4 group">
            <div className="flex items-start justify-between gap-2 mb-1.5">
              <div className="flex-1 min-w-0">
                <Link to="/tool/$name" params={{ name: t.name }}
                  className="text-xs sm:text-sm font-medium text-slate-200 hover:text-indigo-400 transition truncate block">{t.name}</Link>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                {t.security_verdict && (
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-medium ${
                    t.security_verdict === 'Critique' ? 'bg-rose-500/10 text-rose-400' :
                    t.security_verdict === 'Suspect' ? 'bg-amber-500/10 text-amber-400' :
                    'bg-emerald-500/10 text-emerald-400'
                  }`}>{t.security_verdict}</span>
                )}
                <span className="flex items-center gap-0.5 text-[10px] sm:text-xs text-amber-400"><Star size={10} />{t.stars?.toLocaleString()}</span>
              </div>
            </div>
            {t.desc && <p className="text-[10px] sm:text-xs text-slate-500 leading-relaxed line-clamp-2 mb-2">{t.desc}</p>}
            <div className="flex items-center gap-2 text-[9px] sm:text-[10px] text-slate-600">
              {t.lang && <span>{t.lang}</span>}
              {t.vitality_score != null && <span>Vitalite {t.vitality_score}/100</span>}
              <a href={t.url} target="_blank" rel="noopener" className="flex items-center gap-0.5 hover:text-indigo-400 ml-auto"><ExternalLink size={9} /> GitHub</a>
            </div>
          </div>
        ))}
      </div>
      {(!tools || tools.length === 0) && <p className="text-slate-500 text-sm text-center py-8">Aucun outil trouve</p>}
    </div>
  )
}
