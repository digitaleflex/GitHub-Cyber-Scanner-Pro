import { useEffect } from 'react'

export default function useSearchHotkey() {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === '/' && document.activeElement?.tagName !== 'INPUT' && document.activeElement?.tagName !== 'TEXTAREA') {
        e.preventDefault()
        const input = document.querySelector<HTMLInputElement>('input[type="text"][placeholder*="Recherch"]')
        input?.focus()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])
}
