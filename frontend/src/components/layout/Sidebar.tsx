import { 
  Plus, 
  MessageSquare, 
  Settings, 
  LogOut, 
  BarChart2, 
  History,
  Info
} from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { cn } from '@/lib/utils';

export const Sidebar = () => {
  const { history, clearHistory } = useAppStore();

  return (
    <aside className="w-72 h-full bg-background-secondary border-r border-border flex flex-col transition-all duration-300">
      {/* Branding */}
      <div className="p-6 flex items-center space-x-3 group">
        <div className="w-10 h-10 bg-accent rounded-xl flex items-center justify-center shadow-lg transform group-hover:scale-110 transition-transform">
          <BarChart2 className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-extrabold tracking-tight">
            Data<span className="text-accent italic font-black">AI</span>
          </h1>
          <p className="text-[10px] text-text-secondary uppercase tracking-widest font-bold">BI ORCHESTRATOR</p>
        </div>
      </div>

      {/* New Conversation Button */}
      <div className="px-4 mb-6">
        <button
          onClick={clearHistory}
          className="w-full h-12 flex items-center justify-center space-x-2 bg-accent/10 border border-accent/20 text-accent rounded-xl hover:bg-accent/20 transition-all group"
        >
          <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform" />
          <span className="font-bold">New Query</span>
        </button>
      </div>

      {/* History Items */}
      <div className="flex-1 overflow-y-auto px-4 space-y-2 scrollbar-hide">
        <div className="flex items-center space-x-2 text-xs font-bold text-text-secondary mb-3 uppercase tracking-widest pl-2">
          <History className="w-3.5 h-3.5" />
          <span>Recent Activity</span>
        </div>
        {history.map((item) => (
          <button
            key={item.id}
            className="w-full p-3 flex items-start space-x-3 rounded-xl hover:bg-surface border border-transparent hover:border-border/30 transition-all text-left group"
          >
            <MessageSquare className="w-4 h-4 mt-1 text-text-secondary group-hover:text-accent" />
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-semibold truncate text-text-primary group-hover:text-accent transition-colors">
                {item.title}
              </p>
              <p className="text-[10px] text-text-secondary font-medium">
                {item.timestamp}
              </p>
            </div>
          </button>
        ))}
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-border mt-auto space-y-1">
        <button className="w-full p-3 flex items-center space-x-3 rounded-xl hover:bg-surface transition-colors">
          <Settings className="w-4 h-4 text-text-secondary" />
          <span className="text-sm font-bold">Settings</span>
        </button>
        <button className="w-full p-3 flex items-center space-x-3 rounded-xl hover:bg-surface transition-colors">
          <Info className="w-4 h-4 text-text-secondary" />
          <span className="text-sm font-bold">Help & Feedback</span>
        </button>
      </div>
    </aside>
  );
};
