"use client";

import React, { useState } from 'react';
import { 
  BarChart3, 
  Database, 
  Lightbulb, 
  Terminal, 
  Copy, 
  Bookmark, 
  RotateCcw, 
  Check, 
  ChevronDown,
  Eye,
  Table as TableIcon,
  Sparkles,
  Command,
  ShieldCheck,
  Maximize2
} from 'lucide-react';
import { DataTable } from '../visuals/DataTable';
import { DataChart } from '../visuals/DataChart';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppStore } from '@/store/useAppStore';

interface ResponseCardProps {
  data: {
    type?: string;
    title?: string;
    content?: string;
    sections?: { 
        title?: string; 
        heading?: string; 
        content?: string; 
        body?: string 
    }[];
    actions?: string[];
    sql?: string;
    results?: any[];
    table?: any[];
    extras?: {
        code?: string;
        table?: string;
        chart_data?: string;
        knowledge_summary?: string;
    };
    visualization?: any;
    chart?: any;
    insights?: string[];
    knowledge_summary?: string;
    examples?: { title: string; description: string; sql: string }[];
    intent?: 'GENERAL' | 'DATA' | 'HYBRID';
    meta?: any;
  };
}

export const ResponseCard = ({ data }: ResponseCardProps) => {
  const [showSql, setShowSql] = useState(false);
  const [activeTab, setActiveTab] = useState<'view' | 'data'>('view');
  const [copied, setCopied] = useState(false);
  const { saveToKnowledge } = useAppStore();

  const mainContent = data.content || "";
  const tableData = data.results || data.table || data.extras?.table || [];
  const chartConfig = data.visualization || data.chart || data.extras?.chart_data;
  const isDataMode = (Array.isArray(tableData) && tableData.length > 0) || !!chartConfig;
  const knowledgeSummary = data.knowledge_summary || data.extras?.knowledge_summary;

  const copyToClipboard = (text?: string) => {
    navigator.clipboard.writeText(text || data.sql || data.extras?.code || mainContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSave = () => {
      saveToKnowledge({
          title: data.title || mainContent.slice(0, 30) + '...',
          content: mainContent,
          tags: data.intent ? [data.intent] : ['Saved']
      });
  };

  // --- SUB-COMPONENTS (CONTRACT ALIGNED) ---

  const ActionBelt = () => (
    <div className="mt-8 flex flex-wrap items-center gap-3 pt-6 border-t border-border/10">
      {(data.actions || ['save', 'copy']).map((action) => {
        if (action === 'save') return (
          <button key="save" onClick={handleSave} className="group flex items-center space-x-2 px-4 py-2 glass-card hover:bg-accent/5 hover:border-accent/40 transition-all text-[10px] font-black uppercase tracking-wider text-text-secondary hover:text-accent">
            <Bookmark className="w-3.5 h-3.5 group-hover:fill-accent transition-all" />
            <span>Save</span>
          </button>
        );
        if (action === 'copy') return (
          <button key="copy" onClick={() => copyToClipboard()} className="group flex items-center space-x-2 px-4 py-2 glass-card hover:bg-accent/5 hover:border-accent/40 transition-all text-[10px] font-black uppercase tracking-wider text-text-secondary hover:text-accent">
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        );
        return (
          <button key={action} className="flex items-center space-x-2 px-4 py-2 glass-card hover:bg-accent/5 hover:border-accent/40 transition-all text-[10px] font-black uppercase tracking-wider text-text-secondary hover:text-accent">
            <Sparkles className="w-3.5 h-3.5" />
            <span className="capitalize">{action.replace('_', ' ')}</span>
          </button>
        );
      })}
    </div>
  );

  const KnowledgeCapsule = () => (
    knowledgeSummary ? (
      <div className="mb-6 p-4 bg-accent/5 border border-accent/20 rounded-xl">
         <div className="flex items-center space-x-2 mb-1.5">
            <Sparkles className="w-3.5 h-3.5 text-accent" />
            <span className="text-[9px] font-black uppercase tracking-widest text-accent">Knowledge Capsule</span>
         </div>
         <p className="text-xs font-bold text-text-primary italic">"{knowledgeSummary}"</p>
      </div>
    ) : null
  );

  const SectionList = () => (
    data.sections && data.sections.length > 0 ? (
      <div className="grid grid-cols-1 gap-4 mt-6">
        {data.sections.map((section, idx) => (
          <motion.div 
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="p-6 glass-card border-l-4 border-l-accent/40"
          >
            <h4 className="text-xs font-black uppercase tracking-widest text-accent mb-2">{section.heading}</h4>
            <div className="text-sm font-medium text-text-primary leading-relaxed opacity-90">
              {section.body}
            </div>
          </motion.div>
        ))}
      </div>
    ) : null
  );

  const DataSurface = () => (
    isDataMode ? (
      <motion.div 
         initial={{ opacity: 0, scale: 0.98 }}
         animate={{ opacity: 1, scale: 1 }}
         className="glass-card overflow-hidden border-border/20 shadow-2xl relative mt-6"
      >
        <div className="flex items-center justify-between px-8 py-5 border-b border-border/10 bg-surface/30">
           <div className="flex glass bg-background/40 p-1 rounded-xl">
              <button 
                onClick={() => setActiveTab('view')} 
                className={cn(
                  "flex items-center space-x-2 px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all", 
                  activeTab === 'view' ? "bg-[var(--accent)] text-white shadow-lg" : "text-text-secondary hover:text-[var(--text-primary)]"
                )}
              >
                  <BarChart3 className="w-1.5 h-1.5" />
                  <span>Visual</span>
              </button>
              <button 
                onClick={() => setActiveTab('data')} 
                className={cn(
                  "flex items-center space-x-2 px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all", 
                  activeTab === 'data' ? "bg-[var(--accent)] text-white shadow-lg" : "text-text-secondary hover:text-[var(--text-primary)]"
                )}
              >
                  <TableIcon className="w-4 h-4" />
                  <span>Table</span>
              </button>
           </div>
           <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-[9px] font-black uppercase tracking-widest text-text-secondary">
                <Maximize2 className="w-3 h-3" />
                <span>{Array.isArray(tableData) ? tableData.length : 0} rows</span>
              </div>
           </div>
        </div>

        <div className="p-8 h-[400px] bg-gradient-to-b from-accent/5 to-transparent">
           <AnimatePresence mode="wait">
              {activeTab === 'view' && chartConfig ? (
                 <motion.div key="chart" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 1.05 }} className="h-full">
                   <DataChart chart={chartConfig} />
                 </motion.div>
              ) : (
                  <motion.div key="table" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="h-full overflow-hidden">
                      <DataTable data={Array.isArray(tableData) ? tableData : []} />
                  </motion.div>
              )}
           </AnimatePresence>
        </div>
      </motion.div>
    ) : null
  );

  const SQLInfrastructure = () => (
    (data.sql || data.extras?.code) ? (
      <div className="glass-card overflow-hidden group/sql border-border/5 mt-6">
        <button onClick={() => setShowSql(!showSql)} className="w-full flex items-center justify-between px-6 py-4 hover:bg-surface/30 transition-all">
          <div className="flex items-center space-x-3">
              <Terminal className="w-4 h-4 text-emerald-500/70" />
              <span className="text-[10px] font-bold uppercase tracking-[1px] text-text-secondary">SQL Context</span>
          </div>
          <ChevronDown className={cn("w-4 h-4 text-text-secondary transition-transform duration-500", showSql && "rotate-180")} />
        </button>
        
        <AnimatePresence>
          {showSql && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden bg-background/40">
              <div className="px-8 pb-8 pt-2 relative font-mono text-xs">
                <pre className="p-6 glass bg-black/40 rounded-2xl border-border/10 text-emerald-400 overflow-x-auto">
                  {data.sql || data.extras?.code}
                </pre>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    ) : null
  );

  // --- RENDERING STRATEGIES (CONTRACT ALIGNED) ---

  const renderTextCard = () => (
    <div className="w-full space-y-6">
       <div className="glass-card p-8 sm:p-10">
          <KnowledgeCapsule />
          <div className="prose prose-sm dark:prose-invert max-w-none text-text-primary mb-8 font-medium italic opacity-80 border-l-2 border-accent/20 pl-4">
            {mainContent}
          </div>
          <ActionBelt />
       </div>
    </div>
  );

  const renderStepList = () => (
    <div className="w-full space-y-4">
        <div className="glass-card p-8">
            <h3 className="text-sm font-black uppercase tracking-widest text-accent mb-6">Step-by-Step Guide</h3>
            <div className="space-y-6">
                {(data.sections || []).map((step, idx) => (
                    <div key={idx} className="flex items-start space-x-4">
                        <div className="w-6 h-6 rounded-full bg-accent/20 border border-accent/40 flex items-center justify-center text-[10px] font-black text-accent flex-shrink-0">
                            {idx + 1}
                        </div>
                        <div>
                            <h4 className="text-xs font-black text-text-primary uppercase tracking-tight mb-1">{step.heading}</h4>
                            <p className="text-sm text-text-secondary leading-relaxed">{step.body}</p>
                        </div>
                    </div>
                ))}
            </div>
            <ActionBelt />
        </div>
    </div>
  );

  const renderTableView = () => (
    <div className="w-full space-y-6">
        <div className="glass-card p-6">
            <p className="text-sm font-medium text-text-primary mb-4">{mainContent}</p>
            <DataSurface />
            <ActionBelt />
        </div>
    </div>
  );

  const renderMultiSectionCard = () => (
    <div className="w-full space-y-6">
        <div className="glass-card p-8">
            <p className="text-sm font-medium text-text-primary mb-8 leading-relaxed border-b border-border/10 pb-6">{mainContent}</p>
            <SectionList />
            <ActionBelt />
        </div>
    </div>
  );

  const renderMixedRenderer = () => (
    <div className="w-full space-y-6">
       {/* Mixed UI merges all available components intelligently */}
       {data.title && (
            <h3 className="text-lg font-black tracking-tight text-text-primary uppercase mb-2">{data.title}</h3>
       )}
       <div className="glass-card p-8">
          <KnowledgeCapsule />
          <div className="prose prose-sm dark:prose-invert max-w-none text-text-primary mb-6">
            {mainContent}
          </div>
          <ActionBelt />
       </div>
       <SectionList />
       <DataSurface />
       <SQLInfrastructure />
    </div>
  );

  // --- MAIN ADAPTIVE SWITCH ---

  switch (data.type?.toLowerCase()) {
    case 'explanation':
    case 'summary':
      return renderTextCard();
    case 'step_by_step':
      return renderStepList();
    case 'data':
      return renderTableView();
    case 'analysis':
      return renderMultiSectionCard();
    case 'code':
      return (
          <div className="w-full space-y-4">
              <div className="glass-card p-6">
                  <p className="text-sm mb-4">{mainContent}</p>
                  <SQLInfrastructure />
                  <ActionBelt />
              </div>
          </div>
      );
    case 'hybrid':
    default:
      return renderMixedRenderer();
  }
};

