interface Props {
  value: string | number
  label: string
  color?: 'amber' | 'cyan' | 'violet' | 'red' | 'lime' | 'muted' | 'text'
}

export function KpiTile({ value, label, color = 'text' }: Props) {
  const colorMap: Record<string, string> = {
    text: 'var(--text)',
    amber: 'var(--amber)',
    cyan: 'var(--cyan)',
    violet: 'var(--violet)',
    red: 'var(--red)',
    lime: 'var(--lime)',
    muted: 'var(--text-muted)',
  }

  return (
    <div
      className="rounded-xl p-4 text-center transition-all hover:-translate-y-0.5"
      style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
    >
      <div className="font-display text-display" style={{ color: colorMap[color] }}>{value}</div>
      <div className="text-caption t-m mt-1">{label}</div>
    </div>
  )
}
