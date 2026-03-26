"use client";

import React from 'react';
import { cn } from '@/lib/utils';
import { FileDown, Table as TableIcon } from 'lucide-react';

interface DataTableProps {
  data: any[];
}

export const DataTable = ({ data }: DataTableProps) => {
  if (!data || data.length === 0) return (
    <div className="h-full flex flex-col items-center justify-center space-y-4 opacity-30">
        <TableIcon className="w-12 h-12" />
        <p className="text-[10px] font-black uppercase tracking-[4px]">No Data Available</p>
    </div>
  );

  const columns = Object.keys(data[0]);

  return (
    <div className="w-full h-full flex flex-col glass rounded-2xl border-border/10 overflow-hidden group/table shadow-2xl">
      <div className="flex-1 overflow-auto custom-scrollbar">
        <table className="w-full text-left border-collapse min-w-full">
          <thead>
            <tr className="sticky top-0 z-20 bg-surface border-b border-border/10 backdrop-blur-xl">
              {columns.map((col) => (
                <th key={col} className="px-8 py-5 text-[10px] uppercase font-black text-text-secondary tracking-[2px] whitespace-nowrap bg-surface/80">
                  <div className="flex items-center space-x-2">
                    <div className="w-1 h-3 bg-[var(--accent)]/30 rounded-full" />
                    <span>{col}</span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border/5">
            {data.map((row, i) => (
              <tr 
                key={i} 
                className="hover:bg-[var(--accent)]/5 transition-all duration-300 group cursor-default"
              >
                {columns.map((col) => (
                  <td key={col} className={cn(
                    "px-8 py-4 text-[13px] font-bold transition-all truncate max-w-[250px]",
                    typeof row[col] === 'number' ? "text-[var(--accent)] font-medium tabular-nums" : "text-[var(--text-primary)]"
                  )}>
                    {typeof row[col] === 'number' 
                      ? row[col].toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })
                      : String(row[col])
                    }
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Table Action Bar */}
      <div className="px-8 py-4 bg-surface/30 border-t border-border/10 flex items-center justify-between">
         <div className="flex items-center space-x-4">
           <span className="text-[9px] font-black uppercase text-text-secondary tracking-[2px]">
             Collection Size: {data.length} Vectors
           </span>
         </div>
         <div className="flex glass bg-background/40 border border-border/20 rounded-xl overflow-hidden">
           <button className="px-4 py-2 flex items-center space-x-2 text-[9px] font-black uppercase tracking-[1px] text-text-secondary hover:bg-surface hover:text-[var(--accent)] transition-all">
             <FileDown className="w-3 h-3" />
             <span>Export Engine</span>
           </button>
         </div>
      </div>
    </div>
  );
};

