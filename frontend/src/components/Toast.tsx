import { useState, useCallback, createContext, useContext, type ReactNode } from 'react'
import { CheckCircle2, XCircle, AlertCircle, Info, X } from 'lucide-react'

type ToastType = 'success' | 'error' | 'warning' | 'info'
type Toast = { id: number; type: ToastType; message: string }

const ToastCtx = createContext<{ toast: (type: ToastType, msg: string) => void }>({ toast: () => {} })
export const useToast = () => useContext(ToastCtx)

const ICONS: Record<ToastType, ReactNode> = {
  success: <CheckCircle2 size={16} style={{ color: '#22C55E' }} />,
  error: <XCircle size={16} style={{ color: '#EF4444' }} />,
  warning: <AlertCircle size={16} style={{ color: '#F59E0B' }} />,
  info: <Info size={16} style={{ color: '#3B82F6' }} />,
}

const BORDERS: Record<ToastType, string> = {
  success: '#22C55E', error: '#EF4444', warning: '#F59E0B', info: '#3B82F6',
}

let _id = 0

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const toast = useCallback((type: ToastType, message: string) => {
    const id = ++_id
    setToasts(prev => [...prev, { id, type, message }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3500)
  }, [])

  return (
    <ToastCtx.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm" aria-live="polite">
        {toasts.map(t => (
          <div key={t.id} className="animate-slide rounded-xl px-4 py-3 text-sm flex items-start gap-2.5 shadow-xl"
            style={{ background: 'var(--surface-elevated)', border: `1px solid ${BORDERS[t.type]}`, color: 'var(--text)' }}>
            <span className="shrink-0 mt-0.5">{ICONS[t.type]}</span>
            <span className="flex-1 text-xs" style={{ color: 'var(--text-secondary)' }}>{t.message}</span>
            <button onClick={() => setToasts(prev => prev.filter(x => x.id !== t.id))} aria-label="Fermer" className="shrink-0 opacity-50 hover:opacity-100"><X size={14} /></button>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  )
}
