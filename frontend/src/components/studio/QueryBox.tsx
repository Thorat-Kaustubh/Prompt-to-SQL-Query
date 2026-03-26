"use client";

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Plus, 
  Mic, 
  Send, 
  ChevronDown, 
  Sparkles, 
  MoreVertical,
  Brain,
  Zap,
  Command,
  Globe
} from 'lucide-react';
import { useAppStore, API_BASE, AUTH_TOKEN } from '@/store/useAppStore';
import { cn } from '@/lib/utils';

interface GeminiInputBoxProps {
  isChatMode?: boolean;
}

export function QueryBox({ isChatMode = false }: { isChatMode?: boolean }) {
  const [inputValue, setInputValue] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [showModels, setShowModels] = useState(false);
  const { addMessage, updateMessage, setLoading, user, isLoading, currentConversationId, setCurrentConversationId, fetchHistory } = useAppStore();
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const handler = (e: any) => {
        setInputValue(e.detail);
        inputRef.current?.focus();
    };
    window.addEventListener('SET_QUERY', handler);
    return () => window.removeEventListener('SET_QUERY', handler);
  }, []);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMsg = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: inputValue.trim(),
      timestamp: new Date().toLocaleTimeString(),
    };

    addMessage(userMsg);
    setInputValue("");
    setLoading(true, "Thinking...");

    const assistantMsgId = (Date.now() + 1).toString();
    // Create an empty assistant message first
    addMessage({
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toLocaleTimeString(),
        intent: 'GENERAL'
    });

    try {
      const response = await fetch(`${API_BASE}/query/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": AUTH_TOKEN
        },
        body: JSON.stringify({ 
          prompt: userMsg.content,
          conversation_id: currentConversationId
        })
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }

      setLoading(false);
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullContent = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          
          // Special Token handling
          if (chunk.includes("__CONV_ID__:")) {
            const id = chunk.split("__CONV_ID__:")[1].trim();
            if (id && !currentConversationId) {
                setCurrentConversationId(id);
                fetchHistory();
            }
            continue;
          }

          fullContent += chunk;
          
          // Try to extract markdown content if it's JSON, or just show raw
          let displayContent = fullContent;
          try {
             const cleaned = fullContent.match(/\{[\s\S]*\}|[\s\S]*/);
             if (cleaned && fullContent.includes('"explanation":')) {
                const match = fullContent.match(/"explanation":\s*"([^"]*)"/);
                if (match) displayContent = match[1].replace(/\\n/g, '\n');
             }
          } catch(e) {}

          updateMessage(assistantMsgId, { content: displayContent });
        }
      }
      
      // Final full sync after stream ends to get tables/data
      try {
         const jsonMatch = fullContent.match(/\{[\s\S]*\}/);
         if (jsonMatch) {
            const parsed = JSON.parse(jsonMatch[0]);
            updateMessage(assistantMsgId, { 
                content: parsed.explanation || parsed.content || fullContent,
                data: parsed,
                intent: parsed.intent || 'GENERAL'
            });
         }
      } catch(e) {}

    } catch (err: any) {
      console.error(err);
      setLoading(false);
      addMessage({
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: `Sorry, I encountered an issue: ${err.message || "Failed to process query."}`,
        timestamp: new Date().toLocaleTimeString(),
        intent: 'GENERAL'
      });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className={cn(
      "w-full max-w-4xl mx-auto px-4 transition-all duration-700",
      isChatMode ? "mb-4" : "mt-4"
    )}>
      <motion.div 
        layout
        className={cn(
          "relative transition-all duration-500 overflow-visible",
          "rounded-[32px] bg-[var(--surface)] border border-transparent",
          isFocused ? "shadow-lg border-indigo-500/30 ring-4 ring-indigo-500/5 bg-[var(--surface)]" : "shadow-sm",
          "p-2 pr-4 pl-3"
        )}
      >
        <div className="flex flex-col">
          <div className="flex items-center gap-1">
            {/* Attachment Button */}
            <button className="flex items-center justify-center w-10 h-10 rounded-full hover:bg-[var(--border)]/30 transition-all text-[var(--text-secondary)] shrink-0 group">
              <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform duration-300" />
            </button>

            {/* Main Input */}
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => {
                setInputValue(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = (e.target.scrollHeight) + 'px';
              }}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              onKeyDown={handleKeyDown}
              placeholder="Enter a prompt here"
              rows={1}
              className="flex-1 bg-transparent border-none outline-none focus:outline-none focus:ring-0 focus:border-none text-base md:text-[17px] py-2.5 px-3 resize-none custom-scrollbar max-h-52 font-normal placeholder:text-[var(--text-secondary)]/60 shadow-none"
              style={{ overflow: 'hidden' }}
            />

            {/* Right Controls */}
            <div className="flex items-center gap-1 shrink-0">
               {/* Mic Button */}
               <button className="flex items-center justify-center w-10 h-10 rounded-full hover:bg-[var(--border)]/30 transition-all text-[var(--text-secondary)]">
                  <Mic className="w-5 h-5" />
               </button>

               {/* Send Button */}
               {inputValue && (
                 <motion.button 
                   initial={{ scale: 0.8, opacity: 0 }}
                   animate={{ scale: 1, opacity: 1 }}
                   onClick={handleSubmit}
                   className="flex items-center justify-center w-10 h-10 rounded-full bg-indigo-600 text-white shadow-md hover:bg-indigo-700 transition-all"
                 >
                   <Send className="w-4 h-4" />
                 </motion.button>
               )}
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
