import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// Safeguard window.fetch against third-party extension monkey-patches that fail on undefined options
if (typeof window !== 'undefined' && window.fetch) {
  const nativeFetch = window.fetch
  window.fetch = function (resource, options) {
    return nativeFetch.call(this, resource, options || {})
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
