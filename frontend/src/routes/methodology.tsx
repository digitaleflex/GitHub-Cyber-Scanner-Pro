import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { Database, Layers, Brain, Target, Shield, GitBranch, Cpu } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/methodology', component: MethodologyPage })

function MethodologyPage() {
  const sections = [
    {
      icon: <Database size={16} style={{ color: 'var(--mission)' }} />,
      title: '1. Collecte automatisée',
      desc: 'Le pipeline ingère quotidiennement les données de plus de 15 sources officielles : NVD (372k CVE), CISA KEV (1 657 vulnérabilités activement exploitées), Exploit-DB (46k exploits), MITRE ATT&CK (1 140 techniques), abuse.ch (19k IOCs URLhaus/ThreatFox), SigmaHQ (3 141 règles de détection), YARA (5 941 règles), et 19k dépôts GitHub thématiques. Chaque source est interrogée via son API officielle ou ses flux de données publics.',
      badges: ['NVD API 2.0', 'CISA KEV', 'Exploit-DB', 'MITRE ATT&CK', 'abuse.ch', 'SigmaHQ', 'GitHub API'],
    },
    {
      icon: <Layers size={16} style={{ color: 'var(--ai)' }} />,
      title: '2. Enrichissement & Normalisation',
      desc: 'Chaque CVE reçoit un enrichissement multi-couches automatique : produits affectés (CPE — 2.4M entrées, 83% de couverture), EPSS (355k scores de probabilité d\'exploitation), CWE (classification de faiblesse, 297k CVE couvertes), CAPEC (1 017 mappings de patterns d\'attaque), et correctifs + advisories éditeurs. Les données sont normalisées dans un schéma relationnel unifié (PostgreSQL).',
      badges: ['CPE 2.4M', 'EPSS 355k', 'CWE 297k', 'CAPEC 1 017', 'Patches', 'Advisories'],
    },
    {
      icon: <GitBranch size={16} style={{ color: 'var(--brand-text)' }} />,
      title: '3. Corrélation & Mapping',
      desc: 'Un moteur de mapping automatique relie chaque CVE aux référentiels MITRE : techniques ATT&CK (368 mappings via LLM Groq + seed NVD), campagnes et APT (1 290 liens transitifs via le graphe STIX), IOCs (3 900 via heuristique acteur→malware→tags abuse.ch), et CAPEC (1 017 via CWE). Le graphe de connaissances (Neo4j) connecte CVE ↔ exploit ↔ outil ↔ dépôt GitHub pour une vue holistique.',
      badges: ['MITRE ATT&CK', 'STIX 2.1', 'Neo4j', 'Groq LLM'],
    },
    {
      icon: <Target size={16} style={{ color: 'var(--critical)' }} />,
      title: '4. Scoring & Priorisation',
      desc: 'Trois scores indépendants sont calculés : (a) Threat Priority Score (0-100) — combine CVSS, statut KEV, exploits disponibles et ancienneté ; (b) HashScore — score de réputation du dépôt GitHub basé sur stars, forks, activité et qualité du code ; (c) Risk Engine contextuel — multiplie le score de base par la criticité des actifs (×1.0 à ×1.5) et la surface d\'exposition. Le score final = ThreatPriority × MultiplicateurContexte.',
      badges: ['ThreatPriority 0-100', 'HashScore', 'Risk Engine', 'EPSS 0-1', 'CVSS v3/v4'],
    },
    {
      icon: <Brain size={16} style={{ color: 'var(--ai)' }} />,
      title: '5. IA — Analyse & Résumé',
      desc: 'Un daemon IA (Groq, modèle Llama 3.3 70B) analyse automatiquement les CVE prioritaires et génère en français : un résumé de la vulnérabilité, l\'impact métier, un plan de remédiation concret (version corrigée, actions), la vraisemblance d\'exploitation (FAIBLE/MOYEN/CRITIQUE), et l\'audience prioritaire. Les analyses sont persistées dans une table dédiée cve_analysis.',
      badges: ['Groq API', 'Llama 3.3 70B', 'Français', 'Batch 300/h'],
    },
    {
      icon: <Shield size={16} style={{ color: 'var(--decision)' }} />,
      title: '6. Decision Engine',
      desc: 'Le moteur de décision combine les signaux (ThreatPriority, RiskEngine, verdict IA) pour produire une recommandation actionnable : CORRECTIF IMMÉDIAT, SURVEILLANCE RENFORCÉE, ou EN ATTENTE. Un système de feedback utilisateur (calibration) permet d\'affiner la précision au fil du temps. Chaque décision est auditable : tous les facteurs et poids sont exposés dans l\'API.',
      badges: ['Décision auditée', 'Feedback loop', 'Calibration'],
    },
  ]

  return (
    <div className="w-full py-8 sm:py-16 animate-fade">
      <div className="text-center mb-10">
        <h1 className="h1 mb-2" style={{ color: 'var(--text)' }}>Méthodologie</h1>
        <p className="body-sm w-full leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          Comment CyberScan Pro transforme les données brutes en décisions actionnables.
          Un processus transparent, vérifiable et reproductible en 6 étapes.
        </p>
      </div>

      <div className="space-y-4">
        {sections.map((s, i) => (
          <div key={i} className="surface rounded-2xl p-5" style={{ border: '1px solid var(--border)' }}>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'var(--bg-alt)' }}>{s.icon}</div>
              <h2 className="h3" style={{ color: 'var(--text)' }}>{s.title}</h2>
            </div>
            <p className="text-xs sm:text-sm leading-relaxed mb-3" style={{ color: 'var(--text-secondary)' }}>{s.desc}</p>
            <div className="flex flex-wrap gap-1.5">
              {s.badges.map((b, j) => (
                <span key={j} className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)', color: 'var(--text-muted)' }}>{b}</span>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="surface rounded-2xl p-5 mt-8 text-center" style={{ border: '1px solid var(--border)' }}>
        <div className="flex items-center justify-center gap-2 mb-2"><Cpu size={18} style={{ color: 'var(--brand-text)' }} /><h2 className="h3" style={{ color: 'var(--text)' }}>Formule de score final</h2></div>
        <div className="inline-block rounded-xl p-4 text-sm font-mono" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border)', color: 'var(--text)' }}>
          Score<sub>final</sub> = ThreatPriority<sub>0-100</sub> × Multiplicateur<sub>contexte</sub> <span style={{ color: 'var(--text-muted)' }}>(×1.0 – ×1.5)</span>
        </div>
        <p className="text-[10px] text-muted mt-2">Multiplicateur contexte = 1 + 0.06×(criticité−1) + 0.15×exposé + 0.15×KEV∧exposé</p>
        <p className="text-[10px] text-muted mt-2">Tous les facteurs, poids et seuils sont documentés, auditables et configurables.</p>
      </div>
    </div>
  )
}
