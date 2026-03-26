"use client";

import React from 'react';
import { motion } from 'framer-motion';
import { 
  Image as ImageIcon, 
  Lightbulb, 
  Music, 
  PenTool, 
  Sun, 
  Video 
} from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { cn } from '@/lib/utils';

const SUGGESTIONS = [
  { id: 'revenue', label: 'Analyze Q4 revenue vs forecast', icon: Lightbulb, color: 'text-amber-500', prompt: 'Analyze Q4 revenue vs forecast' },
  { id: 'inventory', label: 'Show inventory trends per category', icon: Sun, color: 'text-orange-500', prompt: 'Show inventory trends per category' },
  { id: 'customers', label: 'Identify top 10 loyal customers', icon: PenTool, color: 'text-indigo-500', prompt: 'Identify top 10 loyal customers' },
  { id: 'churn', label: 'Check recent customer churn patterns', icon: Video, color: 'text-rose-500', prompt: 'Check recent customer churn patterns' },
];

export function SuggestionChips() {
  const { messages } = useAppStore();
  
  // This would ideally interact with an input ref or shared state
  // For now, we'll alert that it's clicking, but in a real app would set state.
  return (
    <div className="flex flex-wrap items-center justify-start gap-3 mt-8">
      {SUGGESTIONS.map((chip, i) => (
        <motion.button
          key={chip.id}
          onClick={() => {
              // Note: In a real app we'd trigger the input change, 
              // but SuggestionChips is separate. I'll stick to visual active state first.
              window.dispatchEvent(new CustomEvent('SET_QUERY', { detail: chip.prompt }));
          }}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 + i * 0.05 }}
          className={cn(
            "group flex flex-col items-start gap-4 p-4 min-w-[200px] rounded-2xl transition-all bg-[var(--surface)] hover:bg-[var(--surface)]/80 border border-transparent hover:border-[var(--border)] shadow-sm text-left"
          )}
        >
          <chip.icon className={cn("w-5 h-5", chip.color)} />
          <span className="text-[13px] font-medium text-[var(--text-secondary)]">
            {chip.label}
          </span>
        </motion.button>
      ))}
    </div>
  );
}
