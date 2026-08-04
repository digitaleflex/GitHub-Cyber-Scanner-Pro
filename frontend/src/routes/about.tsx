import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { Shield, Search, Brain, GitBranch, Zap, Globe, Users, Target, Star, CloudLightning, Rocket } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/about', component: AboutPage })

function AboutPage() {
  return (
    <div className="max-w-[900px] mx-auto py-8 sm:py-16 animate-fade">
      <div className="text-center mb-10 sm:mb-16">
        <h1 className="h1 mb-4" style={{ color: 'var(--text)' }}>
          Transformer le chaos en <span style={{ color: 'var(--brand)' }}>décisions</span>
        </h1>
        <p className="body-sm sm:text-lg w-full leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          CyberScan Pro réduit 10 000 signaux quotidiens à 20 informations réellement exploitables.
          Collecte, enrichissement, corrélation et priorisation automatiques pour les professionnels de la cybersécurité.
        </p>
        <Link to="/" className="btn-primary inline-flex mt-6">
          Lancer l'app
        </Link>
      </div>

      {/* Stats */}
      <div className="surface rounded-2xl p-6 mb-8" style={{ border: '1px solid var(--border)' }}>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6 text-center">
          {[
            { label: 'Sources intégrées', value: '30+' },
            { label: 'CVEs', value: '300K+' },
            { label: 'IOCs', value: 'Millions' },
            { label: 'Modèles IA', value: '22' },
          ].map((s, i) => (
            <div key={i}>
              <div className="text-xl sm:text-3xl font-bold" style={{ color: 'var(--text)' }}>{s.value}</div>
              <div className="text-[10px] sm:text-xs text-muted mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Mission */}
      <div className="surface rounded-2xl p-6 mb-8" style={{ border: '1px solid var(--border)' }}>
        <div className="flex items-center gap-2 mb-4"><Rocket size={18} style={{ color: 'var(--info)' }} /><h2 className="h2" style={{ color: 'var(--text)' }}>Notre mission</h2></div>
        <blockquote className="body-sm sm:text-base leading-relaxed italic pl-4 mb-4" style={{ color: 'var(--text-secondary)', borderLeft: '2px solid var(--info)' }}>
          Démocratiser la Cyber Threat Intelligence en rendant accessible, gratuitement et en open source,
          une plateforme de veille qui agrège les meilleures sources de données cybersécurité au monde.
        </blockquote>
        <div className="flex items-center gap-2 mb-4"><Star size={18} style={{ color: 'var(--warning)' }} /><h2 className="h2" style={{ color: 'var(--text)' }}>Notre vision</h2></div>
        <p className="body-sm leading-relaxed pl-4" style={{ color: 'var(--text-secondary)', borderLeft: '2px solid var(--warning)' }}>
          Devenir la référence open source de la Threat Intelligence — la plateforme que chaque SOC, chercheur et
          étudiant utilise pour comprendre le paysage des menaces. Financer la recherche par un modèle freemium
          équitable où 90% des fonctionnalités restent gratuites à vie.
        </p>
      </div>

      {/* 6 Pillars */}
      <h2 className="h3 text-center mb-4" style={{ color: 'var(--text)' }}>Les 6 piliers</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-8">
        {[
          { icon: <Search size={16} style={{ color: 'var(--warning)' }} />, title: 'Collecter', desc: '30+ sources: GitHub, NVD, CISA KEV, Exploit-DB, abuse.ch, OTX, OSV, GHSA, Shodan, VirusTotal...' },
          { icon: <Brain size={16} style={{ color: 'var(--ai)' }} />, title: 'Enrichir', desc: 'Chaque CVE liée à ses exploits, PoC, IOCs. 22 modèles IA pour verdict, classification, Q&A, détection.' },
          { icon: <GitBranch size={16} style={{ color: 'var(--brand)' }} />, title: 'Corréler', desc: "Knowledge Graph Neo4j. CVE ↔ Exploit ↔ Outil ↔ MITRE ATT&CK. Plus rien n'est isolé." },
          { icon: <Target size={16} style={{ color: 'var(--danger)' }} />, title: 'Prioriser', desc: 'Pas un CVSS brut. Score intelligent: EPSS, KEV, exploits disponibles, verdict IA.' },
          { icon: <CloudLightning size={16} style={{ color: 'var(--ai)' }} />, title: 'Automatiser', desc: 'Pipeline d\'ingestion automatisé, STIX 2.1 export, IOC feed, MCP server pour agents IA.' },
          { icon: <Globe size={16} style={{ color: '#06B6D4' }} />, title: 'Partager', desc: '100% open source MIT. API publique, STIX/TAXII, MCP. Intégration avec MISP, OpenCTI, SIEM.' },
        ].map((p, i) => (
          <div key={i} className="surface rounded-xl p-4" style={{ border: '1px solid var(--border)' }}>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'var(--bg-alt)' }}>{p.icon}</div>
              <h3 className="h3" style={{ color: 'var(--text)' }}>{p.title}</h3>
            </div>
            <p className="text-[11px] sm:text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{p.desc}</p>
          </div>
        ))}
      </div>

      {/* Who it's for */}
      <h2 className="h3 text-center mb-4" style={{ color: 'var(--text)' }}>Pour qui ?</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mb-8">
        {[
          { label: 'Pentesters', icon: <Target size={14} />, desc: 'Nouveaux exploits et PoC' },
          { label: 'Blue Teams', icon: <Shield size={14} />, desc: 'IOCs, Sigma, YARA' },
          { label: 'RSSI', icon: <Users size={14} />, desc: 'Risques, tendances, KPI' },
          { label: 'CERTs', icon: <Globe size={14} />, desc: 'Campagnes, APT, STIX' },
          { label: 'Chercheurs', icon: <Brain size={14} />, desc: 'GitHub, datasets, IA' },
          { label: 'Étudiants', icon: <Zap size={14} />, desc: 'Apprendre et pratiquer' },
        ].map((p, i) => (
          <div key={i} className="surface rounded-xl p-3 text-center" style={{ border: '1px solid var(--border)' }}>
            <div className="flex justify-center mb-1.5" style={{ color: 'var(--info)' }}>{p.icon}</div>
            <div className="text-xs font-medium" style={{ color: 'var(--text)' }}>{p.label}</div>
            <div className="text-[9px] text-muted mt-0.5">{p.desc}</div>
          </div>
        ))}
      </div>

      {/* Tech Stack */}
      <div className="surface rounded-2xl p-6 mb-8" style={{ border: '1px solid var(--border)' }}>
        <h2 className="h3 text-center mb-3" style={{ color: 'var(--text)' }}>Stack Technique</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
          {[
            { cat: 'Backend', techs: 'Python FastAPI, PostgreSQL+pgvector, Neo4j, Celery, Docker' },
            { cat: 'Frontend', techs: 'React 19, TypeScript, Tailwind CSS 4, TanStack Router/Query, Recharts' },
            { cat: 'IA / ML', techs: 'Groq (Llama 3.3), 22 HF models, TF-IDF+SVD, scikit-learn' },
            { cat: 'Infra', techs: 'Docker Compose, Traefik, GitHub Actions CI/CD, auto-hébergement' },
          ].map((t, i) => (
            <div key={i} className="rounded-xl p-3" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
              <div className="caption mb-1" style={{ color: 'var(--brand)' }}>{t.cat}</div>
              <p className="text-[10px] leading-relaxed text-muted">{t.techs}</p>
            </div>
          ))}
        </div>
        <div className="flex flex-wrap items-center justify-center gap-2">
          {['NVD API', 'CISA KEV', 'abuse.ch APIs', 'AlienVault OTX', 'OSV.dev', 'GitHub API', 'VirusTotal API', 'Shodan API', 'SecurityTrails API'].map((t, i) => (
            <span key={i} className="text-[10px] px-3 py-1 rounded-full" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}>{t}</span>
          ))}
        </div>
      </div>

      {/* Model */}
      <div className="surface rounded-2xl p-6 text-center" style={{ border: '1px solid var(--border)' }}>
        <h2 className="h3 mb-2" style={{ color: 'var(--text)' }}>Modèle économique</h2>
        <p className="text-xs sm:text-sm w-full leading-relaxed mb-4" style={{ color: 'var(--text-secondary)' }}>
          CyberScan Pro suit un modèle <b style={{ color: 'var(--text)' }}>Open Core / Freemium</b>. La version Community est et restera
          100% gratuite et open source (MIT). Les offres Pro et Enterprise financent l'infrastructure,
          les API premium, et la recherche continue.
        </p>
        <a href="https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro" target="_blank" rel="noopener"
          className="btn-secondary inline-flex text-xs">
          Voir le code source
        </a>
        <p className="text-[10px] sm:text-xs text-muted mt-4">
          100% open source &middot; Auto-hébergeable &middot; Licence MIT &middot; <a href="https://cyberbook.eurin.tech" style={{ color: 'var(--info-text)' }}>cyberbook.eurin.tech</a>
        </p>
      </div>
    </div>
  )
}
