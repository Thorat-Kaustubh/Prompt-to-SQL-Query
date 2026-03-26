"use client";

import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Database, 
  Brain,
  Info,
  Zap,
  Command,
  ArrowRight,
  MessageSquare
} from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

const SUGGESTIONS = [
  { text: "Compare revenue across top categories", intent: "DATA", icon: Database },
  { text: "Teach me how to perform advanced joins", intent: "HYBRID", icon: Brain },
  { text: "How does Postgres indexing work?", intent: "GENERAL", icon: MessageSquare }
];

export const ChatInput = () => {
  const [input, setInput] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const { 
    addMessage, 
    messages, 
    setLoading, 
    isLoading, 
    setError, 
    selectedSchemaId, 
    schemas, 
    currentConversationId,
    setCurrentConversationId,
    fetchHistory
  } = useAppStore();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const selectedSchema = schemas.find(s => s.id === selectedSchemaId);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    addMessage(userMessage);
    const currentInput = input;
    setInput('');
    setLoading(true, 'Analyzing...');

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': 'Bearer local-dev-token'
        },
        body: JSON.stringify({ 
          prompt: currentInput,
          conversation_id: currentConversationId 
        }),
      });

      if (!response.ok) throw new Error('Failed to get response');

      const result = await response.json();
      
      // Update conversation ID if it's a new chat
      if (!currentConversationId && result.conversation_id) {
        setCurrentConversationId(result.conversation_id);
        fetchHistory(); // Refresh history list to show the new chat
      }

      const assistantMsg = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: result.content || result.explanation || 'No response returned.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        intent: result.intent,
        data: {
          sql: result.sql,
          table: result.results,
          chart: result.visualization || null,
          insights: result.insights || [],
          examples: result.examples || []
        }
      };

      addMessage(assistantMsg);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="p-8 pb-10 bg-gradient-to-t from-[var(--bg-primary)] via-[var(--bg-primary)]/80 to-transparent">
      <div className="max-w-4xl mx-auto flex flex-col items-center">
        
        {/* Suggestion Chips */}
        <AnimatePresence>
          {messages.length === 0 && (
            <motion.div 
               initial={{ opacity: 0, y: 20 }}
               animate={{ opacity: 1, y: 0 }}
               exit={{ opacity: 0, y: 20 }}
               className="flex flex-wrap justify-center gap-3 mb-10"
            >
              {SUGGESTIONS.map((s, i) => (
                <button 
                  key={i}
                  onClick={() => { setInput(s.text); textareaRef.current?.focus(); }}
                  className="group flex items-center space-x-3 px-5 py-3 glass-card border-border/20 text-[10px] font-black uppercase tracking-widest text-text-secondary hover:text-[var(--accent)] transition-all"
                >
                  <s.icon className="w-3.5 h-3.5 text-text-secondary group-hover:text-[var(--accent)] transition-colors" />
                  <span>{s.text}</span>
                  <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        <div className={cn(
          "w-full relative glass-card group/input transition-all duration-700 overflow-hidden",
          isFocused ? "border-[var(--accent)]/40 premium-shadow scale-[1.01]" : "border-border/10"
        )}>
          {/* Status Bar */}
          <div className="px-6 py-3 border-b border-border/5 flex items-center justify-between bg-surface/20">
             <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2 px-2 py-1 bg-[var(--accent)]/10 rounded-lg border border-[var(--accent)]/10">
                  <Database className="w-3 h-3 text-[var(--accent)]" />
                  <span className="text-[8px] font-black uppercase tracking-widest text-[var(--accent)]">{selectedSchema?.name}</span>
                </div>
                <div className="w-[1px] h-3 bg-border/20" />
                <div className="flex items-center space-x-2 text-text-secondary/50">
                  <Zap className="w-3 h-3" />
                  <span className="text-[8px] font-black uppercase tracking-widest">Fast Response</span>
                </div>
             </div>
             <div className="flex items-center space-x-3">
                <span className="text-[8px] font-black uppercase tracking-widest text-text-secondary opacity-40">Ready to assist</span>
             </div>
          </div>

          <div className="relative flex items-center">
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder="Ask anything about your data..."
              className="w-full pl-8 pr-32 py-10 bg-transparent outline-none text-[var(--text-primary)] text-lg font-bold placeholder:text-text-secondary/20 resize-none min-h-[120px] scrollbar-hide"
            />

            <div className="absolute right-8 flex items-center space-x-4">
               <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 bg-background/50 border border-border/20 rounded-xl text-[9px] font-black text-text-secondary opacity-40 group-focus-within/input:opacity-100 transition-opacity">
                    <Command className="w-3 h-3" />
                    <span>ENTER</span>
               </div>
               <button
                  onClick={() => handleSubmit()}
                  disabled={!input.trim() || isLoading}
                  className={cn(
                    "w-14 h-14 rounded-2xl flex items-center justify-center transition-all relative overflow-hidden group/btn",
                    !input.trim() || isLoading 
                      ? "bg-surface/10 text-text-secondary/30 opacity-50 cursor-not-allowed" 
                      : "bg-gradient-to-r from-[var(--accent)] to-[#D946EF] text-white shadow-xl shadow-[var(--accent)]/20 hover:scale-105 active:scale-95"
                  )}
                >
                  {isLoading ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      <Send className="w-5 h-5 relative z-10" />
                      <div className="absolute inset-0 bg-white/20 translate-y-full group-hover/btn:translate-y-0 transition-transform duration-300" />
                    </>
                  )}
                </button>
            </div>
          </div>
        </div>

        <div className="mt-6 flex items-center space-x-6">
            <div className="flex items-center space-x-2 text-[9px] font-black uppercase tracking-[3px] text-text-secondary/30 hover:text-text-secondary transition-colors cursor-default">
                <Info className="w-2.5 h-2.5" />
                <span>Secure Connection</span>
            </div>
            <div className="w-1 h-1 bg-border/20 rounded-full" />
            <div className="flex items-center space-x-2 text-[9px] font-black uppercase tracking-[3px] text-text-secondary/30 hover:text-text-secondary transition-colors cursor-default">
                <Brain className="w-2.5 h-2.5" />
                <span>AI Assistant</span>
            </div>
        </div>
      </div>
    </div>
  );
};

