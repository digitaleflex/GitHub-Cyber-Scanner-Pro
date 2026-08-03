import { createRoute } from '@tanstack/react-router'
import { Route as RootRoute } from './__root'
import BooksTable from '../components/BooksTable'
import { BookOpen } from 'lucide-react'

export const Route = createRoute({ getParentRoute: () => RootRoute, path: '/books', component: BooksPage })

function BooksPage() {
  return (
    <div className="max-w-5xl mx-auto py-4 sm:py-8 animate-fade">
      <div className="flex items-center gap-2 mb-2">
        <BookOpen size={18} className="text-cyan-400" />
        <h1 className="text-lg font-semibold text-white">Livres & Ressources Cyber</h1>
      </div>
      <p className="text-xs sm:text-sm text-slate-400 mb-6">
        Ouvrages, cheat sheets, cours et ressources de cybersécurité indexées et vérifiées.
      </p>
      <BooksTable />
    </div>
  )
}
