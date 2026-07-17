import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { ExternalLink, ChevronDown, ChevronUp, Star, Shield } from 'lucide-react'

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
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
}

function formatTime(dateStr: string | null): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

type Props = {
  limit?: number
  showAll?: boolean
}

export default function CyberNewsFeed({ limit = 15, showAll = false }: Props) {
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const { data, isLoading } = useQuery<NewsItem[]>({
    queryKey: ['news', limit],
    queryFn: () => fetch(`/api/news?limit=${limit}`).then((r) => r.json()),
    staleTime: 120_000,
  })

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(showAll ? 8 : 5)].map((_, i) => (
          <div key={i} className="h-20 bg-white/5 rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-600 font-mono text-sm">
        Aucune actualité disponible pour le moment.
      </div>
    )
  }

  const toggleExpand = (id: number) => {
    setExpandedId(expandedId === id ? null : id)
  }

  return (
    <div className={`space-y-3 ${showAll ? '' : 'max-h-[500px] overflow-y-auto pr-1'}`}>
      {data.map((item) => {
        const catColor = CATEGORY_COLORS[item.category] ?? CATEGORY_COLORS.general
        const hasRepos = item.correlated_repos && item.correlated_repos.length > 0
        const isExpanded = expandedId === item.id
        return (
          <article
            key={item.link}
            className="p-4 rounded-lg border border-white/[0.06] hover:border-neon-cyan/20 bg-white/[0.02] hover:bg-white/[0.04] transition-all duration-200"
          >
            <div className="flex items-start gap-3">
              <span className="text-sm mt-0.5 shrink-0">📡</span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <span className={`text-[10px] px-2 py-0.5 rounded font-mono border uppercase ${catColor}`}>
                    {item.category}
                  </span>
                  <span className="text-[10px] text-gray-500 font-mono">{item.source_name}</span>
                  <span className="text-[10px] text-gray-600 font-mono ml-auto">
                    {formatDate(item.published)} {formatTime(item.published) && `· ${formatTime(item.published)}`}
                  </span>
                </div>
                <a
                  href={item.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-200 hover:text-neon-cyan transition-colors font-medium block mb-2"
                >
                  {item.title}
                  <ExternalLink size={12} className="inline ml-1.5 text-gray-600" />
                </a>
                {item.summary && (
                  <p className={`text-xs text-gray-500 font-mono leading-relaxed ${showAll ? '' : 'line-clamp-2'}`}>
                    {item.summary.replace(/<[^>]+>/g, '').slice(0, showAll ? 400 : 150)}
                  </p>
                )}
                {hasRepos && (
                  <div className="mt-3">
                    <button
                      onClick={() => toggleExpand(item.id)}
                      className="flex items-center gap-1 text-[11px] text-neon-cyan/70 hover:text-neon-cyan transition-colors font-mono"
                    >
                      {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                      {item.correlated_repos.length} dépôt{item.correlated_repos.length > 1 ? 's' : ''} corrélé{item.correlated_repos.length > 1 ? 's' : ''}
                    </button>
                    {isExpanded && (
                      <div className="mt-2 space-y-1.5">
                        {item.correlated_repos.map((repo) => (
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
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </article>
        )
      })}
    </div>
  )
}
