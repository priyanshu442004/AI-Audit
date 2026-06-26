import React, { useEffect } from 'react'
import { useStore } from './store'
import UploadPage  from './pages/UploadPage'
import LoadingPage from './pages/LoadingPage'
import Dashboard   from './pages/Dashboard'

export default function App() {
  const { page, sessionId, initTheme, setPage, setSessionId, setResults } = useStore()

  useEffect(() => {
    initTheme()

    const path = window.location.pathname
    const params = new URLSearchParams(window.location.search)
    const sid = params.get('session_id')

    if (path === '/dashboard' && sid) {
      setPage('loading')
      setSessionId(sid)
      fetch(`/api/result/${sid}`)
        .then(res => {
          if (!res.ok) throw new Error('Session not found')
          return res.json()
        })
        .then(data => {
          setResults(data)
          setPage('dashboard')
        })
        .catch(err => {
          console.error(err)
          setPage('upload')
          window.history.replaceState(null, '', '/uploads')
        })
    } else {
      setPage('upload')
      window.history.replaceState(null, '', '/uploads')
    }
  }, [])

  // Sync state changes back to URL
  useEffect(() => {
    if (page === 'upload') {
      if (window.location.pathname !== '/uploads') {
        window.history.pushState(null, '', '/uploads')
      }
    } else if ((page === 'dashboard' || page === 'loading') && sessionId) {
      const target = `/dashboard?session_id=${sessionId}`
      if (window.location.pathname !== '/dashboard' || !window.location.search.includes(sessionId)) {
        window.history.pushState(null, '', target)
      }
    }
  }, [page, sessionId])

  // Handle browser back/forward buttons
  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname
      const params = new URLSearchParams(window.location.search)
      const sid = params.get('session_id')

      if (path === '/dashboard' && sid) {
        setPage('loading')
        setSessionId(sid)
        fetch(`/api/result/${sid}`)
          .then(res => {
            if (!res.ok) throw new Error('Session not found')
            return res.json()
          })
          .then(data => {
            setResults(data)
            setPage('dashboard')
          })
          .catch(() => {
            setPage('upload')
            window.history.replaceState(null, '', '/uploads')
          })
      } else {
        setPage('upload')
      }
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [setPage, setSessionId, setResults])

  if (page === 'loading')   return <LoadingPage />
  if (page === 'dashboard') return <Dashboard />
  return <UploadPage />
}
