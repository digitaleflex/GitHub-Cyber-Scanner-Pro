import { createRoute, Link } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import { useQuery } from '@tanstack/react-query'
import {
  Shield, Activity, TrendingUp, Brain, Target, Layers, Server, AlertCircle, Sparkles,
} from 'lucide-react'
import { PageLoader } from '../components/CyberLoader'
import { InstrumentPanel } from '../components/InstrumentPanel'
import { KpiTile } from '../components/KpiTile'
import { AlertTile } from '../components/AlertTile'
import { ScoreRing } from '../components/ScoreRing'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/', component: HomePage })

interface PriorityDecision {
  cve_id: string; score: number; level: string; severity: string; cvss_score: number | null
  published: string | null; description: string; is_kev: boolean; exploits_count: number
  factors: Record<string, number>; reasons: string[]; risk_if_ignored: string; confidence: string; sources: string[]
}

function HomePage() {
  const { data: org } = useQuery({
    queryKey: ['organization', 1],
    queryFn: () => fetch('/api/organization?profile_id=1').then(r => r.json()),
    staleTime: 300_000,
  })
  const orgName = org?.organization?.name || org?.profile?.org_name || 'Eurin'

  const { data: priority, isLoading, error } = useQuery({
    queryKey: ['priority-home'],
    queryFn: async () => { const r = await fetch('/api/priority/cves?days=90&limit=8'); if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() },
    staleTime: 120_000,
  })

  const summary = priority?.summary
  const decisions: PriorityDecision[] = priority?.decisions || []
  const topAlerts = decisions.slice(0, 4)
  const riskScore = decisions.length > 0
    ? Math.round(decisions.reduce((acc: number, d: PriorityDecision) => acc + d.score, 0) / decisions.length)
    : 0
  const newToday = summary?.new_today ?? 0
  const newKev = summary?.new_kev ?? 0
  const critiques = decisions.filter((d: PriorityDecision) => d.level === 'CRITIQUE').length
  const kevCount = decisions.filter((d: PriorityDecision) => d.is_kev).length

  if (isLoading) return <PageLoader text="Analyse de votre environnement..." />
  if (error) return (
    <div className="py-20 text-center">
      <AlertCircle size={40} className="mx-auto mb-4" style={{ color: 'var(--red)' }} />
      <h2 className="text-h2 t-p mb-2">Service indisponible</h2>
      <p className="text-body-sm t-s">Réessayez dans quelques instants.</p>
    </div>
  )

  const riskColor = riskScore >= 70 ? 'var(--red)' : riskScore >= 40 ? 'var(--amber)' : 'var(--lime)'
  const riskLevel = riskScore >= 70 ? 'ÉLEVÉ' : riskScore >= 40 ? 'MODÉRÉ' : 'FAIBLE'

  return <div className="max-w-[1440px] mx-auto" role="main" aria-label="Cockpit">
    {/* ═══ HERO ═══════════════════════════════════════════ */}
    <section className="py-6 sm:py-8 animate-fade">
      <p className="text-caption mb-1 flex items-center gap-1.5 t-amber"><Sparkles size={12} /> Cockpit</p>
      <h1 className="text-h1 t-p mb-1">Bonjour {orgName}</h1>
      <p className="text-body-sm t-s mb-3">
        {newToday > 0 && <><strong className="t-p">{newToday}</strong> nouvelles CVE aujourd'hui · </>}
        <strong className="t-p">{decisions.length}</strong> décisions prioritaires
        {critiques > 0 && <>. <strong className="t-red">{critiques} critique{critiques > 1 ? 's' : ''}</strong></>}
      </p>
      <div className="flex items-center gap-3 text-caption t-m">
        <Activity size={11} /> Depuis 24h : <span className="t-red">+{newKev} KEV</span> · +{newToday} CVE
      </div>
    </section>

    {/* ═══ MAIN GRID ══════════════════════════════════════ */}
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pb-8">
      {/* ── Colonne principale 2/3 ── */}
      <div className="lg:col-span-2 space-y-6">
        {/* Risque Global */}
        <InstrumentPanel title="Risque Global" icon={<Shield size={18} />} accent="amber">
          <div className="flex flex-col items-center py-4">
            <ScoreRing score={riskScore} color={riskColor} size={160} />
            <div className="mt-4 flex items-center gap-3">
              <span className="text-caption px-3 py-1 rounded"
                style={{ background: `${riskColor}20`, color: riskColor, border: `1px solid ${riskColor}40` }}>
                {riskLevel}
              </span>
              <span className="text-body-sm t-s">{riskScore} / 100 en moyenne</span>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3 mt-4">
            <KpiTile value={decisions.length} label="Décisions" color="amber" />
            <KpiTile value={critiques} label="Critiques" color="red" />
            <KpiTile value={kevCount} label="KEV" color="red" />
          </div>
        </InstrumentPanel>

        {/* Menaces Prioritaires */}
        {topAlerts.length > 0 && (
          <InstrumentPanel title="Menaces Prioritaires" icon={<Brain size={18} />} accent="red">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {topAlerts.map((d, i) => (
                <Link key={i} to="/cve/$id" params={{ id: d.cve_id }} style={{ textDecoration: 'none' }}>
                  <AlertTile
                    cveId={d.cve_id}
                    description={d.description}
                    level={d.level as 'CRITIQUE' | 'ELEVE' | 'MOYEN' | 'BAS'}
                    cvss={d.cvss_score}
                    isKev={d.is_kev}
                    exploits={d.exploits_count}
                  />
                </Link>
              ))}
            </div>
          </InstrumentPanel>
        )}

        {/* Accès Rapide */}
        <div>
          <h2 className="text-h2 t-p mb-4">Accès Rapide</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {[
              { to: '/cves',     icon: <Shield size={16} />,     label: 'CVE Explorer',  color: 'var(--cyan)' },
              { to: '/threats',  icon: <TrendingUp size={16} />, label: 'Menaces',       color: 'var(--red)' },
              { to: '/tools',    icon: <Server size={16} />,     label: 'Outils',        color: 'var(--violet)' },
              { to: '/missions', icon: <Target size={16} />,     label: 'Missions',      color: 'var(--amber)' },
              { to: '/library',  icon: <Layers size={16} />,     label: 'Bibliothèque',  color: 'var(--lime)' },
            ].map(link => (
              <Link key={link.to} to={link.to as any}
                className="rounded-xl p-4 group hover:-translate-y-0.5 transition-all flex flex-col items-center gap-2 text-center"
                style={{ background: 'var(--surface)', border: '1px solid var(--border)', textDecoration: 'none' }}>
                <div style={{ color: link.color }}>{link.icon}</div>
                <div className="text-body-sm font-semibold t-p">{link.label}</div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* ── Side Panel 1/3 (desktop only) ═════════════════ */}
      <div className="hidden lg:flex flex-col space-y-6">
        {/* Activité Récente */}
        <InstrumentPanel title="Activité Récente" icon={<Activity size={18} />} accent="cyan">
          <div className="space-y-4">
            {[
              { label: 'Nouveau KEV',     desc: 'CVE-2026-48323',               time: 'Il y a 2h',       color: 'var(--red)' },
              { label: 'Patch disponible', desc: 'CVE-2024-57757',              time: 'Il y a 5h',       color: 'var(--lime)' },
              { label: 'Scan terminé',    desc: '19 020 repos analysés',         time: 'Il y a 8h',       color: 'var(--cyan)' },
              { label: 'Analyse IA',      desc: `${decisions.length} CVE analysées`, time: "Aujourd'hui", color: 'var(--violet)' },
            ].map((e, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className="w-2 h-2 rounded-full mt-1.5 shrink-0" style={{ background: e.color }} />
                <div className="min-w-0">
                  <div className="text-body-sm font-medium t-p">{e.label}</div>
                  <div className="text-caption t-s truncate" style={{ textTransform: 'none', letterSpacing: 'normal' }}>{e.desc}</div>
                  <div className="text-caption t-m" style={{ textTransform: 'none', letterSpacing: 'normal' }}>{e.time}</div>
                </div>
              </div>
            ))}
          </div>
        </InstrumentPanel>

        {/* Résumé */}
        <InstrumentPanel title="Résumé" icon={<Target size={18} />} accent="violet">
          <div className="grid grid-cols-2 gap-3">
            <KpiTile value={decisions.length} label="Décisions" color="amber" />
            <KpiTile value={critiques} label="Critiques" color="red" />
            <KpiTile value={summary?.patches ?? '—'} label="Patchs" color="lime" />
            <KpiTile value={`${summary?.avg_exploit_days ?? 12}j`} label="Délai exploit." color="amber" />
          </div>
        </InstrumentPanel>
      </div>
    </div>
  </div>
}
