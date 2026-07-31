import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { Shield, Search, Brain, GitBranch, Zap, Globe, Users, Target } from 'lucide-react'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/about',
  component: AboutPage,
})

const PILLARS = [
  { icon: <Search size={16} className="text-amber-400" />, title: 'Collecter', desc: 'GitHub, NVD, CISA KEV, Exploit-DB, FeodoTracker, Awesome Lists, APIs abuse.ch, MITRE ATT&CK — une seule source de verite.' },
  { icon: <Brain size={16} className="text-indigo-400" />, title: 'Enrichir', desc: 'Chaque CVE est liee a ses exploits, ses PoC, ses IOCs. Intelligence artificielle pour le verdict de securite et les resumes automatiques.' },
  { icon: <GitBranch size={16} className="text-emerald-400" />, title: 'Correler', desc: 'Graphe de connaissances Neo4j. CVE ↔ Exploit ↔ Outil ↔ MITRE ATT&CK. Plus rien n\'est isole.' },
  { icon: <Target size={16} className="text-rose-400" />, title: 'Prioriser', desc: 'Pas un CVSS brut. Un score intelligent: exploit dispo ? Exploite activement ? Concerne vos technos ?' },
  { icon: <Zap size={16} className="text-violet-400" />, title: 'Expliquer', desc: 'Debutant ou expert : un resume clair + les details techniques. Ce qui est important, pourquoi, et quoi faire.' },
  { icon: <Globe size={16} className="text-cyan-400" />, title: 'Agir', desc: 'API publique, webhooks, exports STIX/JSON/PDF. Integration avec vos outils existants.' },
]

function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto py-8 sm:py-16 animate-fade">
      {/* Hero */}
      <div className="text-center mb-10 sm:mb-16">
        <h1 className="text-2xl sm:text-4xl font-bold tracking-tight mb-4 bg-gradient-to-r from-indigo-400 via-white to-violet-400 bg-clip-text text-transparent">
          Transformer le chaos en decisions
        </h1>
        <p className="text-sm sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
          CyberScan Pro reduit 10 000 signaux quotidiens a 20 informations reellement exploitables.
          Collecte, enrichissement, correlation et priorisation automatiques pour les professionnels de la cybersecurite.
        </p>
      </div>

      {/* Stats */}
      <div className="glass-card rounded-2xl p-6 sm:p-8 mb-8 sm:mb-12">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6 text-center">
          {[
            { label: 'Outils indexes', value: '7 000+' },
            { label: 'CVE', value: '56 000+' },
            { label: 'Mots-cles', value: '50 000+' },
            { label: 'Exploits', value: '46 000+' },
          ].map((s, i) => (
            <div key={i}>
              <div className="text-xl sm:text-3xl font-bold text-white">{s.value}</div>
              <div className="text-[10px] sm:text-xs text-slate-500 mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Mission */}
      <div className="glass-card rounded-2xl p-6 sm:p-8 mb-8 sm:mb-12">
        <div className="flex items-center gap-2 mb-4">
          <Shield size={18} className="text-indigo-400" />
          <h2 className="text-base sm:text-lg font-semibold text-white">Notre mission</h2>
        </div>
        <blockquote className="text-sm sm:text-base text-slate-300 leading-relaxed italic border-l-2 border-indigo-500/30 pl-4">
          Collecter, verifier, enrichir, correler, prioriser et expliquer les informations de cybersecurite
          afin de fournir, au bon moment, les bonnes decisions aux bonnes personnes.
        </blockquote>
      </div>

      {/* Pillars */}
      <h2 className="text-base sm:text-lg font-semibold text-white mb-4 sm:mb-6 text-center">Les 6 piliers</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mb-8 sm:mb-12">
        {PILLARS.map((p, i) => (
          <div key={i} className="glass-card rounded-xl p-4 sm:p-5">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-lg bg-slate-800/50 flex items-center justify-center">{p.icon}</div>
              <h3 className="text-sm font-semibold text-white">{p.title}</h3>
            </div>
            <p className="text-[11px] sm:text-xs text-slate-400 leading-relaxed">{p.desc}</p>
          </div>
        ))}
      </div>

      {/* Who it's for */}
      <h2 className="text-base sm:text-lg font-semibold text-white mb-4 sm:mb-6 text-center">Pour qui ?</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 sm:gap-3 mb-8 sm:mb-12">
        {[
          { label: 'Pentesters', icon: <Target size={14} />, desc: 'Nouveaux exploits et PoC' },
          { label: 'Blue Teams', icon: <Shield size={14} />, desc: 'IOCs, Sigma, YARA' },
          { label: 'RSSI', icon: <Users size={14} />, desc: 'Risques, tendances, KPI' },
          { label: 'CERTs', icon: <Globe size={14} />, desc: 'Campagnes, APT, STIX' },
          { label: 'Chercheurs', icon: <Brain size={14} />, desc: 'GitHub, arXiv, conferences' },
          { label: 'Etudiants', icon: <Zap size={14} />, desc: 'Apprendre et pratiquer' },
        ].map((p, i) => (
          <div key={i} className="glass-card rounded-xl p-3 text-center">
            <div className="flex justify-center mb-1.5 text-indigo-400">{p.icon}</div>
            <div className="text-xs font-medium text-white">{p.label}</div>
            <div className="text-[9px] sm:text-[10px] text-slate-500 mt-0.5">{p.desc}</div>
          </div>
        ))}
      </div>

      {/* Tech stack */}
      <div className="glass-card rounded-2xl p-6 sm:p-8 text-center">
        <h2 className="text-sm font-semibold text-white mb-3">Technologies</h2>
        <div className="flex flex-wrap items-center justify-center gap-2">
          {[
            'Python FastAPI', 'React TypeScript', 'PostgreSQL + pgvector',
            'Neo4j', 'Groq AI (llama 3.3)', 'TF-IDF + SVD',
            'Docker Compose', 'Traefik', 'GitHub API', 'abuse.ch APIs',
          ].map((t, i) => (
            <span key={i} className="glass px-3 py-1 rounded-full text-[10px] sm:text-xs text-slate-400">{t}</span>
          ))}
        </div>
        <p className="text-[10px] sm:text-xs text-slate-600 mt-4">
          100% open source &middot; Auto-hebergeable &middot; Licence MIT
        </p>
      </div>
    </div>
  )
}
