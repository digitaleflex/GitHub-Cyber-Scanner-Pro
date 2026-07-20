import { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchJson } from '../lib/api'

type GraphNode = {
  id: string
  label: string
  name: string
  properties: Record<string, unknown>
}

type GraphLink = {
  source: string
  target: string
  type: string
  weight: number
}

type GraphData = {
  available: boolean
  nodes: GraphNode[]
  links: GraphLink[]
}

type SimNode = GraphNode & { x: number; y: number; vx: number; vy: number }
type SimLink = { source: SimNode; target: SimNode; type: string; weight: number }

const LABEL_COLORS: Record<string, string> = {
  Hacker: '#00f0ff',
  APTCampaign: '#ff0066',
  Tool: '#00ff66',
  CVE: '#ff4400',
  Repo: '#8b5cf6',
}

const NODE_RADIUS: Record<string, number> = {
  Hacker: 8,
  APTCampaign: 14,
  Tool: 6,
  CVE: 10,
  Repo: 5,
}

function forceSimulation(nodes: SimNode[], links: SimLink[], width: number, height: number) {
  const REPULSION = 8000
  const ATTRACTION = 0.005
  const DAMPING = 0.9
  const CENTER = 0.01

  for (const n of nodes) {
    let fx = 0, fy = 0
    for (const other of nodes) {
      if (n === other) continue
      const dx = n.x - other.x
      const dy = n.y - other.y
      const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1)
      fx += (dx / dist) * REPULSION / (dist * dist)
      fy += (dy / dist) * REPULSION / (dist * dist)
    }
    fx += (width / 2 - n.x) * CENTER
    fy += (height / 2 - n.y) * CENTER
    n.vx = (n.vx + fx) * DAMPING
    n.vy = (n.vy + fy) * DAMPING
  }

  for (const l of links) {
    const dx = l.target.x - l.source.x
    const dy = l.target.y - l.source.y
    const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1)
    const force = (dist - 80) * ATTRACTION
    const fx = (dx / dist) * force
    const fy = (dy / dist) * force
    l.source.vx += fx
    l.source.vy += fy
    l.target.vx -= fx
    l.target.vy -= fy
  }

  for (const n of nodes) {
    n.x += n.vx
    n.y += n.vy
    n.x = Math.max(20, Math.min(width - 20, n.x))
    n.y = Math.max(20, Math.min(height - 20, n.y))
  }
}

export default function GraphView() {
  const [labelFilter, setLabelFilter] = useState('')
  const svgRef = useRef<SVGSVGElement>(null)
  const [simNodes, setSimNodes] = useState<SimNode[]>([])
  const [simLinks, setSimLinks] = useState<SimLink[]>([])
  const animRef = useRef<number>(0)
  const [dim, setDim] = useState({ w: 900, h: 600 })
  const [selected, setSelected] = useState<SimNode | null>(null)

  const qc = useQueryClient()

  const { data, isLoading } = useQuery<GraphData>({
    queryKey: ['graph', labelFilter],
    queryFn: () => fetchJson<GraphData>(`/graph/query?label=${labelFilter}&limit=80`),
    staleTime: 30_000,
  })

  const seedMutation = useMutation({
    mutationFn: () => fetchJson<{ message: string }>('/graph/seed'),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['graph'] }),
  })

  useEffect(() => {
    if (!data?.nodes) return
    const w = dim.w, h = dim.h
    const nodeMap = new Map<string, SimNode>()
    const nodes: SimNode[] = data.nodes.map((n) => {
      const sn: SimNode = {
        ...n,
        x: Math.random() * (w - 100) + 50,
        y: Math.random() * (h - 100) + 50,
        vx: 0, vy: 0,
      }
      nodeMap.set(n.id, sn)
      return sn
    })
    const links: SimLink[] = data.links
      .filter((l) => nodeMap.has(l.source) && nodeMap.has(l.target))
      .map((l) => ({
        source: nodeMap.get(l.source)!,
        target: nodeMap.get(l.target)!,
        type: l.type,
        weight: l.weight,
      }))
    setSimNodes(nodes)
    setSimLinks(links)
    setSelected(null)
  }, [data, dim.w, dim.h])

  const step = useCallback(() => {
    setSimNodes((prev) => {
      if (prev.length === 0) return prev
      const links = simLinks
      forceSimulation(prev, links, dim.w, dim.h)
      return [...prev]
    })
    animRef.current = requestAnimationFrame(step)
  }, [simLinks, dim])

  useEffect(() => {
    animRef.current = requestAnimationFrame(step)
    return () => cancelAnimationFrame(animRef.current)
  }, [step])

  useEffect(() => {
    const onResize = () => {
      if (svgRef.current) {
        const rect = svgRef.current.getBoundingClientRect()
        setDim({ w: rect.width, h: Math.max(400, rect.height) })
      }
    }
    onResize()
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  const labels = ['', 'Hacker', 'APTCampaign', 'Tool', 'CVE', 'Repo']

  return (
    <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan hover:neon-glow-cyan transition-all duration-300">
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider font-cyber">
          Social Graph
        </h2>
        {data && (
          <span className="text-xs text-gray-600 font-mono">
            {data.nodes.length} nœuds · {data.links.length} relations
          </span>
        )}
        <div className="flex-1" />
        <div className="flex items-center gap-2 flex-wrap">
          {labels.map((l) => (
            <button
              key={l || 'all'}
              onClick={() => setLabelFilter(l)}
              className={`text-xs px-3 py-1 rounded-full border transition-colors font-mono ${
                labelFilter === l
                  ? 'bg-white/[0.06] text-white border-white/20'
                  : 'text-gray-600 border-white/[0.06] hover:text-gray-400'
              }`}
            >
              {l || 'Tout'}
            </button>
          ))}
          <button
            onClick={() => seedMutation.mutate()}
            disabled={seedMutation.isPending}
            className="text-xs px-3 py-1 rounded-full border border-neon-cyan/20 text-neon-cyan hover:bg-neon-cyan/10 transition-colors font-mono disabled:opacity-40"
          >
            {seedMutation.isPending ? 'Seed...' : '⟳ Seed'}
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="h-96 bg-white/5 rounded animate-pulse" />
      ) : !data?.available ? (
        <div className="h-96 flex items-center justify-center">
          <p className="text-gray-600 text-sm font-mono">Neo4j non disponible</p>
        </div>
      ) : simNodes.length === 0 ? (
        <div className="h-96 flex items-center justify-center">
          <p className="text-gray-600 text-sm font-mono">Aucune donnée dans le graphe</p>
        </div>
      ) : (
        <div className="relative">
          <svg ref={svgRef} className="w-full h-[600px]" style={{ minHeight: '400px' }}>
            <defs>
              {Object.entries(LABEL_COLORS).map(([k, v]) => (
                <marker key={k} id={`arrow-${k}`} viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                  <path d="M0,0 L10,5 L0,10 Z" fill={v} fillOpacity={0.4} />
                </marker>
              ))}
            </defs>
            {simLinks.map((l, i) => (
              <line
                key={`l-${i}`}
                x1={l.source.x} y1={l.source.y}
                x2={l.target.x} y2={l.target.y}
                stroke={LABEL_COLORS[l.source.label] ?? '#ffffff'}
                strokeOpacity={0.15}
                strokeWidth={Math.min(l.weight, 3)}
                markerEnd={`url(#arrow-${l.source.label})`}
              />
            ))}
            {simNodes.map((n) => {
              const color = LABEL_COLORS[n.label] ?? '#ffffff'
              const r = NODE_RADIUS[n.label] ?? 6
              return (
                <g key={n.id} onClick={() => setSelected(n)} style={{ cursor: 'pointer' }}>
                  <circle cx={n.x} cy={n.y} r={r + 3} fill={color} fillOpacity={0.15} />
                  <circle
                    cx={n.x} cy={n.y} r={r}
                    fill={color}
                    fillOpacity={0.3}
                    stroke={selected?.id === n.id ? '#ffffff' : color}
                    strokeWidth={selected?.id === n.id ? 2 : 1}
                  />
                  <text
                    x={n.x + r + 4} y={n.y + 3}
                    fill="#9ca3af"
                    fontSize="9"
                    fontFamily="JetBrains Mono, monospace"
                  >
                    {n.name.length > 20 ? n.name.slice(0, 18) + '..' : n.name}
                  </text>
                </g>
              )
            })}
          </svg>
          {selected && (
            <div className="absolute top-2 right-2 bg-gray-900/95 border border-white/[0.1] rounded-lg p-4 max-w-xs text-xs font-mono">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: LABEL_COLORS[selected.label] ?? '#fff' }} />
                <span className="text-white font-semibold">{selected.label}</span>
              </div>
              <div className="text-gray-400 mb-1">{selected.name}</div>
              {selected.label === 'Hacker' && (
                <a href={selected.properties.profile_url as string} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-neon-cyan">
                  Voir le profil
                </a>
              )}
              {selected.label === 'CVE' && (
                <a href={`https://nvd.nist.gov/vuln/detail/${selected.name}`} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-neon-cyan">
                  Voir sur NVD
                </a>
              )}
              {selected.label === 'Repo' && (
                <a href={`https://github.com/${selected.name}`} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-neon-cyan">
                  Voir sur GitHub
                </a>
              )}
              <button onClick={() => setSelected(null)} className="mt-2 text-gray-600 hover:text-white transition-colors text-[10px]">
                Fermer
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
