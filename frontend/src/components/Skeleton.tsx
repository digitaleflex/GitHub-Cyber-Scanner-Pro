const base = "bg-slate-700/50 rounded animate-pulse"

export function SkeletonCard() {
  return (
    <div className="glass-card rounded-2xl p-5 space-y-3">
      <div className={`${base} h-4 w-2/3`} />
      <div className={`${base} h-3 w-full`} />
      <div className={`${base} h-3 w-4/5`} />
      <div className="flex gap-2 mt-3">
        <div className={`${base} h-6 w-16 rounded-full`} />
        <div className={`${base} h-6 w-20 rounded-full`} />
      </div>
    </div>
  )
}

export function SkeletonTable({ rows = 8, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="glass-card rounded-2xl overflow-hidden">
      <div className="px-4 py-3 border-b border-white/[0.05]">
        <div className={`${base} h-3 w-32`} />
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex px-4 py-3 border-b border-white/[0.02] gap-4">
          {Array.from({ length: cols }).map((_, c) => (
            <div key={c} className={`${base} h-3 flex-1`} style={{ maxWidth: `${Math.random() * 40 + 60}%` }} />
          ))}
        </div>
      ))}
    </div>
  )
}

export function SkeletonStats({ count = 4 }: { count?: number }) {
  return (
    <div className={`grid grid-cols-2 sm:grid-cols-${count} gap-3`}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="glass-card rounded-xl p-4 text-center space-y-2">
          <div className={`${base} h-8 w-8 mx-auto rounded-full`} />
          <div className={`${base} h-5 w-16 mx-auto`} />
          <div className={`${base} h-3 w-20 mx-auto`} />
        </div>
      ))}
    </div>
  )
}

export function SkeletonGraph() {
  return (
    <div className="glass-card rounded-2xl p-5">
      <div className={`${base} h-4 w-40 mb-4`} />
      <div className={`${base} h-64 w-full`} />
    </div>
  )
}
