import { useState } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { FileText, Download, RefreshCw } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/reports', component: ReportsPage })

function ReportsPage() {
  const [report, setReport] = useState('')
  const [generating, setGenerating] = useState(false)
  const [orgName, setOrgName] = useState('')

  const generate = async () => {
    setGenerating(true)
    const r = await fetch('/api/reports/generate?profile_id=1')
    const d = await r.json()
    setReport(d.report)
    setOrgName(d.org_name)
    setGenerating(false)
  }

  const download = () => {
    const blob = new Blob([report], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `rapport-securite-${orgName || 'hashcode'}.md`; a.click()
  }

  return (
    <div className="max-w-2xl mx-auto py-4 sm:py-8 animate-fade">
      <h1 className="h1 mb-1" style={{ color: 'var(--text)' }}>Rapports</h1>
      <p className="body-sm text-secondary mb-6">Comment communiquer ? Générez des rapports pour la direction, les audits et la conformité.</p>

      <div className="surface rounded-2xl p-5 sm:p-6 mb-6" style={{ border: '1px solid var(--border)' }}>
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'var(--surface-elevated)' }}>
            <FileText size={18} style={{ color: 'var(--cyan)' }} />
          </div>
          <div>
            <h2 className="h3" style={{ color: 'var(--text)' }}>Rapport de sécurité</h2>
            <p className="text-xs text-muted">Résumé exécutif, menaces actives, recommandations</p>
          </div>
        </div>
        <button onClick={generate} disabled={generating}
          className="btn-primary w-full justify-center">
          {generating ? <><RefreshCw size={15} className="animate-spin" /> Génération...</> : 'Générer le rapport'}
        </button>
      </div>

      {report && (
        <div className="surface rounded-2xl p-5 sm:p-6" style={{ border: '1px solid var(--border)' }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="h3" style={{ color: 'var(--text)' }}>Aperçu</h2>
            <button onClick={download} className="btn-secondary text-xs">
              <Download size={12} /> Télécharger
            </button>
          </div>
          <pre className="text-xs whitespace-pre-wrap mono rounded-xl p-4 max-h-96 overflow-auto leading-relaxed"
            style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
            {report}
          </pre>
        </div>
      )}
    </div>
  )
}
