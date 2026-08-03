import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight, Download } from 'lucide-react'

export type DataTableColumn<T> = {
  key: string
  label: string
  sortable?: boolean
  render?: (row: T) => React.ReactNode
  className?: string
}

type DataTableProps<T> = {
  columns: DataTableColumn<T>[]
  data: T[]
  total: number
  page: number
  perPage: number
  onPageChange: (page: number) => void
  onSort?: (key: string, direction: 'asc' | 'desc') => void
  sortKey?: string
  sortDir?: 'asc' | 'desc'
  loading?: boolean
  emptyMessage?: string
  exportCSV?: () => void
  exportLabel?: string
}

const SKELETON_ROWS = 8

export default function DataTable<T extends Record<string, any>>({
  columns, data, total, page, perPage, onPageChange, onSort, sortKey, sortDir, loading, emptyMessage, exportCSV, exportLabel,
}: DataTableProps<T>) {
  const pages = Math.max(1, Math.ceil(total / perPage))
  const handleSort = (key: string) => {
    if (!onSort) return
    if (sortKey === key) onSort(key, sortDir === 'asc' ? 'desc' : 'asc')
    else onSort(key, 'asc')
  }

  const startItem = (page - 1) * perPage + 1
  const endItem = Math.min(page * perPage, total)

  return (
    <div className="glass-card rounded-2xl overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.05]">
        <span className="text-xs text-slate-500">
          {total.toLocaleString()} resultats
          {total > 0 && <span className="ml-2 text-slate-600">{startItem}-{endItem}</span>}
        </span>
        {exportCSV && (
          <button onClick={exportCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 glass rounded-lg text-[10px] text-slate-400 hover:text-white transition">
            <Download size={11} /> {exportLabel || 'CSV'}
          </button>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/[0.05]">
              {columns.map(col => (
                <th key={col.key}
                  onClick={() => col.sortable ? handleSort(col.key) : undefined}
                  className={`px-4 py-3 text-left text-[10px] font-semibold text-slate-500 uppercase tracking-wider ${col.sortable ? 'cursor-pointer hover:text-white select-none' : ''} ${col.className || ''}`}>
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {col.sortable && sortKey === col.key && (
                      sortDir === 'asc' ? <ChevronUp size={10} className="text-indigo-400" /> : <ChevronDown size={10} className="text-indigo-400" />
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: SKELETON_ROWS }).map((_, i) => (
                <tr key={i} className="border-b border-white/[0.02] animate-pulse">
                  {columns.map(col => (
                    <td key={col.key} className="px-4 py-3">
                      <div className={`h-3 bg-slate-700/50 rounded ${i % 2 === 0 ? 'w-3/4' : 'w-1/2'}`} />
                    </td>
                  ))}
                </tr>
              ))
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-16 text-center">
                  <p className="text-slate-600 text-sm">{emptyMessage || 'Aucune donnee'}</p>
                </td>
              </tr>
            ) : (
              data.map((row, i) => (
                <tr key={i} className="border-b border-white/[0.02] hover:bg-white/[0.02] transition">
                  {columns.map(col => (
                    <td key={col.key} className={`px-4 py-3 text-xs text-slate-400 ${col.className || ''}`}>
                      {col.render ? col.render(row) : row[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-white/[0.05]">
          <span className="text-[10px] text-slate-600">Page {page} sur {pages}</span>
          <div className="flex items-center gap-1">
            <button onClick={() => onPageChange(1)} disabled={page === 1}
              className="glass p-1.5 rounded-lg text-slate-500 hover:text-white disabled:opacity-20 transition">
              <ChevronLeft size={12} /><ChevronLeft size={12} className="-ml-2" />
            </button>
            <button onClick={() => onPageChange(Math.max(1, page - 1))} disabled={page === 1}
              className="glass p-1.5 rounded-lg text-slate-500 hover:text-white disabled:opacity-20 transition">
              <ChevronLeft size={12} />
            </button>
            <span className="px-2 text-[10px] text-slate-500">{page}</span>
            <button onClick={() => onPageChange(Math.min(pages, page + 1))} disabled={page >= pages}
              className="glass p-1.5 rounded-lg text-slate-500 hover:text-white disabled:opacity-20 transition">
              <ChevronRight size={12} />
            </button>
            <button onClick={() => onPageChange(pages)} disabled={page >= pages}
              className="glass p-1.5 rounded-lg text-slate-500 hover:text-white disabled:opacity-20 transition">
              <ChevronRight size={12} /><ChevronRight size={12} className="-ml-2" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
