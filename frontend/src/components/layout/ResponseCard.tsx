import React, { useState } from 'react';
import { 
  ChevronDown, 
  ChevronUp, 
  Database, 
  Table as TableIcon, 
  BarChart2, 
  PieChart as PieChartIcon, 
  LineChart as LineChartIcon,
  Code2, 
  Copy, 
  Check, 
  Download,
  Maximize2,
  Minimize2,
  Sparkles,
  Zap,
  LayoutGrid
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { DataChart } from '@/components/visuals/DataChart';
import { DataTable } from '@/components/visuals/DataTable';
import { motion, AnimatePresence } from 'framer-motion';

interface ResponseCardProps {
  data: {
    table?: any[];
    chart?: any;
    sql?: string;
    insights?: string[];
  };
}

export const ResponseCard = ({ data }: ResponseCardProps) => {
  const [activeTab, setActiveTab] = useState<'chart' | 'table' | 'sql'>(
    data.chart ? 'chart' : 'table'
  );
  const [isExpanded, setIsExpanded] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  const copySQL = () => {
    if (data.sql) {
      navigator.clipboard.writeText(data.sql);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    }
  };

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className={cn(
        "w-full bg-background-secondary border border-border/60 rounded-2xl shadow-xl shadow-black/5 overflow-hidden ring-1 ring-black/[0.03] flex flex-col transition-all duration-300",
        isExpanded ? "fixed inset-8 z-50 rounded-3xl h-[calc(100vh-64px)]" : "relative h-fit"
      )}
    >
      {/* Dynamic Background Effects */}
      <div className="absolute top-0 right-0 p-12 -mt-12 -mr-12 bg-accent/5 rounded-full blur-3xl opacity-20 pointer-events-none" />
      <div className="absolute bottom-0 left-0 p-12 -mb-12 -ml-12 bg-accent/5 rounded-full blur-3xl opacity-20 pointer-events-none" />

      {/* Header */}
      <div className="px-6 py-4 flex items-center justify-between border-b border-border/20 z-10">
        <div className="flex items-center space-x-4">
          <div className="p-2 bg-accent/10 border border-accent/20 rounded-xl">
             <LayoutGrid className="w-5 h-5 text-accent" />
          </div>
          <div className="flex bg-surface/50 border border-border/40 p-1 rounded-xl">
             {[
               { id: 'chart', icon: <BarChart2 className="w-4 h-4" />, label: 'Chart' },
               { id: 'table', icon: <TableIcon className="w-4 h-4" />, label: 'Table' },
               { id: 'sql', icon: <Code2 className="w-4 h-4" />, label: 'SQL' }
             ].filter(tab => tab.id !== 'chart' || data.chart).map(tab => (
               <button
                 key={tab.id}
                 onClick={() => setActiveTab(tab.id as any)}
                 className={cn(
                   "flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-black uppercase tracking-widest transition-all",
                   activeTab === tab.id 
                    ? "bg-background-secondary text-accent border border-border shadow-sm shadow-black/5" 
                    : "text-text-secondary hover:text-text-primary"
                 )}
               >
                 {tab.icon}
                 <span>{tab.label}</span>
               </button>
             ))}
          </div>
        </div>

        <div className="flex items-center space-x-2">
           <button 
             onClick={() => setIsExpanded(!isExpanded)}
             className="p-2 hover:bg-surface border border-transparent hover:border-border/40 rounded-lg text-text-secondary transition-all"
           >
             {isExpanded ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
           </button>
           <button className="p-2 hover:bg-surface border border-transparent hover:border-border/40 rounded-lg text-text-secondary transition-all">
             <Download className="w-5 h-5" />
           </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto bg-surface/10 p-6 z-10">
        <AnimatePresence mode="wait">
          {activeTab === 'chart' && (
            <motion.div
              key="chart"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              className="w-full h-[350px]"
            >
              <DataChart chart={data.chart} />
            </motion.div>
          )}

          {activeTab === 'table' && (
            <motion.div
              key="table"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              className="w-full overflow-hidden border border-border/40 rounded-xl"
            >
              <DataTable data={data.table || []} />
            </motion.div>
          )}

          {activeTab === 'sql' && (
            <motion.div
              key="sql"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              className="relative w-full rounded-xl bg-[#0d1117] p-6 border border-border/30 shadow-2xl overflow-hidden font-mono text-sm leading-8 select-all"
            >
               <div className="absolute top-0 left-0 right-0 h-10 px-4 bg-white/[0.03] border-b border-white/[0.05] flex items-center justify-between">
                 <div className="flex items-center space-x-2">
                   <Database className="w-4 h-4 text-accent/80" />
                   <span className="text-[10px] uppercase font-bold text-white/40 tracking-[2px]">PostgreSQL Terminal</span>
                 </div>
                 <button 
                   onClick={copySQL}
                   className="p-1.5 hover:bg-white/5 rounded-md transition-all group"
                 >
                   {isCopied ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4 text-white/40 group-hover:text-white" />}
                 </button>
               </div>
               <div className="mt-8 overflow-x-auto whitespace-pre">
                 <span className="text-pink-400">SELECT</span> <span className="text-blue-300">{data.sql?.split('SELECT ')[1]?.split(' FROM')[0]}</span><br/>
                 <span className="text-pink-400">FROM</span> <span className="text-orange-300">{data.sql?.split('FROM ')[1]?.split(' ')[0]}</span><br/>
                 {data.sql?.includes('WHERE') && (
                   <><span className="text-pink-400">WHERE</span> <span className="text-blue-300">{data.sql?.split('WHERE ')[1]?.split(' GROUP')[0]}</span><br/></>
                 )}
                 {data.sql?.includes('GROUP BY') && (
                   <><span className="text-pink-400">GROUP BY</span> <span className="text-blue-300">{data.sql?.split('GROUP BY ')[1]}</span></>
                 )}
               </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Insights Footer */}
      {data.insights && data.insights.length > 0 && (
        <div className="px-8 py-6 bg-background-secondary border-t border-border/30">
           <div className="flex items-center space-x-3 mb-4 text-accent">
             <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
             <h4 className="text-xs uppercase font-black tracking-widest">Autonomous Insights</h4>
           </div>
           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
             {data.insights.map((insight, i) => (
               <div key={i} className="flex items-start space-x-3 p-3 bg-surface/40 border border-border/20 rounded-xl hover:bg-accent/5 transition-colors group">
                 <Sparkles className="w-4 h-4 mt-0.5 text-accent/40 group-hover:text-accent transform group-hover:scale-110 transition-all" />
                 <p className="text-[13px] font-medium text-text-secondary group-hover:text-text-primary transition-colors leading-relaxed leading-[1.6]">{insight}</p>
               </div>
             ))}
           </div>
        </div>
      )}
    </motion.div>
  );
};
