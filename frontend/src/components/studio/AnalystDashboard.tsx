"use client";

import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, 
  Sparkles, 
  ChevronDown, 
  Database, 
  Shield, 
  RotateCcw,
  User,
  Bot,
  Copy,
  ThumbsUp,
  ThumbsDown,
  Share2,
  Trash2,
  Table as TableIcon,
  BarChart,
  Code
} from 'lucide-react';
import { useAppStore, Message } from '@/store/useAppStore';
import { QueryBox } from './QueryBox';
import { SuggestionChips } from './SuggestionChips';
import { AccountControl } from './AccountControl';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';

export function AnalystDashboard() {
  const { messages, isLoading, loadingStep, user, showThinking, setShowThinking } = useAppStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, isLoading]);

  const isChatMode = messages.length > 0;

  return (
    <div className="flex-1 flex flex-col min-w-0 h-screen relative bg-[var(--bg-primary)] overflow-hidden">
      
      {/* Top Header */}
      <header className="h-16 shrink-0 flex items-center justify-between px-6 z-40 bg-transparent">
        <div className="flex items-center gap-4">
           {isChatMode && (
              <motion.div 
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center gap-2"
              >
                 <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--surface)] border border-[var(--border)]">
                    <Sparkles size={14} className="text-[var(--accent)]" />
                    <span className="font-semibold text-xs text-[var(--text-secondary)]">Advanced AI Studio</span>
                 </div>
              </motion.div>
           )}
        </div>
        <AccountControl />
      </header>

      {/* Main Content Area */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto custom-scrollbar relative"
      >
        <div className={cn(
          "max-w-4xl mx-auto w-full px-4 md:px-6",
          isChatMode ? "pt-8 pb-40" : "h-[calc(100vh-180px)] flex flex-col justify-center"
        )}>
          <AnimatePresence mode="wait">
            {!isChatMode ? (
              <motion.div 
                key="default"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="w-full text-left space-y-2 mb-12"
              >
                 <h1 className="text-5xl md:text-6xl font-medium gemini-gradient tracking-tight leading-tight">
                    Hello, {user.name.split(' ')[0]}
                 </h1>
                 <h2 className="text-5xl md:text-6xl font-medium text-[var(--text-secondary)] opacity-60 tracking-tight leading-tight">
                    How can I help you today?
                 </h2>
                 
                 <div className="pt-12">
                    <SuggestionChips />
                 </div>
              </motion.div>
            ) : (
              <motion.div 
                key="chat"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-12"
              >
                {messages.map((message: Message, i: number) => (
                  <ChatBubble key={message.id} message={message} isLast={i === messages.length - 1} />
                ))}

                {isLoading && (
                  <ThinkingState step={loadingStep} showThinking={showThinking} toggleThinking={() => setShowThinking(!showThinking)} />
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Fixed Bottom Input Area */}
      <div className="absolute bottom-0 left-0 w-full p-4 md:pb-8 bg-gradient-to-t from-[var(--bg-primary)] via-[var(--bg-primary)]/95 to-transparent pt-12 z-40">
         <div className="max-w-4xl mx-auto">
            <QueryBox isChatMode={isChatMode} />
            <p className="text-center text-[10px] text-[var(--text-secondary)] opacity-60 mt-3 font-medium">
               Gemini-powered insights may be inaccurate. Double-check important info.
            </p>
         </div>
      </div>
    </div>
  );
}

function ChatBubble({ message, isLast }: { message: Message; isLast: boolean }) {
  const isUser = message.role === 'user';
  
  return (
    <motion.div 
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "flex w-full group",
        isUser ? "justify-end pl-12" : "justify-start pr-12"
      )}
    >
      <div className={cn(
        "flex gap-5 max-w-[90%]",
        isUser ? "flex-row-reverse" : "flex-row"
      )}>
        {/* Avatar Placeholder */}
        <div className={cn(
          "w-9 h-9 rounded-full shrink-0 flex items-center justify-center border transition-all mt-1",
          isUser 
            ? "bg-indigo-600 border-indigo-500 shadow-sm" 
            : "bg-transparent border-none"
        )}>
          {isUser ? <User size={18} className="text-white" /> : (
            <div className="relative">
              <Sparkles size={24} className="text-indigo-400 animate-pulse" />
              <div className="absolute inset-0 bg-indigo-400 blur-md opacity-20" />
            </div>
          )}
        </div>

        <div className="space-y-3 flex-1 min-w-0">
           {!isUser && (
             <p className="text-[10px] font-bold text-[var(--text-secondary)] uppercase tracking-[1.5px] mb-1">AI Studio</p>
           )}
           <div className={cn(
             "transition-all",
             isUser 
               ? "p-4 px-5 rounded-[24px] bg-[var(--surface)] border border-[var(--border)]/30 text-[var(--text-primary)] rounded-tr-sm" 
               : "text-[var(--text-primary)]"
           )}>
             <div className="prose prose-sm dark:prose-invert max-w-none text-[15px] leading-relaxed font-normal space-y-6">
                <ReactMarkdown>{message.content}</ReactMarkdown>
                
                {/* Render Detailed Sections if they exist */}
                {!isUser && message.data?.sections && Array.isArray(message.data.sections) && message.data.sections.map((section: any, idx: number) => (
                  <div key={idx} className="space-y-2 animate-in fade-in slide-in-from-bottom-2 duration-500" style={{ animationDelay: `${idx * 100}ms` }}>
                    {section.title && <h3 className="text-lg font-bold text-[var(--text-primary)] mt-6">{section.title}</h3>}
                    <ReactMarkdown>{section.content || section.body || ""}</ReactMarkdown>
                  </div>
                ))}
             </div>

             {/* Dynamic Data Cards (e.g. SQL, Table) */}
             {!isUser && message.data && (
                <div className="mt-8 space-y-6">
                   {message.data.error && (
                      <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex gap-3 items-start animate-in shake duration-500">
                         <Shield className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                         <div className="space-y-1">
                            <p className="text-xs font-bold text-red-400 uppercase tracking-widest leading-none">Execution Error</p>
                            <p className="text-sm text-red-200/80 leading-relaxed italic">"{message.data.error}"</p>
                         </div>
                      </div>
                   )}
                   {message.data.sql && <ResponseCard title="Generated SQL" icon={Code} content={message.data.sql} type="code" />}
                   {message.data.table && <ResponseCard title="Data Preview" icon={TableIcon} content={message.data.table} type="table" />}
                   {message.data.insights && message.data.insights.length > 0 && <ResponseCard title="AI Insights" icon={Brain} content={message.data.insights} type="list" />}
                </div>
             )}
           </div>

           {/* Actions (Gemini-style minimal) */}
           {!isUser && (
             <div className={cn(
               "flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity pt-2",
               isUser ? "justify-end" : "justify-start"
             )}>
                <ActionButton icon={ThumbsUp} tooltip="Good response" />
                <ActionButton icon={ThumbsDown} tooltip="Bad response" />
                <ActionButton icon={Share2} tooltip="Share" />
                <ActionButton icon={RotateCcw} tooltip="Regenerate" />
             </div>
           )}
        </div>
      </div>
    </motion.div>
  );
}

function ActionButton({ icon: Icon, tooltip }: { icon: React.ElementType; tooltip: string }) {
  return (
    <button 
      className="p-2 hover:bg-[var(--surface)] rounded-full text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors relative group/btn"
      title={tooltip}
    >
      <Icon size={14} />
    </button>
  );
}

function ResponseCard({ title, icon: Icon, content, type }: { title: string; icon: React.ElementType; content: any; type: 'code' | 'table' | 'list' }) {
  const [copied, setCopied] = React.useState(false);

  return (
    <div className="glass-card border border-[var(--border)] rounded-2xl overflow-hidden bg-[var(--bg-primary)]/50 p-4 group/card">
       <div className="flex items-center justify-between mb-4 border-b border-[var(--border)]/30 pb-3">
          <div className="flex items-center gap-2">
             <Icon size={18} className="text-indigo-500" />
             <span className="text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">{title}</span>
          </div>
          <div className="relative group/copy">
            <button 
                onClick={() => {
                navigator.clipboard.writeText(JSON.stringify(content, null, 2));
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
                }}
                className={cn(
                    "text-xs font-bold transition-all px-3 py-1 rounded-full",
                    copied ? "text-emerald-500 bg-emerald-500/10" : "text-indigo-500 hover:bg-indigo-500/10"
                )}
            >
                {copied ? 'Copied!' : 'Copy'}
            </button>
            
            {/* Hover Tooltip (Black badge) */}
            {!copied && (
                <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-black text-white text-[10px] rounded-md opacity-0 group-hover/copy:opacity-100 transition-opacity pointer-events-none font-bold z-50 shadow-xl">
                    Copy
                </div>
            )}
          </div>
       </div>
       
       <div className="text-sm">
          {type === 'code' && (
             <div className="p-4 bg-[var(--bg-secondary)] rounded-xl font-mono text-xs overflow-x-auto border border-[var(--border)] shadow-inner">
                {content}
             </div>
          )}
          {type === 'list' && (
             <ul className="space-y-3">
                {Array.isArray(content) && content.map((item: string, i: number) => (
                  <li key={i} className="flex gap-3 items-start animate-in fade-in slide-in-from-left duration-300" style={{ animationDelay: `${i * 100}ms` }}>
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-2 shrink-0 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
                    <span className="opacity-80 leading-relaxed">{item}</span>
                  </li>
                ))}
             </ul>
          )}
          {type === 'table' && (
             <div className="overflow-x-auto rounded-xl border border-[var(--border)] max-h-64 custom-scrollbar">
                <table className="w-full text-left border-collapse">
                   <thead className="bg-[var(--bg-secondary)]/80 backdrop-blur-md sticky top-0">
                      <tr>
                         {Object.keys(content[0] || {}).map(key => (
                           <th key={key} className="p-3 text-[10px] font-black uppercase tracking-widest text-[var(--text-secondary)] border-b border-[var(--border)]">{key}</th>
                         ))}
                      </tr>
                   </thead>
                   <tbody>
                      {content.slice(0, 5).map((row: any, i: number) => (
                        <tr key={i} className="hover:bg-indigo-500/5 transition-colors group">
                           {Object.values(row).map((val: any, j: number) => (
                             <td key={j} className="p-3 text-xs font-medium border-b border-[var(--border)]/30 opacity-80 group-hover:opacity-100 transition-opacity">{String(val)}</td>
                           ))}
                        </tr>
                      ))}
                   </tbody>
                </table>
             </div>
          )}
       </div>
    </div>
  );
}

function ThinkingState({ step, showThinking, toggleThinking }: { step: string; showThinking: boolean; toggleThinking: () => void }) {
  return (
    <div className="flex justify-start pr-12 w-full animate-in fade-in slide-in-from-bottom duration-500">
      <div className="flex gap-4 w-full">
        <div className="w-10 h-10 rounded-full bg-[var(--surface)] border border-[var(--border)] flex items-center justify-center text-indigo-500 shrink-0">
           <Brain className="w-5 h-5 animate-pulse" />
        </div>
        <div className="flex-1 space-y-4">
           <div className="flex items-center gap-3">
              <span className="text-xs font-bold uppercase tracking-widest text-indigo-500 animate-pulse">{step || 'AI is thinking...'}</span>
              <button 
                onClick={toggleThinking}
                className="text-[10px] font-black uppercase tracking-widest text-[var(--text-secondary)] hover:text-indigo-500 transition-colors flex items-center gap-1"
              >
                {showThinking ? 'Hide thinking' : 'Show thinking'}
                <ChevronDown className={cn("w-3 h-3 transition-transform duration-300", showThinking && "rotate-180")} />
              </button>
           </div>
           
           <AnimatePresence>
             {showThinking && (
               <motion.div 
                 initial={{ height: 0, opacity: 0 }}
                 animate={{ height: 'auto', opacity: 1 }}
                 exit={{ height: 0, opacity: 0 }}
                 className="overflow-hidden"
               >
                  <div className="p-4 rounded-2xl bg-[var(--surface)] border border-dashed border-[var(--border)] text-xs text-[var(--text-secondary)] leading-relaxed italic space-y-2 shimmer">
                     <p>• Analyzing query intent: "Show me Q4 sales data"</p>
                     <p>• Fetching schema metadata for "sales" and "orders" tables...</p>
                     <p>• Synthesizing SQL join operation with period filters...</p>
                  </div>
               </motion.div>
             )}
           </AnimatePresence>

           <div className="flex gap-2">
              <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: '300ms' }} />
           </div>
        </div>
      </div>
    </div>
  );
}
