import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import { Shield, Clock, CheckCircle2, Target, ArrowRight, ChevronRight, Brain, Wifi, AlertTriangle } from 'lucide-react'
import { useStats } from '../lib/api'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/', component: HomePage })

interface PriorityDecision {
  cve_id: string
  score: number
  level: string
  severity: string
  cvss_score: number | null
  published: string | null
  description: string
  is_kev: boolean
  exploits_count: number
  factors: Record<string, number>
  reasons: string[]
  risk_if_ignored: string
  confidence: string
  sources: string[]
}

function HomePage() {
  const { data: stats } = useStats()
  const { data: priority, isLoading, error } = useQuery({
    queryKey: ['priority-home'],
    queryFn: async () => {
      const r = await fetch('/api/priority/cves?days=90&limit=6')
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      return r.json()
    },
    staleTime: 120_000,
  })

  const summary = priority?.summary
  const decisions: PriorityDecision[] = priority?.decisions || []
  const today = decisions.slice(0, 3)
  const upcoming = decisions.slice(3, 5)
  const completedCount = 0

  const repoCount = stats?.total_repos ? (stats.total_repos >= 1000 ? `${(stats.total_repos / 1000).toFixed(0)}K` : stats.total_repos.toLocaleString()) : '0'
  const cveCount = stats?.total_cves ? (stats.total_cves >= 1000 ? `${(stats.total_cves / 1000).toFixed(0)}K` : stats.total_cves.toLocaleString()) : '0'

  return (
    <div className="max-w-4xl mx-auto w-full animate-fade">
      <section className="py-6 sm:py-10">
        <p className="text-xs sm:text-sm text-slate-500 mb-1">Bonjour</p>
        <h1 className="text-xl sm:text-2xl font-semibold text-white mb-3">
          Que dois-je faire aujourd'hui&nbsp;?
        </h1>
        <div className="flex flex-wrap items-center gap-3 text-xs sm:text-sm text-slate-400">
          <span className="flex items-center gap-1.5">
            <Shield size={13} className="text-emerald-400" />
            <span className="text-emerald-400 font-medium">{cveCount}</span> CVE suivies
          </span>
          <span className="flex items-center gap-1.5">
            <Wifi size={13} className="text-indigo-400" />
            <span className="text-indigo-400 font-medium">{repoCount}</span> outils analysés
          </span>
          {summary?.critiques > 0 && (
            <span className="flex items-center gap-1.5">
              <AlertTriangle size={13} className="text-amber-400" />
              <span className="text-amber-400 font-medium">{summary.critiques.toLocaleString()}</span> critiques actives
            </span>
          )}
        </div>
      </section>

      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <div className="w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {error && (
        <div className="glass-card rounded-2xl p-6 text-center border-rose-500/20">
          <p className="text-sm text-rose-300 mb-3">Le Decision Engine est temporairement indisponible.</p>
          <p className="text-xs text-slate-500">Les donnees NVD sont peut-etre en cours de backfill. Reessayez dans quelques minutes.</p>
        </div>
      )}

      {!isLoading && !error && decisions.length > 0 && (
        <>
          <DecisionHero decision={decisions[0]} />

          <section className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
            <DecisionBlock
              title="Aujourd'hui"
              subtitle={`${today.length} decision${today.length > 1 ? 's' : ''}`}
              icon={<Target size={15} className="text-emerald-400" />}
              decisions={today}
            />
            <DecisionBlock
              title="À venir"
              subtitle={`${upcoming.length} en attente`}
              icon={<Clock size={15} className="text-indigo-400" />}
              decisions={upcoming}
            />
          </section>

          {completedCount > 0 && (
            <section className="mt-6">
              <DecisionBlock
                title="Terminé"
                subtitle={`${completedCount} mission${completedCount > 1 ? 's' : ''}`}
                icon={<CheckCircle2 size={15} className="text-slate-500" />}
                decisions={[]}
              />
            </section>
          )}
        </>
      )}

      {!isLoading && !error && decisions.length === 0 && (
        <div className="glass-card rounded-2xl p-8 text-center">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <CheckCircle2 size={22} className="text-emerald-400" />
          </div>
          <p className="text-sm text-slate-300 font-medium mb-1">Aucune décision urgente aujourd'hui</p>
          <p className="text-xs text-slate-500">Le Decision Engine surveille vos menaces. Revenez plus tard ou verifiez vos actifs.</p>
        </div>
      )}
    </div>
  )
}

function DecisionHero({ decision }: { decision: PriorityDecision }) {
  const levelColor = decision.level === 'CRITIQUE' ? 'rose' : decision.level === 'ELEVE' ? 'amber' : 'slate'
  const cvssColor = (decision.cvss_score || 0) >= 9 ? 'rose' : (decision.cvss_score || 0) >= 7 ? 'amber' : 'emerald'

  return (
    <div className="glass-card rounded-2xl p-5 sm:p-7 border-emerald-500/10">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-[10px] uppercase tracking-widest text-emerald-400 font-medium">Votre prochaine décision</span>
      </div>

      <h2 className="text-lg sm:text-xl font-semibold text-white mb-1.5">
        {decision.description.slice(0, 120)}
      </h2>

      <div className="flex flex-wrap items-center gap-2 mb-4">
        <span className="text-xs font-mono text-indigo-400">{decision.cve_id}</span>
        {decision.cvss_score != null && (
          <span className={`text-xs font-medium text-${cvssColor}-400`}>CVSS {decision.cvss_score}</span>
        )}
        <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium bg-${levelColor}-500/10 text-${levelColor}-400 border border-${levelColor}-500/20`}>
          {decision.level}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
        <div className="glass rounded-xl p-3 text-center">
          <div className="text-lg font-bold text-white">{decision.score}</div>
          <div className="text-[10px] text-slate-500">Score</div>
        </div>
        <div className="glass rounded-xl p-3 text-center">
          <div className="text-lg font-bold text-white">{decision.confidence}</div>
          <div className="text-[10px] text-slate-500">Confiance</div>
        </div>
        <div className="glass rounded-xl p-3 text-center">
          <div className="text-lg font-bold text-white">{decision.exploits_count}</div>
          <div className="text-[10px] text-slate-500">Exploit{decision.exploits_count > 1 ? 's' : ''}</div>
        </div>
        <div className="glass rounded-xl p-3 text-center">
          <div className="text-lg font-bold text-amber-400">{decision.is_kev ? 'Oui' : 'Non'}</div>
          <div className="text-[10px] text-slate-500">CISA KEV</div>
        </div>
      </div>

      <div className="space-y-2 mb-5">
        {decision.reasons.map((r, i) => (
          <div key={i} className="flex items-start gap-2 text-xs sm:text-sm text-slate-400">
            <ChevronRight size={13} className="shrink-0 mt-0.5 text-emerald-500" />
            <span>{r}</span>
          </div>
        ))}
      </div>

      <div className="glass rounded-xl p-4 mb-5 border-amber-500/10">
        <p className="text-[10px] uppercase tracking-widest text-amber-400 mb-1">Si vous ignorez</p>
        <p className="text-xs sm:text-sm text-slate-300">{decision.risk_if_ignored}</p>
      </div>

      <div className="flex items-center gap-2 text-[10px] text-slate-500 mb-4">
        <Brain size={11} />
        <span>Sources: {decision.sources.join(', ')}</span>
      </div>

      <button className="w-full sm:w-auto px-6 py-3 rounded-xl bg-emerald-500 text-white text-sm font-medium hover:bg-emerald-400 transition flex items-center justify-center gap-2">
        Commencer la mission <ArrowRight size={15} />
      </button>
    </div>
  )
}

function DecisionBlock({ title, subtitle, icon, decisions }: {
  title: string
  subtitle: string
  icon: React.ReactNode
  decisions: PriorityDecision[]
}) {
  return (
    <div className="glass-card rounded-2xl p-4 sm:p-5">
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <h3 className="text-sm font-semibold text-white">{title}</h3>
      </div>
      <p className="text-[10px] text-slate-500 mb-3">{subtitle}</p>

      {decisions.length === 0 ? (
        <p className="text-xs text-slate-500 py-4 text-center">Aucune décision</p>
      ) : (
        <div className="space-y-2">
          {decisions.map((d, i) => (
            <div key={i} className="glass rounded-xl p-3 flex items-center justify-between gap-2 group">
              <div className="min-w-0">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <span className={`w-1.5 h-1.5 rounded-full bg-${d.level === 'CRITIQUE' ? 'rose' : d.level === 'ELEVE' ? 'amber' : 'slate'}-400`} />
                  <span className="text-xs font-mono text-indigo-400">{d.cve_id}</span>
                </div>
                <p className="text-xs text-slate-400 line-clamp-1">{d.description.slice(0, 90)}</p>
              </div>
              <span className="text-xs font-bold text-white shrink-0">{d.score}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
