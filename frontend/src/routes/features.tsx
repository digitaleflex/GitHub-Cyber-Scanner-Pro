import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { Search, Star, Shield, Brain, Globe, Bug, Activity, GitBranch, Download, CloudLightning, ShieldCheck, MapPin, Radio, ExternalLink, Zap, TrendingUp, ArrowRight } from 'lucide-react'
import Chip from '../components/Chip'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/features', component: FeaturesPage })

const SOURCES = [
  { category: 'Vulnerabilites', items: [
    { name: 'NVD / CVE', desc: '300K+ vulnerabilites, CVSS, CWE, CPE', icon: Shield, status: 'gratuit' },
    { name: 'CISA KEV', desc: 'Vulnerabilites exploitees activement', icon: ShieldCheck, status: 'gratuit' },
    { name: 'FIRST EPSS', desc: 'Score de probabilite d\'exploitation', icon: TrendingUp, status: 'gratuit' },
    { name: 'Exploit-DB', desc: '46K+ exploits, PoC, shellcode', icon: Bug, status: 'gratuit' },
    { name: 'GitHub Advisories', desc: 'GHSA - vulnerabilites Open Source', icon: Star, status: 'gratuit' },
    { name: 'OSV.dev', desc: 'Google Open Source Vulnerabilities (20+ ecosystems)', icon: Globe, status: 'gratuit' },
  ]},
  { category: 'Threat Intelligence', items: [
    { name: 'AlienVault OTX', desc: '20M+ pulses, 40M+ IOCs', icon: Globe, status: 'gratuit' },
    { name: 'ThreatFox', desc: '1M+ IOCs (IP, domain, hash)', icon: Activity, status: 'gratuit' },
    { name: 'URLhaus', desc: '3M+ URLs malveillantes', icon: ExternalLink, status: 'gratuit' },
    { name: 'FeodoTracker', desc: 'C2 servers, botnets', icon: Zap, status: 'gratuit' },
    { name: 'Ransomware.live', desc: 'Groupes, victimes, rancons', icon: Bug, status: 'gratuit' },
    { name: 'MISP Feed', desc: 'Open source threat sharing', icon: Shield, status: 'gratuit' },
  ]},
  { category: 'Malware & Detection', items: [
    { name: 'MalwareBazaar', desc: '1.5M+ echantillons, signatures', icon: Bug, status: 'gratuit' },
    { name: 'SSL Blacklist', desc: 'Certificats SSL malveillants', icon: Shield, status: 'gratuit' },
    { name: 'SigmaHQ', desc: '1000+ regles detection SIEM/EDR', icon: Search, status: 'gratuit' },
    { name: 'YARAify', desc: 'Regles YARA + hunting', icon: Activity, status: 'gratuit' },
    { name: 'Package Advisories', desc: 'PyPI, npm, Maven, Ruby, Rust', icon: Download, status: 'gratuit' },
  ]},
  { category: 'Frameworks', items: [
    { name: 'MITRE ATT&CK', desc: '200+ techniques, groupes APT', icon: Shield, status: 'gratuit' },
    { name: 'D3FEND', desc: 'Contre-mesures, defenses', icon: ShieldCheck, status: 'gratuit' },
    { name: 'CAPEC', desc: 'Patterns d\'attaque', icon: Activity, status: 'gratuit' },
    { name: 'CWE', desc: 'Faiblesses de code', icon: Bug, status: 'gratuit' },
  ]},
  { category: 'GitHub Scanner', items: [
    { name: '224 requetes', desc: 'Red/Blue Team, Cloud, Malware, OSINT...', icon: GitBranch, status: 'gratuit' },
    { name: 'Slicer temporel', desc: 'Decouverte par tranches', icon: Activity, status: 'gratuit' },
    { name: 'Dorking Engine', desc: 'Code Search profond', icon: Search, status: 'gratuit' },
    { name: 'Anti-noise', desc: 'Filtrage forks, tutos, awesome-lists', icon: Shield, status: 'gratuit' },
  ]},
  { category: 'Premium APIs', items: [
    { name: 'VirusTotal', desc: '2B+ fichiers, 70 AV engines', icon: ShieldCheck, status: 'pro' },
    { name: 'Shodan', desc: '5B+ devices, banners, vulns', icon: MapPin, status: 'pro' },
    { name: 'SecurityTrails', desc: '4B+ DNS, 1B+ domaines, 500M+ certs', icon: Radio, status: 'pro' },
    { name: 'GreyNoise', desc: 'Internet noise analysis', icon: Globe, status: 'pro' },
  ]},
]

function FeaturesPage() {
  return (
    <div className="max-w-6xl mx-auto py-8 sm:py-12 animate-fade">
      <div className="text-center mb-10">
        <h1 className="text-2xl sm:text-4xl font-bold text-white mb-3">Fonctionnalites</h1>
        <p className="text-sm sm:text-base text-slate-400 max-w-2xl mx-auto">
          CyberScan Pro agrege <b className="text-white">30+ sources de donnees</b> cybersecurite — la majorite 100% gratuites et open source.
        </p>
      </div>

      {/* AI + Tech stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3 mb-10">
        {[
          { value: '30+', label: 'Sources integrees', icon: <CloudLightning size={16} className="text-cyan-400" /> },
          { value: '22', label: 'Modeles HF', icon: <Brain size={16} className="text-violet-400" /> },
          { value: 'STIX 2.1', label: 'Export natif', icon: <Download size={16} className="text-indigo-400" /> },
          { value: 'MCP', label: 'AI Server', icon: <Activity size={16} className="text-emerald-400" /> },
        ].map((x, i) => (
          <div key={i} className="glass-card rounded-xl p-3 text-center">
            <div className="flex justify-center mb-1">{x.icon}</div>
            <div className="text-lg font-bold text-white">{x.value}</div>
            <div className="text-[9px] text-slate-500">{x.label}</div>
          </div>
        ))}
      </div>

      {/* Sources grid */}
      <div className="space-y-6">
        {SOURCES.map((cat, i) => (
          <div key={i}>
            <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <span className="text-slate-500">{cat.category}</span>
              <span className="flex-1 h-px bg-white/[0.05]" />
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {cat.items.map((src, j) => {
                const Icon = src.icon
                return (
                  <div key={j} className="glass-card rounded-xl p-3 flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-slate-800/50 flex items-center justify-center shrink-0">
                      <Icon size={14} className={src.status === 'pro' ? 'text-amber-400' : 'text-slate-400'} />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium text-slate-200">{src.name}</span>
                        <Chip variant={src.status === 'pro' ? 'severity' : 'status'} value={src.status === 'pro' ? 'pro' : 'ok'} />
                      </div>
                      <p className="text-[10px] text-slate-500 mt-0.5">{src.desc}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="text-center mt-10">
        <Link to="/pricing" className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl text-sm font-medium hover:bg-indigo-500/20 transition">
          Voir les offres <ArrowRight size={12} />
        </Link>
      </div>
    </div>
  )
}
