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

  if (isLoading) return <div className="flex justify-center py-24"><div className="w-8 h-8 border-2 border-[var(--amber)] border-t-transparent rounded-full animate-spin" /></div>

  return (
    <div className="max-w-3xl mx-auto py-4 sm:py-8 animate-fade">
      <h1 className="h1 mb-1" style={{ color: 'var(--text)' }}>Assets</h1>
      <p className="body-sm text-secondary mb-6">Que protégeons-nous ? Les technologies qui définissent votre surface d'attaque.</p>

      {!hasOrg && (
        <div className="surface rounded-2xl p-6 text-center mb-6" style={{ border: '1px solid var(--border)' }}>
          <Shield size={32} className="mx-auto text-muted mb-3" />
          <p className="body-sm text-secondary mb-3">Définissez d'abord votre organisation.</p>
          <a href="/organization" className="btn-secondary inline-flex text-xs">
            Configurer l'organisation <ChevronRight size={12} />
          </a>
        </div>
      )}

      {hasOrg && (
        <>
          <div className="flex items-center justify-between mb-4">
            <p className="text-xs text-muted">{assets.length} asset{assets.length !== 1 ? 's' : ''}</p>
            <button onClick={() => setAdding(!adding)} className="btn-secondary text-xs">
              <Plus size={12} /> {adding ? 'Annuler' : 'Ajouter'}
            </button>
          </div>

          {adding && (
            <div className="surface rounded-2xl p-4 sm:p-5 mb-5 space-y-3" style={{ border: '1px solid var(--border)' }}>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="caption mb-1 block" style={{ color: 'var(--amber)' }}>Type</label>
                  <div className="flex flex-wrap gap-1">
                    {ASSET_TYPES.map(t => (
                      <button key={t} onClick={() => setNewType(t)}
                        className="px-2.5 py-1 rounded-lg text-[10px] font-medium border capitalize transition-all"
                        style={{
                          background: newType === t ? 'var(--surface-elevated)' : 'var(--surface)',
                          color: newType === t ? 'var(--text)' : 'var(--text-muted)',
                          borderColor: newType === t ? 'var(--amber)' : 'var(--border)',
                        }}>
                        {t}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="caption mb-1 block" style={{ color: 'var(--amber)' }}>Criticité (1-5)</label>
                  <input type="range" min="1" max="5" value={newCrit} onChange={e => setNewCrit(Number(e.target.value))}
                    className="w-full" style={{ accentColor: 'var(--amber)' }} />
                  <span className="text-[10px] text-muted">{newCrit}</span>
                </div>
                <div>
                  <label className="caption mb-1 block" style={{ color: 'var(--amber)' }}>Nom</label>
                  <input type="text" value={newName} onChange={e => setNewName(e.target.value)}
                    placeholder="PostgreSQL, Docker, AWS..."
                    className="w-full rounded-xl px-3 py-2 text-sm ring-brand"
                    style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }} />
                </div>
                <div>
                  <label className="caption mb-1 block" style={{ color: 'var(--amber)' }}>Fournisseur</label>
                  <input type="text" value={newVendor} onChange={e => setNewVendor(e.target.value)}
                    placeholder="PostgreSQL, Docker Inc..."
                    className="w-full rounded-xl px-3 py-2 text-sm ring-brand"
                    style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }} />
                </div>
                <div>
                  <label className="caption mb-1 block" style={{ color: 'var(--amber)' }}>Version</label>
                  <input type="text" value={newVersion} onChange={e => setNewVersion(e.target.value)}
                    placeholder="15.4, 24.0..."
                    className="w-full rounded-xl px-3 py-2 text-sm ring-brand"
                    style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }} />
                </div>
              </div>
              <button onClick={handleAdd} disabled={saving || !newName} className="btn-primary text-xs">
                {saving ? 'Ajout...' : "Ajouter l'asset"}
              </button>
            </div>
          )}

          {Object.keys(grouped).length === 0 && !adding && (
            <div className="surface rounded-2xl p-8 text-center" style={{ border: '1px solid var(--border)' }}>
              <Box size={32} className="mx-auto text-muted mb-3" />
              <p className="body-sm text-secondary mb-1">Aucun asset défini</p>
              <p className="text-xs text-muted">Ajoutez vos technologies pour des décisions personnalisées.</p>
            </div>
          )}

          {Object.entries(grouped).map(([type, items]) => (
            <div key={type} className="mb-5">
              <div className="flex items-center gap-2 mb-2">
                <span style={{ color: 'var(--text-muted)' }}>{TYPE_ICONS[type] || <Box size={13} />}</span>
                <h2 className="text-xs font-semibold uppercase" style={{ color: 'var(--text-secondary)' }}>{type}</h2>
                <span className="text-[10px] text-muted">{items.length}</span>
              </div>
              <div className="space-y-1.5">
                {items.map((a: any) => (
                  <div key={a.id} className="rounded-xl p-3 flex items-center justify-between gap-2" style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border-light)' }}>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium" style={{ color: 'var(--text)' }}>{a.name}</span>
                        {a.vendor && <span className="text-[10px] text-muted">({a.vendor})</span>}
                      </div>
                      {a.version && <span className="text-[10px] text-muted">v{a.version}</span>}
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[10px] text-muted">{'●'.repeat(a.criticality)}</span>
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
