import React, { useState } from 'react'
import { useStore } from '../store'
import { RefreshCw, Upload } from 'lucide-react'

const SECTION_TITLES = {
  cover:        'Cover',
  executive:    'Executive Dashboard',
  postatus:     'Procurement Transaction Compliance Review',
  gateentry:    'GRN & Gate Entry Compliance Review',
  qtyvariance:  'Quantity Variance',
  pricevariance:'Price Variance & Savings',
  pricevariancesame: 'Same-Vendor Price Variance',
  pricevariancecross: 'Cross-Vendor Price Variance',
  vendormaster: 'Vendor Master',
  vendormasternew: 'Vendor Master Analysis',
  grpoexcept:   'GRPO Exceptions',
  threeway:     '3-Way Matching',
  threewaymatching: '3-Way Matching Analysis',
  paymentagingdomestic: 'Domestic Payment Aging',
  paymentagingforeign: 'Foreign Payment Aging',
  paymentagingrelated: 'Related Party Payment Aging',
  paymentagingmsme: 'MSME Payment Aging',
  datamap:      'Data Map & Logic',
  appendix:     'Appendix',
  settings:     'System Settings',
}

export default function Header({ onMenuClick }) {
  const { 
    activeSection, 
    setPage, 
    setResults,
    selectedEntity,
    selectedProcess,
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
        window.dispatchEvent(new CustomEvent('refresh-settings'))
      } else {
        const query = `?entity=${encodeURIComponent(selectedEntity)}&process=${encodeURIComponent(selectedProcess)}`
        const res = await fetch(`/api/result/combined${query}`)
        if (res.ok) {
          const data = await res.json()
          setResults(data)
        }
      }
      await new Promise(r => setTimeout(r, 600))
    } catch (err) {
      console.error('Refresh error:', err)
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <header className="app-header sticky top-0 z-30 border-b h-[72px] flex items-center">
      <div className="flex-1 flex items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-4">
          <button onClick={onMenuClick} className="lg:hidden p-1.5 -ml-1.5 rounded-md app-row-hover app-muted">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight">
              {title}
            </h1>
            <span className="text-slate-300 dark:text-slate-700 hidden sm:inline">|</span>
            <div className="flex flex-col hidden sm:flex">
              <div className="app-label mb-0.5 flex items-center gap-1.5">
                <span>IKIO Technologies Limited</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300">
                  {selectedEntity} • {selectedProcess}
                </span>
              </div>
              <span className="text-xs font-medium app-muted">
                Audit Report • FY 2026-27
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
            <RefreshCw className={`w-3.5 h-3.5 text-blue-500 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>

          <button
            onClick={() => setPage('upload')}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white shadow-sm transition-colors duration-150"
          >
            <Upload className="w-4 h-4" />
            Upload Files
          </button>
        </div>
      </div>
    </header>
  )
}
