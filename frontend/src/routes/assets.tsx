import { useState } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Shield, Plus, Globe, Server, Box, Code, ChevronRight } from 'lucide-react'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/assets',
  component: AssetsPage,
})

const ASSET_TYPES = ['product', 'language', 'framework', 'os', 'vendor']
const TYPE_ICONS: Record<string, React.ReactNode> = {
  product: <Box size={13} />,
  language: <Code size={13} />,
  framework: <Box size={13} />,
  os: <Server size={13} />,
  vendor: <Globe size={13} />,
}

function AssetsPage() {
  const qc = useQueryClient()
  const profileId = 1
  const { data, isLoading } = useQuery({
    queryKey: ['organization', profileId],
    queryFn: () => fetch(`/api/organization?profile_id=${profileId}`).then(r => r.json()),
  })
  const [adding, setAdding] = useState(false)
  const [newName, setNewName] = useState('')
  const [newVendor, setNewVendor] = useState('')
  const [newVersion, setNewVersion] = useState('')
  const [newType, setNewType] = useState('product')
  const [newCrit, setNewCrit] = useState(3)
  const [saving, setSaving] = useState(false)

  const assets = data?.assets || []
  const hasOrg = !!data?.organization
  const grouped: Record<string, typeof assets> = {}
  for (const a of assets) {
    const t = a.type || 'autre'
    if (!grouped[t]) grouped[t] = []
    grouped[t].push(a)
  }

  const handleAdd = async () => {
    if (!newName) return
    setSaving(true)
    const params = new URLSearchParams({
      profile_id: String(profileId),
      asset_type: newType,
      name: newName,
      vendor: newVendor,
      version: newVersion,
      criticality: String(newCrit),
    })
    await fetch('/api/assets/add?' + params.toString(), { method: 'POST' })
    setSaving(false)
    setAdding(false)
    setNewName(''); setNewVendor(''); setNewVersion(''); setNewType('product'); setNewCrit(3)
    qc.invalidateQueries({ queryKey: ['organization'] })
  }

  if (isLoading) return <div className="flex justify-center py-24"><div className="w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" /></div>

  return (
    <div className="max-w-3xl mx-auto py-4 sm:py-8 animate-fade">
      <h1 className="text-xl sm:text-2xl font-semibold text-white mb-1">Assets</h1>
      <p className="text-sm text-slate-500 mb-6">Que protegeons-nous ? Les technologies qui definissent votre surface d'attaque.</p>

      {!hasOrg && (
        <div className="glass-card rounded-2xl p-6 text-center mb-6">
          <Shield size={32} className="mx-auto text-slate-600 mb-3" />
          <p className="text-sm text-slate-400 mb-3">Definissez d'abord votre organisation.</p>
          <a href="/organization" className="inline-flex items-center gap-1.5 px-4 py-2 glass rounded-xl text-xs text-emerald-400 hover:text-white transition">
            Configurer l'organisation <ChevronRight size={12} />
          </a>
        </div>
      )}

      {hasOrg && (
        <>
          <div className="flex items-center justify-between mb-4">
            <p className="text-xs text-slate-500">{assets.length} asset{assets.length !== 1 ? 's' : ''}</p>
            <button onClick={() => setAdding(!adding)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 glass rounded-xl text-xs text-slate-400 hover:text-white transition">
              <Plus size={12} /> {adding ? 'Annuler' : 'Ajouter'}
            </button>
          </div>

          {adding && (
            <div className="glass-card rounded-2xl p-4 sm:p-5 mb-5 space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[10px] uppercase tracking-widest text-slate-500 mb-1 block">Type</label>
                  <div className="flex flex-wrap gap-1">
                    {ASSET_TYPES.map(t => (
                      <button key={t} onClick={() => setNewType(t)}
                        className={`px-2.5 py-1 rounded-lg text-[10px] font-medium transition border capitalize ${
                          newType === t ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'glass text-slate-500 hover:text-slate-300'
                        }`}>
                        {t}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="text-[10px] uppercase tracking-widest text-slate-500 mb-1 block">Criticite (1-5)</label>
                  <input type="range" min="1" max="5" value={newCrit} onChange={e => setNewCrit(Number(e.target.value))}
                    className="w-full accent-emerald-500" />
                  <span className="text-[10px] text-slate-500">{newCrit}</span>
                </div>
                <div>
                  <label className="text-[10px] uppercase tracking-widest text-slate-500 mb-1 block">Nom</label>
                  <input type="text" value={newName} onChange={e => setNewName(e.target.value)}
                    placeholder="PostgreSQL, Docker, AWS..."
                    className="w-full glass rounded-xl px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-emerald-500/30" />
                </div>
                <div>
                  <label className="text-[10px] uppercase tracking-widest text-slate-500 mb-1 block">Fournisseur</label>
                  <input type="text" value={newVendor} onChange={e => setNewVendor(e.target.value)}
                    placeholder="PostgreSQL, Docker Inc..."
                    className="w-full glass rounded-xl px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500/30" />
                </div>
                <div>
                  <label className="text-[10px] uppercase tracking-widest text-slate-500 mb-1 block">Version</label>
                  <input type="text" value={newVersion} onChange={e => setNewVersion(e.target.value)}
                    placeholder="15.4, 24.0..."
                    className="w-full glass rounded-xl px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-2 focus:ring-indigo-500/30" />
                </div>
              </div>
              <button onClick={handleAdd} disabled={saving || !newName}
                className="px-4 py-2 rounded-xl bg-emerald-500 text-white text-xs font-medium hover:bg-emerald-400 disabled:opacity-40 transition">
                {saving ? 'Ajout...' : 'Ajouter l\'asset'}
              </button>
            </div>
          )}

          {Object.keys(grouped).length === 0 && !adding && (
            <div className="glass-card rounded-2xl p-8 text-center">
              <Box size={32} className="mx-auto text-slate-600 mb-3" />
              <p className="text-sm text-slate-400 mb-1">Aucun asset defini</p>
              <p className="text-xs text-slate-500">Ajoutez vos technologies pour des decisions personnalisees.</p>
            </div>
          )}

          {Object.entries(grouped).map(([type, items]) => (
            <div key={type} className="mb-5">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-slate-500">{TYPE_ICONS[type] || <Box size={13} />}</span>
                <h2 className="text-xs font-semibold text-slate-400 uppercase">{type}</h2>
                <span className="text-[10px] text-slate-600">{items.length}</span>
              </div>
              <div className="space-y-1.5">
                {items.map((a: any) => (
                  <div key={a.id} className="glass rounded-xl p-3 flex items-center justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-white font-medium">{a.name}</span>
                        {a.vendor && <span className="text-[10px] text-slate-500">({a.vendor})</span>}
                      </div>
                      {a.version && <span className="text-[10px] text-slate-600">v{a.version}</span>}
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[10px] text-slate-500">{'⬤'.repeat(a.criticality)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  )
}
