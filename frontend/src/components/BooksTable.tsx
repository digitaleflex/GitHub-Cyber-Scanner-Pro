import { useState, useMemo, useEffect } from 'react'
import { useBooks, type Book } from '../lib/api'
import { PageLoader } from './CyberLoader'

const CATEGORIES = [
  { key: null, label: 'Tous' },
  { key: 'Offensive / Red Team', label: 'Red Team' },
  { key: 'Defensive / Blue Team', label: 'Blue Team' },
  { key: 'Certifications', label: 'Certifications' },
  { key: 'Cheat Sheets / Références', label: 'Références' },
  { key: 'Général / InfoSec', label: 'InfoSec' },
]

const TYPE_ACCENT: Record<string, string> = { Book: 'var(--violet)', Tool: 'var(--amber)', 'Write-up': 'var(--cyan)', Hardening: 'var(--lime)', Interview: 'var(--violet)', 'Threat-Intel': 'var(--red)', Template: 'var(--amber)' }

const CAT_ACCENT: Record<string, string> = { 'Offensive / Red Team': 'var(--red)', 'Defensive / Blue Team': 'var(--cyan)', Certifications: 'var(--amber)', 'Cheat Sheets / Références': 'var(--violet)', 'Général / InfoSec': 'var(--lime)' }

function StatusBadge({ book }: { book: Book }) {
  const lastChecked = book.last_checked ? new Date(book.last_checked + 'Z').toLocaleString('fr-FR') : 'Jamais vérifié'
  const title = `Dernier contrôle : ${lastChecked}`
  if (book.is_dead === 1) return <span title={title} className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-danger t-danger b-danger b-d">✕ Hors ligne</span>
  if (book.last_checked) return <span title={title} className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-success t-success b-success b-d">✓ Disponible</span>
  return <span title={title} className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-warn t-warn b-warn b-d">⚠ Non vérifié</span>
}

function useDebounce<T>(value: T, delay: number): T { const [debounced, setDebounced] = useState(value); useEffect(() => { const t = setTimeout(() => setDebounced(value), delay); return () => clearTimeout(t) }, [value, delay]); return debounced }

export default function BooksTable() {
  const [category, setCategory] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounce(search, 300)
  const { data: books, isLoading, error } = useBooks(debouncedSearch || undefined)
  const filtered = useMemo(() => { if (!books) return []; return category ? books.filter(b => b.category === category) : books }, [books, category])

  if (isLoading) return <PageLoader text="Chargement des ressources..." />
  if (error) return <div className="surface p-8 text-center b-d"><p className="t-danger text-sm">Erreur de chargement</p></div>

  return (
    <div className="surface rounded-xl p-5 b-d">
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <h2 className="h3 t-p">Livres & Ressources</h2>
        {books && <span className="text-[11px] t-m">{filtered.length}/{books.length}</span>}
      </div>

      <div className="flex items-center gap-2 mb-4 flex-wrap">
        {CATEGORIES.map(cat => (
          <button key={cat.key ?? 'all'} onClick={() => setCategory(cat.key)}
            className="text-[11px] px-2.5 py-1 rounded-full border transition-colors"
            style={{ background: category === cat.key ? 'var(--surface-elevated)' : 'transparent', color: category === cat.key ? 'var(--text)' : 'var(--text-muted)', borderColor: category === cat.key ? 'var(--surface-hover)' : 'var(--border-light)' }}>
            {cat.label}
          </button>
        ))}
      </div>

      <input type="text" placeholder="Rechercher par titre, catégorie..." value={search} onChange={e => setSearch(e.target.value)}
        className="w-full mb-4 px-4 py-2.5 rounded-lg text-sm focus:outline-none focus:ring-2 transition-colors"
        style={{ background: 'var(--surface-elevated)', border: '1px solid var(--border)', color: 'var(--text)' }}
        aria-label="Rechercher une ressource" />

      {filtered.length === 0 ? (
        <p className="t-m text-sm py-8 text-center">{search || category ? 'Aucun résultat' : 'Aucune donnée'}</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs" role="table">
            <thead><tr className="border-b" style={{ borderColor: 'var(--border-light)' }}>
              <th className="text-left py-2 px-2 t-m font-medium">Titre</th>
              <th className="text-center py-2 px-2 t-m font-medium w-16">Type</th>
              <th className="text-center py-2 px-2 t-m font-medium w-28">Catégorie</th>
              <th className="text-left py-2 px-2 t-m font-medium max-md:hidden">Dépôt</th>
              <th className="text-center py-2 px-2 t-m font-medium w-28">Statut</th>
              <th className="text-center py-2 px-2 t-m font-medium w-20">Lien</th>
            </tr></thead>
            <tbody>
              {filtered.map(book => (
                <tr key={book.id} className={book.is_dead === 1 ? 'opacity-50' : ''} style={{ borderBottom: '1px solid var(--border-light)' }}>
                  <td className="py-2 px-2 t-p font-medium">{book.title}</td>
                  <td className="py-2 px-2 text-center">
                    <span className="inline-block px-2 py-0.5 rounded text-[10px] font-medium border" style={{ background: 'var(--surface-elevated)', borderColor: TYPE_ACCENT[book.type_ressource] || 'var(--border)', color: TYPE_ACCENT[book.type_ressource] || 'var(--text-secondary)' }}>{book.type_ressource || 'Book'}</span>
                  </td>
                  <td className="py-2 px-2 text-center">
                    <span className="inline-block px-2 py-0.5 rounded text-[10px] font-medium border" style={{ background: 'var(--surface-elevated)', borderColor: CAT_ACCENT[book.category] || 'var(--border)', color: CAT_ACCENT[book.category] || 'var(--text-secondary)' }}>{book.category}</span>
                  </td>
                  <td className="py-2 px-2 max-md:hidden">
                    <a href={book.repo_url} target="_blank" rel="noopener noreferrer" className="t-info hover:underline">{book.repo_name}</a>
                  </td>
                  <td className="py-2 px-2 text-center"><StatusBadge book={book} /></td>
                  <td className="py-2 px-2 text-center">
                    <a href={book.url} target="_blank" rel="noopener noreferrer"
                      className="inline-block px-2.5 py-1 rounded text-[10px] font-semibold bg-ai t-ai border b-ai transition-colors hover:opacity-80">{book.is_dead === 1 ? 'Voir' : 'Ouvrir'}</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
