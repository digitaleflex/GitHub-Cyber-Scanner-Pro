import { AlertTriangle } from 'lucide-react'

interface Props {
  cveId: string
  description: string
  level: 'CRITIQUE' | 'ELEVE' | 'MOYEN' | 'BAS'
  cvss?: number | null
  epss?: number | null
  isKev?: boolean
  exploits?: number
  onClick?: () => void
}

const levelConfig = {
  CRITIQUE: { color: 'var(--red)', bg: 'var(--red-light)' },
  ELEVE: { color: 'var(--amber)', bg: 'var(--amber-light)' },
  MOYEN: { color: 'var(--cyan)', bg: 'var(--cyan-light)' },
  BAS: { color: 'var(--text-muted)', bg: 'var(--surface-hover)' },
}

export function AlertTile({ cveId, description, level, cvss, epss, isKev, exploits, onClick }: Props) {
  const config = levelConfig[level] || levelConfig.BAS
  return (
    <button
      onClick={onClick}
      className="w-full text-left rounded-xl p-4 transition-all hover:-translate-y-0.5"
      style={{
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        borderLeft: `3px solid ${config.color}`,
      }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="font-mono text-mono font-semibold" style={{ color: 'var(--cyan)' }}>{cveId}</span>
        <span
          className="text-caption px-2 py-0.5 rounded"
          style={{ background: config.bg, color: config.color, border: `1px solid ${config.color}40` }}
        >
          {level}
        </span>
        {isKev && (
          <span className="inline-flex items-center gap-1 text-caption px-2 py-0.5 rounded" style={{ background: 'var(--red-light)', color: 'var(--red)' }}>
            <AlertTriangle size={10} /> KEV
          </span>
        )}
      </div>
      <p className="text-body-sm t-s line-clamp-2 mb-3">{description}</p>
      <div className="flex items-center gap-3 text-caption t-m">
        {cvss != null && <span>CVSS {cvss}</span>}
        {epss != null && <span>EPSS {(epss * 100).toFixed(1)}%</span>}
        {exploits != null && exploits > 0 && <span>{exploits} exploit{exploits > 1 ? 's' : ''}</span>}
      </div>
    </button>
  )
}
