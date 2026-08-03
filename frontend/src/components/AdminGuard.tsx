import { useEffect } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { isAdminAuthenticated } from '../routes/login'

export default function AdminGuard({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()

  useEffect(() => {
    if (!isAdminAuthenticated()) {
      navigate({ to: '/login' })
    }
  }, [navigate])

  if (!isAdminAuthenticated()) return null

  return <>{children}</>
}
