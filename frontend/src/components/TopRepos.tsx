import { useRepos, type Repo } from '../lib/api'

const SECURITY_COLORS: Record<string, string> = {
  Critique: 'bg-red-500/20 text-red-300 border-red-500/30',
  Suspect: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  Sain: 'bg-green-500/20 text-green-300 border-green-500/30',
}

function RepoRow({ repo, rank }: { repo: Repo; rank: number }) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-white/[0.04] last:border-0">
      <div className="flex items-center gap-3 min-w-0">
        <span className="text-gray-600 text-sm w-5 text-right shrink-0">#{rank}</span>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <a
              href={repo.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-400 hover:text-indigo-300 transition-colors text-sm font-medium truncate block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50 rounded"
            >
              {repo.name}
            </a>
            {repo.security_verdict && (
              <span className={`shrink-0 px-1.5 py-0.5 rounded text-[10px] font-medium border ${SECURITY_COLORS[repo.security_verdict] ?? 'bg-gray-500/20 text-gray-400 border-gray-500/30'}`}>
                {repo.security_verdict}
              </span>
            )}
          </div>
          <p className="text-gray-600 text-xs truncate mt-0.5">{repo.desc}</p>
        </div>
      </div>
      <span className="text-amber-400 text-sm font-semibold shrink-0 ml-4">
        ★ {repo.stars.toLocaleString()}
      </span>
    </div>
  )
}

export default function TopRepos() {
  const { data, isLoading, error } = useRepos()

  if (isLoading) {
    return (
      <div className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-5">
        <h2 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-4">
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
      <div className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-5">
        <p className="text-red-400 text-sm">Erreur de chargement</p>
      </div>
    )
  }

  const top5 = [...(data?.repos ?? [])]
    .sort((a, b) => b.stars - a.stars)
    .slice(0, 5)

  return (
    <div className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-5 hover:bg-white/[0.06] hover:-translate-y-0.5 transition-all duration-300">
      <h2 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-4">
        Top 5
      </h2>
      {top5.length === 0 ? (
        <p className="text-gray-600 text-sm py-4 text-center">Aucune donnée</p>
      ) : (
        top5.map((repo, i) => (
          <div key={repo.name} className="animate-fade-in-up" style={{ animationDelay: `${i * 60}ms` }}>
            <RepoRow repo={repo} rank={i + 1} />
          </div>
        ))
      )}
    </div>
  )
}
