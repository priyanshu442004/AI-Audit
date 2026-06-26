import React, { useState, useRef, useEffect } from 'react'
import { uploadFiles, analyzeStream } from '../api'
import { useStore } from '../store'
import logo from '../assets/logo.jpeg'

const FILE_SLOTS = [
  { role: 'ap_credit_note', label: 'AP Credit Note', desc: 'Credit memos and invoice adjustments', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
  { role: 'ap_invoice_report', label: 'AP Invoice Report', desc: 'Accounts payable invoice ledger', icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
  { role: 'vendor_master', label: 'BP Master', desc: 'Business Partner / Vendor master file', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z' },
  { role: 'gate_entry', label: 'Gate Entry Report', desc: 'Security gate material entry logs', icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4' },
  { role: 'general_ledger', label: 'General Ledger', desc: 'Full accounts and financial journal', icon: 'M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z' },
  { role: 'grpo', label: 'GRPO Report', desc: 'Goods Receipt Purchase Orders (receipts)', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01' },
  { role: 'item_master', label: 'Item Master', desc: 'Material master codes and attributes', icon: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4' },
  { role: 'purchase_order', label: 'Purchase Order Report', desc: 'PO header and line items detail', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
  { role: 'purchase_register', label: 'Purchase Register', desc: 'Tax invoice registration registry', icon: 'M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z' }
]

export default function UploadPage() {
  const { setPage, setSessionId, setResults, setProgress } = useStore()
  const [uploaded, setUploaded] = useState({})  // role → File
  const [error, setError] = useState('')
  const [dragActive, setDragActive] = useState({}) // role → boolean
  const [hasHistory, setHasHistory] = useState(false)
  const inputRefs = useRef({})

  useEffect(() => {
    fetch('/api/history')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setHasHistory(true)
        }
      })
      .catch(console.error)
  }, [])

  const handleFile = (role, file) => {
    if (!file) return
    const ext = file.name.split('.').pop().toLowerCase()
    if (!['csv', 'xlsx', 'xls'].includes(ext)) {
      setError(`Invalid file format for ${file.name}. Only .csv, .xlsx, and .xls are supported.`)
      return
    }
    setError('')
    setUploaded(prev => ({ ...prev, [role]: file }))
  }

  const handleDrop = (role, e) => {
    e.preventDefault()
    setDragActive(prev => ({ ...prev, [role]: false }))
    const file = e.dataTransfer.files[0]
    if (file) handleFile(role, file)
  }

  const handleDragOver = (role, e) => {
    e.preventDefault()
    setDragActive(prev => ({ ...prev, [role]: true }))
  }

  const handleDragLeave = (role, e) => {
    e.preventDefault()
    setDragActive(prev => ({ ...prev, [role]: false }))
  }

  const removeFile = (role, e) => {
    e.stopPropagation()
    setUploaded(prev => {
      const copy = { ...prev }
      delete copy[role]
      return copy
    })
  }

  const fileCount = Object.keys(uploaded).length
  const isComplete = fileCount === FILE_SLOTS.length

  const handleSubmit = async () => {
    if (!isComplete) return
    setError('')
    try {
      setPage('loading')
      const items = Object.entries(uploaded).map(([role, file]) => ({ role, file }))
      const total = items.length
      
      setProgress({
        pct: 2,
        message: `Uploading all ${total} files`
      })
      
      await uploadFiles(items)
      
      setProgress({
        pct: 5,
        message: 'Initializing analytical pipeline...'
      })
      
      setSessionId('combined')
      analyzeStream('combined', {
        onProgress: ({ pct, message }) => setProgress({ pct, message }),
        onResult: (result) => {
          setResults(result)
          setPage('dashboard')
        },
        onError: (msg) => {
          setError(msg)
          setPage('upload')
        },
      })
    } catch (e) {
      setError(e.message || 'An unexpected error occurred during analysis.')
      setPage('upload')
    }
  }

  return (
    <div className="app-gradient-bg min-h-screen flex flex-col justify-between py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto w-full">
        {/* Header */}
        <div className="flex flex-col items-center text-center mb-12">
          <div className="relative group mb-6">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-indigo-500 rounded-full blur opacity-45 group-hover:opacity-75 transition duration-500"></div>
            <div className="relative w-28 h-28 rounded-full bg-white dark:bg-slate-900 p-2 flex items-center justify-center shadow-2xl">
              <img src={logo} alt="IKIO Logo" className="w-24 h-24 object-contain rounded-full" />
            </div>
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white sm:text-5xl">
            Procurement Audit Workspace
          </h1>
          <p className="mt-3 max-w-2xl text-base text-slate-500 dark:text-slate-400">
            Upload the mandatory audit files to launch the comprehensive Procure-to-Pay (P2P) integrity audit. All files are verified automatically.
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-8 max-w-4xl mx-auto p-4 rounded-xl bg-red-50/90 dark:bg-red-950/20 border border-red-200 dark:border-red-800/30 flex items-start gap-3 text-red-800 dark:text-red-300">
            <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="text-sm font-medium">{error}</div>
          </div>
        )}

        {/* Status Bar */}
        <div className="max-w-5xl mx-auto mb-8 bg-white/60 dark:bg-slate-900/40 backdrop-blur border border-slate-200/80 dark:border-slate-800/80 rounded-2xl p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Upload Status</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Ensure all files correspond to the designated audit roles.
              </p>
            </div>
            <div className="text-right">
              <span className="text-2xl font-bold text-slate-900 dark:text-white">{fileCount}</span>
              <span className="text-slate-400 dark:text-slate-500 font-medium"> / {FILE_SLOTS.length} files</span>
            </div>
          </div>
          <div className="w-full bg-slate-200/60 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
            <div
              className="bg-gradient-to-r from-blue-600 to-indigo-600 h-full rounded-full transition-all duration-500 ease-out"
              style={{ width: `${(fileCount / FILE_SLOTS.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Upload Slots Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto mb-12">
          {FILE_SLOTS.map(({ role, label, desc, icon }) => {
            const file = uploaded[role]
            const isDragActive = dragActive[role]
            return (
              <div
                key={role}
                className={`relative flex flex-col justify-between p-5 rounded-2xl border transition-all duration-300 ${
                  file
                    ? 'bg-emerald-50/15 dark:bg-emerald-950/5 border-emerald-500/50 dark:border-emerald-500/30 shadow-emerald-500/5'
                    : isDragActive
                    ? 'bg-blue-50/20 dark:bg-blue-950/10 border-blue-500 dark:border-blue-500 shadow-lg shadow-blue-500/5'
                    : 'bg-white dark:bg-slate-900 border-slate-200/80 dark:border-slate-800/80 hover:border-slate-400 dark:hover:border-slate-600 shadow-sm'
                }`}
                onDrop={e => handleDrop(role, e)}
                onDragOver={e => handleDragOver(role, e)}
                onDragLeave={e => handleDragLeave(role, e)}
                onClick={() => !file && inputRefs.current[role]?.click()}
              >
                <input
                  type="file"
                  className="hidden"
                  accept=".csv,.xlsx,.xls"
                  ref={el => inputRefs.current[role] = el}
                  onChange={e => handleFile(role, e.target.files[0])}
                />

                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className={`p-2.5 rounded-xl ${file ? 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400' : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400'}`}>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
                      </svg>
                    </div>
                    {file && (
                      <button
                        onClick={e => removeFile(role, e)}
                        className="text-slate-400 hover:text-rose-500 dark:text-slate-500 dark:hover:text-rose-400 p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                        title="Remove file"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                  </div>

                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white leading-5">
                    {label}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-normal">
                    {desc}
                  </p>
                </div>

                <div className="mt-5 pt-4 border-t border-slate-100 dark:border-slate-800/80">
                  {file ? (
                    <div className="flex items-center gap-2">
                      <svg className="w-4 h-4 text-emerald-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 truncate max-w-full">
                        {file.name}
                      </span>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between text-xs text-slate-400 dark:text-slate-500 cursor-pointer">
                      <span className="font-medium hover:text-blue-500 transition-colors">Choose file or drag here</span>
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                      </svg>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Action Button */}
        <div className="flex flex-col items-center gap-4">
          <div className="flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto">
            <button
              disabled={!isComplete}
              onClick={handleSubmit}
              className="w-full sm:w-auto px-10 py-4 rounded-xl text-base font-bold text-white shadow-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-40 disabled:cursor-not-allowed disabled:from-slate-500 disabled:to-slate-600 transition-all duration-300"
            >
              {isComplete ? 'Launch P2P Audit Analysis' : 'Upload All Mandatory Files to Start'}
            </button>

            <button
              onClick={() => {
                setSessionId('combined')
                setPage('loading')
                analyzeStream('combined', {
                  onProgress: ({ pct, message }) => setProgress({ pct, message }),
                  onResult: (result) => {
                    setResults(result)
                    setPage('dashboard')
                  },
                  onError: (msg) => {
                    setError(msg)
                    setPage('upload')
                  },
                })
              }}
              className="w-full sm:w-auto px-10 py-4 rounded-xl text-base font-bold text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800/50 shadow-md transition-all duration-300 bg-white/40 dark:bg-slate-900/30 backdrop-blur-sm"
            >
              Go directly to Dashboard
            </button>
          </div>
          
          <span className="text-xs text-slate-400 dark:text-slate-500">
            Accepts CSV, XLSX, and XLS file extensions.
          </span>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center text-xs text-slate-400 dark:text-slate-500 mt-12">
        IKIO Technologies Limited • P2P Compliance Engine v1.0.0
      </div>
    </div>
  )
}
