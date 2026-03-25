import { create } from 'zustand'

export type MessageType = 'user' | 'assistant'

export interface Message {
  id: string
  role: MessageType
  content: string
  timestamp: string
  data?: {
    table?: any[]
    chart?: any
    sql?: string
    insights?: string[]
  }
}

export interface HistoryItem {
  id: string
  title: string
  timestamp: string
}

interface AppState {
  theme: 'dark' | 'light'
  messages: Message[]
  history: HistoryItem[]
  isLoading: boolean
  loadingStep: string
  error: string | null
  
  setTheme: (theme: 'dark' | 'light') => void
  toggleTheme: () => void
  addMessage: (message: Message) => void
  setLoading: (loading: boolean, step?: string) => void
  setError: (error: string | null) => void
  clearHistory: () => void
  loadConversation: (id: string) => void
}

export const useAppStore = create<AppState>((set) => ({
  theme: (localStorage.getItem('theme') as 'dark' | 'light') || 'dark', // Default to Dark
  messages: [],
  history: [
    { id: '1', title: 'Sales in Q4 2025', timestamp: '2 hours ago' },
    { id: '2', title: 'Top 5 customers in NY', timestamp: 'Yesterday' },
    { id: '3', title: 'Growth trend by month', timestamp: '3 days ago' },
  ],
  isLoading: false,
  loadingStep: '',
  error: null,

  setTheme: (theme) => {
    set({ theme })
    localStorage.setItem('theme', theme)
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  },

  toggleTheme: () => {
    set((state) => {
      const next = state.theme === 'dark' ? 'light' : 'dark'
      localStorage.setItem('theme', next)
      if (next === 'dark') {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
      return { theme: next }
    })
  },

  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages, message],
    history: message.role === 'user' ? 
      [{ id: Date.now().toString(), title: message.content, timestamp: 'Just now' }, ...state.history].slice(0, 15) : 
      state.history
  })),

  setLoading: (isLoading, loadingStep = '') => set({ isLoading, loadingStep }),
  setError: (error) => set({ error }),
  clearHistory: () => set({ messages: [] }),
  loadConversation: (id) => {
    // In a real app, this would fetch from an API
    console.log(`Loading conversation: ${id}`)
  }
}))
