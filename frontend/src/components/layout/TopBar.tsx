"use client";

import React from 'react';
import { 
  Bell, 
  Search,
  Sun,
  Moon,
  Command,
  Activity,
  User,
  ExternalLink,
  Menu,
  X
} from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

export const TopBar = ({ onMenuToggleAction, isMenuOpen }: { onMenuToggleAction?: () => void, isMenuOpen?: boolean }) => {
    const { theme, toggleTheme, loadingStep, isLoading } = useAppStore();

    return (
        <div className="h-20 flex items-center justify-between px-6 sm:px-8 z-40 relative">
           {/* Progress Line */}
           <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-[var(--border)] to-transparent opacity-30" />
           {isLoading && (
               <motion.div 
                 className="absolute bottom-0 left-0 h-[1px] bg-[var(--accent)] z-50"
                 initial={{ width: "0%" }}
                 animate={{ width: "100%" }}
                 transition={{ duration: 2, repeat: Infinity }}
               />
           )}

           {/* Left: Menu & Search */}
           <div className="flex items-center space-x-6 flex-1">
               {/* Mobile Toggle */}
               <button 
                  onClick={onMenuToggleAction}
                  className="lg:hidden w-10 h-10 flex items-center justify-center glass bg-surface/40 rounded-xl text-text-secondary hover:text-[var(--accent)] transition-all"
               >
                  {isMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
               </button>

               <div className="relative group max-w-sm w-full hidden sm:block">
                   <div className="absolute inset-0 bg-[var(--accent)]/5 rounded-xl blur-md opacity-0 group-focus-within:opacity-100 transition-opacity" />
                   <div className="relative flex items-center">
                       <Search className="w-4 h-4 absolute left-4 text-text-secondary group-focus-within:text-[var(--accent)] transition-colors" />
                       <input 
                           placeholder="Search..."
                           className="w-full pl-11 pr-12 py-2.5 bg-surface/30 border border-border/10 rounded-xl text-[11px] font-bold outline-none focus:border-[var(--accent)]/30 transition-all placeholder:text-text-secondary/50"
                       />
                       <div className="absolute right-3 flex items-center space-x-1 px-1.5 py-0.5 bg-background/50 border border-border/20 rounded-md text-[8px] font-black text-text-secondary">
                            <Command className="w-2.5 h-2.5" />
                            <span>K</span>
                       </div>
                   </div>
               </div>

               {isLoading && (
                   <div className="hidden lg:flex items-center space-x-3 px-4 py-2 bg-[var(--accent)]/5 border border-[var(--accent)]/10 rounded-xl">
                       <Activity className="w-3.5 h-3.5 text-[var(--accent)] animate-pulse" />
                       <span className="text-[9px] font-black uppercase tracking-[2px] text-[var(--accent)]">{loadingStep || 'Synchronizing'}</span>
                   </div>
               )}
           </div>
           
           {/* Right: Actions */}
           <div className="flex items-center space-x-4">
               <div className="flex items-center space-x-2 bg-surface/30 p-1.5 rounded-xl border border-border/10">
                   <button 
                      onClick={toggleTheme}
                      className="p-2 hover:bg-surface rounded-lg text-text-secondary hover:text-[var(--accent)] transition-all"
                   >
                       {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                   </button>
                   <div className="w-[1px] h-4 bg-border/20" />
                   <button className="p-2 hover:bg-surface rounded-lg text-text-secondary hover:text-[var(--accent)] transition-all relative">
                       <Bell className="w-4 h-4" />
                       <div className="absolute top-2 right-2 w-1.5 h-1.5 bg-[var(--accent)] rounded-full border border-background shadow-[0_0_8px_var(--accent)]" />
                   </button>
               </div>

               <div className="w-[1px] h-8 bg-border/10 mx-2 hidden sm:block" />

               <div className="hidden sm:flex items-center space-x-4 pl-2">
                    <button className="flex items-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-[var(--accent)] to-[#D946EF] rounded-xl text-[9px] font-black text-white shadow-lg shadow-[var(--accent)]/20 hover:shadow-[var(--accent)]/40 hover:scale-[1.02] transition-all">
                        <ExternalLink className="w-3 h-3" />
                        <span className="uppercase tracking-[1px]">Deploy</span>
                    </button>
               </div>
           </div>
        </div>
    );
};


