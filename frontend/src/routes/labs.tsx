import { useState } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import { Brain, Loader2, Activity, MessageSquare, Bug, Search, BarChart3, Shield, Code } from 'lucide-react'
import { SkeletonGraph } from '../components/Skeleton'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/labs', component: LabsPage })

const MODELS = [
  { name: 'RoBERTa Squad2', endpoint: 'qa', desc: 'Question Answering — répond à des questions sur un contexte', icon: MessageSquare, color: 'indigo' },
  { name: 'SecBERT', endpoint: 'vuln-type', desc: 'Détection de type de vulnérabilité — CWE classification', icon: Bug, color: 'rose' },
  { name: 'BART Large MNLI', endpoint: 'classify', desc: 'Zero-shot classification — catégorisation sans entraînement', icon: Search, color: 'violet' },
  { name: 'Granite Guardian', endpoint: 'guard', desc: 'Content Safety — scan de contenu suspect', icon: Shield, color: 'amber' },
  { name: 'all-MiniLM-L6', endpoint: 'embed', desc: 'Embeddings sémantiques — vectorisation de texte', icon: BarChart3, color: 'emerald' },
  { name: 'CodeBERT', endpoint: '-', desc: 'Compréhension de code source — analyse sémantique', icon: Code, color: 'cyan' },
  { name: 'DistilBERT', endpoint: '-', desc: 'Classification de texte — NLP généraliste', icon: Brain, color: 'violet' },
  { name: 'BERT Base Uncased', endpoint: '-', desc: 'Embeddings + classification — fondation NLP', icon: Brain, color: 'indigo' },
]

const COLOR_MAP: Record<string, { bg: string; text: string }> = {
  indigo: { bg: 'bg-indigo-500/10', text: 'text-indigo-400' },
  rose: { bg: 'bg-rose-500/10', text: 'text-rose-400' },
  violet: { bg: 'bg-violet-500/10', text: 'text-violet-400' },
  amber: { bg: 'bg-amber-500/10', text: 'text-amber-400' },
  emerald: { bg: 'bg-emerald-500/10', text: 'text-emerald-400' },
  cyan: { bg: 'bg-cyan-500/10', text: 'text-cyan-400' },
}

function ModelCard({ name, desc, icon: Icon, color }: (typeof MODELS)[0]) {
  const c = COLOR_MAP[color] || COLOR_MAP.indigo
  return (
    <div className="glass-card rounded-xl p-4 group text-center">
      <div className={`w-10 h-10 mx-auto rounded-xl ${c.bg} flex items-center justify-center mb-2`}>
        <Icon size={18} className={c.text} />
      </div>
      <h3 className="text-xs font-semibold text-white">{name}</h3>
      <p className="text-[10px] text-slate-500 mt-1 line-clamp-2">{desc}</p>
    </div>
  )
}

function LabsPage() {
  const { data: hfStatus, isLoading } = useQuery({ queryKey: ['hf-status'], queryFn: () => fetch('/api/hf/status').then(r => r.json()).catch(() => ({})), staleTime: 120_000 })

  return (
    <div className="max-w-5xl mx-auto py-4 sm:py-8 animate-fade">
      <div className="flex items-center gap-2 mb-1">
        <Brain size={20} className="text-violet-400" />
        <h1 className="text-xl font-bold text-white">AI Lab</h1>
      </div>
      <p className="text-xs sm:text-sm text-slate-400 mb-6">
        22 modeles HuggingFace integres — classification, Q&A, detection de vulnerabilites, embeddings, content safety.
      </p>

      {/* Status */}
      {isLoading ? <SkeletonGraph /> : (
        <div className="glass-card rounded-2xl p-4 mb-6">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2"><Activity size={14} className="text-indigo-400" /> Statut des services HF</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div className="glass rounded-xl p-3 text-center">
              <div className={`text-lg font-bold ${hfStatus?.models_loaded ? 'text-emerald-400' : 'text-rose-400'}`}>{hfStatus?.models_loaded || '?'}</div>
              <div className="text-[9px] text-slate-500">Modeles charges</div>
            </div>
            <div className="glass rounded-xl p-3 text-center">
              <div className="text-lg font-bold text-white">{hfStatus?.total_models || 22}</div>
              <div className="text-[9px] text-slate-500">Total modeles</div>
            </div>
            <div className="glass rounded-xl p-3 text-center">
              <div className={`text-lg font-bold ${hfStatus?.api_available ? 'text-emerald-400' : 'text-rose-400'}`}>{hfStatus?.api_available ? 'OK' : 'DOWN'}</div>
              <div className="text-[9px] text-slate-500">API HF</div>
            </div>
            <div className="glass rounded-xl p-3 text-center">
              <div className="text-lg font-bold text-white">{hfStatus?.response_time_ms || '?'}ms</div>
              <div className="text-[9px] text-slate-500">Latence</div>
            </div>
          </div>
        </div>
      )}

      {/* Modeles disponibles */}
      <h2 className="text-sm font-semibold text-white mb-3">Modeles disponibles</h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mb-8">
        {MODELS.map((m, i) => <ModelCard key={i} {...m} />)}
      </div>

      {/* Playgrounds */}
      <h2 className="text-sm font-semibold text-white mb-3">Playgrounds</h2>
      <div className="space-y-4">
        <ClassifyPlayground />
        <QAPlayground />
        <VulnPlayground />
        <EmbedPlayground />
      </div>
    </div>
  )
}

function PlaygroundShell({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="glass-card rounded-2xl p-4 sm:p-5">
      <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">{icon} {title}</h3>
      {children}
    </div>
  )
}

function ClassifyPlayground() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const classify = async () => {
    setLoading(true)
    try { const r = await fetch(`/api/hf/classify?text=${encodeURIComponent(text)}`).then(r => r.json()); setResult(r) } catch {}
    setLoading(false)
  }
  return (
    <PlaygroundShell title="Classification Zero-Shot (BART Large MNLI)" icon={<Search size={14} className="text-violet-400" />}>
      <div className="flex gap-2 mb-3">
        <input value={text} onChange={e => setText(e.target.value)} placeholder="Decrivez un outil ou une technique..."
          className="flex-1 px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500" />
        <button onClick={classify} disabled={loading}
          className="px-4 py-2 bg-violet-500/10 border border-violet-500/20 text-violet-400 rounded-lg text-xs font-medium hover:bg-violet-500/20 disabled:opacity-30">
          {loading ? <Loader2 size={12} className="animate-spin" /> : 'Classifier'}
        </button>
      </div>
      {result?.all && (
        <div className="text-xs space-y-1">
          {Object.entries(result.all as Record<string, number>).slice(0, 5).map(([k, v]) => (
            <div key={k} className="flex items-center gap-2">
              <span className="text-slate-400 w-20">{k}</span>
              <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden"><div className="h-full bg-violet-500/50 rounded-full" style={{ width: `${(v as number) * 100}%` }} /></div>
              <span className="text-slate-500 w-10 text-right">{((v as number) * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      )}
      <div className="text-[9px] text-slate-500 mt-2">Categories: Red Team, Blue Team, Malware, Exploit, OSINT, Cloud, Forensics</div>
    </PlaygroundShell>
  )
}

function QAPlayground() {
  const [question, setQuestion] = useState('')
  const [context, setContext] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const ask = async () => {
    setLoading(true)
    try { const r = await fetch(`/api/hf/qa?question=${encodeURIComponent(question)}&context=${encodeURIComponent(context)}`).then(r => r.json()); setAnswer(r.answer || JSON.stringify(r)) } catch {}
    setLoading(false)
  }
  return (
    <PlaygroundShell title="Question Answering (RoBERTa Squad2)" icon={<MessageSquare size={14} className="text-indigo-400" />}>
      <div className="space-y-2">
        <input value={question} onChange={e => setQuestion(e.target.value)} placeholder="Question..."
          className="w-full px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500" />
        <textarea value={context} onChange={e => setContext(e.target.value)} placeholder="Contexte (description CVE, rapport, article...)"
          className="w-full px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500 min-h-[50px]" />
        <div className="flex items-center gap-2">
          <button onClick={ask} disabled={loading || !question.trim()}
            className="px-4 py-2 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-lg text-xs font-medium hover:bg-indigo-500/20 disabled:opacity-30">
            {loading ? <Loader2 size={12} className="animate-spin" /> : 'Demander'}
          </button>
          {answer && <span className="text-xs text-indigo-400 font-medium">{answer}</span>}
        </div>
      </div>
    </PlaygroundShell>
  )
}

function VulnPlayground() {
  const [text, setText] = useState('')
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)
  const detect = async () => {
    setLoading(true)
    try { const r = await fetch(`/api/hf/vuln-type?text=${encodeURIComponent(text)}`).then(r => r.json()); setResult(r.type || JSON.stringify(r)) } catch {}
    setLoading(false)
  }
  return (
    <PlaygroundShell title="Detection de Vulnerabilite (SecBERT)" icon={<Bug size={14} className="text-rose-400" />}>
      <div className="space-y-2">
        <textarea value={text} onChange={e => setText(e.target.value)} placeholder="Description d'une vulnerabilite, rapport CVE, code suspect..."
          className="w-full px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500 min-h-[60px]" />
        <div className="flex items-center gap-2">
          <button onClick={detect} disabled={loading || !text.trim()}
            className="px-4 py-2 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-lg text-xs font-medium hover:bg-rose-500/20 disabled:opacity-30">
            {loading ? <Loader2 size={12} className="animate-spin" /> : 'Detecter'}
          </button>
          {result && <span className="text-xs text-rose-400 font-mono">{result}</span>}
        </div>
      </div>
    </PlaygroundShell>
  )
}

function EmbedPlayground() {
  const [text, setText] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const embed = async () => {
    setLoading(true)
    try { const r = await fetch(`/api/hf/embed?text=${encodeURIComponent(text)}`).then(r => r.json()); setResult(r) } catch {}
    setLoading(false)
  }
  return (
    <PlaygroundShell title="Embeddings Semantiques (all-MiniLM-L6)" icon={<BarChart3 size={14} className="text-emerald-400" />}>
      <div className="space-y-2">
        <input value={text} onChange={e => setText(e.target.value)} placeholder="Texte a vectoriser..."
          className="w-full px-3 py-2 glass rounded-lg text-xs text-white placeholder-slate-500" />
        <button onClick={embed} disabled={loading || !text.trim()}
          className="px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg text-xs font-medium hover:bg-emerald-500/20 disabled:opacity-30">
          {loading ? <Loader2 size={12} className="animate-spin" /> : 'Generer embedding'}
        </button>
        {result && (
          <div className="text-xs text-slate-500 mt-2">
            <span>{result.dims} dimensions</span>
            <code className="block mt-1 text-[10px] text-slate-500 break-all">{JSON.stringify(result.embedding)}</code>
          </div>
        )}
      </div>
    </PlaygroundShell>
  )
}
