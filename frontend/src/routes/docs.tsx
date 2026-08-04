import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { BookOpen, Database, FileJson, FileSpreadsheet, Shield, Search, Download, Globe, Library, GitBranch, ExternalLink, GraduationCap, Code } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/docs', component: DocsPage })

function DocsPage() {
  return (
    <div className="w-full py-8 sm:py-12 animate-fade">
      <div className="text-center mb-8">
        <h1 className="h1 mb-2" style={{ color: 'var(--text)' }}>Documentation &amp; Recherche</h1>
        <p className="body-sm max-w-xl mx-auto leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          Portail central pour les chercheurs, auditeurs et scientifiques. Toute notre base de connaissances
          est accessible, documentée et exportable — indépendamment du pipeline.
        </p>
      </div>

      {/* ═══ Section 1 : Documentation interne ═══ */}
      <h2 className="h3 mb-3 flex items-center gap-2" style={{ color: 'var(--text)' }}>
        <BookOpen size={18} style={{ color: 'var(--brand-text)' }} /> Documentation de la plateforme
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
        {[
          { to: '/methodology', icon: <GitBranch size={18} />, label: 'Méthodologie', desc: 'Pipeline 6 étapes, formule de scoring, moteur de décision' },
          { to: '/sources', icon: <Globe size={18} />, label: 'Sources', desc: '17 sources de données, licences, fréquences de mise à jour' },
          { to: '/about', icon: <Shield size={18} />, label: 'À propos', desc: 'Mission, vision, 6 piliers, stack technique' },
          { to: '/feedback', icon: <GraduationCap size={18} />, label: 'Contribuer', desc: 'Issues GitHub, suggestions, publications' },
        ].map(doc => (
          <Link key={doc.to} to={doc.to as any}
            className="surface rounded-xl p-4 hover:-translate-y-0.5 transition-all" style={{ border: '1px solid var(--border)', textDecoration: 'none' }}>
            <div className="mb-2" style={{ color: 'var(--brand-text)' }}>{doc.icon}</div>
            <div className="text-sm font-semibold mb-1" style={{ color: 'var(--text)' }}>{doc.label}</div>
            <div className="text-[11px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{doc.desc}</div>
          </Link>
        ))}
      </div>

      {/* ═══ Section 2 : Bibliothèque & Base de données ═══ */}
      <h2 className="h3 mb-3 flex items-center gap-2" style={{ color: 'var(--text)' }}>
        <Database size={18} style={{ color: 'var(--brand-text)' }} /> Base de données — Recherche indépendante
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8">
        {[
          { to: '/library', icon: <Library size={18} />, label: 'Bibliothèque', desc: '19 020 dépôts GitHub · Recherche full-text · Filtres verdict/vitalité · Export CSV', highlight: true },
          { href: '/cves', icon: <Search size={18} />, label: 'Explorateur CVE', desc: '372 899 vulnérabilités · CVSS v2/v3/v4 · CWE · CPE · Patchs · Advisories', external: true },
          { href: '/tools', icon: <Code size={18} />, label: 'Catalogue Outils', desc: '46k exploits · Sigma/YARA/Suricata · Analyse par catégorie', external: true },
        ].map(item => (
          item.to ? (
            <Link key={item.to} to={item.to as any}
              className="surface rounded-xl p-4 hover:-translate-y-0.5 transition-all" style={{ border: item.highlight ? '2px solid var(--brand-text)' : '1px solid var(--border)', textDecoration: 'none' }}>
              <div className="mb-2" style={{ color: item.highlight ? 'var(--brand-text)' : 'var(--text-muted)' }}>{item.icon}</div>
              <div className="text-sm font-semibold mb-1" style={{ color: 'var(--text)' }}>{item.label}</div>
              <div className="text-[11px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{item.desc}</div>
            </Link>
          ) : (
            <Link key={item.href} to={item.href as any}
              className="surface rounded-xl p-4 hover:-translate-y-0.5 transition-all" style={{ border: '1px solid var(--border)', textDecoration: 'none' }}>
              <div className="mb-2" style={{ color: 'var(--text-muted)' }}>{item.icon}</div>
              <div className="text-sm font-semibold mb-1" style={{ color: 'var(--text)' }}>{item.label}</div>
              <div className="text-[11px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{item.desc}</div>
            </Link>
          )
        ))}
      </div>

      {/* ═══ Section 3 : Export & API ═══ */}
      <h2 className="h3 mb-3 flex items-center gap-2" style={{ color: 'var(--text)' }}>
        <Download size={18} style={{ color: 'var(--brand-text)' }} /> Exports &amp; API — Données brutes pour analyse externe
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8">
        {[
          { href: '/api/download', icon: <FileSpreadsheet size={18} />, label: 'Export Excel', desc: 'Catalogue complet en .xlsx · Repos, CVE, scores · Admin requis' },
          { href: '/api/download/json', icon: <FileJson size={18} />, label: 'Export JSON', desc: 'Données brutes en JSON · Format machine-readable · Admin requis' },
          { href: '/api/stix/download?what=cves&limit=500', icon: <Shield size={18} />, label: 'Export STIX 2.1', desc: 'Format standard CTI · Compatible MISP, OpenCTI · CVE + IOCs + techniques' },
        ].map(exp => (
          <a key={exp.href} href={exp.href} target="_blank" rel="noopener noreferrer"
            className="surface rounded-xl p-4 hover:-translate-y-0.5 transition-all" style={{ border: '1px solid var(--border)', textDecoration: 'none' }}>
            <div className="mb-2" style={{ color: 'var(--decision)' }}>{exp.icon}</div>
            <div className="text-sm font-semibold mb-1 flex items-center gap-1" style={{ color: 'var(--text)' }}>
              {exp.label} <ExternalLink size={11} style={{ color: 'var(--text-muted)' }} />
            </div>
            <div className="text-[11px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{exp.desc}</div>
          </a>
        ))}
      </div>

      {/* ═══ Section 4 : Pour les chercheurs ═══ */}
      <h2 className="h3 mb-3 flex items-center gap-2" style={{ color: 'var(--text)' }}>
        <GraduationCap size={18} style={{ color: 'var(--ai)' }} /> Pour les chercheurs &amp; scientifiques
      </h2>
      <div className="surface rounded-xl p-5 mb-8" style={{ border: '1px solid var(--border)' }}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-[11px] sm:text-xs" style={{ color: 'var(--text-secondary)' }}>
          <div>
            <h4 className="text-sm font-semibold mb-1.5" style={{ color: 'var(--text)' }}>🔬 Données utilisables pour vos travaux</h4>
            <ul className="space-y-1 list-disc list-inside">
              <li>372k CVE enrichies (CVSS, KEV, EPSS, CWE, CPE)</li>
              <li>46k exploits avec code source</li>
              <li>19k IOCs (URLhaus, ThreatFox)</li>
              <li>1 140 techniques MITRE ATT&CK</li>
              <li>9 643 règles de détection (Sigma, YARA, Suricata)</li>
              <li>2.4M produits affectés (CPE)</li>
              <li>355k scores EPSS de probabilité d'exploitation</li>
              <li>32k correctifs + 22k advisories éditeurs</li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold mb-1.5" style={{ color: 'var(--text)' }}>📊 Formats disponibles</h4>
            <ul className="space-y-1 list-disc list-inside">
              <li><strong>STIX 2.1</strong> — standard CTI interopérable</li>
              <li><strong>JSON</strong> — format machine-readable</li>
              <li><strong>Excel (.xlsx)</strong> — analyse manuelle</li>
              <li><strong>API REST</strong> — endpoints documentés</li>
              <li><strong>CSV</strong> (via Excel)</li>
            </ul>
            <h4 className="text-sm font-semibold mb-1.5 mt-3" style={{ color: 'var(--text)' }}>📝 Pour nous citer</h4>
            <div className="text-[10px] font-mono rounded-lg p-2.5" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)', color: 'var(--text-secondary)' }}>
              Eurin, T. (2025). HashCode Decision OS — Plateforme open-source de Cyber Threat Intelligence. https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro
            </div>
          </div>
        </div>
      </div>

      {/* ═══ Section 5 : Contact ═══ */}
      <div className="flex flex-col sm:flex-row gap-3 justify-center text-sm">
        <Link to="/contact" className="btn-primary inline-flex items-center gap-2">Nous contacter</Link>
        <a href="https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro" target="_blank" rel="noopener noreferrer"
          className="btn-secondary inline-flex items-center gap-2">
          <Code size={16} /> Code source (MIT)
        </a>
      </div>
    </div>
  )
}
