import React, { useState, useRef, useEffect } from 'react';
import { Send, Zap, Sparkles, Mic, Paperclip } from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

export const ChatInput = () => {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { addMessage, setLoading, setError, loadingStep } = useAppStore();

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = async () => {
    if (!value.trim()) return;
    
    // Add user message
    const userMsg = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: value,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    addMessage(userMsg);
    setValue('');

    // Mock processing steps
    setLoading(true, 'Analyzing intent...');
    
    // Simulations
    setTimeout(() => {
      setLoading(true, 'Architecting SQL...');
      setTimeout(() => {
        setLoading(true, 'Aggregating insights...');
        setTimeout(() => {
          // Success mock
          const assistantMsg = {
            id: (Date.now() + 1).toString(),
            role: 'assistant' as const,
            content: "I've analyzed the sales data for Q4 2025. Total revenue was $1.2M, which is 15% above target.",
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            data: {
              sql: "SELECT month, SUM(revenue) FROM sales WHERE year = 2025 AND quarter = 4 GROUP BY month ORDER BY month",
              table: [
                { Month: 'October', Revenue: 380000, Target: 350000, Growth: '8.5%' },
                { Month: 'November', Revenue: 420000, Target: 390000, Growth: '7.7%' },
                { Month: 'December', Revenue: 450000, Target: 410000, Growth: '9.8%' }
              ],
              chart: {
                type: 'bar',
                options: { title: 'Q4 Revenue Performance' },
                series: [
                  { name: 'Revenue', data: [380000, 420000, 450000] },
                  { name: 'Target', data: [350000, 390000, 410000] }
                ],
                labels: ['Oct', 'Nov', 'Dec']
              },
              insights: [
                "Revenue peaked in December due to holiday demand.",
                "Target was exceeded every month in Q4.",
                "October showed the strongest growth relative to previous quarter."
              ]
            }
          };
          addMessage(assistantMsg);
          setLoading(false);
        }, 1200);
      }, 800);
    }, 1000);
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [value]);

  return (
    <div className="sticky bottom-0 w-full max-w-4xl mx-auto px-6 pb-8 pt-4 bg-gradient-to-t from-background-primary via-background-primary to-transparent">
      <div className="relative group">
        {/* Glow effect */}
        <div className="absolute -inset-1 bg-accent/20 rounded-2xl blur-lg opacity-0 group-focus-within:opacity-100 transition-opacity pointer-events-none" />
        
        <div className="relative flex flex-col bg-background-secondary border border-border/60 rounded-2xl shadow-xl shadow-black/5 overflow-hidden ring-1 ring-black/[0.03]">
          
          <div className="flex items-center px-4 pt-4 pb-2 space-x-2 border-b border-border/20">
             <div className="p-1 px-3 bg-accent/5 rounded-full border border-accent/10 flex items-center space-x-2 text-[11px] font-bold text-accent uppercase tracking-wider">
               <Zap className="w-3 h-3" />
               <span>AI Semantic Engine Active</span>
             </div>
          </div>

          <textarea
            ref={textareaRef}
            rows={1}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Query your database using natural language..."
            className="w-full h-fit min-h-[60px] max-h-[300px] px-6 py-4 bg-transparent resize-none text-text-primary placeholder:text-text-secondary focus:outline-none focus:ring-0 leading-relaxed font-medium"
          />

          <div className="flex items-center justify-between px-4 pb-4">
            <div className="flex items-center space-x-2">
              <button className="p-2 text-text-secondary hover:text-accent hover:bg-accent/10 rounded-lg transition-all">
                <Paperclip className="w-5 h-5" />
              </button>
              <button className="p-2 text-text-secondary hover:text-accent hover:bg-accent/10 rounded-lg transition-all">
                <Mic className="w-5 h-5" />
              </button>
              <div className="w-[1px] h-4 bg-border/40 mx-1" />
              <button className="p-2 text-text-secondary hover:text-accent hover:bg-accent/10 rounded-lg transition-all group">
                <Sparkles className="w-5 h-5 group-hover:animate-spin-slow" />
              </button>
            </div>
            
            <button
              onClick={handleSubmit}
              disabled={!value.trim()}
              className={cn(
                "p-2.5 rounded-xl transition-all shadow-lg",
                value.trim() 
                  ? "bg-accent text-white shadow-accent/20 hover:scale-105 active:scale-95" 
                  : "bg-surface text-text-secondary cursor-not-allowed"
              )}
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
        
        <p className="mt-3 text-[11px] text-center text-text-secondary font-bold uppercase tracking-widest opacity-60">
          PROMPT-TO-SQL | V2.0 PRODUCTION PIPELINE
        </p>
      </div>
    </div>
  );
};
