import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { Lightbulb, Bug, Sparkles, BookOpen, GitPullRequest, Github, ExternalLink } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/feedback', component: FeedbackPage })

function FeedbackPage() {
  const categories = [
    { icon: <Sparkles size={18} />, title: 'Suggestion d\'amélioration', tag: 'enhancement', desc: 'Proposer une nouvelle fonctionnalité, une meilleure UI, une source de données supplémentaire.' },
    { icon: <Bug size={18} />, title: 'Rapport de bug', tag: 'bug', desc: 'Signaler un comportement inattendu, une donnée incorrecte, un crash ou une lenteur.' },
    { icon: <Lightbulb size={18} />, title: 'Idée de recherche', tag: 'research', desc: 'Proposer une piste de recherche, une nouvelle métrique, un modèle IA, une corrélation innovante.' },
    { icon: <BookOpen size={18} />, title: 'Documentation / Publication', tag: 'documentation', desc: 'Suggérer une amélioration de la documentation, citer nos travaux, proposer une publication conjointe.' },
  ]

  const gh = 'https://github.com/digitaleflex/GitHub-Cyber-Scanner-Pro/issues/new'

  return (
    <div className="max-w-[900px] mx-auto py-8 sm:py-16 animate-fade">
      <div className="text-center mb-10">
        <h1 className="h1 mb-2" style={{ color: 'var(--text)' }}>Contribuer &amp; Améliorer</h1>
        <p className="body-sm max-w-xl mx-auto leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
          Chercheurs, scientifiques, ingénieurs — vos retours façonnent la plateforme.
          Chaque suggestion est lue, évaluée et souvent intégrée dans les sprints suivants.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-8">
        {categories.map((cat, i) => (
          <a key={i} href={`${gh}?template=feature_request.md&labels=${cat.tag}`} target="_blank" rel="noopener noreferrer"
            className="surface rounded-xl p-4 hover:border transition-colors flex flex-col gap-2" style={{ border: '1px solid var(--border)' }}>
            <div className="flex items-center gap-2">
              <span style={{ color: 'var(--amber)' }}>{cat.icon}</span>
              <span className="text-sm font-semibold" style={{ color: 'var(--text)' }}>{cat.title}</span>
            </div>
            <p className="text-[11px] leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{cat.desc}</p>
            <span className="text-[10px] flex items-center gap-1" style={{ color: 'var(--text-muted)' }}>Ouvrir une issue <ExternalLink size={10} /></span>
          </a>
        ))}
      </div>

      <div className="surface rounded-2xl p-5 mb-6 text-center" style={{ border: '1px solid var(--border)' }}>
        <h2 className="h3 mb-3" style={{ color: 'var(--text)' }}>Processus de contribution</h2>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-center text-xs">
          {[
            { step: '1', label: 'Vous soumettez', desc: 'Issue GitHub avec le template approprié' },
            { step: '2', label: 'On trie', desc: 'Évaluation sous 48h, label priorité, assignation' },
            { step: '3', label: 'On discute', desc: 'Échange technique dans le fil de discussion' },
            { step: '4', label: 'On intègre', desc: 'PR, review, merge, déploiement en production' },
          ].map((s, i) => (
            <div key={i}>
              <div className="w-8 h-8 rounded-full flex items-center justify-center mx-auto mb-1.5 text-sm font-bold" style={{ background: 'var(--surface-elevated)', color: 'var(--amber)', border: '1px solid var(--border)' }}>{s.step}</div>
              <div className="font-medium mb-0.5" style={{ color: 'var(--text)' }}>{s.label}</div>
              <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{s.desc}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <a href={gh} target="_blank" rel="noopener noreferrer"
          className="btn-primary inline-flex items-center gap-2 text-sm">
          <Github size={16} /> Ouvrir une issue sur GitHub
        </a>
        <a href={`${gh}?template=feature_request.md&labels=research`} target="_blank" rel="noopener noreferrer"
          className="btn-secondary inline-flex items-center gap-2 text-sm">
          <GitPullRequest size={16} /> Proposer une Pull Request
        </a>
      </div>

      <p className="text-[10px] text-muted text-center mt-4">
        Licence MIT · 100% open source · Toute contribution est créditée dans le changelog
      </p>
    </div>
  )
}
