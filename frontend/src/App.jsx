import React, { useEffect } from 'react'
import { useStore } from './store'
import UploadPage  from './pages/UploadPage'
import LoadingPage from './pages/LoadingPage'
import Dashboard   from './pages/Dashboard'
import { analyzeStream } from './api'

export default function App() {
  const { page, sessionId, initTheme, setPage, setSessionId, setResults, setProgress } = useStore()

  useEffect(() => {
    initTheme()

    const path = window.location.pathname
    const params = new URLSearchParams(window.location.search)
    const sid = params.get('session_id')

    if (path === '/dashboard') {
      const targetSid = sid || 'combined'
      setPage('loading')
      setSessionId(targetSid)
      
      fetch(`/api/result/${targetSid}`)
        .then(async res => {
          if (!res.ok) {
            const body = await res.json().catch(() => ({}))
            throw { status: res.status, detail: body.detail || 'Not found' }
          }
          return res.json()
        })
        .then(data => {
          setResults(data)
          setPage('dashboard')
        })
        .catch(err => {
          console.error('Initial result fetch error:', err)
          if (err.detail === 'Result not yet computed') {
            // Start combined stream
            analyzeStream(targetSid, {
              onProgress: ({ pct, message }) => setProgress({ pct, message }),
              onResult: (result) => {
                setResults(result)
                setPage('dashboard')
              },
              onError: (msg) => {
                setPage('upload')
                window.history.replaceState(null, '', '/uploads')
              },
            })
          } else {
            // No files uploaded or session not found
            setResults(null)
            setPage('dashboard')
            useStore.getState().setShowUploadModal(true)
          }
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

      if (path === '/dashboard') {
        const targetSid = sid || 'combined'
        setPage('loading')
        setSessionId(targetSid)
        
        fetch(`/api/result/${targetSid}`)
          .then(async res => {
            if (!res.ok) {
              const body = await res.json().catch(() => ({}))
              throw { status: res.status, detail: body.detail || 'Not found' }
            }
            return res.json()
          })
          .then(data => {
            setResults(data)
            setPage('dashboard')
          })
          .catch(err => {
            if (err.detail === 'Result not yet computed') {
              analyzeStream(targetSid, {
                onProgress: ({ pct, message }) => setProgress({ pct, message }),
                onResult: (result) => {
                  setResults(result)
                  setPage('dashboard')
                },
                onError: (msg) => {
                  setPage('upload')
                  window.history.replaceState(null, '', '/uploads')
                },
              })
            } else {
              setResults(null)
              setPage('dashboard')
              useStore.getState().setShowUploadModal(true)
            }
          })
      } else {
        setPage('upload')
      }
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [setPage, setSessionId, setResults, setProgress])

  if (page === 'loading')   return <LoadingPage />
  if (page === 'dashboard') return <Dashboard />
  return <UploadPage />
}
