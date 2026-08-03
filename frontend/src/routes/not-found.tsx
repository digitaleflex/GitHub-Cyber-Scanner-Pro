import { Link } from '@tanstack/react-router'
import { Shield } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center animate-fade">
      <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500/20 to-violet-500/20 border border-indigo-500/20 flex items-center justify-center mb-6">
        <Shield size={32} className="text-indigo-400" />
      </div>
      <h1 className="text-4xl font-bold text-white mb-2">404</h1>
      <p className="text-slate-400 mb-6">Page introuvable</p>
      <div className="flex gap-3">
        <Link to="/" className="px-4 py-2 glass rounded-lg text-sm text-indigo-400 hover:text-white transition">Accueil</Link>
        <Link to="/search" className="px-4 py-2 glass rounded-lg text-sm text-slate-400 hover:text-white transition">Rechercher</Link>
      </div>
    </div>
  )
}
