import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { Shield, Search, Brain, GitBranch, Zap, Globe, Users, Target, Star, CloudLightning, Rocket } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/about', component: AboutPage })

function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto py-8 sm:py-16 animate-fade">
      <div className="text-center mb-10 sm:mb-16">
        <h1 className="text-2xl sm:text-4xl font-bold tracking-tight mb-4 bg-gradient-to-r from-indigo-400 via-white to-violet-400 bg-clip-text text-transparent">
          Transformer le chaos en decisions
        </h1>
        <p className="text-sm sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
          CyberScan Pro reduit 10 000 signaux quotidiens a 20 informations reellement exploitables.
          Collecte, enrichissement, correlation et priorisation automatiques pour les professionnels de la cybersecurite.
        </p>
        <Link to="/" className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl text-sm font-medium hover:bg-indigo-500/20 transition mt-6">
          Lancer l'app
        </Link>
      </div>

      {/* Stats */}
      <div className="glass-card rounded-2xl p-6 mb-8">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6 text-center">
          {[
            { label: 'Sources integrees', value: '30+' },
            { label: 'CVEs', value: '300K+' },
            { label: 'IOCs', value: 'Millions' },
            { label: 'Modeles IA', value: '22' },
          ].map((s, i) => (
            <div key={i}>
              <div className="text-xl sm:text-3xl font-bold text-white">{s.value}</div>
              <div className="text-[10px] sm:text-xs text-slate-500 mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Mission */}
      <div className="glass-card rounded-2xl p-6 mb-8">
        <div className="flex items-center gap-2 mb-4"><Rocket size={18} className="text-indigo-400" /><h2 className="text-base sm:text-lg font-semibold text-white">Notre mission</h2></div>
        <blockquote className="text-sm sm:text-base text-slate-300 leading-relaxed italic border-l-2 border-indigo-500/30 pl-4 mb-4">
          Democratiser la Cyber Threat Intelligence en rendant accessible, gratuitement et en open source,
          une plateforme de veille qui agrege les meilleures sources de donnees cybersecurite au monde.
        </blockquote>
        <div className="flex items-center gap-2 mb-4"><Star size={18} className="text-amber-400" /><h2 className="text-base sm:text-lg font-semibold text-white">Notre vision</h2></div>
        <p className="text-sm text-slate-400 leading-relaxed border-l-2 border-amber-500/30 pl-4">
          Devenir la reference open source de la Threat Intelligence — la plateforme que chaque SOC, chercheur et
          etudiant utilise pour comprendre le paysage des menaces. Financer la recherche par un modele freemium
          equitable ou 90% des fonctionnalites restent gratuites a vie.
        </p>
      </div>

      {/* 6 Pillars */}
      <h2 className="text-sm font-semibold text-white mb-4 text-center">Les 6 piliers</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-8">
        {[
          { icon: <Search size={16} className="text-amber-400" />, title: 'Collecter', desc: '30+ sources: GitHub, NVD, CISA KEV, Exploit-DB, abuse.ch, OTX, OSV, GHSA, Shodan, VirusTotal...' },
          { icon: <Brain size={16} className="text-indigo-400" />, title: 'Enrichir', desc: 'Chaque CVE liee a ses exploits, PoC, IOCs. 22 modeles IA pour verdict, classification, Q&A, detection.' },
          { icon: <GitBranch size={16} className="text-emerald-400" />, title: 'Correler', desc: 'Knowledge Graph Neo4j. CVE ↔ Exploit ↔ Outil ↔ MITRE ATT&CK. Plus rien n\'est isole.' },
          { icon: <Target size={16} className="text-rose-400" />, title: 'Prioriser', desc: 'Pas un CVSS brut. Score intelligent: EPSS, KEV, exploits disponibles, verdict IA.' },
          { icon: <CloudLightning size={16} className="text-violet-400" />, title: 'Automatiser', desc: 'Pipeline d\'ingestion automatise, STIX 2.1 export, IOC feed, MCP server pour agents IA.' },
          { icon: <Globe size={16} className="text-cyan-400" />, title: 'Partager', desc: '100% open source MIT. API publique, STIX/TAXII, MCP. Integration avec MISP, OpenCTI, SIEM.' },
        ].map((p, i) => (
          <div key={i} className="glass-card rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-lg bg-slate-800/50 flex items-center justify-center">{p.icon}</div>
              <h3 className="text-sm font-semibold text-white">{p.title}</h3>
            </div>
            <p className="text-[11px] sm:text-xs text-slate-400 leading-relaxed">{p.desc}</p>
          </div>
        ))}
      </div>

      {/* Who it's for */}
      <h2 className="text-sm font-semibold text-white mb-4 text-center">Pour qui ?</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mb-8">
        {[
          { label: 'Pentesters', icon: <Target size={14} />, desc: 'Nouveaux exploits et PoC' },
          { label: 'Blue Teams', icon: <Shield size={14} />, desc: 'IOCs, Sigma, YARA' },
          { label: 'RSSI', icon: <Users size={14} />, desc: 'Risques, tendances, KPI' },
          { label: 'CERTs', icon: <Globe size={14} />, desc: 'Campagnes, APT, STIX' },
          { label: 'Chercheurs', icon: <Brain size={14} />, desc: 'GitHub, datasets, IA' },
          { label: 'Etudiants', icon: <Zap size={14} />, desc: 'Apprendre et pratiquer' },
        ].map((p, i) => (
          <div key={i} className="glass-card rounded-xl p-3 text-center">
            <div className="flex justify-center mb-1.5 text-indigo-400">{p.icon}</div>
            <div className="text-xs font-medium text-white">{p.label}</div>
            <div className="text-[9px] text-slate-500 mt-0.5">{p.desc}</div>
          </div>
        ))}
      </div>

      {/* Tech Stack */}
      <div className="glass-card rounded-2xl p-6 mb-8">
        <h2 className="text-sm font-semibold text-white mb-3 text-center">Stack Technique</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
          {[
            { cat: 'Backend', techs: 'Python FastAPI, PostgreSQL+pgvector, Neo4j, Celery, Docker' },
            { cat: 'Frontend', techs: 'React 19, TypeScript, Tailwind CSS 4, TanStack Router/Query, Recharts' },
            { cat: 'IA / ML', techs: 'Groq (Llama 3.3), 22 HF models, TF-IDF+SVD, scikit-learn' },
            { cat: 'Infra', techs: 'Docker Compose, Traefik, GitHub Actions CI/CD, auto-hebergement' },
          ].map((t, i) => (
            <div key={i} className="glass rounded-xl p-3">
              <div className="text-[9px] uppercase tracking-widest text-indigo-400 mb-1">{t.cat}</div>
              <p className="text-[10px] text-slate-500 leading-relaxed">{t.techs}</p>
            </div>
          ))}
        </div>
        <div className="flex flex-wrap items-center justify-center gap-2">
          {['NVD API', 'CISA KEV', 'abuse.ch APIs', 'AlienVault OTX', 'OSV.dev', 'GitHub API', 'VirusTotal API', 'Shodan API', 'SecurityTrails API'].map((t, i) => (
            <span key={i} className="glass px-3 py-1 rounded-full text-[10px] text-slate-400">{t}</span>
          ))}
        </div>
      </div>

      {/* Model */}
      <div className="glass-card rounded-2xl p-6 text-center">
        <h2 className="text-sm font-semibold text-white mb-2">Modele economique</h2>
        <p className="text-xs sm:text-sm text-slate-400 max-w-2xl mx-auto leading-relaxed mb-4">
          CyberScan Pro suit un modele <b className="text-white">Open Core / Freemium</b>. La version Community est et restera
          100% gratuite et open source (MIT). Les offres Pro et Enterprise financent l'infrastructure,
          les API premium, et la recherche continue.
        </p>
        <a href="https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro" target="_blank" rel="noopener" className="inline-flex items-center gap-2 px-4 py-2 glass rounded-lg text-xs text-indigo-400 hover:text-white transition">
          Voir le code source
        </a>
        <p className="text-[10px] sm:text-xs text-slate-500 mt-4">
          100% open source &middot; Auto-hebergeable &middot; Licence MIT &middot; <a href="https://cyberbook.eurin.tech" className="text-indigo-400 hover:text-indigo-300">cyberbook.eurin.tech</a>
        </p>
      </div>
    </div>
  )
}
