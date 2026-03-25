import React, { useEffect } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { ChatArea } from './components/layout/ChatArea';
import { ChatInput } from './components/layout/ChatInput';
import { ThemeToggle } from './components/ui/ThemeToggle';
import { useAppStore } from './store/useAppStore';
import { AnimatePresence, motion } from 'framer-motion';
import { Bell, Search, User, SlidersHorizontal, Settings } from 'lucide-react';

function App() {
  const { theme, setTheme } = useAppStore();

  useEffect(() => {
    // Initial theme set
    const savedTheme = localStorage.getItem('theme') as 'dark' | 'light' || 'dark';
    setTheme(savedTheme);
  }, []);

  return (
    <div className={`flex h-screen w-screen overflow-hidden font-inter transition-colors duration-300 ${theme === 'dark' ? 'dark bg-[#0B0F17]' : 'bg-[#F9FAFB]'}`}>
      
      {/* Sidebar */}
      <Sidebar />

      {/* Main Container */}
      <main className="flex-1 flex flex-col h-full bg-background-primary relative">
        
        {/* Top Navbar */}
        <header className="h-16 px-8 flex items-center justify-between border-b border-border/40 bg-background-primary/80 backdrop-blur-xl sticky top-0 z-40">
           <div className="flex items-center space-x-6">
              <div className="relative group max-w-md">
                 <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary group-focus-within:text-accent transition-colors" />
                 <input 
                   placeholder="Search past queries / insights..." 
                   className="pl-10 pr-4 py-2 bg-surface/40 hover:bg-surface/60 border border-border/20 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-accent/10 focus:border-accent/40 transition-all w-64 md:w-80"
                 />
              </div>
           </div>

           <div className="flex items-center space-x-4">
              <div className="flex bg-surface/40 border border-border/20 p-1 rounded-xl">
                 <button className="p-1.5 hover:bg-background-secondary rounded-lg transition-all text-text-secondary hover:text-accent">
                    <SlidersHorizontal className="w-4 h-4" />
                 </button>
                 <div className="w-[1px] h-3 bg-border/40 self-center" />
                 <button className="p-1.5 hover:bg-background-secondary rounded-lg transition-all text-text-secondary hover:text-accent">
                    <Bell className="w-4 h-4" />
                 </button>
              </div>
              
              <ThemeToggle />

              <div className="h-8 w-[1px] bg-border/40 mx-2" />

              <button className="flex items-center space-x-3 pl-2 pr-1 py-1 bg-surface/20 border border-border/20 rounded-xl hover:bg-surface/40 transition-all group active:scale-95">
                 <div className="flex flex-col items-end mr-1">
                    <span className="text-xs font-black uppercase text-text-primary group-hover:text-accent transition-colors">Archie Architect</span>
                    <span className="text-[10px] font-bold text-text-secondary uppercase tracking-widest leading-none">Senior Admin</span>
                 </div>
                 <div className="w-9 h-9 rounded-xl bg-accent-gradient flex items-center justify-center p-0.5 shadow-lg shadow-accent/20">
                    <div className="w-full h-full bg-background-secondary rounded-lg flex items-center justify-center overflow-hidden">
                       <User className="w-5 h-5 text-accent" />
                    </div>
                 </div>
              </button>
           </div>
        </header>

        {/* Chat Interface Area */}
        <ChatArea>
           <ChatInput />
        </ChatArea>

        {/* Background Gradients */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-accent/5 rounded-full blur-[120px] -mr-64 -mt-64 pointer-events-none opacity-40" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-accent/5 rounded-full blur-[100px] -ml-48 -mb-48 pointer-events-none opacity-40" />
      </main>
    </div>
  );
}

export default App;
