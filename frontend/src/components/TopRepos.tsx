import { useState } from 'react'
import { useRepos, type Repo } from '../lib/api'
import FicheFlashModal from './FicheFlashModal'

function VitalityBadge({ score }: { score: number | null }) {
  if (score == null) return null
  const color = score >= 70
    ? 'bg-neon-green/15 text-neon-green border-neon-green/30'
    : score >= 40
      ? 'bg-neon-amber/15 text-neon-amber border-neon-amber/30'
      : 'bg-neon-red/15 text-neon-red border-neon-red/30'
  return (
    <span className={`shrink-0 px-1.5 py-0.5 rounded text-[10px] font-medium border font-mono ${color}`}>
      {score}
    </span>
  )
}

const SECURITY_COLORS: Record<string, string> = {
  Critique: 'bg-neon-red/15 text-neon-red border-neon-red/30 shadow-[0_0_8px_rgba(255,0,68,0.15)]',
  Suspect: 'bg-neon-amber/15 text-neon-amber border-neon-amber/30 shadow-[0_0_8px_rgba(255,187,0,0.15)]',
  Sain: 'bg-neon-green/15 text-neon-green border-neon-green/30 shadow-[0_0_8px_rgba(0,255,102,0.15)]',
}

const RANK_GRADIENTS = [
  'from-neon-cyan to-neon-cyan/50',
  'from-gray-300 to-gray-500',
  'from-neon-amber to-neon-amber/50',
]

function RepoRow({ repo, rank, onSelect }: { repo: Repo; rank: number; onSelect: (r: Repo) => void }) {
  const gradient = RANK_GRADIENTS[rank - 1] ?? 'from-gray-600 to-gray-700'
  return (
    <div className="flex items-center justify-between py-3 border-b border-white/[0.04] last:border-0 group hover:bg-white/[0.02] transition-colors px-2 -mx-2 rounded-lg">
      <div className="flex items-center gap-3 min-w-0">
        <span className={`bg-gradient-to-br ${gradient} bg-clip-text text-transparent text-sm font-bold w-6 text-right shrink-0 font-cyber`}>
          #{rank}
        </span>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <button
              onClick={() => onSelect(repo)}
              className="text-indigo-400 hover:text-neon-cyan transition-colors text-sm font-medium truncate text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50 rounded"
            >
              {repo.name}
            </button>
            {repo.security_verdict && (
              <span className={`shrink-0 px-1.5 py-0.5 rounded text-[10px] font-medium border font-mono ${SECURITY_COLORS[repo.security_verdict] ?? 'bg-gray-500/20 text-gray-400 border-gray-500/30'}`}>
                {repo.security_verdict}
              </span>
            )}
            <VitalityBadge score={repo.vitality_score ?? null} />
          </div>
          <p className="text-slate-500 text-xs truncate mt-0.5 font-mono">{repo.desc}</p>
        </div>
      </div>
      <span className="text-neon-amber text-sm font-semibold shrink-0 ml-4 font-mono">
        ★ {repo.stars.toLocaleString()}
      </span>
    </div>
  )
}

export default function TopRepos() {
  const { data, isLoading, error } = useRepos()
  const [selectedRepo, setSelectedRepo] = useState<Repo | null>(null)

  if (isLoading) {
    return (
      <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan">
        <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider mb-4 font-cyber">
          Top 5
        </h2>
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-12 bg-white/5 rounded mb-2 animate-pulse" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan">
        <p className="text-neon-red text-sm font-mono">Erreur de chargement</p>
      </div>
    )
  }

  const top5 = [...(data?.repos ?? [])]
    .sort((a, b) => b.stars - a.stars)
    .slice(0, 5)

  return (
    <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan hover:neon-glow-cyan transition-all duration-300">
      <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider mb-4 font-cyber flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-neon-cyan animate-glow-pulse" />
        Top 5
      </h2>
      {top5.length === 0 ? (
        <p className="text-slate-500 text-sm py-4 text-center font-mono">Aucune donnée</p>
      ) : (
        top5.map((repo, i) => (
          <div key={repo.name} className="animate-fade-in-up" style={{ animationDelay: `${i * 60}ms` }}>
            <RepoRow repo={repo} rank={i + 1} onSelect={setSelectedRepo} />
          </div>
        ))
      )}

      {selectedRepo && (
        <FicheFlashModal repo={selectedRepo} onClose={() => setSelectedRepo(null)} />
      )}
    </div>
  )
}
