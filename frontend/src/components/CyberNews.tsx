import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Newspaper, ExternalLink, Radio, ChevronDown, ChevronUp, Star, Shield } from 'lucide-react'

type CorrelatedRepo = {
  name: string
  url: string
  stars: number
  desc: string
  lang: string
  security_verdict: string | null
  vitality_score: number
  relevance: number
  match_type: string
}

type NewsItem = {
  id: number
  title: string
  link: string
  summary: string
  source_name: string
  category: string
  published: string | null
  discovered_at: string
  correlated_repos: CorrelatedRepo[]
}

const CATEGORY_COLORS: Record<string, string> = {
  ransomware: 'bg-neon-red/15 text-neon-red border-neon-red/30',
  malware: 'bg-neon-red/10 text-neon-red/80 border-neon-red/20',
  vulnerability: 'bg-neon-amber/15 text-neon-amber border-neon-amber/30',
  phishing: 'bg-neon-magenta/15 text-neon-magenta border-neon-magenta/30',
  apt: 'bg-neon-cyan/15 text-neon-cyan border-neon-cyan/30',
  'data-breach': 'bg-neon-red/15 text-neon-red border-neon-red/30',
  critical: 'bg-neon-red/20 text-neon-red border-neon-red/40',
  general: 'bg-gray-500/15 text-gray-400 border-gray-500/30',
}

function VitalityBadge({ score }: { score: number }) {
  const color = score >= 70
    ? 'text-neon-green'
    : score >= 40
      ? 'text-neon-amber'
      : 'text-neon-red'
  return <span className={`font-mono text-[10px] ${color}`}>{score}</span>
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })
}

export default function CyberNews() {
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const { data, isLoading } = useQuery<NewsItem[]>({
    queryKey: ['news'],
    queryFn: () => fetch('/api/news?limit=15').then((r) => r.json()),
    staleTime: 120_000,
  })

  if (isLoading) {
    return (
      <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan">
        <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider mb-4 font-cyber flex items-center gap-2">
          <Radio size={14} />
          Actualités Cyber
        </h2>
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-12 bg-white/5 rounded mb-2 animate-pulse" />
        ))}
      </div>
    )
  }

  if (!data || data.length === 0) return null

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id)
  }

  return (
    <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan hover:neon-glow-cyan transition-all duration-300">
      <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider mb-4 font-cyber flex items-center gap-2">
        <Newspaper size={14} />
        Actualités Cyber
        <span className="text-[10px] text-gray-600 font-mono font-normal normal-case ml-1">
          {data.length} articles
        </span>
      </h2>

      <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
        {data.map((item) => {
          const catColor = CATEGORY_COLORS[item.category] ?? CATEGORY_COLORS.general
          const hasRepos = item.correlated_repos && item.correlated_repos.length > 0
          const isExpanded = expandedId === item.id
          return (
            <div
              key={item.link}
              className="p-3 rounded-lg border border-white/[0.04] hover:border-white/[0.08] transition-all duration-200"
            >
              <div className="flex items-start gap-3">
                <span className="text-xs mt-0.5 shrink-0">📡</span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono border ${catColor}`}>
                      {item.category}
                    </span>
                    <span className="text-[10px] text-gray-600 font-mono">{item.source_name}</span>
                    <span className="text-[10px] text-gray-700 font-mono ml-auto">{formatDate(item.published)}</span>
                  </div>
                  <a
                    href={item.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-gray-300 hover:text-neon-cyan transition-colors line-clamp-2 font-medium block"
                  >
                    {item.title}
                    <ExternalLink size={10} className="inline ml-1 text-gray-700" />
                  </a>
                  {item.summary && (
                    <p className="text-[11px] text-gray-600 mt-1 line-clamp-1 font-mono">
                      {item.summary.replace(/<[^>]+>/g, '').slice(0, 150)}
                    </p>
                  )}
                  {hasRepos && (
                    <div className="mt-2">
                      <button
                        onClick={() => toggleExpand(item.id)}
                        className="flex items-center gap-1 text-[10px] text-neon-cyan/60 hover:text-neon-cyan transition-colors font-mono"
                      >
                        {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                        {item.correlated_repos.length} dépôt{item.correlated_repos.length > 1 ? 's' : ''} corrélé{item.correlated_repos.length > 1 ? 's' : ''}
                      </button>
                      {isExpanded && (
                        <div className="mt-2 space-y-1.5">
                          {item.correlated_repos.slice(0, 5).map((repo) => (
                            <a
                              key={repo.name}
                              href={repo.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-2 py-1.5 px-2 rounded bg-white/[0.03] hover:bg-white/[0.05] transition-colors text-xs group"
                            >
                              <Shield size={10} className="text-gray-700 shrink-0" />
                              <span className="text-indigo-400 group-hover:text-neon-cyan transition-colors truncate flex-1">
                                {repo.name}
                              </span>
                              <span className="text-neon-amber font-mono flex items-center gap-0.5 shrink-0">
                                <Star size={9} />{repo.stars}
                              </span>
                              <VitalityBadge score={repo.vitality_score} />
                            </a>
                          ))}
                          {item.correlated_repos.length > 5 && (
                            <p className="text-[10px] text-gray-700 font-mono text-center">
                              +{item.correlated_repos.length - 5} autres
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="mt-3 pt-3 border-t border-white/[0.04] flex items-center gap-2 text-[10px] text-gray-700 font-mono">
        <span className="w-1 h-1 rounded-full bg-neon-cyan/40" />
        <span>FLUX RSS — CERT-FR</span>
      </div>
    </div>
  )
}
