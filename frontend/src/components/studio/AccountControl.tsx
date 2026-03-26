"use client";

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  User, 
  Settings, 
  HelpCircle, 
  LogOut, 
  Plus, 
  ChevronRight, 
  Star, 
  UserPlus, 
  Key,
  Database,
  Shield,
  Palette
} from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { cn } from '@/lib/utils';

export function AccountControl() {
  const [isOpen, setIsOpen] = useState(false);
  const { user } = useAppStore();

  return (
    <div className="relative">
      {/* Profile Icon Trigger */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-10 h-10 rounded-full border-2 border-indigo-500/20 p-0.5 hover:border-indigo-500/60 transition-all duration-500 hover:scale-105 active:scale-95 group relative group"
      >
        <div className="absolute inset-0 bg-indigo-500 blur-md opacity-20 group-hover:opacity-40 animate-pulse transition-opacity" />
        <img 
          src={user.avatar} 
          alt={user.name} 
          className="w-full h-full rounded-full object-cover relative z-10"
        />
        <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 border-2 border-[var(--bg-primary)] rounded-full z-20 group-hover:scale-125 transition-transform" />
      </button>

      {/* Profile Dropdown / Modal Overlay */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop for closing */}
            <motion.div 
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               exit={{ opacity: 0 }}
               onClick={() => setIsOpen(false)}
               className="fixed inset-0 z-[100] cursor-default pointer-events-auto"
            />

            {/* Account Modal */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: -20, x: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0, x: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20, x: 20 }}
              className="absolute top-12 right-0 w-[400px] glass-card border-[1px] border-[var(--border)] overflow-hidden z-[110] shadow-2xl shadow-indigo-500/20"
            >
              <div className="p-6 text-center space-y-4">
                 <p className="text-sm font-bold text-[var(--text-secondary)] tracking-tight">{user.email}</p>
                 <div className="relative inline-block group">
                    <div className="absolute -inset-4 bg-indigo-500/10 rounded-full blur-2xl group-hover:bg-indigo-500/20 transition-all" />
                    <img 
                      src={user.avatar} 
                      alt={user.name} 
                      className="w-24 h-24 rounded-full border-4 border-indigo-500/20 mx-auto relative z-10 hover:rotate-3 transition-transform duration-500" 
                    />
                 </div>
                 <h2 className="text-2xl font-black gradient-text">Hi, {user.name.split(' ')[0]}!</h2>
                 <button className="px-6 py-2.5 rounded-full border border-indigo-500/30 font-bold text-sm bg-indigo-500/5 hover:bg-indigo-500/10 hover:border-indigo-500/50 transition-all">
                    Manage your Account
                 </button>
              </div>

              <div className="grid grid-cols-1 gap-1 px-3 py-4 border-y border-[var(--border)]/50 bg-[var(--surface)]/30 backdrop-blur-md">
                 {[
                   { name: 'Add another account', icon: UserPlus },
                   { name: 'Upgrade current plan', icon: Star, highlight: true },
                   { name: 'Settings & Privacy', icon: Shield },
                   { name: 'Appearance & Themes', icon: Palette },
                 ].map(item => (
                   <button 
                     key={item.name}
                     className={cn(
                       "flex items-center gap-4 w-full p-4 rounded-2xl hover:bg-[var(--surface)] transition-all font-bold group",
                       item.highlight && "text-indigo-500"
                     )}
                   >
                     <item.icon size={20} className={cn("opacity-70 group-hover:opacity-100 transition-opacity", item.highlight && "opacity-100")} />
                     <span className="text-sm flex-1 text-left">{item.name}</span>
                     <ChevronRight size={14} className="opacity-30 group-hover:opacity-100 transition-all group-hover:translate-x-1" />
                   </button>
                 ))}
              </div>

              <div className="p-3 text-center bg-[var(--bg-secondary)]/80">
                 <button className="flex items-center justify-center gap-2 w-full p-4 rounded-2xl hover:bg-red-500/5 text-red-500 transition-all font-bold text-sm group">
                    <LogOut size={18} className="group-hover:-translate-x-1 transition-transform" />
                    Sign out
                 </button>
              </div>

              <div className="p-4 flex items-center justify-center gap-4 text-[10px] font-black uppercase tracking-[2px] opacity-40 border-t border-[var(--border)]/30">
                 <a href="#" className="hover:opacity-100 transition-opacity">Privacy Policy</a>
                 <div className="w-1 h-1 bg-current rounded-full" />
                 <a href="#" className="hover:opacity-100 transition-opacity">Terms of Service</a>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
