import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { Globe, ShieldAlert, Brain, FileSearch, Server, ExternalLink, BarChart3 } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/sources', component: SourcesPage })

function SourcesPage() {
  const categories = [
    {
      icon: <ShieldAlert size={16} style={{ color: 'var(--danger)' }} />,
      title: 'Vulnérabilités & Exploits',
      sources: [
        { name: 'NVD (National Vulnerability Database)', url: 'https://nvd.nist.gov/', freq: 'Mise à jour continue (API 2.0)', data: '372 899 CVE, descriptions, CVSS v2/v3/v4, CWE, CPE, références, correctifs, advisories éditeurs', license: 'Domaine public (US Gov)' },
        { name: 'CISA KEV (Known Exploited Vulnerabilities)', url: 'https://www.cisa.gov/known-exploited-vulnerabilities-catalog', freq: 'Mise à jour quotidienne', data: '1 657 CVE activement exploitées, date d\'ajout, action requise, campagne ransomware associée', license: 'Domaine public (US Gov)' },
        { name: 'Exploit-DB (Offensive Security)', url: 'https://www.exploit-db.com/', freq: 'Mise à jour quotidienne', data: '46 636 exploits, code source, plateforme cible, type d\'exploit, date de publication', license: 'Domaine public' },
        { name: 'GitHub Security Advisories (GHSA)', url: 'https://github.com/advisories', freq: 'Mise à jour continue', data: 'Advisories de sécurité des dépôts GitHub, versions affectées, correctifs', license: 'Open (GitHub)' },
      ],
    },
    {
      icon: <BarChart3 size={16} style={{ color: 'var(--warning)' }} />,
      title: 'Scoring & Classification',
      sources: [
        { name: 'CVSS (Common Vulnerability Scoring System)', url: 'https://www.first.org/cvss/', freq: 'Inclus dans les données NVD', data: 'Scores CVSS v3.1, v3.0, v2.0, v4.0, vecteurs d\'attaque, sévérité qualitative', license: 'Standard ouvert (FIRST.org)' },
        { name: 'EPSS (Exploit Prediction Scoring System)', url: 'https://www.first.org/epss', freq: 'Mise à jour quotidienne', data: '355 094 scores de probabilité d\'exploitation (0-1), percentile (0-1), date', license: 'Domaine public (FIRST.org)' },
        { name: 'CWE (Common Weakness Enumeration)', url: 'https://cwe.mitre.org/', freq: 'Inclus dans les données NVD', data: '297 850 CVE classifiées, 747 types de faiblesses distincts (CWE-79 XSS, CWE-89 SQLi...)', license: 'Domaine public (MITRE)' },
        { name: 'CAPEC (Common Attack Pattern Enumeration)', url: 'https://capec.mitre.org/', freq: 'Mapping statique CWE→CAPEC', data: '1 017 mappings de patterns d\'attaque (CAPEC-63 XSS, CAPEC-66 SQLi, CAPEC-88 CMDi...)', license: 'Domaine public (MITRE)' },
      ],
    },
    {
      icon: <Globe size={16} style={{ color: 'var(--brand)' }} />,
      title: 'Threat Intelligence',
      sources: [
        { name: 'MITRE ATT&CK', url: 'https://attack.mitre.org/', freq: 'Mise à jour via bundles STIX locaux', data: '1 140 techniques, 193 groupes APT, 136 campagnes, 21 025 relations (uses, mitigates, detects...), 729 malwares, 95 outils', license: 'Domaine public (MITRE)' },
        { name: 'URLhaus (abuse.ch)', url: 'https://urlhaus.abuse.ch/', freq: 'Mise à jour continue', data: 'IOCs URLs malveillantes, type de menace, tags, malware associé, date de première observation', license: 'CC0 (domaine public)' },
        { name: 'ThreatFox (abuse.ch)', url: 'https://threatfox.abuse.ch/', freq: 'Mise à jour continue', data: 'IOCs IP/hash/domaine, famille de malware, confidence level, tags, contexte', license: 'CC0 (domaine public)' },
        { name: 'AlienVault OTX', url: 'https://otx.alienvault.com/', freq: 'Mise à jour continue', data: 'Pulses OTX, IOCs, indicateurs de compromission, campagnes', license: 'Open (AT&T)' },
      ],
    },
    {
      icon: <FileSearch size={16} style={{ color: 'var(--ai)' }} />,
      title: 'Détection & Règles',
      sources: [
        { name: 'Sigma Rules (SigmaHQ)', url: 'https://github.com/SigmaHQ/sigma', freq: 'Mise à jour quotidienne (GitHub)', data: '3 141 règles Sigma, titre, description, source, tactique MITRE, niveau de sévérité', license: 'Open source (MIT)' },
        { name: 'YARA Rules (Yara-Rules)', url: 'https://github.com/Yara-Rules/rules', freq: 'Mise à jour quotidienne (GitHub)', data: '5 941 règles YARA, nom, description, source, URL du fichier', license: 'Open source (GPL)' },
        { name: 'Suricata/Snort IDS Rules', url: 'https://www.snort.org/', freq: 'Mise à jour quotidienne', data: '561 règles IDS, moteur, SID, message, sévérité, référence CVE', license: 'Open source (GPLv2)' },
      ],
    },
    {
      icon: <Server size={16} style={{ color: 'var(--info)' }} />,
      title: 'Code Source & Repositories',
      sources: [
        { name: 'GitHub API (recherche thématique)', url: 'https://docs.github.com/en/rest', freq: 'Scan périodique (toutes les 30 min)', data: '19 020 dépôts scannés, stars, forks, description, langages, verdict de sécurité, score de vitalité', license: 'API GitHub (rate limits)' },
        { name: 'GitHub Advisory Database', url: 'https://github.com/advisories', freq: 'Mise à jour continue', data: 'Advisories de dépendances (npm, pip, maven...), CVE liées, versions corrigées', license: 'CC-BY 4.0' },
      ],
    },
    {
      icon: <Brain size={16} style={{ color: 'var(--ai)' }} />,
      title: 'IA & Modèles',
      sources: [
        { name: 'Groq (Llama 3.3 70B)', url: 'https://groq.com/', freq: 'Appel à la demande (batch 300/h)', data: 'Résumé CVE en français, impact métier, plan de remédiation, mapping ATT&CK via LLM', license: 'API Groq (gratuit, rate-limited)' },
        { name: 'HuggingFace (22 modèles)', url: 'https://huggingface.co/', freq: 'Appel à la demande', data: 'Classification de texte, analyse de sentiment, détection de malware, NER, Q&A', license: 'Open source (modèles HF)' },
      ],
    },
  ]

  return (
    <div className="max-w-[900px] mx-auto py-8 sm:py-16 animate-fade">
      <div className="text-center mb-10">
        <h1 className="h1 mb-2" style={{ color: 'var(--text)' }}>Sources de données</h1>
        <p className="body-sm w-full leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          Transparence totale : chaque source, sa licence, sa fréquence de mise à jour et les données extraites.
          Tout est vérifiable publiquement.
        </p>
      </div>

      <div className="space-y-6">
        {categories.map((cat, ci) => (
          <div key={ci}>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'var(--bg-alt)' }}>{cat.icon}</div>
              <h2 className="h3" style={{ color: 'var(--text)' }}>{cat.title}</h2>
            </div>
            <div className="grid grid-cols-1 gap-2">
              {cat.sources.map((s, si) => (
                <div key={si} className="surface rounded-xl p-4" style={{ border: '1px solid var(--border)' }}>
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-sm font-semibold hover:underline flex items-center gap-1" style={{ color: 'var(--text)' }}>
                        {s.name} <ExternalLink size={12} style={{ color: 'var(--text-muted)' }} />
                      </a>
                      <div className="text-[10px] text-muted mt-0.5">{s.license} · {s.freq}</div>
                    </div>
                  </div>
                  <p className="text-[11px] sm:text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{s.data}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="surface rounded-2xl p-5 mt-8 text-center" style={{ border: '1px solid var(--border)' }}>
        <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          Toutes les sources listées ci-dessus sont <b style={{ color: 'var(--text)' }}>publiques, gratuites et vérifiables</b>.
          Aucune donnée propriétaire n'est utilisée. Les métadonnées de chaque source (licence, fréquence, volume) sont
          documentées pour permettre un audit indépendant complet.
        </p>
        <p className="text-[10px] text-muted mt-2">
          Dernière mise à jour de cette page : {new Date().toLocaleDateString('fr-FR', { year: 'numeric', month: 'long' })}
        </p>
      </div>
    </div>
  )
}
