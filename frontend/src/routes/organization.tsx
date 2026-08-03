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

  if (isLoading) return <div className="flex justify-center py-24"><div className="w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" /></div>

  const org = data?.organization
  const profile = data?.profile

  return (
    <div className="max-w-3xl mx-auto py-4 sm:py-8 animate-fade">
      <h1 className="text-xl sm:text-2xl font-semibold text-white mb-1">Organisation</h1>
      <p className="text-sm text-slate-500 mb-6">Qui sommes-nous ? Définissez votre contexte pour des décisions personnalisees.</p>

      {!editing && org ? (
        <div className="space-y-4">
          <div className="glass-card rounded-2xl p-5 sm:p-6">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <h2 className="text-lg font-semibold text-white">{org.name}</h2>
                <p className="text-sm text-slate-400 mt-0.5">{org.sector || 'Secteur non defini'}</p>
              </div>
              <button onClick={() => setEditing(true)}
                className="px-4 py-2 glass rounded-xl text-xs text-slate-400 hover:text-white transition">
                Modifier
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="glass rounded-xl p-4">
                <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-2">Role</p>
                <p className="text-sm text-white font-medium capitalize">{profile?.role || 'Non defini'}</p>
              </div>
              <div className="glass rounded-xl p-4">
                <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-2">Secteur</p>
                <p className="text-sm text-white font-medium">{org.sector || 'Non defini'}</p>
              </div>
            </div>

            {org.compliance && (
              <div className="mt-4 glass rounded-xl p-4">
                <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-2">Conformite</p>
                <div className="flex flex-wrap gap-1.5">
                  {org.compliance.split(',').map((c: string, i: number) => (
                    <span key={i} className="px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {c.trim()}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="text-center">
            <p className="text-xs text-slate-600">Ces informations sont utilisees pour personnaliser vos decisions de securite.</p>
          </div>
        </div>
      ) : (
        <div className="glass-card rounded-2xl p-5 sm:p-6 space-y-5">
          <div>
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

          <div>
            <label className="text-[10px] uppercase tracking-widest text-slate-500 mb-1.5 block">Nom de l'organisation</label>
            <input type="text" value={orgName} onChange={e => setOrgName(e.target.value)}
              placeholder="Ex: MaBoite, Acme Corp..."
              className="w-full glass rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-emerald-500/30" />
          </div>

          <div>
            <label className="text-[10px] uppercase tracking-widest text-slate-500 mb-1.5 block">Secteur</label>
            <div className="flex flex-wrap gap-1.5">
              {SECTORS.map(s => (
                <button key={s} onClick={() => setSector(s)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition border capitalize ${
                    sector === s ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' : 'glass text-slate-500 hover:text-slate-300'
                  }`}>
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="text-[10px] uppercase tracking-widest text-slate-500 mb-1.5 block">Conformite</label>
            <div className="flex flex-wrap gap-1.5">
              {COMPLIANCE_OPTS.map(c => (
                <button key={c} onClick={() => toggleCompliance(c)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition border ${
                    compliance.includes(c) ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'glass text-slate-500 hover:text-slate-300'
                  }`}>
                  {c}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3 pt-2">
            <button onClick={handleSave} disabled={saving || !orgName}
              className="px-5 py-2.5 rounded-xl bg-emerald-500 text-white text-sm font-medium hover:bg-emerald-400 disabled:opacity-40 transition flex items-center gap-2">
              {done ? <><Check size={15} /> Enregistre</> : saving ? 'Enregistrement...' : 'Enregistrer'}
            </button>
            {org && (
              <button onClick={() => setEditing(false)}
                className="px-5 py-2.5 rounded-xl glass text-sm text-slate-400 hover:text-white transition">
                Annuler
              </button>
            )}
          </div>
        </div>
      )}

      <div className="mt-6 text-right">
        <a href="/assets" className="inline-flex items-center gap-1.5 text-xs text-indigo-400 hover:text-indigo-300 transition">
          Gerer les assets <ArrowRight size={12} />
        </a>
      </div>
    </div>
  )
}
