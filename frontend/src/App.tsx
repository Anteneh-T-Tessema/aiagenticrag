import React, { useState, useEffect, useRef } from 'react';
import { Gavel, Search, ShieldCheck, AlertTriangle, PenTool, LayoutDashboard, History, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

type SwarmEvent = {
  orchestrator?: any;
  retriever?: any;
  verifier?: any;
  synthesizer?: any;
};

// Utility for cleaner class management
const cn = (...classes: any[]) => classes.filter(Boolean).join(' ');

export default function App() {
  const [query, setQuery] = useState("");
  const [events, setEvents] = useState<SwarmEvent[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query) return;

    setEvents([]);
    setIsSearching(true);
    setActiveAgent('orchestrator');

    try {
      // Changed to 127.0.0.1 to avoid localhost resolution issues
      const response = await fetch('http://127.0.0.1:8888/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error("No reader");

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const eventData = JSON.parse(line.slice(6));
              setEvents(prev => [...prev, eventData]);
              const agentName = Object.keys(eventData)[0];
              if (agentName) setActiveAgent(agentName);
            } catch (e) {
              console.error("Error parsing SSE data", e);
            }
          }
        }
      }
    } catch (err) {
      console.error("Swarm connection failed", err);
      alert("Swarm connection failed. Is the backend running on port 8888?");
    } finally {
      setIsSearching(false);
      setActiveAgent(null);
    }
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 flex flex-col font-sans">
      {/* Header */}
      <header className="h-16 border-b border-slate-800 bg-slate-900/50 backdrop-blur-xl flex items-center px-6 justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-amber-600 rounded-lg flex items-center justify-center shadow-lg shadow-amber-500/20">
            <Gavel className="text-slate-900" size={24} />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">LexiSwarm <span className="text-amber-500">Discovery</span></h1>
            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Autonomous Legal Intelligence</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
            <span className="text-[10px] font-bold text-emerald-500 uppercase">Swarm Online</span>
          </div>
        </div>
      </header>

      <main className="flex-1 flex gap-6 p-6 overflow-hidden max-w-[1600px] mx-auto w-full">
        {/* Left Col: Activity */}
        <div className="flex-[1.2] flex flex-col gap-6 overflow-hidden">
          <div className="flex justify-between items-center p-4 bg-slate-900/50 border border-slate-800 rounded-xl">
            {[
              { id: 'orchestrator', icon: LayoutDashboard, label: 'Orchestrate' },
              { id: 'retriever', icon: Search, label: 'Retrieve' },
              { id: 'verifier', icon: ShieldCheck, label: 'Verify' },
              { id: 'synthesizer', icon: PenTool, label: 'Synthesize' }
            ].map((agent) => (
              <div key={agent.id} className={cn("flex flex-col items-center gap-1 transition-all", activeAgent === agent.id ? "text-amber-400 scale-110" : "text-slate-500 opacity-50")}>
                <agent.icon size={20} />
                <span className="text-[8px] font-bold uppercase tracking-tighter">{agent.label}</span>
              </div>
            ))}
          </div>

          <div className="flex-1 bg-slate-900/50 border border-slate-800 rounded-xl p-4 flex flex-col overflow-hidden shadow-inner">
            <div className="flex items-center gap-2 mb-4 text-slate-400 border-b border-slate-800 pb-2">
              <History size={14} />
              <h2 className="text-[10px] font-bold uppercase tracking-widest">Discovery Log</h2>
            </div>
            
            <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 pr-2 custom-scrollbar">
              <AnimatePresence>
                {events.map((event, idx) => (
                  <motion.div key={idx} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
                    {Object.entries(event).map(([agent, data]: [string, any]) => (
                      <div key={agent} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className={cn(
                            "px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider",
                            agent === 'verifier' && data.deficiencies?.length ? "bg-amber-500/10 text-amber-500 border border-amber-500/20" :
                            agent === 'verifier' ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20" :
                            "bg-slate-800 text-slate-400"
                          )}>
                            {agent}
                          </span>
                        </div>
                        <div className="text-xs text-slate-400 font-mono leading-relaxed bg-black/30 p-2 rounded border border-white/5">
                          {data.plan ? data.plan[0] : 
                           data.deficiencies ? data.deficiencies[0] :
                           data.final_response ? "Final Verified Memo Synthesized." :
                           "Action in progress..."}
                        </div>
                      </div>
                    ))}
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* Right Col: Input & Output */}
        <div className="flex-[2] flex flex-col gap-6 overflow-hidden">
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl shadow-2xl">
            <form onSubmit={handleSubmit} className="relative">
              <input 
                type="text" 
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Submit complex legal query..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl py-4 pl-12 pr-4 text-white focus:outline-none focus:ring-2 focus:ring-amber-500/50 transition-all placeholder:text-slate-600"
              />
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={20} />
              <button 
                type="submit"
                disabled={isSearching}
                className="absolute right-2 top-1/2 -translate-y-1/2 bg-amber-500 hover:bg-amber-600 text-slate-900 px-8 py-2 rounded-lg font-bold transition-all disabled:opacity-50 flex items-center gap-2"
              >
                {isSearching ? <div className="w-4 h-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" /> : "DISCOVER"}
              </button>
            </form>
          </div>

          <div className="flex-1 bg-white/[0.02] border border-slate-800 p-10 rounded-xl overflow-y-auto relative group">
            <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
               <ShieldCheck className="text-emerald-500" size={24} />
            </div>
            
            {events.find(e => e.synthesizer)?.synthesizer?.final_response ? (
              <div className="max-w-3xl mx-auto">
                <div className="mb-10 text-center border-b border-slate-800 pb-10">
                   <h2 className="text-3xl font-serif font-bold text-white mb-2">Verified Discovery Memo</h2>
                   <p className="text-xs text-slate-500 uppercase tracking-widest font-bold">LexiSwarm Autonomous Audit Report</p>
                </div>
                <div className="text-slate-300 leading-relaxed text-lg font-serif whitespace-pre-wrap">
                  {events.find(e => e.synthesizer)?.synthesizer?.final_response}
                </div>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center opacity-10 py-20 text-center">
                 <Gavel size={80} className="mb-6" />
                 <p className="text-2xl font-serif italic">Swarm standing by for discovery instructions...</p>
              </div>
            )}
          </div>
        </div>
      </main>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
      `}</style>
    </div>
  );
}
