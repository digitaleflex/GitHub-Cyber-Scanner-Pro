import { useEffect } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { isAdminAuthenticated } from '../routes/login'
import AdminSidebar from './AdminSidebar'

export default function AdminGuard({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()

  useEffect(() => {
    if (!isAdminAuthenticated()) {
      navigate({ to: '/login' })
    }
  }, [navigate])

  if (!isAdminAuthenticated()) return null

  return (
    <div className="flex gap-6 items-start">
      <AdminSidebar />
      <div className="flex-1 min-w-0">{children}</div>
    </div>
  )
}
