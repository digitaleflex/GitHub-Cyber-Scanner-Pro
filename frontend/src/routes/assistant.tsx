import { useState, useRef, useEffect } from 'react'
import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { Send, Brain, User } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/assistant', component: AssistantPage })

interface Message { role: 'user' | 'assistant'; text: string }

function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([{
    role: 'assistant',
    text: "Bonjour. Je suis votre assistant HashCode Decision OS. Je connais vos technologies, vos missions et votre contexte de sécurité. Que puis-je faire pour vous ?"
  }])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => { scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight) }, [messages])

  const send = async () => {
    if (!input.trim() || loading) return
    const msg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: msg }])
    setLoading(true)
    try {
      const r = await fetch(`/api/assistant/chat?message=${encodeURIComponent(msg)}&profile_id=1`, { method: 'POST' })
      const d = await r.json()
      setMessages(prev => [...prev, { role: 'assistant', text: d.reply || "Désolé, je n'ai pas pu traiter votre demande." }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', text: "L'assistant est temporairement indisponible." }])
    }
    setLoading(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => { if (e.key === 'Enter') send() }

  return (
    <div className="max-w-2xl mx-auto py-4 sm:py-8 animate-fade h-[calc(100vh-8rem)] flex flex-col">
      <h1 className="h1 mb-1" style={{ color: 'var(--text)' }}>Assistant</h1>
      <p className="body-sm text-secondary mb-4">Posez-moi vos questions sur vos menaces, missions et décisions.</p>

      <div ref={scrollRef} className="flex-1 overflow-y-auto surface rounded-2xl p-4 mb-3 space-y-3"
        style={{ border: '1px solid var(--border)' }}>
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : ''}`}>
            {m.role === 'assistant' && (
              <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                style={{ background: 'var(--ai-light)' }}>
                <Brain size={13} style={{ color: 'var(--ai)' }} />
              </div>
            )}
            <div className="rounded-2xl px-4 py-2.5 text-sm max-w-[80%]" style={{
              background: m.role === 'user' ? 'var(--decision-light)' : 'var(--bg-alt)',
              color: 'var(--text)',
              border: m.role === 'user' ? '1px solid var(--decision)' : '1px solid var(--border-light)',
            }}>
              <p className="leading-relaxed whitespace-pre-wrap">{m.text}</p>
            </div>
            {m.role === 'user' && (
              <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5"
                style={{ background: 'var(--surface-hover)', border: '1px solid var(--border)' }}>
                <User size={13} style={{ color: 'var(--text-muted)' }} />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: 'var(--ai-light)' }}>
              <Brain size={13} style={{ color: 'var(--ai)' }} />
            </div>
            <div className="rounded-2xl px-4 py-2.5" style={{ background: 'var(--bg-alt)', border: '1px solid var(--border-light)' }}>
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--text-muted)', animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--text-muted)', animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--text-muted)', animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input ref={inputRef} type="text" value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
          placeholder="Ex: Pourquoi Docker est prioritaire ? Prends un rapport..."
          className="flex-1 rounded-xl px-4 py-3 text-sm ring-brand"
          style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            color: 'var(--text)',
          }}
        />
        <button onClick={send} disabled={loading || !input.trim()}
          className="px-4 py-3 rounded-xl font-medium transition-all disabled:opacity-40 flex items-center justify-center"
          style={{
            background: 'var(--decision)',
            color: 'white',
          }}>
          <Send size={16} />
        </button>
      </div>
    </div>
  )
}
