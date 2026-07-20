import { useState, useMemo } from 'react'
import { useCves, type CveEntry } from '../lib/api'

const SEVERITIES = [
  { key: '', label: 'Toutes' },
  { key: 'CRITICAL', label: 'CRITICAL' },
  { key: 'HIGH', label: 'HIGH' },
  { key: 'MEDIUM', label: 'MEDIUM' },
  { key: 'LOW', label: 'LOW' },
  { key: 'NONE', label: 'NONE' },
]

const SEVERITY_CLASSES: Record<string, string> = {
  CRITICAL: 'bg-neon-red/10 text-neon-red border-neon-red/20',
  HIGH: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  MEDIUM: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  LOW: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  NONE: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
}

function SeverityBadge({ severity, score }: { severity: string; score: number | null }) {
  const cls = SEVERITY_CLASSES[severity] ?? 'bg-gray-500/10 text-gray-400 border-gray-500/20'
  const label = score != null ? `${severity} (${score.toFixed(1)})` : severity
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium border font-mono ${cls}`}>
      {label}
    </span>
  )
}

export default function CveTable() {
  const [search, setSearch] = useState('')
  const [severity, setSeverity] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading, error } = useCves(search || undefined, severity || undefined, page)

  const totalPages = data?.pages ?? 1

  const pages = useMemo(() => {
    const arr: number[] = []
    const start = Math.max(1, page - 2)
    const end = Math.min(totalPages, page + 2)
    for (let i = start; i <= end; i++) arr.push(i)
    return arr
  }, [page, totalPages])

  const goPage = (p: number) => {
    if (p >= 1 && p <= totalPages) setPage(p)
  }

  return (
    <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan hover:neon-glow-cyan transition-all duration-300">
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider font-cyber">
          Vulnérabilités CVE
        </h2>
        {data && (
          <span className="text-xs text-gray-600 font-mono">
            {data.total} au total
          </span>
        )}
      </div>

      <div className="flex items-center gap-2 mb-4 flex-wrap">
        {SEVERITIES.map((s) => (
          <button
            key={s.key || 'all'}
            onClick={() => { setSeverity(s.key); setPage(1) }}
            className={`text-xs px-3 py-1 rounded-full border transition-colors font-mono ${
              severity === s.key
                ? 'bg-white/[0.06] text-white border-white/20'
                : 'text-gray-600 border-white/[0.06] hover:text-gray-400'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      <input
        type="text"
        placeholder="Rechercher par CVE ID, description, faiblesse..."
        value={search}
        onChange={(e) => { setSearch(e.target.value); setPage(1) }}
        className="w-full mb-4 px-4 py-2.5 bg-white/[0.05] border border-white/[0.1] rounded-lg text-white text-sm placeholder-gray-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50 transition-colors font-mono"
        aria-label="Rechercher une CVE"
      />

      {isLoading ? (
        <div className="space-y-3" role="status">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-10 bg-white/5 rounded animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <p className="text-neon-red text-sm py-4 text-center font-mono">Erreur de chargement</p>
      ) : !data || data.cves.length === 0 ? (
        <p className="text-gray-600 text-sm py-8 text-center font-mono">
          {search || severity ? 'Aucun résultat' : 'Aucune CVE importée'}
        </p>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-sm" role="table">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  <th className="text-left py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider w-28">CVE</th>
                  <th className="text-left py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider">Description</th>
                  <th className="text-center py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider w-28">Sévérité</th>
                  <th className="text-center py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider w-28">Publiée</th>
                  <th className="text-left py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider max-md:hidden">Faiblesses</th>
                </tr>
              </thead>
              <tbody>
                {data.cves.map((cve: CveEntry) => (
                  <tr
                    key={cve.cve_id}
                    className="border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors"
                  >
                    <td className="py-2.5 px-2">
                      <a
                        href={`https://nvd.nist.gov/vuln/detail/${cve.cve_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-indigo-400 hover:text-neon-cyan transition-colors text-sm font-mono"
                      >
                        {cve.cve_id}
                      </a>
                    </td>
                    <td className="py-2.5 px-2 text-white/70 text-xs max-w-md truncate">
                      {cve.description}
                    </td>
                    <td className="py-2.5 px-2 text-center">
                      <SeverityBadge severity={cve.severity} score={cve.cvss_score} />
                    </td>
                    <td className="py-2.5 px-2 text-center text-gray-500 text-xs font-mono">
                      {cve.published ?? '-'}
                    </td>
                    <td className="py-2.5 px-2 max-md:hidden">
                      <div className="flex flex-wrap gap-1">
                        {cve.weaknesses.length > 0 ? (
                          cve.weaknesses.slice(0, 3).map((w: string) => (
                            <span key={w} className="inline-block px-1.5 py-0.5 rounded text-[10px] font-mono bg-white/[0.04] text-gray-500 border border-white/[0.06]">
                              {w.trim()}
                            </span>
                          ))
                        ) : (
                          <span className="text-gray-700 text-xs">-</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-center gap-2 mt-4">
            <button
              onClick={() => goPage(page - 1)}
              disabled={page <= 1}
              className="px-3 py-1 rounded text-xs font-mono border border-white/[0.06] text-gray-500 hover:text-white hover:border-white/20 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              Prev
            </button>
            {pages.map((p) => (
              <button
                key={p}
                onClick={() => goPage(p)}
                className={`px-3 py-1 rounded text-xs font-mono border transition-colors ${
                  p === page
                    ? 'bg-neon-cyan/10 text-neon-cyan border-neon-cyan/30'
                    : 'border-white/[0.06] text-gray-500 hover:text-white hover:border-white/20'
                }`}
              >
                {p}
              </button>
            ))}
            <button
              onClick={() => goPage(page + 1)}
              disabled={page >= totalPages}
              className="px-3 py-1 rounded text-xs font-mono border border-white/[0.06] text-gray-500 hover:text-white hover:border-white/20 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  )
}
