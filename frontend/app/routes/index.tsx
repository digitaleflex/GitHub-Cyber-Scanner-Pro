import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Shield, Zap, BookOpen, AlertCircle, LayoutDashboard, Search as SearchIcon } from 'lucide-react'
import axios from 'axios'

// --- COMPOSANTS UI ---
import { Button } from '@/components/ui/button'
import { DetailsDrawer } from '@/components/DetailsDrawer'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DashboardView } from '@/components/DashboardView'

// --- CONNECTEUR API ---
const fetchSearchResults = async (query: string) => {
  if (!query) return []
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
  
  const { data: results, isLoading } = useQuery({
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
      <header className="flex justify-between items-center mb-12 max-w-6xl mx-auto">
        <div className="flex items-center gap-3">
          <Shield className="text-cyber-accent w-8 h-8" />
          <h1 className="text-2xl font-bold tracking-tighter uppercase">CyberScan<span className="text-cyber-accent italic">Hub</span></h1>
        </div>
        <div className="hidden md:flex gap-4 p-1 bg-cyber-card border border-cyber-border rounded-lg">
          <span className="text-[10px] text-gray-500 uppercase px-3 py-1 font-bold">V1.0 ALPHA</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto">
        <Tabs defaultValue="search" className="w-full">
          <div className="flex justify-center mb-12">
            <TabsList className="grid w-[400px] grid-cols-2">
              <TabsTrigger value="search" className="flex items-center gap-2">
                <SearchIcon size={16} /> RECHERCHE
              </TabsTrigger>
              <TabsTrigger value="dashboard" className="flex items-center gap-2">
                <LayoutDashboard size={16} /> SOC VISION
              </TabsTrigger>
            </TabsList>
          </div>

          {/* VUE RECHERCHE */}
          <TabsContent value="search" className="space-y-12">
            <div className="text-center">
              <h2 className="text-4xl font-extrabold mb-4 bg-gradient-to-r from-white to-gray-600 bg-clip-text text-transparent">
                Indexation Sémantique Souveraine
              </h2>
              <p className="text-gray-400">Explorez 10 000+ ressources cyber auditées par IA locale.</p>
            </div>

            <div className="max-w-4xl mx-auto relative group">
              <div className="absolute -inset-0.5 bg-cyber-accent opacity-20 group-focus-within:opacity-40 rounded-xl blur transition-all duration-500"></div>
              <div className="relative bg-cyber-card border border-cyber-border rounded-xl p-2 flex items-center">
                <Search className="ml-4 text-gray-500" />
                <input 
                  type="text" 
                  placeholder="Recherche en langage naturel..."
                  className="w-full bg-transparent border-none focus:ring-0 px-4 py-4 text-lg placeholder:text-gray-600 outline-none"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                <Button className="bg-cyber-accent text-black font-bold px-8 h-12 rounded-lg hover:scale-95 transition-transform">
                  ANALYSER
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {isLoading && <div className="col-span-full text-center text-cyber-accent animate-pulse py-12 uppercase tracking-widest text-xs">Alignement des vecteurs...</div>}
              
              {results?.map((res: any) => (
                <div 
                  key={res.id} 
                  onClick={() => handleOpenDetails(res)}
                  className="bg-cyber-card border border-cyber-border p-6 rounded-xl hover:border-cyber-accent/50 transition-all cursor-pointer group"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex gap-2">
                      <span className="bg-cyber-accent/10 text-cyber-accent text-[10px] font-bold px-2 py-1 rounded border border-cyber-accent/20">SCORE: {res.score_qualite}</span>
                    </div>
                    <Zap className="w-4 h-4 text-gray-700 group-hover:text-cyber-accent" />
                  </div>
                  <h3 className="text-md font-bold mb-2 group-hover:text-white transition-colors line-clamp-1">{res.title}</h3>
                  <p className="text-gray-500 text-xs mb-4 line-clamp-3 leading-relaxed">
                    {res.description || "Analyse sémantique en attente."}
                  </p>
                  <div className="flex items-center gap-4 text-[10px] text-gray-600 uppercase font-bold">
                    <span>{res.language}</span>
                    <span>{res.stars} stars</span>
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>

          {/* VUE DASHBOARD STATISTIQUE */}
          <TabsContent value="dashboard">
            <DashboardView />
          </TabsContent>
        </Tabs>
      </main>

      <DetailsDrawer 
        repo={selectedRepo} 
        isOpen={isDrawerOpen} 
        onClose={setIsDrawerOpen} 
      />

      <footer className="mt-20 border-t border-cyber-border pt-8 flex justify-center gap-12 text-[10px] text-gray-700 uppercase tracking-widest font-bold">
        <div className="flex flex-col items-center">
          <span className="text-cyber-accent text-lg">12,452</span>
          <span>Dépôts</span>
        </div>
        <div className="flex flex-col items-center text-red-500">
          <span className="text-lg">3,109</span>
          <span>Menaces</span>
        </div>
        <div className="flex flex-col items-center">
          <span className="text-white text-lg">0€</span>
          <span>Coût Cloud</span>
        </div>
      </footer>
    </div>
  )
}
