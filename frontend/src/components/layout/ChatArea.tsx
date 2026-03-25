import React, { useRef, useEffect } from 'react';
import { Zap, PieChart as PieChartIcon, Table as TableIcon, Database, Terminal } from 'lucide-react';
import { useAppStore, Message } from '@/store/useAppStore';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { ResponseCard } from './ResponseCard';

export const ChatArea = ({ children }: { children: React.ReactNode }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const { messages, isLoading, loadingStep } = useAppStore();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [messages, isLoading]);

  return (
    <div className="flex-1 flex flex-col h-full bg-background-primary relative overflow-hidden">
      {/* Messages */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-6 py-12 space-y-8 scroll-smooth"
      >
        {messages.length === 0 && (
          <div className="max-w-3xl mx-auto flex flex-col items-center justify-center h-full text-center space-y-6 pt-24">
            <div className="w-20 h-20 bg-accent/5 rounded-3xl flex items-center justify-center border-2 border-accent/10 border-dashed animate-pulse">
              <Zap className="w-10 h-10 text-accent/50" />
            </div>
            <div className="space-y-2">
              <h2 className="text-3xl font-black tracking-tight">How can I help you <span className="gradient-text">analyze</span> today?</h2>
              <p className="text-text-secondary font-medium">Ask questions about your data in natural language, and I'll generate the SQL and visualizations.</p>
            </div>
            
            <div className="grid grid-cols-2 gap-4 w-full max-w-xl">
              {[
                { icon: <PieChartIcon className="w-4 h-4 text-purple-400"/>, text: "Compare Q4 revenue vs forecast" },
                { icon: <TableIcon className="w-4 h-4 text-blue-400"/>, text: "List top 5 products by margin" },
                { icon: <Database className="w-4 h-4 text-emerald-400" />, text: "Show recent customer churn" },
                { icon: <Terminal className="w-4 h-4 text-orange-400" />, text: "Execute manual raw SQL query" }
              ].map((suggestion, i) => (
                <button
                  key={i}
                  className="p-4 bg-background-secondary border border-border/40 rounded-xl text-left hover:border-accent/40 hover:bg-accent/5 transition-all group"
                >
                  <div className="flex items-center space-x-3">
                    {suggestion.icon}
                    <span className="text-sm font-semibold truncate group-hover:text-accent ">{suggestion.text}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        <AnimatePresence>
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          
          {isLoading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start max-w-4xl mx-auto w-full group"
            >
              <div className="flex space-x-4 w-full">
                <div className="w-10 h-10 shrink-0 bg-accent/10 rounded-xl flex items-center justify-center border border-accent/20">
                  <Zap className="w-5 h-5 text-accent animate-pulse" />
                </div>
                <div className="flex-1 space-y-3 pt-2">
                  <div className="flex items-center space-x-3">
                    <div className="flex space-x-1">
                      <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce [animation-delay:-0.3s]" />
                      <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce [animation-delay:-0.15s]" />
                      <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" />
                    </div>
                    <span className="text-xs font-bold text-accent uppercase tracking-widest">{loadingStep || 'Thinking...'}</span>
                  </div>
                  <div className="max-w-sm space-y-2">
                    <div className="h-4 bg-surface rounded-full w-full animate-pulse" />
                    <div className="h-4 bg-surface rounded-full w-2/3 animate-pulse" />
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {children}
    </div>
  );
};

const MessageBubble = ({ message }: { message: Message }) => {
  const isUser = message.role === 'user';
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className={cn(
        "flex max-w-4xl mx-auto w-full group",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div className={cn(
        "flex max-w-[85%] w-fit",
        isUser ? "flex-row-reverse" : "flex-row",
        "space-x-4",
        isUser && "space-x-reverse"
      )}>
        <div className={cn(
          "w-10 h-10 shrink-0 rounded-xl flex items-center justify-center border transform hover:scale-105 transition-transform",
          isUser 
            ? "bg-accent/10 border-accent/30" 
            : "bg-background-secondary border-border shadow-sm shadow-black/5"
        )}>
          {isUser ? (
            <div className="w-8 h-8 rounded-lg bg-accent text-white flex items-center justify-center font-black text-xs">U</div>
          ) : (
            <Zap className="w-5 h-5 text-accent" />
          )}
        </div>
        
        <div className={cn(
          "flex-1 space-y-4 pt-1",
          isUser && "text-right"
        )}>
          <div className={cn(
            "p-5 rounded-2xl shadow-sm border transition-all",
            isUser 
              ? "bg-accent text-white border-accent shadow-accent/20" 
              : "bg-background-secondary border-border glass"
          )}>
            <p className={cn(
              "text-[15px] leading-relaxed",
              isUser ? "font-semibold" : "font-medium text-text-primary"
            )}>
              {message.content}
            </p>
          </div>
          
          {!isUser && message.data && (
            <ResponseCard data={message.data} />
          )}
        </div>
      </div>
    </motion.div>
  );
};
