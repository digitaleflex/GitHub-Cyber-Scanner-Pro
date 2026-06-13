import { 
  Sheet, 
  SheetContent, 
  SheetHeader, 
  SheetTitle, 
  SheetDescription 
} from "@/components/ui/sheet"
import { Shield, Zap, AlertTriangle, Lock, Terminal, ExternalLink } from "lucide-react"
import { Badge } from "@/components/ui/badge" // Note: On le créera juste après

interface DetailsDrawerProps {
  repo: any
  isOpen: boolean
  onClose: (open: boolean) => void
}

export function DetailsDrawer({ repo, isOpen, onClose }: DetailsDrawerProps) {
  if (!repo) return null

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent className="overflow-y-auto">
        <SheetHeader className="mb-8">
          <div className="flex items-center gap-2 text-cyber-accent mb-2">
            <Shield size={18} />
            <span className="text-xs font-bold uppercase tracking-widest">Analyse de Sécurité Certifiée</span>
          </div>
          <SheetTitle className="text-3xl tracking-tighter">{repo.title}</SheetTitle>
          <SheetDescription className="text-gray-400">
            Dépôt découvert le {new Date().toLocaleDateString()} • {repo.stars} étoiles
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-10">
          {/* SECTION 1 : SYNTHÈSE IA */}
          <section>
            <h4 className="flex items-center gap-2 text-white font-bold mb-4 uppercase text-xs tracking-wider">
              <Zap className="text-yellow-500" size={14} /> Synthèse Executive IA
            </h4>
            <div className="bg-cyber-bg border border-cyber-border p-4 rounded-lg leading-relaxed text-gray-300 text-sm">
              {repo.description || "Analyse sémantique en cours..."}
              <p className="mt-4 text-cyber-accent/80 italic">
                💡 Recommandation : Idéal pour les environnements de Red Team souhaitant automatiser l'énumération AD.
              </p>
            </div>
          </section>

          {/* SECTION 2 : VULNÉRABILITÉS (TRIVY) */}
          <section>
            <h4 className="flex items-center gap-2 text-white font-bold mb-4 uppercase text-xs tracking-wider">
              <AlertTriangle className="text-red-500" size={14} /> Rapport de Vulnérabilités (Trivy)
            </h4>
            <div className="grid grid-cols-3 gap-2 mb-4">
              <div className="bg-red-500/10 border border-red-500/20 p-3 rounded-lg text-center">
                <div className="text-red-500 font-bold text-xl">2</div>
                <div className="text-[10px] text-red-500/70 uppercase">Critiques</div>
              </div>
              <div className="bg-orange-500/10 border border-orange-500/20 p-3 rounded-lg text-center">
                <div className="text-orange-500 font-bold text-xl">5</div>
                <div className="text-[10px] text-orange-500/70 uppercase">Hautes</div>
              </div>
              <div className="bg-blue-500/10 border border-blue-500/20 p-3 rounded-lg text-center">
                <div className="text-blue-500 font-bold text-xl">12</div>
                <div className="text-[10px] text-blue-500/70 uppercase">Moyennes</div>
              </div>
            </div>
            <div className="text-xs text-gray-500 italic">
              Dernière exécution du scan : il y a 2 heures dans une micro-VM gVisor.
            </div>
          </section>

          {/* SECTION 3 : SECRETS DÉTECTÉS (GITLEAKS) */}
          <section>
            <h4 className="flex items-center gap-2 text-white font-bold mb-4 uppercase text-xs tracking-wider">
              <Lock className="text-cyber-accent" size={14} /> Fuites de Secrets (Gitleaks)
            </h4>
            <div className="border border-cyber-border rounded-lg overflow-hidden">
              <div className="bg-cyber-border/50 p-3 text-[10px] font-mono text-gray-400 flex justify-between">
                <span>FICHIER</span>
                <span>TYPE</span>
              </div>
              <div className="p-3 text-sm font-mono text-gray-500 flex justify-between border-t border-cyber-border">
                <span className="text-gray-300">config/settings.yaml</span>
                <span className="text-red-400 text-[10px] border border-red-400/30 px-1 rounded">AWS_KEY</span>
              </div>
              <div className="p-3 text-sm font-mono text-gray-500 flex justify-between border-t border-cyber-border">
                <span className="text-gray-300">.env.example</span>
                <span className="text-red-400 text-[10px] border border-red-400/30 px-1 rounded">DB_PASS</span>
              </div>
            </div>
          </section>

          {/* SECTION 4 : ACTIONS */}
          <section className="pt-6 border-t border-cyber-border flex gap-4">
            <a 
              href={repo.url} 
              target="_blank" 
              className="flex-1 bg-cyber-accent text-black font-bold py-3 rounded-lg text-center text-sm flex items-center justify-center gap-2 hover:bg-cyber-accent/80 transition-colors"
            >
              VOIR SUR GITHUB <ExternalLink size={14} />
            </a>
            <button className="flex-1 border border-cyber-border text-white font-bold py-3 rounded-lg text-sm hover:bg-cyber-card transition-colors">
              GÉNÉRER PDF
            </button>
          </section>
        </div>
      </SheetContent>
    </Sheet>
  )
}
