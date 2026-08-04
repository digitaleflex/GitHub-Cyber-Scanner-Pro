import { useState, useEffect } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, ArrowRight } from 'lucide-react'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/organization',
  component: OrganizationPage,
})

const ROLES = ['rssi', 'devsecops', 'pentester', 'developpeur', 'soc', 'cloud_engineer', 'administrateur', 'etudiant']
const SECTORS = ['finance', 'sante', 'defense', 'education', 'tech', 'industrie', 'energie', 'gouvernement', 'consulting', 'pme', 'startup', 'autre']
const COMPLIANCE_OPTS = ['PCI DSS', 'ISO 27001', 'NIST', 'SOC2', 'HIPAA', 'RGPD', 'OWASP', 'NIS2', 'DORA', 'Aucune']

function OrganizationPage() {
  const qc = useQueryClient()
  const profileId = 1
  const { data, isLoading } = useQuery({
    queryKey: ['organization', profileId],
    queryFn: () => fetch(`/api/organization?profile_id=${profileId}`).then(r => r.json()),
  })
  const [editing, setEditing] = useState(false)
  const [orgName, setOrgName] = useState('')
  const [sector, setSector] = useState('')
  const [compliance, setCompliance] = useState<string[]>([])
  const [role, setRole] = useState('devsecops')
  const [saving, setSaving] = useState(false)
  const [done, setDone] = useState(false)

  useEffect(() => {
    if (data?.organization) {
      setOrgName(data.organization.name || '')
      setSector(data.organization.sector || '')
      setCompliance((data.organization.compliance || '').split(',').map((s: string) => s.trim()).filter(Boolean))
    }
    if (data?.profile?.role) setRole(data.profile.role)
  }, [data])

  const handleSave = async () => {
    setSaving(true)
    await fetch(`/api/profile/onboard?profile_id=${profileId}&role=${role}&org_name=${encodeURIComponent(orgName)}&sector=${encodeURIComponent(sector)}&compliance=${encodeURIComponent(compliance.join(','))}&assets=[]`, { method: 'POST' })
    setSaving(false)
    setDone(true)
    qc.invalidateQueries({ queryKey: ['organization'] })
    setTimeout(() => setDone(false), 2000)
  }

  const toggleCompliance = (c: string) => {
    setCompliance(prev => prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c])
  }

  if (isLoading) return <div className="flex justify-center py-24"><div className="w-8 h-8 border-2 border-[var(--brand)] border-t-transparent rounded-full animate-spin" /></div>

  const org = data?.organization
  const profile = data?.profile

  const getChipStyle = (active: boolean) => ({
    background: active ? 'var(--surface-elevated)' : 'var(--surface)',
    color: active ? 'var(--text)' : 'var(--text-muted)',
    borderColor: active ? 'var(--brand)' : 'var(--border)',
    boxShadow: active ? 'var(--shadow-sm)' : 'none',
  })

  return (
    <div className="max-w-3xl mx-auto py-4 sm:py-8 animate-fade">
      <h1 className="h1 mb-1" style={{ color: 'var(--text)' }}>Organisation</h1>
      <p className="body-sm text-secondary mb-6">Qui sommes-nous ? Définissez votre contexte pour des décisions personnalisées.</p>

      {!editing && org ? (
        <div className="space-y-4">
          <div className="surface rounded-2xl p-5 sm:p-6" style={{ border: '1px solid var(--border)' }}>
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <h2 className="h2" style={{ color: 'var(--text)' }}>{org.name}</h2>
                <p className="body-sm text-secondary mt-0.5">{org.sector || 'Secteur non défini'}</p>
              </div>
              <button onClick={() => setEditing(true)} className="btn-secondary text-xs">
                Modifier
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="rounded-xl p-4" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                <p className="caption mb-2" style={{ color: 'var(--brand)' }}>Rôle</p>
                <p className="body font-medium capitalize" style={{ color: 'var(--text)' }}>{profile?.role || 'Non défini'}</p>
              </div>
              <div className="rounded-xl p-4" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                <p className="caption mb-2" style={{ color: 'var(--brand)' }}>Secteur</p>
                <p className="body font-medium" style={{ color: 'var(--text)' }}>{org.sector || 'Non défini'}</p>
              </div>
            </div>

            {org.compliance && (
              <div className="mt-4 rounded-xl p-4" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
                <p className="caption mb-2" style={{ color: 'var(--brand)' }}>Conformité</p>
                <div className="flex flex-wrap gap-1.5">
                  {org.compliance.split(',').map((c: string, i: number) => (
                    <span key={i} className="badge badge-success">
                      {c.trim()}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="text-center">
            <p className="text-xs text-muted">Ces informations sont utilisées pour personnaliser vos décisions de sécurité.</p>
          </div>
        </div>
      ) : (
        <div className="surface rounded-2xl p-5 sm:p-6 space-y-5" style={{ border: '1px solid var(--border)' }}>
          <div>
            <label className="caption mb-1.5 block" style={{ color: 'var(--brand)' }}>Rôle</label>
            <div className="flex flex-wrap gap-1.5">
              {ROLES.map(r => (
                <button key={r} onClick={() => setRole(r)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium border capitalize transition-all"
                  style={getChipStyle(role === r)}>
                  {r}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="caption mb-1.5 block" style={{ color: 'var(--brand)' }}>Nom de l'organisation</label>
            <input type="text" value={orgName} onChange={e => setOrgName(e.target.value)}
              placeholder="Ex: MaBoite, Acme Corp..."
              className="w-full rounded-xl px-4 py-3 text-sm ring-brand"
              style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }} />
          </div>

          <div>
            <label className="caption mb-1.5 block" style={{ color: 'var(--brand)' }}>Secteur</label>
            <div className="flex flex-wrap gap-1.5">
              {SECTORS.map(s => (
                <button key={s} onClick={() => setSector(s)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium border capitalize transition-all"
                  style={getChipStyle(sector === s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="caption mb-1.5 block" style={{ color: 'var(--brand)' }}>Conformité</label>
            <div className="flex flex-wrap gap-1.5">
              {COMPLIANCE_OPTS.map(c => (
                <button key={c} onClick={() => toggleCompliance(c)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all"
                  style={getChipStyle(compliance.includes(c))}>
                  {c}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button onClick={handleSave} disabled={saving || !orgName} className="btn-primary">
              {done ? <><Check size={15} /> Enregistré</> : saving ? 'Enregistrement...' : 'Enregistrer'}
            </button>
            {org && (
              <button onClick={() => setEditing(false)} className="btn-secondary">
                Annuler
              </button>
            )}
          </div>
        </div>
      )}

      <div className="mt-6 text-right">
        <a href="/assets" className="btn-ghost text-xs inline-flex items-center gap-1.5">
          Gérer les assets <ArrowRight size={12} />
        </a>
      </div>
    </div>
  )
}
