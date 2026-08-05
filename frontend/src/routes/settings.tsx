import { useState, useEffect } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell, Shield, Key, Check } from 'lucide-react'
import { getProfileId } from '../lib/profile'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/settings', component: SettingsPage })

const ROLES = ['rssi', 'devsecops', 'pentester', 'developpeur', 'soc', 'cloud_engineer', 'administrateur', 'etudiant']

function SettingsPage() {
  const qc = useQueryClient()
  const profileId = getProfileId()
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

  if (isLoading) return <div className="flex justify-center py-24"><div className="w-8 h-8 border-2 border-[var(--amber)] border-t-transparent rounded-full animate-spin" /></div>

  const chipStyle = (active: boolean) => ({
    background: active ? 'var(--surface-elevated)' : 'var(--surface)',
    color: active ? 'var(--text)' : 'var(--text-muted)',
    borderColor: active ? 'var(--amber)' : 'var(--border)',
  })

  return (
    <div className="max-w-xl mx-auto py-4 sm:py-8 animate-fade">
      <h1 className="h1 mb-1" style={{ color: 'var(--text)' }}>Paramètres</h1>
      <p className="body-sm text-secondary mb-6">Profil, notifications, préférences.</p>

      <div className="space-y-4">
        <div className="surface rounded-2xl p-5" style={{ border: '1px solid var(--border)' }}>
          <div className="flex items-center gap-2 mb-4">
            <Shield size={15} style={{ color: 'var(--cyan)' }} />
            <h2 className="h3" style={{ color: 'var(--text)' }}>Profil</h2>
          </div>
          <div className="mb-3">
            <label className="caption mb-1.5 block" style={{ color: 'var(--amber)' }}>Rôle</label>
            <div className="flex flex-wrap gap-1.5">
              {ROLES.map(r => (
                <button key={r} onClick={() => setRole(r)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium border capitalize transition-all"
                  style={chipStyle(role === r)}>
                  {r}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="surface rounded-2xl p-5" style={{ border: '1px solid var(--border)' }}>
          <div className="flex items-center gap-2 mb-4">
            <Bell size={15} style={{ color: 'var(--amber)' }} />
            <h2 className="h3" style={{ color: 'var(--text)' }}>Notifications</h2>
          </div>
          <label className="flex items-center justify-between cursor-pointer">
            <span className="body-sm" style={{ color: 'var(--text-secondary)' }}>Alertes urgentes (KEV, exploit actif)</span>
            <button onClick={() => setNotifyUrgent(!notifyUrgent)}
              className="w-10 h-6 rounded-full transition relative"
              style={{ background: notifyUrgent ? 'var(--lime)' : 'var(--border)' }}>
              <span className="absolute top-0.5 w-5 h-5 rounded-full bg-white transition" style={{ left: notifyUrgent ? '1.25rem' : '0.125rem' }} />
            </button>
          </label>
        </div>

        <div className="surface rounded-2xl p-5" style={{ border: '1px solid var(--border)' }}>
          <div className="flex items-center gap-2 mb-4">
            <Key size={15} style={{ color: 'var(--text-muted)' }} />
            <h2 className="h3" style={{ color: 'var(--text)' }}>API & Intégrations</h2>
          </div>
          <p className="text-xs text-muted">Les clés API (HF, Groq, Gemini) sont configurées via les variables d'environnement du conteneur.</p>
        </div>

        <button onClick={save} disabled={saving}
          className="btn-primary w-full justify-center">
          {done ? <><Check size={15} /> Enregistré</> : saving ? 'Enregistrement...' : 'Enregistrer les préférences'}
        </button>
      </div>
    </div>
  )
}
