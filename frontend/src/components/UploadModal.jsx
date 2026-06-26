import React, { useState, useRef, useEffect } from 'react'
import { uploadFiles, analyzeStream } from '../api'
import { useStore } from '../store'

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

export default function UploadModal() {
  const { setPage, setSessionId, setResults, setProgress, setShowUploadModal } = useStore()
  const [uploaded, setUploaded] = useState({})
  const [error, setError] = useState('')
  const [dragActive, setDragActive] = useState({})
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
      setShowUploadModal(false)
      
      const items = Object.entries(uploaded).map(([role, file]) => ({ role, file }))
      const total = items.length
      
      for (let i = 0; i < total; i++) {
        const { role, file } = items[i]
        const slot = FILE_SLOTS.find(s => s.role === role)
        const label = slot ? slot.label : role
        
        setProgress({
          pct: Math.round((i / total) * 5),
          message: `Uploading ${file.name} (${label}) to S3 (${i + 1}/${total})...`
        })
        
        await uploadFiles([{ role, file }])
      }
      
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
          setPage('dashboard')
          setShowUploadModal(true)
        },
      })
    } catch (e) {
      setError(e.message || 'An unexpected error occurred.')
      setPage('dashboard')
      setShowUploadModal(true)
    }
  }

  const handleUseHistory = () => {
    setSessionId('combined')
    setPage('loading')
    setShowUploadModal(false)

    analyzeStream('combined', {
      onProgress: ({ pct, message }) => setProgress({ pct, message }),
      onResult: (result) => {
        setResults(result)
        setPage('dashboard')
      },
      onError: (msg) => {
        setError(msg)
        setPage('dashboard')
        setShowUploadModal(true)
      },
    })
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="relative w-full max-w-5xl rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 md:p-8 shadow-2xl overflow-y-auto max-h-[90vh] space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white">
            Audit Initialization Required
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            No active compliance sheets found. Upload the 9 mandatory P2P files to launch the compliance dashboard, or proceed with S3 history.
          </p>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-800/30 text-rose-800 dark:text-rose-300 text-sm">
            {error}
          </div>
        )}

        {/* Progress Bar */}
        <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800/80">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Upload progress</span>
            <span className="text-sm font-bold text-slate-900 dark:text-white">{fileCount} / {FILE_SLOTS.length}</span>
          </div>
          <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
            <div
              className="bg-gradient-to-r from-blue-600 to-indigo-600 h-full rounded-full transition-all duration-300"
              style={{ width: `${(fileCount / FILE_SLOTS.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Upload Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[45vh] overflow-y-auto pr-1">
          {FILE_SLOTS.map(({ role, label, desc, icon }) => {
            const file = uploaded[role]
            const isDragActive = dragActive[role]
            return (
              <div
                key={role}
                className={`relative flex flex-col justify-between p-4 rounded-xl border transition-all duration-200 cursor-pointer ${
                  file
                    ? 'bg-emerald-50/10 dark:bg-emerald-950/5 border-emerald-500/50'
                    : isDragActive
                    ? 'bg-blue-50/20 dark:bg-blue-950/10 border-blue-500'
                    : 'bg-slate-50/55 dark:bg-slate-950/20 border-slate-200 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700'
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

                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h4 className="text-xs font-bold text-slate-900 dark:text-white leading-tight">
                      {label}
                    </h4>
                    <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5 leading-normal">
                      {desc}
                    </p>
                  </div>
                  {file && (
                    <button
                      onClick={e => removeFile(role, e)}
                      className="text-slate-400 hover:text-rose-500 p-0.5 rounded transition-colors"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>

                <div className="mt-3 pt-2 border-t border-slate-200/50 dark:border-slate-800/50 text-[10px] text-slate-500 dark:text-slate-400">
                  {file ? (
                    <span className="text-emerald-600 dark:text-emerald-400 font-semibold truncate block">
                      ✓ {file.name}
                    </span>
                  ) : (
                    <span className="hover:text-blue-500 transition-colors">Select file or drag here</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Footer Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <button
            disabled={!isComplete}
            onClick={handleSubmit}
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl text-sm font-bold text-white shadow-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-300"
          >
            Launch P2P Compliance Audit
          </button>
          {hasHistory && (
            <button
              onClick={handleUseHistory}
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl text-sm font-bold text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all duration-300"
            >
              Use S3 History
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
