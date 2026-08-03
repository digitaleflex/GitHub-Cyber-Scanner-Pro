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
      <h1 className="text-xl sm:text-2xl font-semibold text-white mb-1">Rapports</h1>
      <p className="text-sm text-slate-500 mb-6">Comment communiquer ? Generez des rapports pour la direction, les audits et la conformite.</p>

      <div className="glass-card rounded-2xl p-5 sm:p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center"><FileText size={18} className="text-indigo-400" /></div>
          <div>
            <h2 className="text-sm font-semibold text-white">Rapport de securite</h2>
            <p className="text-xs text-slate-500">Resume executif, menaces actives, recommandations</p>
          </div>
        </div>
        <button onClick={generate} disabled={generating}
          className="w-full px-4 py-2.5 rounded-xl bg-indigo-500 text-white text-sm font-medium hover:bg-indigo-400 disabled:opacity-40 transition flex items-center justify-center gap-2">
          {generating ? <><RefreshCw size={15} className="animate-spin" /> Generation...</> : <>Generer le rapport</>}
        </button>
      </div>

      {report && (
        <div className="glass-card rounded-2xl p-5 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white">Apercu</h2>
            <button onClick={download}
              className="px-3 py-1.5 glass rounded-lg text-xs text-emerald-400 hover:text-white transition flex items-center gap-1.5">
              <Download size={12} /> Telecharger
            </button>
          </div>
          <pre className="text-xs text-slate-300 whitespace-pre-wrap font-mono bg-slate-900/50 rounded-xl p-4 max-h-96 overflow-auto leading-relaxed">
            {report}
          </pre>
        </div>
      )}
    </div>
  )
}
