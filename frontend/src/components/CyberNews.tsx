import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { Newspaper, Radio, ArrowRight } from 'lucide-react'
import CyberNewsFeed from './CyberNewsFeed'

type NewsItem = {
  id: number
  title: string
  link: string
  summary: string
  source_name: string
  category: string
  published: string | null
  discovered_at: string
}

export default function CyberNews() {
  const { data, isLoading } = useQuery<NewsItem[]>({
    queryKey: ['news', 50],
    queryFn: () => fetch('/api/news?limit=50').then((r) => r.json()),
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

  return (
    <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan hover:neon-glow-cyan transition-all duration-300">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider font-cyber flex items-center gap-2">
          <Newspaper size={14} />
          Actualités Cyber
          <span className="text-[10px] text-gray-600 font-mono font-normal normal-case ml-1">
            {data.length} articles
          </span>
        </h2>
        <Link
          to="/news"
          className="text-[10px] text-neon-cyan/70 hover:text-neon-cyan font-mono flex items-center gap-1 transition-colors"
        >
          Voir tout
          <ArrowRight size={10} />
        </Link>
      </div>

      <CyberNewsFeed limit={50} />

      <div className="mt-3 pt-3 border-t border-white/[0.04] flex items-center gap-2 text-[10px] text-gray-700 font-mono">
        <span className="w-1 h-1 rounded-full bg-neon-cyan/40" />
        <span>FLUX RSS — {data.length} articles récents</span>
      </div>
    </div>
  )
}
