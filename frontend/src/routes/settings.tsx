import { useState, useEffect } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell, Shield, Key, Check } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/settings', component: SettingsPage })

const ROLES = ['rssi', 'devsecops', 'pentester', 'developpeur', 'soc', 'cloud_engineer', 'administrateur', 'etudiant']

function SettingsPage() {
  const qc = useQueryClient()
  const profileId = 1
  const { data, isLoading } = useQuery({
    queryKey: ['settings', profileId],
    queryFn: () => fetch(`/api/settings?profile_id=${profileId}`).then(r => r.json()),
  })
  const [role, setRole] = useState('')
  const [notifyUrgent, setNotifyUrgent] = useState(true)
  const [saving, setSaving] = useState(false)
  const [done, setDone] = useState(false)

  useEffect(() => {
    if (data) {
      setRole(data.role || '')
      setNotifyUrgent(data.preferences?.notify_urgent !== false)
    }
  }, [data])

  const save = async () => {
    setSaving(true)
    await fetch(`/api/settings?profile_id=${profileId}&role=${role}&preferences=${encodeURIComponent(JSON.stringify({ notify_urgent: notifyUrgent }))}`, { method: 'POST' })
    setSaving(false)
    setDone(true)
    qc.invalidateQueries({ queryKey: ['settings'] })
    setTimeout(() => setDone(false), 2000)
  }

  if (isLoading) return <div className="flex justify-center py-24"><div className="w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" /></div>

  return (
    <div className="max-w-xl mx-auto py-4 sm:py-8 animate-fade">
      <h1 className="text-xl sm:text-2xl font-semibold text-white mb-1">Parametres</h1>
      <p className="text-sm text-slate-500 mb-6">Profil, notifications, preferences.</p>

      <div className="space-y-4">
        <div className="glass-card rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Shield size={15} className="text-indigo-400" />
            <h2 className="text-sm font-semibold text-white">Profil</h2>
          </div>
          <div className="mb-3">
            <label className="text-[10px] uppercase tracking-widest text-slate-500 mb-1.5 block">Role</label>
            <div className="flex flex-wrap gap-1.5">
              {ROLES.map(r => (
                <button key={r} onClick={() => setRole(r)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition border capitalize ${
                    role === r ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'glass text-slate-500 hover:text-slate-300'
                  }`}>
                  {r}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Bell size={15} className="text-amber-400" />
            <h2 className="text-sm font-semibold text-white">Notifications</h2>
          </div>
          <label className="flex items-center justify-between cursor-pointer">
            <span className="text-sm text-slate-300">Alertes urgentes (KEV, exploit actif)</span>
            <button onClick={() => setNotifyUrgent(!notifyUrgent)}
              className={`w-10 h-6 rounded-full transition relative ${notifyUrgent ? 'bg-emerald-500' : 'bg-slate-700'}`}>
              <span className={`absolute top-0.5 w-5 h-5 rounded-full bg-white transition ${notifyUrgent ? 'left-5' : 'left-0.5'}`} />
            </button>
          </label>
        </div>

        <div className="glass-card rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Key size={15} className="text-slate-500" />
            <h2 className="text-sm font-semibold text-white">API & Integrations</h2>
          </div>
          <p className="text-xs text-slate-500">Les cles API (HF, Groq, Gemini) sont configurees via les variables d'environnement du conteneur.</p>
        </div>

        <button onClick={save} disabled={saving}
          className="w-full px-4 py-3 rounded-xl bg-emerald-500 text-white text-sm font-medium hover:bg-emerald-400 disabled:opacity-40 transition flex items-center justify-center gap-2">
          {done ? <><Check size={15} /> Enregistre</> : saving ? 'Enregistrement...' : 'Enregistrer les preferences'}
        </button>
      </div>
    </div>
  )
}
