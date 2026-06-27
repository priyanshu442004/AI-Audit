import { create } from 'zustand'

const THEME_KEY = 'theme'
const THEMES = new Set(['light', 'dark'])

const getInitialTheme = () => {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem(THEME_KEY)
    return THEMES.has(saved) ? saved : 'light'
  }
  return 'light'
}

const applyTheme = (theme) => {
  if (typeof document === 'undefined') return
  document.documentElement.classList.toggle('dark', theme === 'dark')
  document.documentElement.dataset.theme = theme
  document.documentElement.style.colorScheme = theme
}

export const useStore = create((set, get) => ({
  // App state
  page: 'upload',      // 'upload' | 'loading' | 'dashboard'
  sessionId: null,
  results: null,
  showUploadModal: false,
  priceVarianceSame: null,
  priceVarianceCross: null,

  // Loading progress
  progress: { pct: 0, message: 'Preparing data…', stage: '' },

  // Theme
  theme: getInitialTheme(),

  // Active dashboard section
  activeSection: 'cover',

  // Actions
  setPage: (page) => set({ page }),
  setSessionId: (id) => set({ sessionId: id }),
  setResults: (r) => set({ results: r, priceVarianceSame: null, priceVarianceCross: null }),
  setProgress: (p) => set({ progress: p }),
  setActiveSection: (s) => set({ activeSection: s }),
  setShowUploadModal: (show) => set({ showUploadModal: show }),
  setPriceVarianceSame: (data) => set({ priceVarianceSame: data }),
  setPriceVarianceCross: (data) => set({ priceVarianceCross: data }),

  setTheme: (theme) => {
    const next = THEMES.has(theme) ? theme : 'light'
    if (typeof window !== 'undefined') {
      localStorage.setItem(THEME_KEY, next)
    }
    applyTheme(next)
    set({ theme: next })
  },

  toggleTheme: () => get().setTheme(get().theme === 'dark' ? 'light' : 'dark'),

  initTheme: () => {
    const theme = getInitialTheme()
    applyTheme(theme)
    set({ theme })
  },
}))
