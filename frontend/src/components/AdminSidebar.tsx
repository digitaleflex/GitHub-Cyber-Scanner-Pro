import { Link } from '@tanstack/react-router'
import { Shield, Hash, GitGraph, FileText, LogOut, Settings } from 'lucide-react'
import { clearAuthToken } from '../routes/login'

const links = [
  { to: '/admin', label: 'Dashboard', icon: <Settings size={14} />, desc: 'Contrôles & statuts' },
  { to: '/cves', label: 'CVEs', icon: <Shield size={14} />, desc: '56 000 vulnérabilités' },
  { to: '/keywords', label: 'Mots-clés', icon: <Hash size={14} />, desc: '4 071 termes cyber' },
  { to: '/graph', label: 'Graph', icon: <GitGraph size={14} />, desc: 'Neo4j relations' },
  { to: '/reports', label: 'Rapports', icon: <FileText size={14} />, desc: 'Exports & dashboards' },
]

export default function AdminSidebar() {
  return (
    <aside className="w-56 shrink-0">
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 sticky top-4">
        <div className="mb-4 pb-3 border-b border-slate-800">
          <h3 className="text-xs font-semibold text-indigo-400 uppercase tracking-widest mb-0.5">Administration</h3>
          <p className="text-[10px] text-slate-500">CyberScan Pro v3.1</p>
        </div>

        <nav className="space-y-0.5">
          {links.map(l => (
            <Link key={l.to} to={l.to}
              className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs transition group [&.active]:bg-indigo-500/10 [&.active]:text-indigo-400 hover:bg-slate-800/50 text-slate-400">
              <span className="[&.active]:text-indigo-400 text-slate-500 group-hover:text-slate-300">{l.icon}</span>
              <div>
                <div className="text-slate-300 group-hover:text-white">{l.label}</div>
                <div className="text-[9px] text-slate-500">{l.desc}</div>
              </div>
            </Link>
          ))}
        </nav>

        <div className="mt-4 pt-3 border-t border-slate-800">
          <button
            onClick={() => { clearAuthToken(); window.location.href = '/' }}
            className="flex items-center gap-2 px-2.5 py-2 w-full rounded-lg text-xs text-slate-500 hover:text-rose-400 hover:bg-rose-500/5 transition"
          >
            <LogOut size={12} /> Déconnexion
          </button>
        </div>
      </div>
    </aside>
  )
}
