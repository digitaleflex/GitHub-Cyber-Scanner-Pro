import { useState, useMemo, useEffect } from 'react'
import { useBooks, type Book } from '../lib/api'

const CATEGORIES = [
  { key: null, label: 'Tous' },
  { key: 'Offensive / Red Team', label: 'Offensive / Red Team' },
  { key: 'Defensive / Blue Team', label: 'Defensive / Blue Team' },
  { key: 'Certifications', label: 'Certifications' },
  { key: 'Cheat Sheets / Références', label: 'Cheat Sheets / Références' },
  { key: 'Général / InfoSec', label: 'Général / InfoSec' },
]

const TYPE_CLASSES: Record<string, string> = {
  Book: 'bg-neon-cyan/10 text-neon-cyan border-neon-cyan/20',
  Tool: 'bg-neon-amber/10 text-neon-amber border-neon-amber/20',
  'Write-up': 'bg-neon-green/10 text-neon-green border-neon-green/20',
  Hardening: 'bg-neon-cyan/10 text-neon-cyan border-neon-cyan/20',
  Interview: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
  'Threat-Intel': 'bg-neon-red/10 text-neon-red border-neon-red/20',
  Template: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
}

function StatusBadge({ book }: { book: Book }) {
  const lastChecked = book.last_checked
    ? new Date(book.last_checked + 'Z').toLocaleString('fr-FR')
    : 'Jamais vérifié'
  const title = `Dernier contrôle : ${lastChecked}`

  if (book.is_dead === 1) {
    return (
      <span title={title} className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-neon-red/10 text-neon-red border border-neon-red/20">
        <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
        Hors ligne
      </span>
    )
  }
  if (book.last_checked) {
    return (
      <span title={title} className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-neon-green/10 text-neon-green border border-neon-green/20">
        <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>
        Disponible
      </span>
    )
  }
  return (
    <span title={title} className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold bg-neon-amber/10 text-neon-amber border border-neon-amber/20">
      <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      Non vérifié
    </span>
  )
}

const CAT_BG_CLASSES: Record<string, string> = {
  'Offensive / Red Team': 'bg-red-500/10 text-red-400 border-red-500/20',
  'Defensive / Blue Team': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  Certifications: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  'Cheat Sheets / Références': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  'Général / InfoSec': 'bg-violet-500/10 text-violet-400 border-violet-500/20',
}

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

export default function BooksTable() {
  const [category, setCategory] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounce(search, 300)

  const { data: books, isLoading, error } = useBooks(debouncedSearch || undefined)

  const filtered = useMemo(() => {
    if (!books) return []
    if (category) {
      return books.filter((b) => b.category === category)
    }
    return books
  }, [books, category])

  return (
    <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 neon-border-cyan hover:neon-glow-cyan transition-all duration-300">
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <h2 className="text-neon-cyan text-sm font-semibold uppercase tracking-wider font-cyber">
          Livres & Ressources
        </h2>
        {books && (
          <span className="text-xs text-gray-600 font-mono">
            {filtered.length}/{books.length}
          </span>
        )}
      </div>

      <div className="flex items-center gap-2 mb-4 flex-wrap">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.key ?? 'all'}
            onClick={() => setCategory(cat.key)}
            className={`text-xs px-3 py-1 rounded-full border transition-colors font-mono ${
              category === cat.key
                ? 'bg-white/[0.06] text-white border-white/20'
                : 'text-gray-600 border-white/[0.06] hover:text-gray-400'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      <input
        type="text"
        placeholder="Rechercher par titre, catégorie, dépôt..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full mb-4 px-4 py-2.5 bg-white/[0.05] border border-white/[0.1] rounded-lg text-white text-sm placeholder-gray-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan/50 transition-colors font-mono"
        aria-label="Rechercher une ressource"
      />

      {isLoading ? (
        <div className="space-y-3" role="status">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-10 bg-white/5 rounded animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <p className="text-neon-red text-sm py-4 text-center font-mono">Erreur de chargement</p>
      ) : filtered.length === 0 ? (
        <p className="text-gray-600 text-sm py-8 text-center font-mono">
          {search || category ? 'Aucun résultat' : 'Aucune donnée disponible'}
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm" role="table">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <th className="text-left py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider">Titre</th>
                <th className="text-center py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider w-20">Type</th>
                <th className="text-center py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider w-44">Catégorie</th>
                <th className="text-left py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider max-md:hidden">Dépôt</th>
                <th className="text-center py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider w-28">Disponibilité</th>
                <th className="text-center py-3 px-2 text-gray-500 font-medium font-mono text-xs uppercase tracking-wider w-24">Lien</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((book) => (
                <tr
                  key={book.id}
                  className={`border-b border-white/[0.03] hover:bg-white/[0.03] transition-colors ${
                    book.is_dead === 1 ? 'opacity-55' : ''
                  }`}
                >
                  <td className="py-2.5 px-2 font-medium text-white/80">{book.title}</td>
                  <td className="py-2.5 px-2 text-center">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium border font-mono ${TYPE_CLASSES[book.type_ressource] ?? 'bg-gray-500/10 text-gray-400 border-gray-500/20'}`}>
                      {book.type_ressource || 'Book'}
                    </span>
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium border font-mono ${CAT_BG_CLASSES[book.category] ?? 'bg-gray-500/10 text-gray-400 border-gray-500/20'}`}>
                      {book.category}
                    </span>
                  </td>
                  <td className="py-2.5 px-2 max-md:hidden">
                    <a
                      href={book.repo_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-400 hover:text-neon-cyan transition-colors text-sm"
                    >
                      {book.repo_name}
                    </a>
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    <StatusBadge book={book} />
                  </td>
                  <td className="py-2.5 px-2 text-center">
                    <a
                      href={book.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block px-3 py-1 rounded text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 hover:bg-indigo-500/20 transition-colors"
                    >
                      {book.is_dead === 1 ? 'Accéder' : 'Ouvrir'}
                    </a>
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
