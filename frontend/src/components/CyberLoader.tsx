import { Shield, Cpu, Radar } from 'lucide-react'

export function CyberLoader({ text = 'Analyse en cours...' }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 animate-fade" role="status" aria-label={text}>
      {/* Icône centrale avec triple animation */}
      <div className="relative mb-6">
        {/* Anneau pulsant externe */}
        <div className="absolute inset-0 w-20 h-20 rounded-full mx-auto -mt-10 -ml-10"
          style={{ border: '2px solid var(--brand)', opacity: 0.15, animation: 'pulse-ring 2s ease-out infinite' }} />
        {/* Anneau scan */}
        <div className="absolute w-20 h-20 rounded-full mx-auto -mt-10 -ml-10"
          style={{
            border: '2px solid transparent',
            borderTopColor: 'var(--brand)',
            opacity: 0.5,
            animation: 'spin-scan 1.5s linear infinite',
          }} />
        <div className="absolute w-16 h-16 rounded-full mx-auto -mt-8 -ml-8"
          style={{
            border: '2px solid transparent',
            borderRightColor: 'var(--ai)',
            opacity: 0.3,
            animation: 'spin-scan 2s linear infinite reverse',
          }} />
        <Shield size={32} className="relative z-10" style={{
          color: 'var(--brand)',
          animation: 'pulse-brand-loader 2s ease-in-out infinite',
        }} />
      </div>

      {/* Texte animé */}
      <p className="text-xs font-mono tracking-wider" style={{
        color: 'var(--text-secondary)',
        animation: 'fade-text 1.5s ease-in-out infinite',
      }}>
        {text}
      </p>

      {/* Barre de progression infinie */}
      <div className="mt-4 w-48 h-1 rounded-full overflow-hidden" style={{ background: 'var(--bg-alt)' }}>
        <div className="h-full rounded-full" style={{
          background: 'linear-gradient(90deg, var(--brand), var(--ai), var(--warning))',
          width: '30%',
          animation: 'slide-bar 1.2s ease-in-out infinite',
        }} />
      </div>

      {/* Légende */}
      <div className="flex items-center gap-3 mt-6 text-[10px]" style={{ color: 'var(--text-muted)' }}>
        <div className="flex items-center gap-1">
          <Cpu size={10} />
          <span>Groq IA</span>
        </div>
        <span className="w-1 h-1 rounded-full" style={{ background: 'var(--border)' }} />
        <div className="flex items-center gap-1">
          <Radar size={10} />
          <span>NVD</span>
        </div>
        <span className="w-1 h-1 rounded-full" style={{ background: 'var(--border)' }} />
        <div className="flex items-center gap-1">
          <Shield size={10} />
          <span>MITRE</span>
        </div>
      </div>
    </div>
  )
}

export function PageLoader({ text }: { text?: string }) {
  return (
    <div className="max-w-4xl mx-auto">
      <CyberLoader text={text ?? 'Chargement de la page...'} />
    </div>
  )
}

export function DecisionLoader() {
  return (
    <div className="card-hero p-8 animate-fade" role="status" aria-label="Analyse de la décision" style={{ border: '1px solid var(--border)' }}>
      <CyberLoader text="Calcul de la décision..." />
    </div>
  )
}
