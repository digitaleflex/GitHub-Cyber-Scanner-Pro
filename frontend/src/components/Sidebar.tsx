import { Link, useRouter } from '@tanstack/react-router'
import { Shield, Target, Wrench, Rocket, BookOpen, Bug, Clock, Sparkles, Settings, HelpCircle } from 'lucide-react'

const groups = [
  {
    title: 'INSTRUMENTS',
    items: [
      { to: '/', label: "Aujourd'hui", icon: Shield },
      { to: '/threats', label: 'Menaces', icon: Target },
      { to: '/tools', label: 'Outils', icon: Wrench },
      { to: '/missions', label: 'Missions', icon: Rocket },
      { to: '/library', label: 'Bibliothèque', icon: BookOpen },
    ],
  },
  {
    title: 'INTELLIGENCE',
    items: [
      { to: '/cves', label: 'CVE', icon: Bug },
      { to: '/timeline', label: 'Timeline', icon: Clock },
      { to: '/assistant', label: 'Assistant', icon: Sparkles },
    ],
  },
]

export function Sidebar() {
  const router = useRouter()
  const pathname = router.state.location.pathname

  const isActive = (to: string) => {
    if (to === '/') return pathname === '/'
    return pathname.startsWith(to)
  }

  return (
    <aside
      className="fixed left-0 top-0 h-full flex flex-col"
      style={{
        width: '240px',
        background: 'var(--surface)',
        borderRight: '1px solid var(--border)',
      }}
    >
      <div className="h-14 flex items-center gap-3 px-5" style={{ borderBottom: '1px solid var(--border)' }}>
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm"
          style={{ background: 'var(--amber)', color: 'var(--text-inverse)' }}
        >
          H
        </div>
        <div>
          <div className="font-display text-h2" style={{ lineHeight: 1 }}>HashCode</div>
          <div className="text-caption t-m">Cockpit</div>
        </div>
      </div>

      <nav className="flex-1 py-4 px-3 space-y-6 overflow-y-auto">
        {groups.map((group) => (
          <div key={group.title}>
            <div className="text-caption t-m px-3 mb-2">{group.title}</div>
            <div className="space-y-1">
              {group.items.map((item) => {
                const active = isActive(item.to)
                const Icon = item.icon
                return (
                  <Link
                    key={item.to}
                    to={item.to as any}
                    className="flex items-center gap-3 px-3 py-2 rounded-lg transition-all"
                    style={{
                      background: active ? 'var(--surface-elevated)' : 'transparent',
                      color: active ? 'var(--text)' : 'var(--text-secondary)',
                      borderLeft: active ? '4px solid var(--amber)' : '4px solid transparent',
                    }}
                  >
                    <Icon size={16} style={{ color: active ? 'var(--amber)' : 'var(--text-muted)' }} />
                    <span className="text-body-sm font-medium">{item.label}</span>
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="p-3 space-y-1" style={{ borderTop: '1px solid var(--border)' }}>
        <Link
          to="/settings"
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-body-sm font-medium t-s hover:bg-[var(--surface-elevated)] transition-colors"
        >
          <Settings size={16} className="t-m" /> Paramètres
        </Link>
        <Link
          to="/docs"
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-body-sm font-medium t-s hover:bg-[var(--surface-elevated)] transition-colors"
        >
          <HelpCircle size={16} className="t-m" /> Documentation
        </Link>
      </div>
    </aside>
  )
}
