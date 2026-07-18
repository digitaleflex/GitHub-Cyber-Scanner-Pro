import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import CyberNewsFeed from '../components/CyberNewsFeed'
import { useNewsHealth, useNewsCountries } from '../lib/api'
import { Newspaper, Radio, Activity, ShieldAlert, Globe } from 'lucide-react'
import { useState } from 'react'

function FeedHealthBadge() {
  const { data, isLoading } = useNewsHealth()
  if (isLoading || !data) return null
  const pct = data.feeds_total
    ? Math.round((data.feeds_usable / data.feeds_total) * 100)
    : 0
  const blocked = (data.feeds_dead?.length || 0) + (data.feeds_blocked_antibot?.length || 0)
  const color = pct >= 80 ? 'text-neon-green' : pct >= 50 ? 'text-neon-amber' : 'text-neon-red'
  return (
    <div className="flex items-center gap-2 mb-4 text-[10px] font-mono uppercase tracking-wider">
      <span className={`flex items-center gap-1.5 ${color}`}>
        <Activity size={12} />
        {data.feeds_usable}/{data.feeds_total} flux sains ({pct}%)
      </span>
      {blocked > 0 && (
        <span className="flex items-center gap-1 text-neon-red/80" title={`Morts: ${data.feeds_dead?.join(', ')}\nAnti-bot: ${data.feeds_blocked_antibot?.join(', ')}`}>
          <ShieldAlert size={12} />
          {blocked} auto-exclus
        </span>
      )}
      <span className="text-gray-700">
        collecteur: {data.collector}
      </span>
    </div>
  )
}

const COUNTRY_NAMES: Record<string, string> = {
  FR: 'France', US: 'États-Unis', GB: 'Royaume-Uni', DE: 'Allemagne', EU: 'Union Européenne',
  CA: 'Canada', AU: 'Australie', JP: 'Japon', CH: 'Suisse', ES: 'Espagne', IT: 'Italie',
  NL: 'Pays-Bas', PL: 'Pologne', SE: 'Suède', BE: 'Belgique', AT: 'Autriche', BR: 'Brésil',
  PT: 'Portugal', FI: 'Finlande', NO: 'Norvège', DK: 'Danemark', CZ: 'Tchéquie', HU: 'Hongrie',
  RO: 'Roumanie', UA: 'Ukraine', IL: 'Israël', SG: 'Singapour', HK: 'Hong Kong', EG: 'Égypte',
  HR: 'Croatie', LV: 'Lettonie', SI: 'Slovénie', SK: 'Slovaquie', LY: 'Libye', DZ: 'Algérie',
}

function CountryFilter({ value, onChange }: { value: string | null; onChange: (c: string | null) => void }) {
  const { data } = useNewsCountries()
  if (!data || data.length === 0) return null
  return (
    <div className="flex items-center gap-2 mb-4">
      <Globe size={14} className="text-neon-cyan" />
      <select
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value || null)}
        className="bg-white/5 border border-white/10 rounded-md px-3 py-1.5 text-xs font-mono text-gray-200 focus:outline-none focus:border-neon-cyan/50"
      >
        <option value="">🌍 Tous les pays ({data.reduce((a, c) => a + c.count, 0)})</option>
        {data.map((c) => (
          <option key={c.country} value={c.country}>
            {COUNTRY_NAMES[c.country] ?? c.country} ({c.count})
          </option>
        ))}
      </select>
    </div>
  )
}

function NewsPage() {
  const [country, setCountry] = useState<string | null>(null)
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
              Veille CERT mondiaux / ANSSI / Threat Intel
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-6 neon-border-cyan">
        <div className="flex items-center gap-2 text-neon-cyan text-sm font-semibold uppercase tracking-wider mb-2 font-cyber">
          <Radio size={14} />
          Fil RSS
        </div>
        <FeedHealthBadge />
        <CountryFilter value={country} onChange={setCountry} />
        <CyberNewsFeed limit={100} showAll={true} country={country} />
      </div>
    </div>
  )
}

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/news',
  component: NewsPage,
})
