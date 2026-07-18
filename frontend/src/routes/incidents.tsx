import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useNewsIncidents, useNewsCountries } from '../lib/api'
import { ShieldAlert, Globe, Radio, Activity, ExternalLink, Tag, Crosshair } from 'lucide-react'
import { useState } from 'react'

function SeverityBadge({ score }: { score: number }) {
  const color =
    score >= 80 ? 'text-neon-red bg-neon-red/10 border-neon-red/30'
    : score >= 50 ? 'text-neon-amber bg-neon-amber/10 border-neon-amber/30'
    : 'text-neon-cyan bg-neon-cyan/10 border-neon-cyan/30'
  const label = score >= 80 ? 'CRITIQUE' : score >= 50 ? 'ELEVE' : 'MODERE'
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono border ${color}`}>
      <Crosshair size={9} />
      {score}/100 {label}
    </span>
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

function EntityBadges({ items, color }: { items: string[]; color: string }) {
  if (!items.length) return null
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {items.slice(0, 12).map((it) => (
        <span
          key={it}
          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono ${color}`}
        >
          <Tag size={9} />
          {it}
        </span>
      ))}
      {items.length > 12 && (
        <span className="px-2 py-0.5 rounded text-[10px] font-mono text-gray-600">
          +{items.length - 12}
        </span>
      )}
    </div>
  )
}

function IncidentsPage() {
  const [country, setCountry] = useState<string | null>(null)
  const { data, isLoading, error } = useNewsIncidents(50, country ?? undefined)

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-neon-magenta/20 to-neon-red/20 border border-neon-magenta/20 flex items-center justify-center">
            <ShieldAlert size={18} className="text-neon-magenta" />
          </div>
          <div>
            <h1 className="text-xl font-cyber font-bold text-white tracking-wider">
              Incidents Cyber
            </h1>
            <p className="text-gray-600 text-[10px] font-mono tracking-wider uppercase">
              Corrélation multi-flux par CVE / IOC / produit
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-6 neon-border-magenta">
        <div className="flex items-center gap-2 text-neon-magenta text-sm font-semibold uppercase tracking-wider mb-2 font-cyber">
          <Radio size={14} />
          Incidents unifiés
        </div>
        <CountryFilter value={country} onChange={setCountry} />

        {isLoading && (
          <div className="flex items-center gap-2 text-gray-600 text-xs font-mono mt-4">
            <Activity size={12} className="animate-pulse" />
            Corrélation des flux en cours...
          </div>
        )}
        {error && (
          <div className="text-neon-red text-xs font-mono mt-4">
            Erreur de chargement des incidents.
          </div>
        )}
        {data && data.incidents.length === 0 && (
          <div className="text-gray-600 text-xs font-mono mt-4">
            Aucun incident corrélé pour l'instant. Lancez un scan pour alimenter la base.
          </div>
        )}

        <div className="space-y-4 mt-4">
          {data?.incidents.map((inc) => (
            <div
              key={inc.incident_id}
              className="bg-white/[0.02] border border-white/[0.07] rounded-lg p-4 hover:border-neon-magenta/30 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <a
                    href={inc.primary_link}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm font-semibold text-white hover:text-neon-cyan transition-colors flex items-center gap-1.5"
                  >
                    {inc.title}
                    <ExternalLink size={12} className="text-gray-600 shrink-0" />
                  </a>
                  <div className="flex items-center gap-3 mt-1 text-[10px] font-mono text-gray-600 uppercase tracking-wider">
                    <span className="flex items-center gap-1 text-neon-green">
                      <Radio size={10} />
                      {inc.num_sources} source(s)
                    </span>
                    {inc.countries.map((c) => (
                      <span key={c} className="text-neon-cyan/70">
                        {COUNTRY_NAMES[c] ?? c}
                      </span>
                    ))}
                  </div>
                </div>
                <SeverityBadge score={inc.severity_score} />
              </div>

              <EntityBadges items={inc.cves} color="text-neon-red bg-neon-red/10" />
              <EntityBadges items={inc.products} color="text-neon-amber bg-neon-amber/10" />
              <EntityBadges items={inc.domains} color="text-neon-cyan bg-neon-cyan/10" />
              <EntityBadges items={inc.ips} color="text-neon-red bg-neon-red/10" />
              <EntityBadges items={inc.hashes} color="text-neon-magenta bg-neon-magenta/10" />
              {inc.attack_details.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {inc.attack_details.map((a) => (
                    <span
                      key={a.technique}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono text-neon-magenta bg-neon-magenta/10"
                      title={a.name}
                    >
                      <Tag size={9} />
                      {a.technique} · {a.tactic}
                    </span>
                  ))}
                </div>
              )}

              {inc.news.length > 1 && (
                <details className="mt-3">
                  <summary className="cursor-pointer text-[10px] font-mono text-gray-500 hover:text-neon-cyan uppercase tracking-wider">
                    Voir les {inc.news.length} articles sources
                  </summary>
                  <ul className="mt-2 space-y-1.5 border-l border-white/10 pl-3">
                    {inc.news.map((n) => (
                      <li key={n.id} className="text-[11px]">
                        <a
                          href={n.link}
                          target="_blank"
                          rel="noreferrer"
                          className="text-gray-400 hover:text-neon-cyan transition-colors"
                        >
                          {n.title}
                        </a>
                        <span className="text-gray-700 font-mono ml-2">
                          {n.source_name}
                          {n.country ? ` · ${COUNTRY_NAMES[n.country] ?? n.country}` : ''}
                        </span>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export const Route = createRoute({
  getParentRoute: () => RootRoute,
  path: '/incidents',
  component: IncidentsPage,
})
