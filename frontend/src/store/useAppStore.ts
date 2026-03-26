import { create } from 'zustand'

export type MessageType = 'user' | 'assistant'
export type Intent = 'GENERAL' | 'DATA' | 'HYBRID'

export interface Message {
  id: string
  role: MessageType
  content: string
  timestamp: string
  intent?: Intent
  data?: {
    type?: string
    title?: string
    sections?: { title?: string; heading?: string; content?: string; body?: string }[]
    actions?: string[]
    table?: any[]
    chart?: any
    sql?: string
    insights?: string[]
    examples?: { title: string; description: string; sql: string }[]
    error?: string
    meta?: any
  }
}

export interface HistoryItem {
  id: string
  title: string
  timestamp: string
  isPinned?: boolean
  isArchived?: boolean
}

export interface KnowledgeItem {
  id: string
  title: string
  content: string
  tags: string[]
  timestamp: string
}

export interface Schema {
  id: string
  name: string
  tables: string[]
}

interface AppState {
  theme: 'dark' | 'light'
  messages: Message[]
  history: HistoryItem[]
  searchQuery: string
  currentConversationId: string | null
  savedKnowledge: KnowledgeItem[]
  schemas: Schema[]
  selectedSchemaId: string
  isLoading: boolean
  loadingStep: string
  error: string | null
  showThinking: boolean
  user: {
    name: string
    email: string
    avatar: string
  }
  
  setTheme: (theme: 'dark' | 'light') => void
  toggleTheme: () => void
  addMessage: (message: Message) => void
  updateMessage: (id: string, updates: Partial<Message>) => void
  setLoading: (loading: boolean, step?: string) => void
  setError: (error: string | null) => void
  setShowThinking: (show: boolean) => void
  setSearchQuery: (query: string) => void
  clearHistory: () => void
  fetchHistory: () => Promise<void>
  loadConversation: (id: string) => Promise<void>
  setCurrentConversationId: (id: string | null) => void
  createNewChat: () => void
  deleteConversation: (id: string) => Promise<void>
  renameConversation: (id: string, newTitle: string) => Promise<void>
  updateConversation: (id: string, updates: Partial<HistoryItem>) => Promise<void>
  saveToKnowledge: (item: Omit<KnowledgeItem, 'id' | 'timestamp'>) => void
  selectSchema: (id: string) => void
}

export const API_BASE = 'http://127.0.0.1:8000'
export const AUTH_TOKEN = 'Bearer local-dev-token'

export const useAppStore = create<AppState>((set, get) => ({
  theme: 'dark', 
  messages: [],
  history: [],
  searchQuery: '',
  currentConversationId: null,
  savedKnowledge: [],
  schemas: [
    { id: 'public', name: 'Public Analytics', tables: ['users', 'products', 'categories'] }
  ],
  selectedSchemaId: 'public',
  isLoading: false,
  loadingStep: '',
  error: null,
  showThinking: true,
  user: {
    name: 'Kaustubh Thorat',
    email: 'thorat.kaustubh@example.com',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Kaustubh'
  },

  setTheme: (theme) => {
    set({ theme })
    localStorage.setItem('theme', theme)
    if (theme === 'dark') document.documentElement.classList.add('dark')
    else document.documentElement.classList.remove('dark')
  },

  toggleTheme: () => {
    set((state) => {
      const next = state.theme === 'dark' ? 'light' : 'dark'
      localStorage.setItem('theme', next)
      if (next === 'dark') document.documentElement.classList.add('dark')
      else document.documentElement.classList.remove('dark')
      return { theme: next }
    })
  },

  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages, message],
  })),

  updateMessage: (id, updates) => set((state) => ({
    messages: state.messages.map(m => m.id === id ? { ...m, ...updates } : m)
  })),

  setCurrentConversationId: (id) => set({ currentConversationId: id }),

  setSearchQuery: (searchQuery) => set({ searchQuery }),

  setLoading: (isLoading, loadingStep = '') => set({ isLoading, loadingStep }),
  setError: (error) => set({ error }),
  setShowThinking: (showThinking) => set({ showThinking }),
  
  createNewChat: () => set({ messages: [], currentConversationId: null }),

  fetchHistory: async () => {
    try {
      const res = await fetch(`${API_BASE}/history/conversations`, {
        headers: { 'Authorization': AUTH_TOKEN }
      })
      const data = await res.json()
      set({ history: data.map((c: any) => ({
        id: c.id,
        title: c.title,
        timestamp: new Date(c.last_message_at).toLocaleDateString(),
        isPinned: c.is_pinned,
        isArchived: c.is_archived
      }))})
    } catch (e) {
      console.error('Failed to fetch history', e)
    }
  },

  loadConversation: async (id) => {
    set({ isLoading: true, loadingStep: 'Loading conversation...', currentConversationId: id })
    try {
      const res = await fetch(`${API_BASE}/history/conversations/${id}/messages`, {
        headers: { 'Authorization': AUTH_TOKEN }
      })
      const rawMessages = await res.json()
      const formatted: Message[] = rawMessages.map((m: any) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        timestamp: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        data: m.data
      }))
      set({ messages: formatted, isLoading: false })
    } catch (e) {
      set({ error: 'Failed to load conversation', isLoading: false })
    }
  },

  deleteConversation: async (id) => {
    try {
      await fetch(`${API_BASE}/history/conversations/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': AUTH_TOKEN }
      })
      set((state) => ({
        history: state.history.filter(h => h.id !== id),
        currentConversationId: state.currentConversationId === id ? null : state.currentConversationId,
        messages: state.currentConversationId === id ? [] : state.messages
      }))
    } catch (e) {
      console.error('Failed to delete conversation', e)
    }
  },

  renameConversation: async (id, newTitle) => {
     await get().updateConversation(id, { title: newTitle });
  },

  updateConversation: async (id, updates) => {
    try {
      const snakeCaseUpdates = {
        title: updates.title,
        is_pinned: updates.isPinned,
        is_archived: updates.isArchived
      }
      
      await fetch(`${API_BASE}/history/conversations/${id}`, {
        method: 'PATCH',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': AUTH_TOKEN 
        },
        body: JSON.stringify(snakeCaseUpdates)
      })
      
      set((state) => ({
        history: state.history.map(h => h.id === id ? { ...h, ...updates } : h)
      }))
    } catch (e) {
      console.error('Failed to update conversation', e)
    }
  },
  
  clearHistory: () => set({ messages: [], currentConversationId: null }),
  
  saveToKnowledge: (item) => set((state) => ({
    savedKnowledge: [{ ...item, id: Date.now().toString(), timestamp: 'Just now' }, ...state.savedKnowledge]
  })),
  
  selectSchema: (id) => set({ selectedSchemaId: id })
}))
