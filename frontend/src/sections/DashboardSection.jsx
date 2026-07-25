import React, { useState, useEffect, useRef } from 'react'
import { useStore } from '../store'
import { analyzeStream, fetchLogs } from '../api'
import DonutChart from '../components/DonutChart'
import BarRow from '../components/BarRow'
import RiskTable from '../components/RiskTable'
import AiInsightBox from '../components/AiInsightBox'
import TruncatedCell from '../components/TruncatedCell'
import { BAR_COLORS, CHART_COLORS } from '../theme'
import { calculateConsolidatedMetrics } from '../utils/dashboardConsolidator'

const PREFETCH_METADATA = {
  priceVarianceSame: {
    label: 'Same-Vendor Price Variance',
    desc: 'Analyzes price variance for identical items purchased from the same vendor over time.',
  },
  priceVarianceCross: {
    label: 'Cross-Vendor Price Variance',
    desc: 'Compares unit rates for identical items across multiple vendors.',
  },
  paymentAgingDomestic: {
    label: 'Domestic Payment Aging',
    desc: 'Categorizes outstanding trade payables for domestic vendors.',
  },
  paymentAgingForeign: {
    label: 'Foreign Payment Aging',
    desc: 'Tracks aging and payment details for international suppliers.',
  },
  paymentAgingRelated: {
    label: 'Related Party Payment Aging',
    desc: 'Identifies transactions and aging profiles for related companies.',
  },
  paymentAgingMsme: {
    label: 'MSME Payment Aging',
    desc: 'Reconciles payment delays and interests for registered MSMEs.',
  },
  vendorMasterNew: {
    label: 'Vendor Master Analysis',
    desc: 'Checks BP Registry for duplicate tax IDs, missing GSTINs, and dormancy.',
  },
  threeWayMatching: {
    label: 'Three-Way Matching Analysis',
    desc: 'Performs line-by-line reconciliation of PO, GRPO, and AP Invoices.',
  },
}

const ROLE_LABELS = {
  vendor_master: 'BP Master',
  purchase_order: 'Purchase Order Report',
  gate_entry: 'Gate Entry Report',
  grpo: 'GRPO Report',
  purchase_register: 'Purchase Register',
  general_ledger: 'General Ledger',
  ap_credit_note: 'AP Credit Note',
  ap_invoice_report: 'AP Invoice Report',
  item_master: 'Item Master',
}

function Kpi({ label, value, sub, color, desc, isLoading }) {
  return (
    <div className="group relative overflow-hidden rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm hover:shadow-md transition-all duration-200">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">{label}</span>
        {isLoading && (
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
          </span>
        )}
      </div>
      {isLoading ? (
        <div className="space-y-2 py-1">
          <div className="h-6 w-24 bg-slate-200 dark:bg-slate-800 rounded animate-pulse" />
          <div className="h-3.5 w-32 bg-slate-100 dark:bg-slate-800/60 rounded animate-pulse" />
        </div>
      ) : (
        <>
          <div className={`text-2xl font-black tracking-tight ${color || 'text-slate-900 dark:text-white'}`}>
            {value ?? '—'}
          </div>
          {sub && <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 font-medium">{sub}</div>}
        </>
      )}
      {desc && <div className="text-[10px] text-slate-400 mt-0.5">{desc}</div>}
    </div>
  )
}

export default function DashboardSection({ results }) {
  const store = useStore()
  const { setPage, setResults, setProgress, backgroundStates = {} } = store
  const [showHydrationDetails, setShowHydrationDetails] = useState(false)

  const isModuleLoading = (key) => {
    const status = backgroundStates[key]
    return status !== 'success' && status !== 'error'
  }
  
  // Extract cover & executive data
  const coverData = results?.cover || {}
  const coverKpis = coverData.kpis || {}
  const execData = results?.executive || {}
  
  // Compute consolidated metrics dynamically
  const { execKpis, recoveriesSubtext, overdueSubtext } = calculateConsolidatedMetrics(store)
  
  const charts = execData.charts || {}
  const risks = execData.top_risks || []

  // Charts
  const poChart = charts.po_status || { total: 0, segments: [] }
  const twChart = charts.three_way || { total: 0, segments: [] }
  const agingBars = charts.payment_aging || []
  const poSegs = poChart.segments || []
  const twSegs = (twChart.segments || []).slice(0, 5)

  // Cover cards (Database source counts)
  const sourceCards = [
    { label: 'Purchase Orders', value: (coverKpis.purchase_orders ?? 0).toLocaleString(), icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2', color: 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300' },
    { label: 'GRPO Documents', value: (coverKpis.grpo_documents ?? 0).toLocaleString(), icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', color: 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300' },
    { label: 'Gate Entries', value: (coverKpis.gate_entries ?? 0).toLocaleString(), icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16', color: 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300' },
    { label: 'AP Invoices', value: (coverKpis.ap_invoices ?? 0).toLocaleString(), icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2', color: 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300' },
  ]

  // File management & logs state
  const [files, setFiles] = useState([])
  const [logs, setLogs] = useState([])
  const [loadingFiles, setLoadingFiles] = useState(true)
  const [loadingLogs, setLoadingLogs] = useState(true)
  const [error, setError] = useState('')
  const [replacingId, setReplacingId] = useState(null)
  const fileInputRef = useRef(null)

  const fetchHistoryAndLogs = () => {
    setLoadingFiles(true)
    setLoadingLogs(true)
    
    // Fetch files
    fetch('/api/history')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch history')
        return res.json()
      })
      .then((data) => {
        setFiles(data)
        setLoadingFiles(false)
      })
      .catch((err) => {
        setError(err.message || 'Error loading history.')
        setLoadingFiles(false)
      })

    // Fetch logs
    fetchLogs(20)
      .then((data) => {
        setLogs(data)
        setLoadingLogs(false)
      })
      .catch((err) => {
        console.error('Error loading audit logs', err)
        setLoadingLogs(false)
      })
  }

  useEffect(() => {
    fetchHistoryAndLogs()
  }, [])

  const handleDelete = async (id, filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"? This will exclude it from future audit runs.`)) {
      return
    }

    try {
      const res = await fetch(`/api/history/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Delete failed')
      fetchHistoryAndLogs()
    } catch (err) {
      alert(`Error deleting file: ${err.message}`)
    }
  }

  const handleReplaceClick = (id) => {
    setReplacingId(id)
    if (fileInputRef.current) {
      fileInputRef.current.click()
    }
  }

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file || !replacingId) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      setLoadingFiles(true)
      const res = await fetch(`/api/history/replace/${replacingId}`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) throw new Error('Replacement failed')
      fetchHistoryAndLogs()
    } catch (err) {
      alert(`Error replacing file: ${err.message}`)
      setLoadingFiles(false)
    } finally {
      setReplacingId(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleRerun = () => {
    setPage('loading')
    analyzeStream('combined', {
      onProgress: ({ pct, message }) => setProgress({ pct, message }),
      onResult: (result) => {
        setResults(result)
        setPage('dashboard')
      },
      onError: (msg) => {
        alert(`Analysis error: ${msg}`)
        setPage('dashboard')
      },
    })
  }

  return (
    <div className="space-y-8 pb-16">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        accept=".csv,.xlsx,.xls"
      />

      {/* ── Welcome Hero Banner ── */}
      <div className="relative overflow-hidden rounded-xl bg-slate-900 border border-slate-800 text-white p-8 sm:p-10 shadow-lg">
        {/* Subtle grid pattern */}
        <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-20"></div>
        
        <div className="relative z-10 max-w-3xl space-y-3">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold bg-blue-500/20 text-blue-300 border border-blue-500/30">
            System Status: Audit Complete
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            IKIO Technologies Limited
          </h1>
          <p className="text-base text-slate-300 font-medium">
            Procure-to-Pay (P2P) Comprehensive Compliance &amp; Transaction Integrity Audit
          </p>
          <div className="pt-2 flex flex-wrap gap-4 text-xs text-slate-400">
            <div>Audit Cycle: <span className="text-white font-medium">FY 2026-27</span></div>
            <div className="hidden sm:block">•</div>
            <div>Classification: <span className="text-white font-medium">Confidential Executive Document</span></div>
          </div>
        </div>
      </div>

      {/* ── Background Analytics Sync Status ── */}
      <div className="rounded-xl border border-slate-200/80 dark:border-slate-800/80 bg-gradient-to-r from-slate-50 to-white dark:from-slate-950 dark:to-slate-900 p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5">
              <h2 className="text-sm font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wider">
                Background Analytics Sync Status
              </h2>
              {(() => {
                const totalTasks = 8
                const completedTasks = Object.values(backgroundStates).filter(s => s === 'success').length
                const pctComplete = Math.round((completedTasks / totalTasks) * 100)
                const isHydrated = completedTasks === totalTasks

                if (isHydrated) {
                  return (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                      Synchronized
                    </span>
                  )
                }
                if (completedTasks > 0 || Object.values(backgroundStates).some(s => s === 'loading')) {
                  return (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                      Syncing ({pctComplete}%)
                    </span>
                  )
                }
                return (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-500/20">
                    Idle
                  </span>
                )
              })()}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-2xl">
              Proactively syncing all audit modules in the background to compile a consolidated executive overview and enable instant tab navigation.
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase">Progress</div>
              <div className="text-lg font-black text-slate-800 dark:text-white">
                {Object.values(backgroundStates).filter(s => s === 'success').length} / 8 Modules
              </div>
            </div>
            <button
              onClick={() => setShowHydrationDetails(!showHydrationDetails)}
              className="flex items-center justify-center p-2 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition duration-200"
              title="Toggle Details"
            >
              <svg
                className={`w-5 h-5 transform transition-transform duration-200 ${showHydrationDetails ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
        </div>

        {/* Linear Progress Bar */}
        <div className="mt-4 w-full bg-slate-200 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
          <div
            className="bg-blue-600 dark:bg-blue-500 h-2 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${Math.round((Object.values(backgroundStates).filter(s => s === 'success').length / 8) * 100)}%` }}
          />
        </div>

        {/* Expanded Task list */}
        {showHydrationDetails && (
          <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 border-t border-slate-200/60 dark:border-slate-800/60 pt-5">
            {Object.entries(PREFETCH_METADATA).map(([key, meta]) => {
              const status = backgroundStates[key]
              const isTaskLoading = status === 'loading'
              const isTaskSuccess = status === 'success'
              const isTaskError = status === 'error'

              let statusIcon = (
                <div className="w-5 h-5 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              )
              let statusText = 'Pending'
              let statusColor = 'text-slate-400 dark:text-slate-500'
              let borderHoverClass = 'border-slate-200/80 dark:border-slate-800/80'

              if (isTaskLoading) {
                statusIcon = (
                  <div className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-950/40 flex items-center justify-center text-blue-600 dark:text-blue-400">
                    <svg className="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                  </div>
                )
                statusText = 'Syncing...'
                statusColor = 'text-blue-600 dark:text-blue-400 font-semibold'
                borderHoverClass = 'border-blue-500/40 dark:border-blue-500/20'
              } else if (isTaskSuccess) {
                statusIcon = (
                  <div className="w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-950/40 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="3" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                )
                statusText = 'Synced'
                statusColor = 'text-emerald-600 dark:text-emerald-400 font-semibold'
                borderHoverClass = 'border-emerald-500/40 dark:border-emerald-500/20'
              } else if (isTaskError) {
                statusIcon = (
                  <div className="w-5 h-5 rounded-full bg-rose-100 dark:bg-rose-950/40 flex items-center justify-center text-rose-600 dark:text-rose-400">
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="3" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                )
                statusText = 'Failed'
                statusColor = 'text-rose-600 dark:text-rose-400 font-semibold'
                borderHoverClass = 'border-rose-500/40 dark:border-rose-500/20'
              }

              return (
                <div
                  key={key}
                  onClick={() => setPage(key.toLowerCase())}
                  className={`group flex items-start gap-3 p-3 rounded-xl border bg-white dark:bg-slate-900 shadow-sm cursor-pointer hover:shadow transition-all duration-200 ${borderHoverClass}`}
                >
                  <div className="mt-0.5">{statusIcon}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                        {meta.label}
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5 line-clamp-2 leading-normal">
                      {meta.desc}
                    </p>
                    <div className="flex items-center justify-between mt-1.5">
                      <span className={`text-[10px] uppercase tracking-wider ${statusColor}`}>{statusText}</span>
                      {isTaskSuccess && (
                        <span className="text-[9px] text-blue-500 dark:text-blue-400 font-medium group-hover:underline">
                          View Module →
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* ── Source counts cards ── */}
      <div>
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Database Source Counts</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {sourceCards.map(c => (
            <div key={c.label} className="group relative overflow-hidden rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm hover:shadow-md transition-all duration-200">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  {c.label}
                </span>
                <div className={`p-2 rounded-md ${c.color} border border-slate-200 dark:border-slate-700/50`}>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d={c.icon} />
                  </svg>
                </div>
              </div>
              <div className="text-2xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                {c.value}
              </div>
              <div className="mt-1 text-[11px] text-slate-400">
                Verified records processed
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── AI Narrative (From Executive) ── */}
      <AiInsightBox section="executive" kpis={execKpis} topRisks={risks} />

      {/* ── Executive Key Metrics ── */}
      <div>
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Key Audit Findings</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Kpi 
            label="Purchase Order Value" 
            value={`₹${execKpis.po_value_cr ?? 0} Cr`} 
            sub={`Open PO: ₹${execKpis.open_value_cr ?? 0} Cr`} 
            desc="Total PO commitment analyzed" 
            isLoading={false}
          />
          <Kpi 
            label="AP Outstanding" 
            value={`₹${execKpis.ap_outstanding_cr ?? 0} Cr`} 
            sub={`Total Invoices: ${(execKpis.ap_invoices ?? 0).toLocaleString()}`} 
            color="text-sky-600 dark:text-sky-400"
            desc="Open trade payables" 
            isLoading={isModuleLoading('paymentAgingDomestic') || isModuleLoading('paymentAgingForeign') || isModuleLoading('paymentAgingRelated') || isModuleLoading('paymentAgingMsme')}
          />
          <Kpi 
            label="MSME Breaches" 
            value={execKpis.msme_breaches ?? 0} 
            sub="Violations of 45-Day Payment Rule" 
            color="text-rose-600 dark:text-rose-400"
            desc="Strict regulatory compliance check" 
            isLoading={isModuleLoading('paymentAgingMsme')}
          />
          <Kpi 
            label="Potential Recoveries" 
            value={`₹${execKpis.savings_l ?? 0} L`} 
            sub={recoveriesSubtext} 
            color="text-emerald-600 dark:text-emerald-400"
            desc="Immediate savings opportunity" 
            isLoading={isModuleLoading('priceVarianceSame') || isModuleLoading('priceVarianceCross')}
          />
          <Kpi 
            label="Overdue AP Invoices" 
            value={execKpis.late_overdue ?? 0} 
            sub={overdueSubtext} 
            color="text-amber-600 dark:text-amber-500"
            desc="Aging ledger exceptions" 
            isLoading={isModuleLoading('paymentAgingDomestic') || isModuleLoading('paymentAgingForeign') || isModuleLoading('paymentAgingRelated') || isModuleLoading('paymentAgingMsme')}
          />
          <Kpi 
            label="Quantity Deviations" 
            value={execKpis.qty_above_5pct ?? 0} 
            sub="Over 5% tolerance threshold" 
            color="text-rose-600 dark:text-rose-400"
            desc="GRPO vs PO quantity checks" 
            isLoading={isModuleLoading('threeWayMatching')}
          />
          <Kpi 
            label="Three-Way Matches" 
            value={execKpis.threeway_perfect ?? 0} 
            sub={execKpis.threeway_pct != null ? `Perfect Match Rate: ${execKpis.threeway_pct}%` : 'Perfect Match Rate: --'}
            desc="Fully verified document lineage" 
            isLoading={isModuleLoading('threeWayMatching')}
          />
          <Kpi 
            label="Master Data Flags" 
            value={execKpis.vendor_issues ?? 0} 
            sub={`${execKpis.duplicates ?? 0} Dup + ${execKpis.missing_gstin ?? 0} Missing Tax IDs`} 
            color="text-amber-600 dark:text-amber-500"
            desc="BP Registry anomalies" 
            isLoading={isModuleLoading('vendorMasterNew')}
          />
        </div>
      </div>

      {/* ── Executive Charts ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* PO Status */}
        <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">PO Lifecycle Profile</h3>
            <p className="text-xs text-slate-400 mt-0.5">Distribution of PO line items by status</p>
          </div>
          <div className="flex items-center justify-center my-6">
            <DonutChart
              segments={poSegs.map(s => ({
                ...s,
                color: s.label === 'Open' ? CHART_COLORS.warning : CHART_COLORS.success
              }))}
              centerText={(poChart.total || 0).toLocaleString()}
              centerSub="Total Line Items"
            />
          </div>
          <div className="space-y-2 text-xs border-t border-slate-100 dark:border-slate-800/80 pt-3">
            {poSegs.map(s => {
              const col = s.label === 'Open' ? 'bg-amber-500' : 'bg-green-600'
              return (
                <div key={s.label} className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-slate-600 dark:text-slate-300 font-medium">
                    <span className={`w-2.5 h-2.5 rounded-full ${col}`} />
                    {s.label}
                  </span>
                  <span className="font-semibold text-slate-950 dark:text-white">{(s.value || 0).toLocaleString()}</span>
                </div>
              )
            })}
          </div>
        </div>

        {/* 3-Way matching */}
        <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">3-Way Match Verification</h3>
            <p className="text-xs text-slate-400 mt-0.5">Comparison of Purchase Orders, GRPO, and Invoices</p>
          </div>
          <div className="flex items-center justify-center my-6">
            <DonutChart
              segments={twSegs}
              centerText={(twChart.total || 0).toLocaleString()}
              centerSub="Audited Invoices"
            />
          </div>
          <div className="space-y-2 text-xs border-t border-slate-100 dark:border-slate-800/80 pt-3">
            {twSegs.map(s => (
              <div key={s.label} className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-slate-600 dark:text-slate-300 font-medium truncate max-w-[200px]">
                  <span className="w-2.5 h-2.5 rounded-md" style={{ background: s.color }} />
                  {s.label}
                </span>
                <span className="font-semibold text-slate-950 dark:text-white">{(s.value || 0).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Payment aging */}
        <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Accounts Payable Aging</h3>
            <p className="text-xs text-slate-400 mt-0.5">Distribution of outstanding payables by due date bracket</p>
          </div>
          <div className="space-y-3.5 my-6 flex-1 flex flex-col justify-center">
            {agingBars.map(b => (
              <BarRow key={b.label} label={b.label} value={b.value} pct={b.pct} color={BAR_COLORS.primary} />
            ))}
          </div>
          <div className="text-[10px] text-slate-400 border-t border-slate-100 dark:border-slate-800/80 pt-3 text-center">
            Total AP value matches the verified Purchase Register.
          </div>
        </div>
      </div>

      {/* Risks Table */}
      <RiskTable risks={risks} />

      {/* ── History and Audit Log (Consolidated Section) ── */}
      <div className="border-t border-slate-200 dark:border-slate-800 pt-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Data Files &amp; Audit History
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
              Manage analytical datasets and review system execution logs.
            </p>
          </div>

          <button
            disabled={files.length === 0}
            onClick={handleRerun}
            className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
            </svg>
            Re-run Consolidated Pipeline
          </button>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-800/30 text-rose-800 dark:text-rose-300 text-sm">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* File Manager */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
              Active Source Files ({files.length})
            </h3>
            
            <div className="overflow-hidden rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm">
              {loadingFiles ? (
                <div className="py-12 text-center text-slate-400">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2" />
                  Loading active files...
                </div>
              ) : files.length === 0 ? (
                <div className="py-12 text-center text-slate-400">No active files found.</div>
              ) : (
                <div className="overflow-x-auto max-h-[350px] overflow-y-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-50 dark:bg-slate-950/80 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100 dark:border-slate-800/80 sticky top-0 z-10">
                        <th className="px-4 py-3">Role</th>
                        <th className="px-4 py-3">Filename</th>
                        <th className="px-4 py-3 text-right">Rows</th>
                        <th className="px-4 py-3 text-center">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 text-xs">
                      {files.map((file) => (
                        <tr key={file.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors">
                          <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white truncate max-w-[120px]">
                            {ROLE_LABELS[file.role] || file.role}
                          </td>
                          <td className="px-4 py-3 text-slate-600 dark:text-slate-300 font-mono truncate max-w-[150px]" title={file.filename}>
                            <a href={file.s3Url || file.s3_url} target="_blank" rel="noopener noreferrer" className="hover:underline hover:text-blue-500">
                              {file.filename}
                            </a>
                          </td>
                          <td className="px-4 py-3 text-right font-semibold text-slate-900 dark:text-white">
                            {(file.rowCount ?? file.row_count ?? 0).toLocaleString()}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <div className="flex items-center justify-center gap-1.5">
                              <button
                                onClick={() => handleReplaceClick(file.id)}
                                className="flex items-center gap-0.5 px-2 py-1 rounded border border-slate-200 dark:border-slate-800 hover:border-blue-500 hover:bg-blue-500/5 text-slate-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-all"
                                title="Replace file"
                              >
                                Replace
                              </button>
                              <button
                                onClick={() => handleDelete(file.id, file.filename)}
                                className="flex items-center gap-0.5 px-2 py-1 rounded border border-slate-200 dark:border-slate-800 hover:border-rose-500 hover:bg-rose-500/5 text-slate-700 dark:text-slate-300 hover:text-rose-600 dark:hover:text-rose-400 transition-all"
                                title="Delete file"
                              >
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* Audit Logs */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
              System Audit Trails (Live Actions)
            </h3>
            
            <div className="overflow-hidden rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm">
              {loadingLogs ? (
                <div className="py-12 text-center text-slate-400">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2" />
                  Loading execution logs...
                </div>
              ) : logs.length === 0 ? (
                <div className="py-12 text-center text-slate-400">No logs generated yet.</div>
              ) : (
                <div className="overflow-x-auto max-h-[350px] overflow-y-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-50 dark:bg-slate-950/80 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100 dark:border-slate-800/80 sticky top-0 z-10">
                        <th className="px-4 py-3">Timestamp</th>
                        <th className="px-4 py-3">Action Type</th>
                        <th className="px-4 py-3">Target Entity</th>
                        <th className="px-4 py-3">Details</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 text-xs">
                      {logs.map((log) => {
                        let actionBadgeColor = 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300'
                        if (log.action === 'File Uploaded') actionBadgeColor = 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
                        if (log.action === 'File Replaced') actionBadgeColor = 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-400'
                        if (log.action === 'File Deleted') actionBadgeColor = 'bg-rose-50 text-rose-700 dark:bg-rose-900/20 dark:text-rose-400'
                        if (log.action === 'Pipeline Run') actionBadgeColor = 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400'
                        if (log.action === 'Dashboard Fetched') actionBadgeColor = 'bg-teal-50 text-teal-700 dark:bg-teal-900/20 dark:text-teal-400'

                        return (
                          <tr key={log.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors">
                            <td className="px-4 py-3 text-slate-500 dark:text-slate-400">
                              <TruncatedCell value={new Date(log.timestamp).toLocaleString()} />
                            </td>
                            <td className="px-4 py-3 font-semibold">
                              <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide ${actionBadgeColor}`}>
                                {log.action}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-slate-900 dark:text-white font-mono">
                              <TruncatedCell value={log.filename || '—'} />
                            </td>
                            <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                              <TruncatedCell value={log.user_action || '—'} />
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
