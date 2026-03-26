"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { 
  Plus, 
  MessageSquare, 
  Settings, 
  HelpCircle, 
  ChevronLeft, 
  ChevronRight,
  Sparkles,
  LayoutGrid,
  Clock
} from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { cn } from '@/lib/utils';

export function NavigationSidebar({ isOpen, toggleSidebarAction }: { isOpen: boolean; toggleSidebarAction: () => void }) {
  const { history, clearHistory, loadConversation, fetchHistory } = useAppStore();

  React.useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  return (
    <motion.div
      initial={false}
      animate={{ 
        width: isOpen ? 280 : 72,
      }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className={cn(
        "h-screen bg-[var(--surface)] flex flex-col relative z-50 overflow-hidden shrink-0 transition-colors duration-500",
        !isOpen && "items-center"
      )}
    >
      {/* Menu Header */}
      <div className={cn("p-4 flex items-center h-16 shrink-0", isOpen ? "pl-5" : "justify-center")}>
        <button 
          onClick={toggleSidebarAction}
          className="p-2 hover:bg-[var(--border)]/40 rounded-full transition-colors text-[var(--text-secondary)]"
        >
          {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
        </button>
      </div>

      {/* New Chat Button */}
      <div className={cn("px-4 py-2 shrink-0 flex justify-center", isOpen ? "w-full" : "w-auto")}>
        <button 
          onClick={clearHistory}
          className={cn(
            "flex items-center gap-3 bg-[var(--bg-primary)] hover:bg-[var(--border)]/30 transition-all text-sm group overflow-hidden border border-[var(--border)]/30 shadow-sm",
            isOpen ? "rounded-full py-2.5 px-4 w-full" : "rounded-full p-3 w-11 h-11 flex items-center justify-center"
          )}
        >
          <Plus className="min-w-[18px] text-indigo-500" />
          {isOpen && <span className="whitespace-nowrap font-medium text-[var(--text-secondary)]">New Chat</span>}
        </button>
      </div>

      {/* Scrolling Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar px-3 pt-4 space-y-6">
        <div>
          {isOpen && (
            <div className="flex items-center gap-2 px-3 mb-2 opacity-50">
              <Clock size={12} className="text-[var(--text-secondary)]" />
              <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Recent</p>
            </div>
          )}
          
          <div className="space-y-1">
            {history.map((item: { id: string; title: string }) => (
              <button
                key={item.id}
                onClick={() => loadConversation(item.id)}
                className={cn(
                  "flex items-center gap-3 w-full p-3 rounded-xl hover:bg-[var(--surface)] transition-all group text-sm text-left overflow-hidden border border-transparent hover:border-[var(--border)]/50",
                  !isOpen && "justify-center"
                )}
              >
                <MessageSquare size={18} className="min-w-[18px] text-[var(--accent)]/70 group-hover:text-[var(--accent)] transition-colors" />
                {isOpen && <span className="truncate flex-1 font-medium opacity-80 group-hover:opacity-100">{item.title}</span>}
              </button>
            ))}
          </div>
        </div>

        {/* Gems Section Placeholder */}
         <div>
          {isOpen && (
             <div className="flex items-center gap-2 px-3 mb-2 opacity-50">
               <Sparkles size={12} className="text-[var(--text-secondary)]" />
               <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">My Stuff</p>
             </div>
          )}
          <div className="space-y-1">
            <button className={cn(
              "flex items-center gap-3 w-full p-3 rounded-xl hover:bg-[var(--surface)] transition-all text-sm border border-transparent hover:border-[var(--border)]/50 group",
              !isOpen && "justify-center"
            )}>
              <LayoutGrid size={18} className="min-w-[18px] text-amber-500/70 group-hover:text-amber-500" />
              {isOpen && <span className="font-medium opacity-80 group-hover:opacity-100">Gems</span>}
            </button>
          </div>
        </div>
      </div>

      {/* Footer Items */}
      <div className="p-3 border-t border-[var(--border)]/50 space-y-1 bg-[var(--bg-secondary)]/50 backdrop-blur-sm">
        <button className={cn(
          "flex items-center gap-3 w-full p-3 rounded-xl hover:bg-[var(--surface)] transition-colors text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)]",
          !isOpen && "justify-center"
        )}>
          <HelpCircle size={18} className="min-w-[18px]" />
          {isOpen && <span className="font-medium">Help</span>}
        </button>
        <button className={cn(
          "flex items-center gap-3 w-full p-3 rounded-xl hover:bg-[var(--surface)] transition-colors text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)]",
          !isOpen && "justify-center"
        )}>
          <Settings size={18} className="min-w-[18px]" />
          {isOpen && <span className="font-medium">Settings</span>}
        </button>
      </div>
    </motion.div>
  );
}
