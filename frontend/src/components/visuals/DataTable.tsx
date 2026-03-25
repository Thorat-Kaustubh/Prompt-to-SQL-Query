import React from 'react';
import { cn } from '@/lib/utils';

interface DataTableProps {
  data: any[];
}

export const DataTable = ({ data }: DataTableProps) => {
  if (!data || data.length === 0) return (
    <div className="p-8 text-center text-text-secondary font-bold uppercase tracking-widest text-xs">No data available</div>
  );

  const columns = Object.keys(data[0]);

  return (
    <div className="w-full h-full overflow-hidden flex flex-col bg-background-secondary shadow-2xl rounded-xl border border-border/20">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse min-w-full divide-y divide-border/20">
          <thead className="bg-surface/50 border-b border-border/20 text-[10px] uppercase font-black text-text-secondary tracking-[2px]">
            <tr>
              {columns.map((col) => (
                <th key={col} className="px-6 py-4 font-black whitespace-nowrap">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border/10">
            {data.map((row, i) => (
              <tr 
                key={i} 
                className="hover:bg-accent/5 transition-colors group cursor-default"
              >
                {columns.map((col) => (
                  <td key={col} className={cn(
                    "px-6 py-4 text-sm font-bold transition-all truncate max-w-[200px]",
                    typeof row[col] === 'number' ? "text-accent font-black text-right" : "text-text-primary"
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
      
      {/* Table Footer / Summary */}
      <div className="px-6 py-3 bg-surface/20 flex items-center justify-between">
         <span className="text-[10px] font-black uppercase text-text-secondary tracking-widest">
           Showing {data.length} records
         </span>
         <div className="flex bg-background-secondary border border-border/40 rounded-lg p-0.5">
           <button className="px-3 py-1 font-bold text-[10px] uppercase text-text-secondary hover:text-accent transition-colors">Export CSV</button>
           <div className="w-[1px] h-3 bg-border/40 self-center" />
           <button className="px-3 py-1 font-bold text-[10px] uppercase text-text-secondary hover:text-accent transition-colors">JSON</button>
         </div>
      </div>
    </div>
  );
};
