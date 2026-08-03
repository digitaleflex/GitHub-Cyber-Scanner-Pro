import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { Shield, Check, Zap, Building2 } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/pricing', component: PricingPage })

const TIERS = [
  {
    name: 'Community',
    price: '0€',
    period: 'a vie',
    icon: <Shield size={20} className="text-indigo-400" />,
    color: 'indigo',
    desc: 'Tout ce dont vous avez besoin pour demarrer la veille cyber.',
    features: [
      'GitHub Scanner (224 requetes)',
      'Base CVE (300K+ vulns)',
      'OSINT Lab (7 outils)',
      'Knowledge Graph Neo4j',
      'AI Verdict Groq (limite)',
      '22 modeles HuggingFace',
      'Threat Intel (OTX, abuse.ch)',
      'STIX 2.1 Export',
      'Dashboard + KPI',
      'API REST publique',
      'Auto-hebergement Docker',
      'Open Source MIT',
    ],
    cta: 'Commencer gratuitement',
    href: '/',
  },
  {
    name: 'Pro',
    price: '29€',
    period: '/mois',
    icon: <Zap size={20} className="text-amber-400" />,
    color: 'amber',
    highlight: true,
    desc: 'Pour les professionnels et les petites equipes SOC.',
    features: [
      'Tout Community',
      'GitHub Scanner illimite',
      'VirusTotal API (500 req/j)',
      'Shodan API (50 req)',
      'SecurityTrails API',
      'AI Digest quotidien illimite',
      'API REST 1000 req/j',
      'Export CSV/JSON/PDF',
      'Alertes email/webhook',
      'IOC Feed temps reel',
      'Support email',
      '1 utilisateur',
    ],
    cta: 'Essai 14 jours gratuit',
    href: '#',
  },
  {
    name: 'Enterprise',
    price: '199€',
    period: '/mois',
    icon: <Building2 size={20} className="text-violet-400" />,
    color: 'violet',
    desc: 'Pour les SOC, MSSP et grandes organisations.',
    features: [
      'Tout Pro',
      'Multi-tenant (equipes)',
      'SSO / LDAP / SAML',
      'API illimitee',
      'Webhooks + SIEM integration',
      'SLA 99.9%',
      'Support prioritaire 24/7',
      'On-premise deployment',
      'Custom branding',
      'Formation equipe',
      'Acces early features',
      'Contrat SLA personnalise',
    ],
    cta: 'Contacter les ventes',
    href: '#',
  },
]

function PricingPage() {
  return (
    <div className="max-w-6xl mx-auto py-8 sm:py-16 animate-fade">
      <div className="text-center mb-10">
        <h1 className="text-2xl sm:text-4xl font-bold text-white mb-3">Tarifs simples et transparents</h1>
        <p className="text-sm sm:text-base text-slate-400 max-w-xl mx-auto">
          90% des fonctionnalites sont gratuites et open source. Les offres payantes financent la recherche et l'infrastructure.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
        {TIERS.map((tier, i) => (
          <div key={i} className={`glass-card rounded-2xl p-6 relative ${tier.highlight ? 'border-amber-500/30 ring-1 ring-amber-500/20' : ''}`}>
            {tier.highlight && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-amber-500/20 border border-amber-500/30 text-amber-400 rounded-full text-[10px] font-medium">
                Le plus populaire
              </span>
            )}
            <div className="flex items-center gap-2 mb-3">{tier.icon}<h2 className="text-lg font-bold text-white">{tier.name}</h2></div>
            <div className="mb-1"><span className="text-3xl font-bold text-white">{tier.price}</span><span className="text-slate-500 text-sm ml-1">{tier.period}</span></div>
            <p className="text-xs text-slate-500 mb-4">{tier.desc}</p>
            <a href={tier.href}
              className={`block w-full text-center py-2.5 rounded-xl text-sm font-medium transition mb-6 ${
                tier.highlight
                  ? 'bg-amber-500/20 border border-amber-500/30 text-amber-400 hover:bg-amber-500/30'
                  : 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 hover:bg-indigo-500/20'
              }`}>
              {tier.cta}
            </a>
            <ul className="space-y-2">
              {tier.features.map((f, j) => (
                <li key={j} className="flex items-start gap-2 text-xs">
                  <Check size={12} className={`text-emerald-400 mt-0.5 shrink-0`} />
                  <span className="text-slate-400">{f}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="text-center mt-10 glass-card rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-white mb-2">Pourquoi ce modele ?</h3>
        <p className="text-xs sm:text-sm text-slate-400 max-w-2xl mx-auto leading-relaxed">
          CyberScan Pro est un projet de recherche open source. La version Community restera <b className="text-white">toujours gratuite</b>.
          Les offres Pro et Enterprise financent les serveurs, les API premium, et le developpement de nouvelles fonctionnalites.
          Nous croyons que la democratisation de la Threat Intelligence passe par un acces libre et gratuit.
        </p>
      </div>

      <div className="text-center mt-6">
        <p className="text-xs text-slate-600">
          Prix en euros HT. Facturation annuelle : -20%.{' '}
          <Link to="/about" className="text-indigo-400 hover:text-indigo-300">En savoir plus sur notre mission</Link>
        </p>
      </div>
    </div>
  )
}
