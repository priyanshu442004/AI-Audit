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
  // Auth state
  user: (() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('user')
        return saved ? JSON.parse(saved) : null
      } catch (e) {
        return null
      }
    }
    return null
  })(),
  loginError: null,

  // App state
  page: 'upload',      // 'upload' | 'loading' | 'dashboard'
  sessionId: null,
  results: null,
  showUploadModal: false,
  priceVarianceSame: null,
  priceVarianceCross: null,
  paymentAgingDomestic: null,
  paymentAgingForeign: null,
  paymentAgingRelated: null,
  paymentAgingMsme: null,
  vendorMasterNew: null,
  threeWayMatching: null,
  backgroundStates: {},

  // Loading progress
  progress: { pct: 0, message: 'Preparing data…', stage: '' },

  // Theme
  theme: getInitialTheme(),

  // Active dashboard section
  activeSection: 'dashboard',

  // Actions
  login: (email, password) => {
    if (email === 'admin@ikio.com' && password === 'admin') {
      const userData = { email, role: 'admin' }
      if (typeof window !== 'undefined') {
        localStorage.setItem('user', JSON.stringify(userData))
      }
      set({ user: userData, loginError: null })
      return true
    } else {
      set({ loginError: 'Invalid email or password.' })
      return false
    }
  },
  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('user')
    }
    set({ user: null, loginError: null, page: 'upload', results: null })
  },

  setPage: (page) => set({ page }),
  setSessionId: (id) => set({ sessionId: id }),
  setResults: (r) => set({ results: r, priceVarianceSame: null, priceVarianceCross: null, paymentAgingDomestic: null, paymentAgingForeign: null, paymentAgingRelated: null, paymentAgingMsme: null, vendorMasterNew: null, threeWayMatching: null, backgroundStates: {} }),
  setBackgroundState: (key, state) => set((s) => ({ backgroundStates: { ...s.backgroundStates, [key]: state } })),
  setProgress: (p) => set({ progress: p }),
  setActiveSection: (s) => set({ activeSection: s }),
  setShowUploadModal: (show) => set({ showUploadModal: show }),
  setPriceVarianceSame: (data) => set({ priceVarianceSame: data }),
  setPriceVarianceCross: (data) => set({ priceVarianceCross: data }),
  setPaymentAgingDomestic: (data) => set({ paymentAgingDomestic: data }),
  setPaymentAgingForeign: (data) => set({ paymentAgingForeign: data }),
  setPaymentAgingRelated: (data) => set({ paymentAgingRelated: data }),
  setPaymentAgingMsme: (data) => set({ paymentAgingMsme: data }),
  setVendorMasterNew: (data) => set({ vendorMasterNew: data }),
  setThreeWayMatching: (data) => set({ threeWayMatching: data }),

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
