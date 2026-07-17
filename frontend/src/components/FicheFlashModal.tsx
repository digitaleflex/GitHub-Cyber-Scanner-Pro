import { X, Star, Shield, Activity, Code2, ExternalLink, GitBranch, Calendar } from 'lucide-react'
import type { Repo } from '../lib/api'

type Props = {
  repo: Repo
  onClose: () => void
}

const VERDICT_DETAILS: Record<string, { label: string; color: string; glow: string }> = {
  Critique: { label: 'Critique', color: 'text-neon-red border-neon-red/30 bg-neon-red/10', glow: 'shadow-[0_0_20px_rgba(255,0,68,0.15)]' },
  Suspect: { label: 'Suspect', color: 'text-neon-amber border-neon-amber/30 bg-neon-amber/10', glow: 'shadow-[0_0_20px_rgba(255,187,0,0.15)]' },
  Sain: { label: 'Sain', color: 'text-neon-green border-neon-green/30 bg-neon-green/10', glow: 'shadow-[0_0_20px_rgba(0,255,102,0.15)]' },
}

function formatDate(d: string): string {
  if (!d) return '—'
  const date = new Date(d)
  return date.toLocaleDateString('fr-FR', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
}

export default function FicheFlashModal({ repo, onClose }: Props) {
  const v = VERDICT_DETAILS[repo.security_verdict ?? ''] ?? null
  const vitalityColor = repo.vitality_score != null && repo.vitality_score >= 70
    ? 'text-neon-green'
    : repo.vitality_score != null && repo.vitality_score >= 40
      ? 'text-neon-amber'
      : 'text-neon-red'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      <div
        className="relative bg-[#0d1225] border border-white/[0.1] rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto animate-fade-in-up neon-border-cyan"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-6 pb-4 border-b border-white/[0.06]">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-lg font-cyber font-bold text-white truncate">{repo.name}</h2>
            </div>
            <p className="text-gray-500 text-sm font-mono mt-1 line-clamp-2">{repo.desc || 'Aucune description'}</p>
            {repo.synopsis && (
              <p className="text-neon-cyan/70 text-xs font-mono mt-2 italic leading-relaxed">
                {repo.synopsis}
              </p>
            )}
            {repo.semantic_category && (
              <span className="inline-flex mt-2 px-2 py-0.5 rounded-full bg-neon-magenta/10 border border-neon-magenta/30 text-neon-magenta text-[10px] font-mono tracking-wider">
                {repo.semantic_category.toUpperCase()}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="shrink-0 ml-4 p-1.5 rounded-lg text-gray-600 hover:text-neon-cyan hover:bg-white/[0.05] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50"
            aria-label="Fermer"
          >
            <X size={20} />
          </button>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-4 p-6">
          {/* Stars */}
          <div className="bg-white/[0.03] rounded-xl p-4 border border-white/[0.06]">
            <div className="flex items-center gap-2 text-neon-amber mb-1">
              <Star size={16} />
              <span className="text-xs font-mono text-gray-500 tracking-wider">STARS</span>
            </div>
            <span className="text-2xl font-bold font-mono text-neon-amber">
              {repo.stars.toLocaleString()}
            </span>
          </div>

          {/* Vitality */}
          <div className="bg-white/[0.03] rounded-xl p-4 border border-white/[0.06]">
            <div className="flex items-center gap-2 mb-1">
              <Activity size={16} className={vitalityColor} />
              <span className="text-xs font-mono text-gray-500 tracking-wider">VITALITÉ</span>
            </div>
            <span className={`text-2xl font-bold font-mono ${vitalityColor}`}>
              {repo.vitality_score ?? '—'}
            </span>
            <span className="text-gray-600 text-xs font-mono ml-1">/100</span>
          </div>

          {/* Language */}
          <div className="bg-white/[0.03] rounded-xl p-4 border border-white/[0.06]">
            <div className="flex items-center gap-2 text-neon-cyan mb-1">
              <Code2 size={16} />
              <span className="text-xs font-mono text-gray-500 tracking-wider">LANGAGE</span>
            </div>
            <span className="text-lg font-bold font-mono text-gray-300">
              {repo.lang || '?'}
            </span>
          </div>

          {/* Security */}
          <div className={`bg-white/[0.03] rounded-xl p-4 border ${v ? v.color : 'border-white/[0.06]'} ${v ? v.glow : ''}`}>
            <div className="flex items-center gap-2 mb-1">
              <Shield size={16} className={v?.color ?? 'text-gray-500'} />
              <span className="text-xs font-mono text-gray-500 tracking-wider">SÉCURITÉ</span>
            </div>
            <span className={`text-lg font-bold font-mono ${v?.color ?? 'text-gray-500'}`}>
              {repo.security_verdict || 'Non audité'}
            </span>
          </div>
        </div>

        {/* Details row */}
        <div className="px-6 pb-4 flex flex-wrap gap-4 text-xs font-mono text-gray-600">
          <div className="flex items-center gap-1.5">
            <Calendar size={12} />
            Mis à jour : {formatDate(repo.updated)}
          </div>
          <div className="flex items-center gap-1.5">
            <GitBranch size={12} />
            Créé : {formatDate(repo.created)}
          </div>
        </div>

        {/* Actions */}
        <div className="px-6 pb-6 flex gap-3">
          <a
            href={repo.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2.5 bg-neon-cyan/10 border border-neon-cyan/30 rounded-lg text-neon-cyan text-sm font-mono hover:bg-neon-cyan/20 hover:border-neon-cyan/50 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50"
          >
            <ExternalLink size={14} />
            Voir sur GitHub
          </a>
        </div>
      </div>
    </div>
  )
}
