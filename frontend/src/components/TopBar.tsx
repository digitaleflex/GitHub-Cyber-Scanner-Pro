import { Activity } from 'lucide-react'
import { useRouter } from '@tanstack/react-router'
import { useScanStatus } from '../lib/api'
import { useState, useCallback } from 'react'

export function TopBar({ title }: { title: string }) {
  const { data, refetch } = useScanStatus()
  const router = useRouter()
  const [scanning, setScanning] = useState(false)
  const isScanning = scanning || data?.status?.includes('en cours')

  const handleScan = useCallback(async () => {
    if (isScanning) return
    setScanning(true)
    try {
      const res = await fetch('/api/scan', { method: 'POST' })
      if (res.ok) { setTimeout(() => { refetch(); router.invalidate() }, 1000) }
    } catch {}
    setTimeout(() => setScanning(false), 2000)
  }, [isScanning, refetch, router])

  return (
    <header
      className="h-14 flex items-center justify-between px-6"
      style={{
        background: 'var(--bg)',
        borderBottom: '1px solid var(--border)',
      }}
    >
      <h1 className="font-display text-h1">{title}</h1>

      <div className="flex items-center gap-6">
        <div className="hidden md:flex items-center gap-3 text-caption t-m">
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--lime)' }} />
            NVD
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--lime)' }} />
            CISA
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--lime)' }} />
            GitHub
          </span>
        </div>

        <div className="font-mono text-mono t-s">
          {new Date().toISOString().slice(11, 16)} UTC
        </div>

        <button
          onClick={handleScan}
          disabled={isScanning}
          className="flex items-center gap-2 px-4 py-1.5 rounded-md text-body-sm font-semibold transition-all active:scale-[0.98]"
          style={{
            background: isScanning ? 'var(--surface-elevated)' : 'var(--amber)',
            color: isScanning ? 'var(--text-secondary)' : 'var(--text-inverse)',
            border: isScanning ? '1px solid var(--border)' : 'none',
          }}
        >
          <Activity size={14} className={isScanning ? 'animate-spin-scan' : ''} />
          {isScanning ? 'Scan...' : 'Scanner'}
        </button>
      </div>
    </header>
  )
}
