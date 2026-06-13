import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar
} from 'recharts'
import { Shield, Zap, TrendingUp, AlertCircle, FileText, Globe } from 'lucide-react'

// --- DONNÉES SIMULÉES (En attente de connexion API réelle) ---
const trendData = [
  { name: '01/06', discoveries: 120 },
  { name: '05/06', discoveries: 450 },
  { name: '10/06', discoveries: 300 },
  { name: '15/06', discoveries: 800 },
  { name: '20/06', discoveries: 600 },
  { name: '25/06', discoveries: 1100 },
  { name: '30/06', discoveries: 950 },
]

const categoryData = [
  { name: 'Offensif', value: 45, color: '#ff4d4d' },
  { name: 'Défensif', value: 30, color: '#00ff9d' },
  { name: 'Gouvernance', value: 15, color: '#4da6ff' },
  { name: 'PoC Exploit', value: 10, color: '#ffcc00' },
]

export function DashboardView() {
  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* STATS RAPIDES */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Indice de Menace', val: '8.4', color: 'text-red-500', icon: AlertCircle },
          { label: 'Scans Actifs', val: '142', color: 'text-cyber-accent', icon: Zap },
          { label: 'Rapports PDF', val: '1,024', color: 'text-white', icon: FileText },
          { label: 'Nodes OSINT', val: '12', color: 'text-blue-400', icon: Globe },
        ].map((item, i) => (
          <div key={i} className="bg-cyber-card border border-cyber-border p-5 rounded-xl">
            <div className="flex justify-between items-start mb-2 text-gray-500">
              <span className="text-[10px] uppercase font-bold tracking-widest">{item.label}</span>
              <item.icon size={14} />
            </div>
            <div className={`text-2xl font-black ${item.color}`}>{item.val}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* GRAPHIQUE DE TENDANCE (DISCOVERIES) */}
        <div className="lg:col-span-2 bg-cyber-card border border-cyber-border p-6 rounded-xl">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-white font-bold flex items-center gap-2">
              <TrendingUp size={18} className="text-cyber-accent" /> Flux de Découverte (30j)
            </h3>
            <span className="text-[10px] bg-cyber-accent/10 text-cyber-accent px-2 py-1 rounded">+24% cette semaine</span>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f1f1f" vertical={false} />
                <XAxis dataKey="name" stroke="#555" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#555" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0d0d0d', border: '1px solid #1f1f1f', borderRadius: '8px' }}
                  itemStyle={{ color: '#00ff9d', fontSize: '12px' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="discoveries" 
                  stroke="#00ff9d" 
                  strokeWidth={3} 
                  dot={{ r: 4, fill: '#00ff9d', strokeWidth: 0 }} 
                  activeDot={{ r: 6, strokeWidth: 0 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* GRAPHIQUE CAMEMBERT (RÉPARTITION) */}
        <div className="bg-cyber-card border border-cyber-border p-6 rounded-xl">
          <h3 className="text-white font-bold mb-6 flex items-center gap-2">
            <Shield size={18} className="text-cyber-accent" /> Nature des Ressources
          </h3>
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0d0d0d', border: '1px solid #1f1f1f', borderRadius: '8px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 space-y-2">
            {categoryData.map((item, i) => (
              <div key={i} className="flex justify-between items-center text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }}></div>
                  <span className="text-gray-400">{item.name}</span>
                </div>
                <span className="text-white font-mono">{item.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* TABLEAU DES TOP PÉPITES */}
      <div className="bg-cyber-card border border-cyber-border rounded-xl overflow-hidden">
        <div className="p-6 border-b border-cyber-border flex justify-between items-center">
          <h3 className="text-white font-bold">Top Pépites Sémantiques (Score > 90)</h3>
          <button className="text-xs text-cyber-accent hover:underline">Voir tout</button>
        </div>
        <table className="w-full text-left text-sm text-gray-500">
          <thead className="bg-cyber-bg text-[10px] uppercase tracking-widest border-b border-cyber-border">
            <tr>
              <th className="px-6 py-4 font-bold">Ressource</th>
              <th className="px-6 py-4 font-bold">Expertise IA</th>
              <th className="px-6 py-4 font-bold">Scan Sécurité</th>
              <th className="px-6 py-4 font-bold">Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-cyber-border">
            {[
              { name: 'AD-Hardening-Suite', type: 'Blue Team', sec: 'SAIN', score: 98 },
              { name: 'ZeroDay-Scanner-X', type: 'Offensif', sec: 'CRITIQUE', score: 94 },
              { name: 'Cloud-Leak-Detector', type: 'SaaS Security', sec: 'SAIN', score: 92 },
            ].map((row, i) => (
              <tr key={i} className="hover:bg-cyber-border/20 transition-colors cursor-pointer group">
                <td className="px-6 py-4 font-bold text-gray-300 group-hover:text-cyber-accent">{row.name}</td>
                <td className="px-6 py-4">{row.type}</td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${row.sec === 'SAIN' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                    {row.sec}
                  </span>
                </td>
                <td className="px-6 py-4 font-mono text-cyber-accent font-bold">{row.score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
