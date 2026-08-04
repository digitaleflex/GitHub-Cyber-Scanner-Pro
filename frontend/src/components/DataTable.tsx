import { memo } from 'react'
import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight, Download } from 'lucide-react'
import EmptyState from './EmptyState'
import ErrorState from './ErrorState'

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
  error?: string | null
  onRetry?: () => void
  exportCSV?: () => void
  exportLabel?: string
}

const SKELETON_ROWS = 8

function DataTableInner<T extends Record<string, any>>({
  columns, data, total, page, perPage, onPageChange, onSort, sortKey, sortDir, loading, emptyMessage, error, onRetry, exportCSV, exportLabel,
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
    <div className="surface rounded-2xl overflow-hidden" style={{ border: '1px solid var(--border)' }}>
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: '1px solid var(--border)' }}>
        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
          {total.toLocaleString()} résultats
          {total > 0 && <span className="ml-2">{startItem}-{endItem}</span>}
        </span>
        {exportCSV && (
          <button onClick={exportCSV}
            className="btn-ghost text-xs">
            <Download size={11} /> {exportLabel || 'CSV'}
          </button>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)' }}>
              {columns.map(col => (
                <th key={col.key}
                  onClick={() => col.sortable ? handleSort(col.key) : undefined}
                  className={`px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-wider ${col.sortable ? 'cursor-pointer select-none' : ''} ${col.className || ''}`}
                  style={{ color: 'var(--text-muted)' }}>
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {col.sortable && sortKey === col.key && (
                      sortDir === 'asc'
                        ? <ChevronUp size={10} style={{ color: 'var(--info)' }} />
                        : <ChevronDown size={10} style={{ color: 'var(--info)' }} />
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: SKELETON_ROWS }).map((_, i) => (
                <tr key={i} className="animate-pulse" style={{ borderBottom: '1px solid var(--border-light)' }}>
                  {columns.map(col => (
                    <td key={col.key} className="px-4 py-3">
                      <div className="h-3 rounded" style={{ background: 'var(--border)', width: i % 2 === 0 ? '75%' : '50%' }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : error ? (
              <tr>
                <td colSpan={columns.length} className="px-4">
                  <ErrorState compact description={error} onRetry={onRetry} />
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4">
                  <EmptyState compact title={emptyMessage || 'Aucune donnée'} />
                </td>
              </tr>
            ) : (
              data.map((row, i) => (
                <tr key={i} className="transition-colors" style={{ borderBottom: '1px solid var(--border-light)' }}>
                  {columns.map(col => (
                    <td key={col.key} className={`px-4 py-3 text-xs ${col.className || ''}`}
                      style={{ color: 'var(--text-secondary)' }}>
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
        <div className="flex items-center justify-between px-4 py-3" style={{ borderTop: '1px solid var(--border)' }}>
          <span className="text-[10px]" style={{ color: 'var(--text-muted)' }}>Page {page} sur {pages}</span>
          <div className="flex items-center gap-1">
            <button onClick={() => onPageChange(1)} disabled={page === 1} aria-label="Première page"
              className="p-1.5 rounded-lg disabled:opacity-20 transition-all" style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}>
              <ChevronLeft size={12} /><ChevronLeft size={12} className="-ml-2" />
            </button>
            <button onClick={() => onPageChange(Math.max(1, page - 1))} disabled={page === 1} aria-label="Page précédente"
              className="p-1.5 rounded-lg disabled:opacity-20 transition-all" style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}>
              <ChevronLeft size={12} />
            </button>
            <span className="px-2 text-[10px]" style={{ color: 'var(--text-muted)' }} aria-current="page">{page}</span>
            <button onClick={() => onPageChange(Math.min(pages, page + 1))} disabled={page >= pages} aria-label="Page suivante"
              className="p-1.5 rounded-lg disabled:opacity-20 transition-all" style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}>
              <ChevronRight size={12} />
            </button>
            <button onClick={() => onPageChange(pages)} disabled={page >= pages} aria-label="Dernière page"
              className="p-1.5 rounded-lg disabled:opacity-20 transition-all" style={{ background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}>
              <ChevronRight size={12} /><ChevronRight size={12} className="-ml-2" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

const DataTable = memo(DataTableInner) as typeof DataTableInner
export default DataTable
