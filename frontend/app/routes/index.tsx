import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Shield, Zap, BookOpen, AlertCircle } from 'lucide-react'
import axios from 'axios'

// --- COMPOSANTS UI ---
import { Button } from '@/components/ui/button'
import { DetailsDrawer } from '@/components/DetailsDrawer'

// --- CONNECTEUR API ---
const fetchSearchResults = async (query: string) => {
  if (!query) return []
  // Simule l'appel à votre FastAPI backend:8000
  const response = await axios.get(`http://localhost:8000/api/search?q=${query}`)
  return response.data
}

export const Route = createFileRoute('/')({
  component: CyberSearchPage,
})

function CyberSearchPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedRepo, setSelectedRepo] = useState<any>(null)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  
  const { data: results, isLoading, isError } = useQuery({
    queryKey: ['search', searchTerm],
    queryFn: () => fetchSearchResults(searchTerm),
    enabled: searchTerm.length > 2,
    placeholderData: (previousData) => previousData,
  })

  const handleOpenDetails = (repo: any) => {
    setSelectedRepo(repo)
    setIsDrawerOpen(true)
  }

  return (
    <div className="min-h-screen bg-cyber-bg text-cyber-text font-sans p-8">
      {/* HEADER / NAVIGATION */}
      <header className="flex justify-between items-center mb-16 max-w-6xl mx-auto">
        <div className="flex items-center gap-3">
          <Shield className="text-cyber-accent w-8 h-8" />
          <h1 className="text-2xl font-bold tracking-tighter uppercase">CyberScan<span className="text-cyber-accent italic">Hub</span></h1>
        </div>
        <nav className="flex gap-6 text-sm uppercase tracking-widest text-gray-500">
          <a href="#" className="hover:text-cyber-accent transition-colors">Dashboard</a>
          <a href="#" className="hover:text-cyber-accent transition-colors">Alertes</a>
          <a href="#" className="hover:text-cyber-accent transition-colors">Rapports</a>
        </nav>
      </header>

      {/* HERO / SEARCH SECTION */}
      <main className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-extrabold mb-4 bg-gradient-to-r from-white to-gray-600 bg-clip-text text-transparent">
            Indexation Sémantique Souveraine
          </h2>
          <p className="text-gray-400">Explorez 10 000+ ressources cyber auditées par IA locale.</p>
        </div>

        <div className="relative group mb-16">
          <div className="absolute -inset-0.5 bg-cyber-accent opacity-20 group-focus-within:opacity-40 rounded-xl blur transition-all duration-500"></div>
          <div className="relative bg-cyber-card border border-cyber-border rounded-xl p-2 flex items-center">
            <Search className="ml-4 text-gray-500" />
            <input 
              type="text" 
              placeholder="Tapez votre recherche (ex: 'Rapports exploit Active Directory 2026')..."
              className="w-full bg-transparent border-none focus:ring-0 px-4 py-4 text-lg placeholder:text-gray-600 outline-none"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <Button className="bg-cyber-accent text-black font-bold px-8 h-12 rounded-lg hover:scale-95 transition-transform">
              ANALYSER
            </Button>
          </div>
        </div>

        {/* RÉSULTATS / FEED */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {isLoading && <div className="col-span-2 text-center text-cyber-accent animate-pulse">Calcul des vecteurs sémantiques en cours...</div>}
          
          {results?.map((res: any) => (
            <div 
              key={res.id} 
              onClick={() => handleOpenDetails(res)}
              className="bg-cyber-card border border-cyber-border p-6 rounded-xl hover:border-cyber-accent/50 transition-all cursor-pointer group"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex gap-2">
                  <span className="bg-cyber-accent/10 text-cyber-accent text-[10px] font-bold px-2 py-1 rounded border border-cyber-accent/20">SCORE: {res.score_qualite}</span>
                  <span className="bg-gray-800 text-gray-300 text-[10px] font-bold px-2 py-1 rounded">{res.type_ressource}</span>
                </div>
                <Zap className="w-4 h-4 text-gray-700 group-hover:text-cyber-accent" />
              </div>
              <h3 className="text-lg font-bold mb-2 group-hover:text-white transition-colors">{res.title}</h3>
              <p className="text-gray-500 text-sm mb-4 line-clamp-3 leading-relaxed">
                {res.description || "Aucune analyse disponible pour ce module."}
              </p>
              <div className="flex items-center gap-4 text-xs text-gray-600">
                <span className="flex items-center gap-1"><BookOpen size={12}/> {res.language}</span>
                <span className="flex items-center gap-1"><Zap size={12}/> {res.stars} stars</span>
              </div>
            </div>
          ))}

          {!isLoading && !results?.length && searchTerm.length > 0 && (
            <div className="col-span-2 text-center py-20 border-2 border-dashed border-cyber-border rounded-3xl">
              <AlertCircle className="mx-auto mb-4 text-gray-700" size={48} />
              <p className="text-gray-500">Aucune pépite cyber ne correspond à cette signature sémantique.</p>
            </div>
          )}
        </div>
      </main>

      {/* TIROIR DE DÉTAILS */}
      <DetailsDrawer 
        repo={selectedRepo} 
        isOpen={isDrawerOpen} 
        onClose={setIsDrawerOpen} 
      />

      {/* FOOTER STATS */}
      <footer className="mt-20 border-t border-cyber-border pt-8 flex justify-center gap-12 text-[10px] text-gray-700 uppercase tracking-widest">
        <div className="flex flex-col items-center">
          <span className="text-cyber-accent font-bold text-lg">12,452</span>
          <span>Dépôts Indexés</span>
        </div>
        <div className="flex flex-col items-center">
          <span className="text-white font-bold text-lg">3,109</span>
          <span>Analyses Sécurité</span>
        </div>
        <div className="flex flex-col items-center">
          <span className="text-white font-bold text-lg">0€</span>
          <span>Coût Cloud API</span>
        </div>
      </footer>
    </div>
  )
}
