import React, { useState, useEffect, useRef } from 'react'
import { useStore } from '../store'
import { analyzeStream } from '../api'

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

export default function History() {
  const { setPage, setResults, setProgress } = useStore()
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [replacingId, setReplacingId] = useState(null)
  const [selectedIds, setSelectedIds] = useState([])
  const fileInputRef = useRef(null)

  const fetchHistory = () => {
    setLoading(true)
    setSelectedIds([])
    fetch('/api/history')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch history')
        return res.json()
      })
      .then((data) => {
        setFiles(data)
        setLoading(false)
        if (Array.isArray(data) && data.length === 0) {
          setResults(null)
          setPage('upload')
        }
      })
      .catch((err) => {
        setError(err.message || 'Error loading history.')
        setLoading(false)
      })
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  const handleDelete = async (id, filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"? This will exclude it from future audit runs.`)) {
      return
    }

    try {
      const res = await fetch(`/api/history/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Delete failed')
      fetchHistory()
    } catch (err) {
      alert(`Error deleting file: ${err.message}`)
    }
  }

  const handleBulkDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete the ${selectedIds.length} selected files?`)) {
      return
    }
    setLoading(true)
    try {
      await Promise.all(
        selectedIds.map(id =>
          fetch(`/api/history/${id}`, { method: 'DELETE' }).then(res => {
            if (!res.ok) throw new Error('Failed to delete some files')
          })
        )
      )
      setSelectedIds([])
      fetchHistory()
    } catch (err) {
      alert(`Error performing bulk delete: ${err.message}`)
      fetchHistory()
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
      setLoading(true)
      const res = await fetch(`/api/history/replace/${replacingId}`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) throw new Error('Replacement failed')
      fetchHistory()
    } catch (err) {
      alert(`Error replacing file: ${err.message}`)
      setLoading(false)
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

  const filteredFiles = files.filter(f =>
    f.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (ROLE_LABELS[f.role] || f.role).toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        accept=".csv,.xlsx,.xls"
      />

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
            Audit History & File Management
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            View, delete, or replace KPI datasets and trigger consolidated reconciliation runs.
          </p>
        </div>

        <button
          disabled={files.length === 0}
          onClick={handleRerun}
          className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl text-sm font-bold text-white shadow-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-300"
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

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-xl">
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Total Active KPI Files</div>
            <div className="text-2xl font-black text-slate-900 dark:text-white">{loading ? '...' : files.length}</div>
            <div className="text-[10px] text-slate-400 mt-0.5">Aggregated in consolidated engine</div>
          </div>
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-2xl">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Toolbar / Search */}
      <div className="flex items-center justify-between gap-4 p-4 rounded-xl bg-white/60 dark:bg-slate-900/40 backdrop-blur border border-slate-200/80 dark:border-slate-800/80 shadow-sm">
        <div className="relative flex-1 max-w-md">
          <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </span>
          <input
            type="text"
            placeholder="Search by filename or role..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {selectedIds.length > 0 && (
          <button
            onClick={handleBulkDelete}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-sm font-bold shadow-md transition-all animate-fade-in"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Delete Selected ({selectedIds.length})
          </button>
        )}
      </div>

      {/* Main Files Table */}
      <div className="overflow-hidden rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm">
        {loading ? (
          <div className="py-20 text-center text-slate-400">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4" />
            Fetching history files...
          </div>
        ) : filteredFiles.length === 0 ? (
          <div className="py-20 text-center text-slate-400">
            <svg className="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z" />
            </svg>
            No active files found.
          </div>
        ) : (
          <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 z-20 bg-slate-50 dark:bg-slate-950 backdrop-blur-sm">
                <tr className="bg-slate-50 dark:bg-slate-950/80 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-100 dark:border-slate-800/80">
                  <th className="px-6 py-4 w-12 text-center">
                    <input
                      type="checkbox"
                      checked={filteredFiles.length > 0 && selectedIds.length === filteredFiles.length}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedIds(filteredFiles.map(f => f.id))
                        } else {
                          setSelectedIds([])
                        }
                      }}
                      className="rounded border-slate-300 dark:border-slate-700 text-blue-600 focus:ring-blue-500 w-4 h-4 cursor-pointer"
                    />
                  </th>
                  <th className="px-6 py-4">KPI Sheet Role</th>
                  <th className="px-6 py-4">Filename</th>
                  <th className="px-6 py-4 text-right">Row Count</th>
                  <th className="px-6 py-4">Uploaded At</th>
                  <th className="px-6 py-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 text-sm">
                {filteredFiles.map((file) => (
                  <tr key={file.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors">
                    <td className="px-6 py-4 w-12 text-center">
                      <input
                        type="checkbox"
                        checked={selectedIds.includes(file.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedIds(prev => [...prev, file.id])
                          } else {
                            setSelectedIds(prev => prev.filter(id => id !== file.id))
                          }
                        }}
                        className="rounded border-slate-300 dark:border-slate-700 text-blue-600 focus:ring-blue-500 w-4 h-4 cursor-pointer"
                      />
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-900 dark:text-white">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400">
                        {ROLE_LABELS[file.role] || file.role}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-600 dark:text-slate-300 font-mono text-xs max-w-xs truncate">
                      <a href={file.s3Url || file.s3_url} target="_blank" rel="noopener noreferrer" className="hover:underline hover:text-blue-500" title={file.filename}>
                        {file.filename}
                      </a>
                    </td>
                    <td className="px-6 py-4 text-right font-semibold text-slate-900 dark:text-white">
                      {(file.rowCount ?? file.row_count ?? 0).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-slate-500 dark:text-slate-400 text-xs">
                      {new Date(file.uploadedAt || file.uploaded_at || Date.now()).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => handleReplaceClick(file.id)}
                          className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 hover:border-blue-500 hover:bg-blue-500/5 text-slate-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 text-xs font-medium transition-all"
                          title="Replace this file with a new dataset"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                          </svg>
                          Replace
                        </button>
                        <button
                          onClick={() => handleDelete(file.id, file.filename)}
                          className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 hover:border-rose-500 hover:bg-rose-500/5 text-slate-700 dark:text-slate-300 hover:text-rose-600 dark:hover:text-rose-400 text-xs font-medium transition-all"
                          title="Delete this file"
                        >
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
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
  )
}
