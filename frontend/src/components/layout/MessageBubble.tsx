"use client";

import React from 'react';
import { User, Sparkles, Brain, Fingerprint, Cpu } from 'lucide-react';
import { useAppStore, Message } from '@/store/useAppStore';
import { cn } from '@/lib/utils';
import { ResponseCard } from './ResponseCard';
import { motion } from 'framer-motion';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble = ({ message }: MessageBubbleProps) => {
  const isUser = message.role === 'user';

  return (
    <motion.div 
      initial={{ opacity: 0, y: 30, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
      className={cn(
        "flex w-full mb-16 relative group",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Visual Identity Marker */}
      <div className={cn(
        "flex-shrink-0 w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-500 group-hover:rotate-12 relative",
        isUser ? "ml-6 glass border-border/20 shadow-xl" : "mr-6 bg-gradient-to-br from-[var(--accent)] to-[#D946EF] text-white shadow-2xl shadow-[var(--accent)]/30"
      )}>
        {isUser ? (
          <div className="relative">
            <Fingerprint className="w-6 h-6 text-[var(--accent)]" />
            <div className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-500 rounded-full border-2 border-[var(--bg-primary)]" />
          </div>
        ) : (
          <div className="relative">
            <Cpu className="w-6 h-6" />
            <div className="absolute -top-1 -right-1 w-2 h-2 bg-white rounded-full border-2 border-[var(--accent)] animate-pulse" />
          </div>
        )}
      </div>

      {/* Message Content Area */}
      <div className={cn(
        "max-w-[85%] space-y-4",
        isUser ? "text-right flex flex-col items-end" : "text-left"
      )}>
        {/* Info Header */}
        <div className={cn(
          "flex items-center space-x-4 mb-1",
          isUser && "flex-row-reverse space-x-reverse"
        )}>
          <span className="text-[10px] font-black uppercase tracking-[3px] text-[var(--text-primary)]">
            {isUser ? 'You' : 'AI Assistant'}
          </span>
          <div className="w-1 h-1 rounded-full bg-border/40" />
          <span className="text-[10px] font-black text-text-secondary opacity-40 uppercase tracking-widest">{message.timestamp}</span>
          
          {!isUser && message.intent && (
            <div className={cn(
                "flex items-center space-x-1.5 px-3 py-1 rounded-full border glass shadow-sm",
                message.intent === 'DATA' ? "border-emerald-500/30 text-emerald-500" : 
                message.intent === 'GENERAL' ? "border-[var(--accent)]/30 text-[var(--accent)]" :
                "border-orange-500/30 text-orange-500"
            )}>
                <Sparkles className="w-3 h-3" />
                <span className="text-[9px] font-black uppercase tracking-[2px] leading-none translate-y-[0.5px]">
                  {message.intent === 'DATA' ? 'DATA' : message.intent === 'GENERAL' ? 'INFO' : 'ANALYSIS'}
                </span>
            </div>
          )}
        </div>

        {/* Bubble (User only uses simple bubble, Assistant uses the ResponseCard) */}
        {isUser ? (
          <div className="p-6 glass border-[var(--border)] rounded-[32px] rounded-tr-none shadow-2xl text-[var(--text-primary)] font-bold tracking-tight leading-relaxed max-w-xl relative overflow-hidden group/bubble">
            <div className="absolute inset-0 bg-gradient-to-br from-[var(--accent)]/5 to-transparent opacity-0 group-hover/bubble:opacity-100 transition-opacity" />
            <p className="relative z-10 text-lg sm:text-xl font-display">{message.content}</p>
          </div>
        ) : (
          <div className="w-full">
            <ResponseCard data={message.data || {}} />
          </div>
        )}
      </div>
    </motion.div>
  );
};

