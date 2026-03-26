"use client";

import React, { useState, useMemo } from 'react';
import { 
  Plus, 
  MessageSquare, 
  Settings, 
  Database, 
  BookOpen, 
  Brain,
  ChevronRight,
  Zap,
  LayoutGrid,
  Search,
  MoreVertical,
  Share2,
  UserPlus,
  Edit2,
  Pin,
  Archive,
  Trash2,
  Check,
  X
} from 'lucide-react';
import { useAppStore } from '@/store/useAppStore';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

export const Sidebar = ({ isOpen, onCloseAction }: { isOpen?: boolean; onCloseAction?: () => void }) => {
  const { 
    history, 
    savedKnowledge, 
    schemas, 
    selectedSchemaId, 
    selectSchema,
    currentConversationId,
    loadConversation,
    createNewChat,
    deleteConversation,
    renameConversation,
    updateConversation,
    searchQuery,
    setSearchQuery
  } = useAppStore();
  
  const [activeTab, setActiveTab] = useState<'chats' | 'knowledge'>('chats');
  const [isSchemaOpen, setIsSchemaOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [activeMenu, setActiveMenu] = useState<string | null>(null);

  const selectedSchema = schemas.find(s => s.id === selectedSchemaId);

  const filteredHistory = useMemo(() => {
    return history.filter(h => 
      h.title.toLowerCase().includes(searchQuery.toLowerCase()) && !h.isArchived
    );
  }, [history, searchQuery]);

  const pinnedChats = useMemo(() => filteredHistory.filter(h => h.isPinned), [filteredHistory]);
  const otherChats = useMemo(() => filteredHistory.filter(h => !h.isPinned), [filteredHistory]);

  const handleRename = async (id: string) => {
    if (editTitle.trim()) {
      await renameConversation(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const handleNewChat = () => {
    createNewChat();
    if (window.innerWidth < 1024 && onCloseAction) onCloseAction();
  };

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'n') {
        e.preventDefault();
        handleNewChat();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  React.useEffect(() => {
    const handleClickOutside = () => setActiveMenu(null);
    window.addEventListener('click', handleClickOutside);
    return () => window.removeEventListener('click', handleClickOutside);
  }, []);

  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onCloseAction}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[90] lg:hidden"
          />
        )}
      </AnimatePresence>

      <aside className={cn(
        "fixed inset-y-0 left-0 w-80 h-full flex flex-col flex-shrink-0 z-[100] glass border-r-0 transition-transform duration-500 lg:relative lg:translate-x-0",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
      <div className="absolute inset-y-0 right-0 w-[1px] bg-gradient-to-b from-transparent via-[var(--border)] to-transparent opacity-50" />
      
      {/* Brand Header */}
      <div className="p-8 pb-4">
        <div className="flex items-center space-x-3 mb-8 px-1">
          <div className="relative group">
            <div className="absolute -inset-2 bg-gradient-to-r from-[var(--accent)] to-[#D946EF] rounded-2xl blur-lg opacity-20 group-hover:opacity-40 transition-opacity duration-500" />
            <div className="relative w-10 h-10 bg-surface border border-border/20 rounded-2xl flex items-center justify-center premium-shadow">
              <Brain className="w-5 h-5 text-[var(--accent)]" />
            </div>
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-black tracking-[2px] text-[var(--text-primary)] uppercase">Data AI</span>
            <span className="text-[10px] font-black tracking-[3px] text-[var(--accent)] uppercase opacity-80">Assistant</span>
          </div>
        </div>
        
        <button 
          onClick={handleNewChat}
          className="w-full flex items-center justify-between p-4 bg-surface/40 hover:bg-surface/60 border border-border/10 hover:border-[var(--accent)]/30 rounded-[var(--rounded-premium)] text-[var(--text-primary)] transition-all group active:scale-[0.98] shimmer"
        >
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-xl bg-[var(--accent)]/10 flex items-center justify-center group-hover:bg-[var(--accent)] transition-colors">
              <Plus className="w-4 h-4 text-[var(--accent)] group-hover:text-white transition-colors" />
            </div>
            <span className="text-[10px] font-black uppercase tracking-[2px]">New Chat</span>
          </div>
          <div className="flex items-center space-x-1 px-1.5 py-0.5 bg-background/40 border border-border/20 rounded-md text-[8px] font-black text-text-secondary">
             <span>⌘</span>
             <span>N</span>
          </div>
        </button>
      </div>

      {/* Nav Tabs */}
      <div className="px-8 mt-2">
         <div className="relative group mb-6">
            <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                <Search className="w-3.5 h-3.5 text-text-secondary opacity-40 group-focus-within/input:text-[var(--accent)] transition-colors" />
            </div>
            <input 
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search chats..."
              className="w-full pl-11 pr-4 py-3 bg-surface/30 border border-border/5 focus:border-[var(--accent)]/20 outline-none rounded-2xl text-[10px] font-black uppercase tracking-widest placeholder:text-text-secondary/20 transition-all text-[var(--text-primary)]"
            />
         </div>

        <div className="flex glass bg-surface/30 p-1.5 rounded-[var(--rounded-premium)] relative overflow-hidden">
          <motion.div 
            layoutId="tab-bg"
            className="absolute inset-y-1.5 bg-[var(--accent)]/10 border border-[var(--accent)]/20 rounded-xl"
            style={{ 
              left: activeTab === 'chats' ? '6px' : '52%',
              right: activeTab === 'chats' ? '52%' : '6px'
            }}
            transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
          />
          <button 
            onClick={() => setActiveTab('chats')}
            className={cn(
              "flex-1 relative z-10 flex items-center justify-center space-x-2 py-2.5 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all",
              activeTab === 'chats' ? "text-[var(--accent)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            )}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Chats</span>
          </button>
          <button 
            onClick={() => setActiveTab('knowledge')}
            className={cn(
              "flex-1 relative z-10 flex items-center justify-center space-x-2 py-2.5 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all",
              activeTab === 'knowledge' ? "text-[var(--accent)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            )}
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Library</span>
          </button>
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto px-6 space-y-8 custom-scrollbar pb-8 mt-6">
        {/* Schema Status */}
        <div className="space-y-3">
          <div className="flex items-center justify-between px-2">
            <span className="text-[9px] font-black text-text-secondary uppercase tracking-[3px]">Data Sources</span>
            <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
          </div>
          
          <div className="relative group">
            <button 
                onClick={() => setIsSchemaOpen(!isSchemaOpen)}
                className="w-full flex items-center justify-between p-4 bg-surface/20 hover:bg-surface/40 border border-border/10 rounded-2xl transition-all group-hover:border-[var(--accent)]/20"
            >
                <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-lg bg-surface flex items-center justify-center border border-border/10">
                      <Database className={cn("w-3.5 h-3.5 transition-colors", isSchemaOpen ? "text-[var(--accent)]" : "text-text-secondary")} />
                    </div>
                    <div className="text-left">
                      <p className="text-[10px] font-black text-[var(--text-primary)] uppercase tracking-widest">{selectedSchema?.name}</p>
                      <p className="text-[8px] font-black text-text-secondary uppercase tracking-[1px]">{selectedSchema?.tables.length} Active Tables</p>
                    </div>
                </div>
                <ChevronRight className={cn("w-3 h-3 text-text-secondary transition-transform", isSchemaOpen && "rotate-90")} />
            </button>
            <AnimatePresence>
                {isSchemaOpen && (
                    <motion.div 
                       initial={{ opacity: 0, y: -10 }} 
                       animate={{ opacity: 1, y: 0 }} 
                       exit={{ opacity: 0, y: -10 }} 
                       className="absolute left-0 right-0 top-full mt-2 glass-card p-1.5 z-[100] shadow-2xl overflow-hidden"
                    >
                        {schemas.map(s => (
                            <button 
                              key={s.id} 
                              onClick={() => { selectSchema(s.id); setIsSchemaOpen(false); }} 
                              className={cn(
                                "w-full p-3 rounded-xl text-left transition-all", 
                                selectedSchemaId === s.id ? "bg-[var(--accent)] text-white" : "hover:bg-surface"
                              )}
                            >
                                <p className="text-[10px] font-black uppercase tracking-widest">{s.name}</p>
                                <p className={cn("text-[8px] font-bold uppercase tracking-[1px]", selectedSchemaId === s.id ? "text-white/70" : "text-text-secondary")}>
                                  Connected
                                </p>
                            </button>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
          </div>
        </div>

        {/* Dynamic Lists */}
        <div className="space-y-4">
          <div className="flex items-center justify-between px-2">
            <span className="text-[9px] font-black text-text-secondary uppercase tracking-[3px]">
              {activeTab === 'chats' ? 'History' : 'Saved'}
            </span>
            <LayoutGrid className="w-3 h-3 text-text-secondary opacity-40" />
          </div>

          <div className="space-y-1">
            {activeTab === 'chats' ? (
              <>
                {/* Pinned Chats */}
                {pinnedChats.map((item) => (
                  <ChatListItem 
                    key={item.id} 
                    item={item} 
                    isActive={currentConversationId === item.id} 
                    onSelect={() => loadConversation(item.id)}
                    editingId={editingId}
                    editTitle={editTitle}
                    setEditTitle={setEditTitle}
                    setEditingId={setEditingId}
                    handleRename={handleRename}
                    deleteConversation={deleteConversation}
                    activeMenu={activeMenu}
                    setActiveMenu={setActiveMenu}
                    updateConversation={updateConversation}
                  />
                ))}
                
                {/* Other Chats */}
                {otherChats.map((item) => (
                  <ChatListItem 
                    key={item.id} 
                    item={item} 
                    isActive={currentConversationId === item.id} 
                    onSelect={() => loadConversation(item.id)}
                    editingId={editingId}
                    editTitle={editTitle}
                    setEditTitle={setEditTitle}
                    setEditingId={setEditingId}
                    handleRename={handleRename}
                    deleteConversation={deleteConversation}
                    activeMenu={activeMenu}
                    setActiveMenu={setActiveMenu}
                    updateConversation={updateConversation}
                  />
                ))}
              </>
            ) : (
              savedKnowledge.map((item) => (
                <div key={item.id} className="p-4 bg-surface/20 border border-border/10 rounded-2xl hover:border-[var(--accent)]/40 transition-all cursor-pointer group hover:bg-surface/40">
                    <div className="flex items-center space-x-2 mb-2">
                      <Zap className="w-3 h-3 text-[var(--accent)]" />
                      <p className="text-[10px] font-black text-[var(--text-primary)] uppercase truncate">{item.title}</p>
                    </div>
                    <p className="text-[9px] text-text-secondary line-clamp-2 leading-relaxed opacity-70 group-hover:opacity-100">{item.content}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Footer Profile */}
      <div className="p-6 mt-auto">
        <div className="glass-card p-4 border-[var(--border)] group cursor-pointer hover:bg-surface/40 transition-all">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <div className="absolute inset-0 bg-[var(--accent)] rounded-xl blur-md opacity-20 group-hover:opacity-40 transition-opacity" />
              <div className="relative w-10 h-10 rounded-xl bg-surface border border-border/10 flex items-center justify-center overflow-hidden">
                <span className="text-xs font-black text-[var(--accent)]">AD</span>
              </div>
            </div>
            <div className="flex-1">
              <p className="text-[10px] font-black text-[var(--text-primary)] uppercase tracking-wider">User Profile</p>
              <p className="text-[8px] font-black text-[var(--accent)] uppercase tracking-widest opacity-80">Pro Account</p>
            </div>
            <Settings className="w-3.5 h-3.5 text-text-secondary group-hover:text-[var(--accent)] group-hover:rotate-90 transition-all duration-500" />
          </div>
        </div>
      </div>
    </aside>
    </>
  );
};

const ChatListItem = ({ 
  item, 
  isActive, 
  onSelect,
  editingId,
  editTitle,
  setEditTitle,
  setEditingId,
  handleRename,
  deleteConversation,
  activeMenu,
  setActiveMenu,
  updateConversation
}: any) => {
  return (
    <div className="relative group/item">
      {editingId === item.id ? (
        <div className="w-full flex items-center space-x-3 p-3.5 rounded-2xl bg-surface border border-[var(--accent)]/30">
          <input 
            autoFocus
            value={editTitle}
            onChange={(e) => setEditTitle(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleRename(item.id);
              if (e.key === 'Escape') setEditingId(null);
            }}
            className="flex-1 bg-transparent outline-none text-[11px] font-bold text-[var(--text-primary)]"
          />
          <div className="flex items-center space-x-2">
            <button onClick={() => handleRename(item.id)} className="text-emerald-500 hover:scale-110 transition-transform"><Check className="w-3.5 h-3.5" /></button>
            <button onClick={() => setEditingId(null)} className="text-rose-500 hover:scale-110 transition-transform"><X className="w-3.5 h-3.5" /></button>
          </div>
        </div>
      ) : (
        <button
          onClick={onSelect}
          className={cn(
            "w-full flex items-center space-x-3 p-3.5 rounded-2xl transition-all group/btn text-left relative overflow-hidden",
            isActive ? "bg-[var(--accent)]/10 border-[var(--accent)]/20 shadow-lg shadow-[var(--accent)]/5" : "hover:bg-surface/50 border border-transparent hover:border-border/10"
          )}
        >
          {item.isPinned && <Pin className="absolute top-2 right-2 w-2.5 h-2.5 text-[var(--accent)] opacity-60" />}
          <div className={cn(
            "w-1.5 h-1.5 rounded-full transition-colors absolute left-0",
            isActive ? "bg-[var(--accent)]" : "bg-zinc-700 group-hover/btn:bg-[var(--accent)]"
          )} />
          <div className="flex-1 truncate pl-2">
            <p className={cn(
              "text-[11px] font-bold truncate transition-colors",
              isActive ? "text-[var(--text-primary)]" : "text-text-secondary group-hover/btn:text-[var(--text-primary)]"
            )}>{item.title}</p>
            <p className={cn(
              "text-[8px] font-black uppercase tracking-widest transition-colors",
              isActive ? "text-[var(--accent)]" : "text-text-secondary/60 group-hover/btn:text-[var(--accent)]"
            )}>{item.timestamp}</p>
          </div>
          
          <div className="relative">
            <button 
              onClick={(e) => {
                e.stopPropagation();
                setActiveMenu(activeMenu === item.id ? null : item.id);
              }}
              className="p-1 rounded-lg hover:bg-surface opacity-0 group-hover/item:opacity-100 transition-all"
            >
              <MoreVertical className="w-3.5 h-3.5 text-text-secondary" />
            </button>
            
            <AnimatePresence>
                {activeMenu === item.id && (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.95, y: 10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 10 }}
                    className="absolute right-0 top-full mt-2 w-48 bg-surface border border-border/10 rounded-2xl shadow-2xl z-[150] p-1.5 overflow-hidden glass"
                  >
                    <MenuButton icon={Share2} label="Share" onClick={() => {}} />
                    <MenuButton icon={UserPlus} label="Start group chat" onClick={() => {}} />
                    <MenuButton icon={Edit2} label="Rename" onClick={() => { setEditingId(item.id); setEditTitle(item.title); setActiveMenu(null); }} />
                    <div className="h-[1px] bg-border/5 my-1" />
                    <MenuButton icon={Pin} label={item.isPinned ? "Unpin chat" : "Pin chat"} onClick={() => updateConversation(item.id, { isPinned: !item.isPinned })} />
                    <MenuButton icon={Archive} label="Archive" onClick={() => updateConversation(item.id, { isArchived: true })} />
                    <MenuButton icon={Trash2} label="Delete" color="text-rose-500" onClick={() => deleteConversation(item.id)} />
                  </motion.div>
                )}
            </AnimatePresence>
          </div>
        </button>
      )}
    </div>
  );
};

const MenuButton = ({ icon: Icon, label, onClick, color = "text-text-secondary" }: any) => (
  <button 
    onClick={(e) => { e.stopPropagation(); onClick(); }}
    className={cn(
      "w-full flex items-center space-x-3 p-2.5 rounded-xl hover:bg-white/5 transition-all text-left group/menu",
      color
    )}
  >
    <Icon className="w-3.5 h-3.5 transition-colors group-hover/menu:text-[var(--accent)]" />
    <span className="text-[10px] font-black uppercase tracking-widest">{label}</span>
  </button>
);
;

