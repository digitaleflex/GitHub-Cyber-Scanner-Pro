import { useState } from 'react'
import { Shield, Lock, Mail, ArrowRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export function AuthPage() {
  const [mode, setMode] = useState<'login' | 'signup'>('login')

  return (
    <div className="min-h-screen bg-cyber-bg flex items-center justify-center p-6">
      <div className="w-full max-w-[400px] space-y-8">
        {/* LOGO */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-cyber-accent/10 border border-cyber-accent/20 mb-6">
            <Shield className="text-cyber-accent w-8 h-8" />
          </div>
          <h1 className="text-3xl font-black tracking-tighter text-white uppercase">
            CyberScan<span className="text-cyber-accent italic">Hub</span>
          </h1>
          <p className="text-gray-500 text-sm mt-2 uppercase tracking-widest">Accès Sécurisé Souverain</p>
        </div>

        {/* CARD FORM */}
        <div className="bg-cyber-card border border-cyber-border p-8 rounded-2xl shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyber-accent to-transparent opacity-50"></div>
          
          <div className="space-y-6">
            <div className="space-y-2">
              <label className="text-[10px] uppercase font-bold text-gray-500 tracking-widest">Identifiant / Email</label>
              <div className="relative group">
                <Mail className="absolute left-3 top-3 w-4 h-4 text-gray-600 group-focus-within:text-cyber-accent transition-colors" />
                <input 
                  type="email" 
                  placeholder="agent@cyberhub.local"
                  className="w-full bg-cyber-bg border border-cyber-border rounded-lg py-2.5 pl-10 pr-4 text-sm text-white placeholder:text-gray-700 outline-none focus:border-cyber-accent/50 transition-all"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] uppercase font-bold text-gray-500 tracking-widest">Mot de passe</label>
              <div className="relative group">
                <Lock className="absolute left-3 top-3 w-4 h-4 text-gray-600 group-focus-within:text-cyber-accent transition-colors" />
                <input 
                  type="password" 
                  placeholder="••••••••••••"
                  className="w-full bg-cyber-bg border border-cyber-border rounded-lg py-2.5 pl-10 pr-4 text-sm text-white placeholder:text-gray-700 outline-none focus:border-cyber-accent/50 transition-all"
                />
              </div>
            </div>

            {mode === 'signup' && (
              <div className="flex items-center space-x-2">
                <input type="checkbox" id="terms" className="w-4 h-4 rounded border-cyber-border bg-cyber-bg text-cyber-accent focus:ring-cyber-accent" />
                <label htmlFor="terms" className="text-[10px] text-gray-500 leading-none cursor-pointer">
                  J'accepte la clause de <span className="text-white underline">Neutralité et Double-Usage</span>.
                </label>
              </div>
            )}

            <Button className="w-full bg-cyber-accent text-black font-black py-6 rounded-xl group overflow-hidden relative">
              <span className="relative z-10 flex items-center justify-center gap-2 uppercase tracking-tighter">
                {mode === 'login' ? 'Initialiser la Session' : 'Créer un Compte Agent'}
                <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
              </span>
            </Button>
          </div>
        </div>

        {/* SWITCH MODE */}
        <div className="text-center">
          <button 
            onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}
            className="text-xs text-gray-500 hover:text-cyber-accent transition-colors uppercase tracking-widest"
          >
            {mode === 'login' ? "Pas encore de compte ? S'enregistrer" : "Déjà un compte ? Se connecter"}
          </button>
        </div>
      </div>
    </div>
  )
}
