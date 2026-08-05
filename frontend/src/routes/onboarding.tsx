import { useState } from 'react'
import type { ReactNode } from 'react'
import { createRoute, useRouter } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQueryClient } from '@tanstack/react-query'
import {
  Shield, Target, Bug, Activity, Cpu, Cloud, ChevronLeft, ChevronRight,
  Plus, X, Check, Sparkles, PartyPopper, Box,
} from 'lucide-react'
import { getProfileId } from '../lib/profile'

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/onboarding',
  component: OnboardingPage,
})

const ROLES = [
  { id: 'rssi', label: 'RSSI', icon: Shield, color: 'var(--red)', desc: 'Exposition, conformité, priorités stratégiques' },
  { id: 'pentester', label: 'Pentester', icon: Target, color: 'var(--amber)', desc: 'Exploits, PoC, nouveaux outils offensifs' },
  { id: 'developpeur', label: 'Développeur', icon: Bug, color: 'var(--cyan)', desc: 'Mes technologies sont-elles touchées ?' },
  { id: 'soc', label: 'Analyste SOC', icon: Activity, color: 'var(--violet)', desc: 'Alertes, IOCs, campagnes actives' },
  { id: 'devsecops', label: 'DevSecOps', icon: Cpu, color: 'var(--lime)', desc: 'CI/CD, pipelines, dépendances' },
  { id: 'cloud_engineer', label: 'Cloud Engineer', icon: Cloud, color: 'var(--cyan)', desc: 'Infra cloud, expositions externes' },
]

const SECTORS = ['finance', 'sante', 'defense', 'education', 'tech', 'industrie', 'energie', 'gouvernement', 'consulting', 'pme', 'startup', 'autre']
const COMPLIANCE_OPTS = ['PCI DSS', 'ISO 27001', 'NIST', 'SOC2', 'HIPAA', 'RGPD', 'OWASP', 'NIS2', 'DORA', 'Aucune']

const SUGGESTED_TECHS = [
  'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Kafka', 'Elasticsearch',
  'Docker', 'Kubernetes', 'Nginx', 'Apache HTTP Server', 'OpenSSL', 'OpenSSH',
  'Python', 'Node.js', 'Java', 'PHP', 'React', 'WordPress',
  'Linux', 'Windows Server', 'Amazon Web Services', 'Microsoft Azure', 'Google Cloud', 'GitLab',
]

const OBJECTIVES = [
  { id: 'reduire_exposition', label: 'Réduire mon exposition' },
  { id: 'prioriser_patchs', label: 'Prioriser les correctifs' },
  { id: 'surveiller_stack', label: 'Surveiller ma stack technique' },
  { id: 'conformite', label: 'Préparer les audits de conformité' },
  { id: 'detection', label: 'Améliorer la détection' },
  { id: 'veille', label: 'Veille offensive / nouveaux outils' },
]

interface Asset { name: string; type: string; criticality: number }

const STEPS = [
  { n: 1, title: 'Votre rôle' },
  { n: 2, title: 'Organisation' },
  { n: 3, title: 'Technologies' },
  { n: 4, title: 'Objectifs' },
]
const TOTAL_STEPS = STEPS.length

function chipStyle(active: boolean) {
  return {
    background: active ? 'var(--surface-elevated)' : 'var(--surface)',
    color: active ? 'var(--text)' : 'var(--text-muted)',
    borderColor: active ? 'var(--amber)' : 'var(--border)',
  }
}

function OnboardingPage() {
  const router = useRouter()
  const qc = useQueryClient()

  const [step, setStep] = useState(0)
  const [role, setRole] = useState('')
  const [orgName, setOrgName] = useState('')
  const [sector, setSector] = useState('')
  const [compliance, setCompliance] = useState<string[]>([])
  const [assets, setAssets] = useState<Asset[]>([])
  const [techInput, setTechInput] = useState('')
  const [objectives, setObjectives] = useState<string[]>([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)

  const canNext = step === 0 ? !!role : step === 1 ? !!orgName : step === 2 || step === 3
  const progress = ((step + 1) / TOTAL_STEPS) * 100

  const addTech = (name: string) => {
    const n = name.trim()
    if (!n || assets.some(a => a.name.toLowerCase() === n.toLowerCase())) return
    setAssets(prev => [...prev, { name: n, type: 'product', criticality: 3 }])
  }
  const removeTech = (name: string) => setAssets(prev => prev.filter(a => a.name !== name))
  const toggleSuggestion = (name: string) =>
    assets.some(a => a.name.toLowerCase() === name.toLowerCase()) ? removeTech(name) : addTech(name)

  const toggleCompliance = (c: string) =>
    setCompliance(prev => prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c])
  const toggleObjective = (id: string) =>
    setObjectives(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])

  const submit = async () => {
    setSaving(true)
    setError('')
    const pid = getProfileId()
    try {
      const assetJson = JSON.stringify(assets.map(a => ({ name: a.name, asset_type: a.type, criticality: a.criticality })))
      const params = new URLSearchParams({
        profile_id: pid,
        role,
        org_name: orgName,
        sector,
        compliance: compliance.join(','),
        assets: assetJson,
      })
      const r1 = await fetch('/api/profile/onboard?' + params.toString(), { method: 'POST' })
      if (!r1.ok) throw new Error(`onboard ${r1.status}`)
      const r2 = await fetch(`/api/settings?profile_id=${pid}&role=${role}&preferences=${encodeURIComponent(JSON.stringify({ objectives }))}`, { method: 'POST' })
      if (!r2.ok) throw new Error(`settings ${r2.status}`)
      qc.invalidateQueries({ queryKey: ['organization'] })
      qc.invalidateQueries({ queryKey: ['settings'] })
      qc.invalidateQueries({ queryKey: ['priority-home'] })
      setDone(true)
    } catch {
      setError("Échec de l'enregistrement. Réessayez.")
    } finally {
      setSaving(false)
    }
  }

  const progressStep = (s: ReactNode) => (
    <section className="animate-fade" style={{ maxWidth: 640, margin: '0 auto' }}>
      {s}
    </section>
  )

  const next = () => { if (step === TOTAL_STEPS - 1) submit(); else setStep(step + 1) }
  const back = () => setStep(step - 1)

  if (done) {
    return (
      <div className="py-16 text-center animate-fade">
        <div className="w-16 h-16 rounded-2xl mx-auto mb-5 flex items-center justify-center"
          style={{ background: 'var(--lime-light)', color: 'var(--lime)' }}>
          <PartyPopper size={28} />
        </div>
        <h1 className="text-h1 t-p mb-2">Onboarding terminé</h1>
        <p className="text-body-sm t-s mb-6 max-w-md mx-auto">
          Votre cockpit est maintenant <span className="t-amber">personnalisé</span> pour le rôle <strong className="t-p capitalize">{role}</strong>
          {orgName ? <> de <strong className="t-p">{orgName}</strong></> : ''}
          . Les décisions vont prioriser {assets.length} technologie{assets.length !== 1 ? 's' : ''} et vos objectifs.
        </p>
        <button onClick={() => router.navigate({ to: '/' })} className="flex items-center gap-2 mx-auto px-5 py-2.5 rounded-xl font-semibold text-sm"
          style={{ background: 'var(--amber)', color: 'var(--text-inverse)' }}>
          Aller au cockpit <Sparkles size={15} />
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-[720px] mx-auto py-6 sm:py-10 animate-fade">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <p className="text-caption t-amber flex items-center gap-1.5"><Sparkles size={12} /> Configuration</p>
        <span className="text-caption t-m">{step + 1} / {TOTAL_STEPS}</span>
      </div>
      <h1 className="text-h1 t-p mb-1 flex items-center gap-2 flex-wrap">
        <span className="flex items-center gap-2 font-display">
          Bonjour <span className="t-amber">HashCode</span>
        </span>
      </h1>
      <p className="text-body-sm t-s mb-4">En 4 étapes, on adapte vos décisions à votre contexte.</p>

      {/* Progress bar */}
      <div className="h-1.5 rounded-full mb-8 overflow-hidden" style={{ background: 'var(--surface-elevated)' }}>
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${progress}%`, background: 'var(--amber)' }} />
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 rounded-xl text-sm t-red" style={{ background: 'var(--red-light)', border: '1px solid var(--red)' }}>
          {error}
        </div>
      )}

      {/* STEP 0 — Rôle */}
      {step === 0 && progressStep(
        <div>
          <h2 className="text-h2 t-p mb-1">{STEPS[0].title}</h2>
          <p className="text-body-sm t-m mb-6">Que faites-vous ? Chaque rôle a sa propre vue.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {ROLES.map(r => {
              const Icon = r.icon
              const active = role === r.id
              return (
                <button key={r.id} onClick={() => setRole(r.id)}
                  className="rounded-xl p-4 text-left transition-all hover:-translate-y-0.5 flex gap-3"
                  style={{ background: active ? 'var(--surface-elevated)' : 'var(--surface)', border: `1px solid ${active ? r.color : 'var(--border)'}` }}>
                  <div className="w-9 h-9 rounded-lg shrink-0 flex items-center justify-center"
                    style={{ background: `${r.color}1f`, color: r.color }}>
                    <Icon size={17} />
                  </div>
                  <div className="min-w-0">
                    <div className="text-body font-semibold t-p mb-0.5">{r.label}</div>
                    <div className="text-caption t-m" style={{ textTransform: 'none', letterSpacing: 'normal' }}>{r.desc}</div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* STEP 1 — Organisation */}
      {step === 1 && progressStep(
        <div className="space-y-5">
          <div>
            <h2 className="text-h3 t-p mb-1">{STEPS[1].title}</h2>
            <p className="text-body-sm t-m mb-4">Le contexte de vérité : qui vous protégez ?</p>
            <label className="text-caption t-amber mb-1.5 block">Nom de l'organisation</label>
            <input type="text" value={orgName} onChange={e => setOrgName(e.target.value)}
              placeholder="Ex: Acme Corp"
              className="w-full rounded-xl px-4 py-3 text-sm ring-brand"
              style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }} />
          </div>
          <div>
            <label className="text-caption t-amber mb-1.5 block">Secteur</label>
            <div className="flex flex-wrap gap-1.5">
              {SECTORS.map(s => (
                <button key={s} onClick={() => setSector(s)} className="px-3 py-1.5 rounded-lg text-xs font-medium border capitalize transition-all"
                  style={chipStyle(sector === s)}>{s}</button>
              ))}
            </div>
          </div>
          <div>
            <label className="text-caption t-amber mb-1.5 block">Conformité</label>
            <div className="flex flex-wrap gap-1.5">
              {COMPLIANCE_OPTS.map(c => (
                <button key={c} onClick={() => toggleCompliance(c)} className="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all"
                  style={chipStyle(compliance.includes(c))}>{c}</button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* STEP 2 — Technologies */}
      {step === 2 && progressStep(
        <div className="space-y-5">
          <div>
            <h2 className="text-h3 t-p mb-1">{STEPS[2].title}</h2>
            <p className="text-body-sm t-m mb-4">Les technologies de votre surface d'attaque. Les CVE les touchant seront priorisées.</p>
            <div className="flex gap-2">
              <input type="text" value={techInput} onChange={e => setTechInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { addTech(techInput); setTechInput('') } }}
                placeholder="Ajouter une technologie (ex: Nginx)"
                className="flex-1 rounded-xl px-4 py-2.5 text-sm ring-brand"
                style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)' }} />
              <button onClick={() => { addTech(techInput); setTechInput('') }}
                className="px-4 rounded-xl flex items-center gap-1.5 text-sm font-semibold"
                style={{ background: 'var(--surface-elevated)', color: 'var(--text)', border: '1px solid var(--border)' }}>
                <Plus size={14} /> Ajouter
              </button>
            </div>
          </div>

          {assets.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-caption t-amber">Sélectionnés ({assets.length})</label>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {assets.map(a => (
                  <button key={a.name} onClick={() => removeTech(a.name)}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition-all"
                    style={{ background: 'var(--surface-elevated)', border: '1px solid var(--amber)', color: 'var(--text)' }}>
                    <Box size={11} style={{ color: 'var(--amber)' }} />{a.name}<X size={12} className="t-m" />
                  </button>
                ))}
              </div>
            </div>
          )}

          <div>
            <label className="text-caption t-m mb-2 block">Suggestions</label>
            <div className="flex flex-wrap gap-1.5">
              {SUGGESTED_TECHS.map(t => {
                const on = assets.some(a => a.name.toLowerCase() === t.toLowerCase())
                return (
                  <button key={t} onClick={() => toggleSuggestion(t)} className="px-3 py-1.5 rounded-lg text-xs font-medium border transition-all"
                    style={chipStyle(on)}>{t}</button>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* STEP 3 — Objectifs */}
      {step === 3 && progressStep(
        <div className="space-y-5">
          <div>
            <h2 className="text-h3 t-p mb-1">{STEPS[3].title}</h2>
            <p className="text-body-sm t-m mb-5">Ce qui motive vos priorités. (plusieurs possible)</p>
            <div className="space-y-2">
              {OBJECTIVES.map(o => {
                const on = objectives.includes(o.id)
                return (
                  <button key={o.id} onClick={() => toggleObjective(o.id)}
                    className="w-full flex items-center justify-between gap-3 rounded-xl px-4 py-3 text-left transition-all"
                    style={{ background: on ? 'var(--surface-elevated)' : 'var(--surface)', border: `1px solid ${on ? 'var(--amber)' : 'var(--border)'}` }}>
                    <span className="text-body t-p">{o.label}</span>
                    <span className="w-5 h-5 rounded-md flex items-center justify-center shrink-0"
                      style={{ background: on ? 'var(--amber)' : 'transparent', border: `1px solid ${on ? 'var(--amber)' : 'var(--border)'}`, color: on ? 'var(--text-inverse)' : 'transparent' }}>
                      <Check size={13} />
                    </span>
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Nav buttons */}
      <div className="flex items-center justify-between mt-8">
        <button onClick={back} disabled={step === 0}
          className="px-4 py-2 rounded-xl text-sm flex items-center gap-1.5 transition-all disabled:opacity-30"
          style={{ color: 'var(--text-secondary)', border: '1px solid var(--border)' }}>
          <ChevronLeft size={15} /> Retour
        </button>
        <button onClick={next} disabled={!canNext || saving}
          className="px-5 py-2.5 rounded-xl font-semibold text-sm flex items-center gap-1.5 transition-all disabled:opacity-40"
          style={{ background: 'var(--amber)', color: 'var(--text-inverse)' }}>
          {saving ? 'Enregistrement...'
            : step === TOTAL_STEPS - 1 ? <><Check size={15} /> Terminer</>
            : <><span>{step === 0 ? 'Continuer' : 'Suivant'}</span><ChevronRight size={15} /></>}
        </button>
      </div>
    </div>
  )
}