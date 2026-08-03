import { useState } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { ExternalLink, Loader2, MapPin, User, Hash, Brain, Mail, Phone, Globe, Search, Bug, Target, Play, Zap, BarChart3 } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/osint', component: OsintPage })

const TABS = [
  { id: 'person', label: 'Enquête personne', icon: <User size={12} /> },
  { id: 'v2', label: 'Multi-candidats', icon: <Zap size={12} /> },
  { id: 'pipeline', label: 'Pipeline IA', icon: <Brain size={12} /> },
  { id: 'pro', label: 'Pro (email/phone/domaine)', icon: <Globe size={12} /> },
  { id: 'dorks', label: 'Dorking', icon: <Search size={12} /> },
  { id: 'tools', label: 'Outils externes', icon: <Bug size={12} /> },
]

function OsintPage() {
  const [tab, setTab] = useState('person')

  return (
    <div className="max-w-4xl mx-auto py-4 sm:py-8 animate-fade">
      <h1 className="text-lg font-semibold text-white mb-2">OSINT Lab</h1>
      <p className="text-xs sm:text-sm text-slate-400 mb-4 sm:mb-6">
        Recherche de personnes par IA — décrivez qui vous cherchez, l'IA extrait les paramètres, les outils OSINT enquêtent.
      </p>

      <div className="flex flex-wrap gap-1 mb-4">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition border ${tab === t.id ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' : 'glass text-slate-400 hover:text-white'}`}>
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {tab === 'person' && <PersonTab />}
      {tab === 'v2' && <V2Tab />}
      {tab === 'pipeline' && <PipelineTab />}
      {tab === 'pro' && <ProTab />}
      {tab === 'dorks' && <DorksTab />}
      {tab === 'tools' && <ToolsTab />}
    </div>
  )
}

function OsintError({ message }: { message: string | null }) {
  if (!message) return null
  return (
    <div className="glass-card rounded-xl p-3 mb-4 border-rose-500/20 flex items-center gap-2" role="alert">
      <Bug size={13} className="text-rose-400 shrink-0" />
      <p className="text-xs text-rose-300">{message}</p>
    </div>
  )
}

function OsintResult({ result }: { result: any }) {
  if (!result) return null
  return (
    <div className="space-y-4 animate-fade">
      {/* AI Extraction */}
      {result.ai_extracted?.name && (
        <div className="glass-card rounded-2xl p-4">
          <div className="flex items-center gap-2 mb-3"><Brain size={15} className="text-violet-400" /><h3 className="text-sm font-semibold text-white">Paramètres extraits par l'IA</h3></div>
          <div className="flex flex-wrap gap-2">
            {result.ai_extracted.name && <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 text-xs"><User size={11} /> {result.ai_extracted.name}</span>}
            {result.ai_extracted.location && <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 text-xs"><MapPin size={11} /> {result.ai_extracted.location}</span>}
            {result.ai_extracted.keywords?.map((k: string, i: number) => (
              <span key={i} className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-500/10 text-slate-300 text-xs"><Hash size={11} /> {k}</span>
            ))}
          </div>
          {result.ai_extracted.strategy && <p className="text-xs text-slate-500 mt-3 italic">Stratégie: {result.ai_extracted.strategy}</p>}
        </div>
      )}

      {/* Summary */}
      {result.summary && <p className="text-sm text-slate-400">{result.summary}</p>}

      {/* Candidates (v2) */}
      {result.candidates?.length > 0 && (
        <div className="glass-card rounded-2xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Candidats ({result.candidates.length})</h3>
          <div className="space-y-2">
            {result.candidates.map((c: any, i: number) => (
              <div key={i} className="glass rounded-xl p-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-white">{c.name}</span>
                  <span className="text-[10px] text-indigo-400">Score: {c.score}</span>
                </div>
                {c.reason && <p className="text-[10px] text-slate-500">{c.reason}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* GitHub Profiles */}
      {result.findings?.github_profiles?.length > 0 && (
        <div className="glass-card rounded-2xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Profils GitHub ({result.findings.github_profiles.length})</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {result.findings.github_profiles.map((p: any, i: number) => (
              <a key={i} href={p.url} target="_blank" rel="noopener" className="glass-card rounded-xl p-3 flex items-start gap-3 group">
                <img src={p.avatar} className="w-10 h-10 rounded-full" alt="" />
                <div className="min-w-0">
                  <div className="text-xs font-medium text-slate-200 group-hover:text-indigo-400">{p.username}</div>
                  {p.name && <div className="text-[10px] text-slate-400">{p.name}</div>}
                  {p.location && <div className="text-[9px] text-slate-500">{p.location}</div>}
                  {p.bio && <div className="text-[10px] text-slate-500 mt-1 line-clamp-2">{p.bio}</div>}
                  <div className="flex items-center gap-2 mt-1 text-[9px] text-slate-500">
                    {p.company && <span>{p.company}</span>}
                    {p.twitter && <span>@{p.twitter}</span>}
                    <span>{p.followers} followers</span>
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Social Presence */}
      {result.findings?.social_presence?.length > 0 && (
        <div className="glass-card rounded-2xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Présence sociale</h3>
          <div className="flex flex-wrap gap-2">
            {result.findings.social_presence.filter((s: any) => s.present).map((s: any, i: number) => (
              <a key={i} href={s.url} target="_blank" rel="noopener" className="px-3 py-1.5 glass rounded-lg text-xs text-emerald-400 hover:bg-emerald-500/10 transition flex items-center gap-1.5">
                {s.platform} <ExternalLink size={10} />
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Breaches */}
      {result.findings?.email_breaches?.length > 0 && (
        <div className="glass-card rounded-2xl p-4">
          <h3 className="text-sm font-semibold text-rose-400 mb-3">Brèches email ({result.findings.email_breaches.length})</h3>
          <div className="space-y-2">
            {result.findings.email_breaches.map((b: any, i: number) => (
              <div key={i} className="glass rounded-xl p-2 text-xs">
                <span className="text-slate-200 font-medium">{b.Name || b.Title || b.Domain}</span>
                {b.BreachDate && <span className="text-slate-500 ml-2">{b.BreachDate}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Phone */}
      {result.findings?.phone_analysis && (
        <div className="glass-card rounded-2xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Analyse téléphone</h3>
          <pre className="text-[11px] text-slate-400 whitespace-pre-wrap">{JSON.stringify(result.findings.phone_analysis, null, 2)}</pre>
        </div>
      )}

      {/* Domain */}
      {result.findings?.domain_info && (
        <div className="glass-card rounded-2xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Info domaine</h3>
          <pre className="text-[11px] text-slate-400 whitespace-pre-wrap">{JSON.stringify(result.findings.domain_info, null, 2)}</pre>
        </div>
      )}

      {/* Pipeline phases */}
      {result.phases && (
        <div className="glass-card rounded-2xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Pipeline IA (12 modèles)</h3>
          <div className="space-y-2">
            {Object.entries(result.phases as Record<string, any>).map(([k, v]) => (
              <div key={k} className="glass rounded-lg p-2 text-xs">
                <span className="text-indigo-400 font-medium">{k}:</span>
                <span className="text-slate-400 ml-2">{typeof v === 'string' ? v.slice(0, 200) : JSON.stringify(v).slice(0, 200)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tools status */}
      {result.tools && (
        <div className="glass-card rounded-2xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3">Outils disponibles</h3>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(result.tools as Record<string, any>).map(([k, v]) => (
              <div key={k} className="glass rounded-lg p-2 text-xs flex items-center justify-between">
                <span className="text-slate-300">{k}</span>
                <span className={v === 'OK' || v === true ? 'text-emerald-400' : 'text-slate-500'}>{String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ── TAB COMPONENTS ─────────────────────────────────────────────────────

function PersonTab() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = async () => {
    if (!text.trim()) return
    setLoading(true); setResult(null); setError(null)
    try {
      const r = await fetch(`/api/osint/investigate?free_text=${encodeURIComponent(text)}`, { method: 'POST' }).then(r => r.json())
      if (r?.error) { setError(r.error); return }
      setResult(r)
    } catch { setError("Échec de la requête. Réessayez.") }
    setLoading(false)
  }

  return (
    <div>
      <div className="glass-card rounded-2xl p-4 mb-6">
        <div className="flex flex-col sm:flex-row gap-3">
          <textarea value={text} onChange={e => setText(e.target.value)}
            placeholder="Ex: un chercheur en sécurité allemand qui travaille sur la détection de malwares avec YARA et Sigma..."
            className="flex-1 px-4 py-3 glass rounded-xl text-sm text-white placeholder-slate-500 min-h-[80px] focus:ring-2 focus:ring-cyan-500/40"
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); search() } }} />
          <button onClick={search} disabled={loading || !text.trim()}
            className="px-6 py-3 bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 rounded-xl text-sm font-medium hover:bg-cyan-500/20 disabled:opacity-30 transition self-end">
            {loading ? <Loader2 size={16} className="animate-spin" /> : 'Enquêter'}
          </button>
        </div>
      </div>
      <OsintError message={error} />
      <OsintResult result={result} />
    </div>
  )
}

function V2Tab() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = async () => {
    if (!text.trim()) return
    setLoading(true); setResult(null); setError(null)
    try {
      const r = await fetch(`/api/osint/investigate-v2?free_text=${encodeURIComponent(text)}`, { method: 'POST' }).then(r => r.json())
      if (r?.error) { setError(r.error); return }
      setResult(r)
    } catch { setError("Échec de la requête. Réessayez.") }
    setLoading(false)
  }

  return (
    <div>
      <div className="glass-card rounded-2xl p-4 mb-6">
        <p className="text-xs text-slate-500 mb-3">Version 2.0: multi-candidats, scoring, decision engine.</p>
        <div className="flex flex-col sm:flex-row gap-3">
          <textarea value={text} onChange={e => setText(e.target.value)}
            placeholder="Ex: John Doe, security researcher, Python developer..."
            className="flex-1 px-4 py-3 glass rounded-xl text-sm text-white placeholder-slate-500 min-h-[80px] focus:ring-2 focus:ring-cyan-500/40" />
          <button onClick={search} disabled={loading || !text.trim()}
            className="px-6 py-3 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-xl text-sm font-medium hover:bg-amber-500/20 disabled:opacity-30 transition self-end">
            {loading ? <Loader2 size={16} className="animate-spin" /> : 'V2 Enquêter'}
          </button>
        </div>
      </div>
      <OsintError message={error} />
      <OsintResult result={result} />
    </div>
  )
}

function PipelineTab() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = async () => {
    if (!text.trim()) return
    setLoading(true); setResult(null); setError(null)
    try {
      const r = await fetch(`/api/osint/pipeline?free_text=${encodeURIComponent(text)}`, { method: 'POST' }).then(r => r.json())
      if (r?.error) { setError(r.error); return }
      setResult(r)
    } catch { setError("Échec de la requête. Réessayez.") }
    setLoading(false)
  }

  return (
    <div>
      <div className="glass-card rounded-2xl p-4 mb-6">
        <div className="flex items-center gap-2 mb-3"><Brain size={14} className="text-violet-400" /><span className="text-xs text-slate-400">12 modèles IA chaînés: extraction → classification → GitHub → social → dorks → analyse → rapport → sécurité</span></div>
        <div className="flex flex-col sm:flex-row gap-3">
          <textarea value={text} onChange={e => setText(e.target.value)}
            placeholder="Décrivez la personne à rechercher..."
            className="flex-1 px-4 py-3 glass rounded-xl text-sm text-white placeholder-slate-500 min-h-[80px] focus:ring-2 focus:ring-violet-500/40" />
          <button onClick={search} disabled={loading || !text.trim()}
            className="px-6 py-3 bg-violet-500/10 border border-violet-500/30 text-violet-400 rounded-xl text-sm font-medium hover:bg-violet-500/20 disabled:opacity-30 transition self-end">
            {loading ? <Loader2 size={16} className="animate-spin" /> : 'Pipeline complet'}
          </button>
        </div>
      </div>
      <OsintError message={error} />
      <OsintResult result={result} />
    </div>
  )
}

function ProTab() {
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [domain, setDomain] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [activeField, setActiveField] = useState('')
  const [error, setError] = useState<string | null>(null)

  const search = async (type: string) => {
    setLoading(true); setResult(null); setError(null); setActiveField(type)
    try {
      let url = ''
      if (type === 'email') url = `/api/osint/pro/email?email=${encodeURIComponent(email)}`
      else if (type === 'phone') url = `/api/osint/pro/phone?phone=${encodeURIComponent(phone)}`
      else if (type === 'domain') url = `/api/osint/pro/domain?domain=${encodeURIComponent(domain)}`
      else if (type === 'report') url = `/api/osint/pro/report?email=${encodeURIComponent(email)}&phone=${encodeURIComponent(phone)}&domain=${encodeURIComponent(domain)}`
      const r = await fetch(url, { method: 'POST' }).then(r => r.json())
      if (r?.error) { setError(r.error); return }
      setResult(r)
    } catch { setError("Échec de la requête. Réessayez.") }
    setLoading(false)
  }

  return (
    <div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        <div className="glass-card rounded-2xl p-4">
          <div className="flex items-center gap-2 mb-3"><Mail size={14} className="text-indigo-400" /><h3 className="text-xs font-semibold text-white">Email</h3></div>
          <input value={email} onChange={e => setEmail(e.target.value)}
            placeholder="user@example.com" className="w-full px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500 mb-2" />
          <button onClick={() => search('email')} disabled={loading || !email.trim()}
            className="w-full py-1.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-lg text-xs font-medium hover:bg-indigo-500/20 disabled:opacity-30">
            {loading && activeField === 'email' ? <Loader2 size={12} className="animate-spin mx-auto" /> : 'Chercher breaches'}
          </button>
        </div>
        <div className="glass-card rounded-2xl p-4">
          <div className="flex items-center gap-2 mb-3"><Phone size={14} className="text-emerald-400" /><h3 className="text-xs font-semibold text-white">Téléphone</h3></div>
          <input value={phone} onChange={e => setPhone(e.target.value)}
            placeholder="+33..." className="w-full px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500 mb-2" />
          <button onClick={() => search('phone')} disabled={loading || !phone.trim()}
            className="w-full py-1.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg text-xs font-medium hover:bg-emerald-500/20 disabled:opacity-30">
            {loading && activeField === 'phone' ? <Loader2 size={12} className="animate-spin mx-auto" /> : 'Analyser'}
          </button>
        </div>
        <div className="glass-card rounded-2xl p-4">
          <div className="flex items-center gap-2 mb-3"><Globe size={14} className="text-cyan-400" /><h3 className="text-xs font-semibold text-white">Domaine</h3></div>
          <input value={domain} onChange={e => setDomain(e.target.value)}
            placeholder="example.com" className="w-full px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500 mb-2" />
          <button onClick={() => search('domain')} disabled={loading || !domain.trim()}
            className="w-full py-1.5 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded-lg text-xs font-medium hover:bg-cyan-500/20 disabled:opacity-30">
            {loading && activeField === 'domain' ? <Loader2 size={12} className="animate-spin mx-auto" /> : 'WHOIS lookup'}
          </button>
        </div>
      </div>
      {(email || phone || domain) && (
        <button onClick={() => search('report')} disabled={loading}
          className="mb-6 px-6 py-3 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-xl text-sm font-medium hover:bg-rose-500/20 disabled:opacity-30 transition flex items-center gap-2">
          <Target size={14} /> Rapport complet
        </button>
      )}
      <OsintError message={error} />
      <OsintResult result={result} />
    </div>
  )
}

function DorksTab() {
  const [name, setName] = useState('')
  const [location, setLocation] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = async () => {
    if (!name.trim()) return
    setLoading(true); setResult(null); setError(null)
    try {
      const r = await fetch(`/api/osint/dorks?name=${encodeURIComponent(name)}&location=${encodeURIComponent(location)}&extract=true`, { method: 'POST' }).then(r => r.json())
      if (r?.error) { setError(r.error); return }
      setResult(r)
    } catch { setError("Échec de la requête. Réessayez.") }
    setLoading(false)
  }

  return (
    <div>
      <div className="glass-card rounded-2xl p-4 mb-6">
        <p className="text-xs text-slate-500 mb-3">Multi-engine dorking: DuckDuckGo, Bing, SearXNG. Recherche avancée par nom et localisation.</p>
        <div className="flex flex-col sm:flex-row gap-3">
          <input value={name} onChange={e => setName(e.target.value)}
            placeholder="Nom complet" className="flex-1 px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500" />
          <input value={location} onChange={e => setLocation(e.target.value)}
            placeholder="Localisation (optionnel)" className="flex-1 px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500" />
          <button onClick={search} disabled={loading || !name.trim()}
            className="px-6 py-2 bg-orange-500/10 border border-orange-500/30 text-orange-400 rounded-lg text-xs font-medium hover:bg-orange-500/20 disabled:opacity-30">
            {loading ? <Loader2 size={12} className="animate-spin" /> : 'Dorker'}
          </button>
        </div>
      </div>
      <OsintError message={error} />
      {result && (
        <div className="space-y-3">
          {result.top_findings && Object.entries(result.top_findings as Record<string, any[]>).map(([engine, urls]) => (
            <div key={engine} className="glass-card rounded-2xl p-4">
              <h3 className="text-sm font-semibold text-white mb-2 capitalize">{engine} ({urls.length})</h3>
              {urls.slice(0, 5).map((u: any, i: number) => (
                <a key={i} href={u.url} target="_blank" rel="noopener" className="block glass rounded-lg p-2 text-xs text-slate-400 hover:text-indigo-400 mb-1 truncate">
                  {u.title || u.url}
                </a>
              ))}
            </div>
          ))}
          {result.extracted_info && (
            <div className="glass-card rounded-2xl p-4">
              <h3 className="text-sm font-semibold text-white mb-2">Info extraite</h3>
              <pre className="text-[10px] text-slate-400 whitespace-pre-wrap">{JSON.stringify(result.extracted_info, null, 2).slice(0, 1000)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function ToolsTab() {
  const [username, setUsername] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [toolsStatus, setToolsStatus] = useState<any>(null)

  useState(() => {
    fetch('/api/osint/tools').then(r => r.json()).then(setToolsStatus).catch(() => {})
  })

  const runAll = async () => {
    if (!username.trim()) return
    setLoading(true); setResult(null); setError(null)
    try {
      const r = await fetch(`/api/osint/run-all?username=${encodeURIComponent(username)}`, { method: 'POST' }).then(r => r.json())
      if (r?.error) { setError(r.error); return }
      setResult(r)
    } catch { setError("Échec de la requête. Réessayez.") }
    setLoading(false)
  }

  return (
    <div className="space-y-4">
      {toolsStatus && (
        <div className="glass-card rounded-2xl p-4">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2"><BarChart3 size={14} className="text-cyan-400" /> Outils disponibles</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {Object.entries(toolsStatus as Record<string, any>).map(([k, v]) => (
              <div key={k} className="glass rounded-lg p-2 text-xs flex items-center justify-between">
                <span className="text-slate-300">{k}</span>
                <span className={v === 'available' || v === true ? 'text-emerald-400' : 'text-slate-500'}>{String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="glass-card rounded-2xl p-4">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2"><Bug size={14} className="text-amber-400" /> Lancer tous les outils (Sherlock, Maigret, Holehe)</h3>
        <p className="text-xs text-slate-500 mb-3">Fournissez un username pour lancer une recherche cross-plateforme.</p>
        <div className="flex gap-3">
          <input value={username} onChange={e => setUsername(e.target.value)}
            placeholder="Username..." className="flex-1 px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500" />
          <button onClick={runAll} disabled={loading || !username.trim()}
            className="px-6 py-2 bg-amber-500/10 border border-amber-500/30 text-amber-400 rounded-lg text-xs font-medium hover:bg-amber-500/20 disabled:opacity-30 flex items-center gap-1.5">
            <Play size={11} /> {loading ? <Loader2 size={12} className="animate-spin" /> : 'Run all'}
          </button>
        </div>
      </div>

      <OsintError message={error} />
      <OsintResult result={result} />
    </div>
  )
}
