import React, { useState } from 'react'
import { useStore } from '../store'

const SECTION_TITLES = {
  cover:        'Cover',
  executive:    'Executive Dashboard',
  postatus:     'PO Status Analysis',
  gateentry:    'Gate Entry Date Check',
  qtyvariance:  'Quantity Variance',
  pricevariance:'Price Variance & Savings',
  vendormaster: 'Vendor Master',
  grpoexcept:   'GRPO Exceptions',
  threeway:     '3-Way Matching',
  datamap:      'Data Map & Logic',
  appendix:     'Appendix',
  settings:     'System Settings',
}

export default function Header({ onMenuClick }) {
  const { 
    activeSection, 
    setPage, 
    setResults,
    setPriceVarianceSame,
    setPriceVarianceCross,
    setPaymentAgingDomestic,
    setPaymentAgingForeign,
    setPaymentAgingRelated,
    setPaymentAgingMsme,
    setVendorMasterNew,
    setThreeWayMatching
  } = useStore()
  
  const [refreshing, setRefreshing] = useState(false)
  const title = SECTION_TITLES[activeSection] || activeSection

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      if (activeSection === 'pricevariancesame') {
        setPriceVarianceSame(null)
      } else if (activeSection === 'pricevariancecross') {
        setPriceVarianceCross(null)
      } else if (activeSection === 'paymentagingdomestic') {
        setPaymentAgingDomestic(null)
      } else if (activeSection === 'paymentagingforeign') {
        setPaymentAgingForeign(null)
      } else if (activeSection === 'paymentagingrelated') {
        setPaymentAgingRelated(null)
      } else if (activeSection === 'paymentagingmsme') {
        setPaymentAgingMsme(null)
      } else if (activeSection === 'vendormasternew') {
        setVendorMasterNew(null)
      } else if (activeSection === 'threewaymatching') {
        setThreeWayMatching(null)
      } else if (activeSection === 'settings') {
        // Dispatch custom event to trigger refresh inside Settings component
        window.dispatchEvent(new CustomEvent('refresh-settings'))
      } else {
        // For pages that consume the global 'results' state
        const res = await fetch('/api/result/combined')
        if (res.ok) {
          const data = await res.json()
          setResults(data)
        }
      }
      // Wait a tiny bit for UX feel
      await new Promise(r => setTimeout(r, 600))
    } catch (err) {
      console.error('Refresh error:', err)
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <header className="app-header sticky top-0 z-30 border-b">
      <div className="flex items-center justify-between px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex items-center gap-4">
          <button onClick={onMenuClick} className="lg:hidden p-1.5 -ml-1.5 rounded-md app-row-hover app-muted">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
          </button>
          <div className="flex flex-col">
            <div className="app-label mb-0.5">
              IKIO Technologies Limited
            </div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold tracking-tight app-title">
                {title}
              </h1>
              <span className="app-faint hidden sm:block">|</span>
              <span className="text-sm font-medium app-muted hidden sm:block">
                P2P Audit Report • FY 2026-27
              </span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 shadow-sm transition-all duration-150 disabled:opacity-50"
            title="Refresh current page data"
          >
            <svg 
              className={`w-3.5 h-3.5 text-slate-500 dark:text-slate-400 ${refreshing ? 'animate-spin' : ''}`} 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89M21 3v5h-5" />
            </svg>
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>

          <button
            onClick={() => setPage('upload')}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-colors duration-150"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Upload Files
          </button>
        </div>
      </div>
    </header>
  )
}
