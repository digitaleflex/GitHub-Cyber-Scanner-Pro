import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import CyberNewsFeed from '../components/CyberNewsFeed'
import { Newspaper, Radio } from 'lucide-react'

function NewsPage() {
  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-neon-cyan/20 to-neon-magenta/20 border border-neon-cyan/20 flex items-center justify-center">
            <Newspaper size={18} className="text-neon-cyan" />
          </div>
          <div>
            <h1 className="text-xl font-cyber font-bold text-white tracking-wider">
              Actualités Cyber
            </h1>
            <p className="text-gray-600 text-[10px] font-mono tracking-wider uppercase">
              Veille CERT-FR / ANSSI
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-6 neon-border-cyan">
        <div className="flex items-center gap-2 text-neon-cyan text-sm font-semibold uppercase tracking-wider mb-6 font-cyber">
          <Radio size={14} />
          Fil RSS
        </div>
        <CyberNewsFeed limit={100} showAll={true} />
      </div>
    </div>
  )
}

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/news',
  component: NewsPage,
})
