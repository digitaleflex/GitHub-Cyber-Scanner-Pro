import { useState, useEffect } from 'react'
import { createRoute, useNavigate } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { Lock } from 'lucide-react'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/login',
  component: LoginPage,
})

const AUTH_KEY = 'cyberscan_admin_auth'

export function getAuthToken(): string | null {
  return sessionStorage.getItem(AUTH_KEY)
}

export function setAuthToken(user: string, pass: string) {
  sessionStorage.setItem(AUTH_KEY, btoa(`${user}:${pass}`))
}

export function clearAuthToken() {
  sessionStorage.removeItem(AUTH_KEY)
}

export function isAdminAuthenticated(): boolean {
  return getAuthToken() !== null
}

export function getAuthHeaders(): Record<string, string> {
  const token = getAuthToken()
  if (!token) return {}
  return { Authorization: `Basic ${token}` }
}

function LoginPage() {
  const [user, setUser] = useState('')
  const [pass, setPass] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    if (isAdminAuthenticated()) navigate({ to: '/cves' })
  }, [navigate])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    const headers = { Authorization: `Basic ${btoa(`${user}:${pass}`)}` }
    try {
      const r = await fetch('/api/stats', { headers })
      if (r.ok) {
        setAuthToken(user, pass)
        navigate({ to: '/cves' })
      } else {
        setError('Identifiants invalides')
      }
    } catch {
      setError('Erreur réseau')
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-20">
      <div className="text-center mb-6">
        <div className="w-12 h-12 mx-auto bg-indigo-500/20 border border-indigo-500/30 rounded-xl flex items-center justify-center mb-3">
          <Lock size={22} className="text-indigo-400" />
        </div>
        <h1 className="text-xl font-semibold text-white">Admin</h1>
        <p className="text-sm text-slate-500 mt-1">Authentification requise</p>
      </div>
      <form onSubmit={handleLogin} className="space-y-3">
        <input type="text" value={user} onChange={e => setUser(e.target.value)}
          placeholder="Utilisateur" autoFocus
          className="w-full px-3 py-2.5 bg-slate-900/80 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/30" />
        <input type="password" value={pass} onChange={e => setPass(e.target.value)}
          placeholder="Mot de passe"
          className="w-full px-3 py-2.5 bg-slate-900/80 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/30" />
        {error && <p className="text-xs text-rose-400">{error}</p>}
        <button type="submit"
          className="w-full py-2.5 bg-indigo-500/20 border border-indigo-500/40 text-indigo-400 rounded-lg text-sm font-medium hover:bg-indigo-500/30 transition">
          Se connecter
        </button>
      </form>
    </div>
  )
}
