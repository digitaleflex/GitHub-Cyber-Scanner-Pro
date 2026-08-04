import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { Mail, Github, MessageCircle, Globe, Send } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/contact', component: ContactPage })

function ContactPage() {
  const contacts = [
    {
      icon: <Mail size={20} style={{ color: 'var(--brand-text)' }} />,
      title: 'Email direct',
      desc: 'Pour les demandes professionnelles, partenariats, ou questions confidentielles.',
      action: 'contact@eurin.tech',
      href: 'mailto:contact@eurin.tech',
    },
    {
      icon: <Github size={20} style={{ color: 'var(--brand-text)' }} />,
      title: 'GitHub Issues',
      desc: 'Bugs, suggestions, contributions techniques. Le moyen le plus rapide d\'obtenir une réponse.',
      action: 'github.com/digitaleflex/GitHub-Cyber-Scanner-Pro/issues',
      href: 'https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro/issues',
    },
    {
      icon: <MessageCircle size={20} style={{ color: 'var(--brand-text)' }} />,
      title: 'Discussions GitHub',
      desc: 'Échanges techniques, questions d\'architecture, propositions de design, roadmap.',
      action: 'github.com/digitaleflex/GitHub-Cyber-Scanner-Pro/discussions',
      href: 'https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro/discussions',
    },
    {
      icon: <Globe size={20} style={{ color: 'var(--brand-text)' }} />,
      title: 'Site web',
      desc: 'Documentation complète, API reference, guides de déploiement et cas d\'usage.',
      action: 'cyberbook.eurin.tech',
      href: 'https://cyberbook.eurin.tech',
    },
  ]

  return (
    <div className="w-full py-8 sm:py-16 animate-fade">
      <div className="text-center mb-10">
        <h1 className="h1 mb-2" style={{ color: 'var(--text)' }}>Nous contacter</h1>
        <p className="body-sm max-w-lg mx-auto leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          Une question, une collaboration, un bug, une idée ? Choisissez le canal le plus adapté.
          Réponse sous 48h en moyenne.
        </p>
      </div>

      <div className="space-y-3 mb-8">
        {contacts.map((c, i) => (
          <a key={i} href={c.href} target="_blank" rel="noopener noreferrer"
            className="surface rounded-xl p-4 flex items-start gap-4 hover:border transition-colors" style={{ border: '1px solid var(--border)' }}>
            <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: 'var(--bg-alt)' }}>
              {c.icon}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-sm font-semibold mb-0.5" style={{ color: 'var(--text)' }}>{c.title}</div>
              <p className="text-[11px] leading-relaxed mb-1" style={{ color: 'var(--text-secondary)' }}>{c.desc}</p>
              <span className="text-xs font-mono flex items-center gap-1" style={{ color: 'var(--text-muted)' }}>
                {c.action} <Send size={10} />
              </span>
            </div>
          </a>
        ))}
      </div>

      <div className="surface rounded-2xl p-5 text-center" style={{ border: '1px solid var(--border)' }}>
        <h2 className="h3 mb-2" style={{ color: 'var(--text)' }}>Pour les chercheurs &amp; scientifiques</h2>
        <p className="text-xs leading-relaxed mb-3 max-w-md mx-auto" style={{ color: 'var(--text-secondary)' }}>
          Vous travaillez sur une publication, une thèse, ou un projet de recherche en cybersécurité ?
          Nous pouvons vous fournir des datasets, des accès API dédiés, ou collaborer sur des analyses conjointes.
        </p>
        <a href="mailto:contact@eurin.tech?subject=Recherche%20CyberScan%20Pro"
          className="btn-primary inline-flex items-center gap-2 text-sm">
          <Mail size={16} /> Contacter l'équipe recherche
        </a>
        <p className="text-[10px] text-muted mt-3">
          Licence MIT · Code source ouvert · Données publiques vérifiables
        </p>
      </div>
    </div>
  )
}
