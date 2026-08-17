import React, { useState, useEffect } from 'react'
import * as XLSX from 'xlsx'
import { FileSpreadsheet, Download, X, CheckSquare, Square } from 'lucide-react'

export default function ExportModal({
  isOpen,
  onClose,
  title = 'Export Data to Excel',
  columns = [],
  data = [],
  filenamePrefix = 'Audit_Export'
}) {
  const [exportMode, setExportMode] = useState('all') // 'all' | 'select'
  const [selectedCols, setSelectedCols] = useState([])

  useEffect(() => {
    if (isOpen) {
      setExportMode('all')
      setSelectedCols(columns)
    }
  }, [isOpen, columns])

  if (!isOpen) return null

  const handleToggleCol = (col) => {
    setSelectedCols(prev =>
      prev.includes(col) ? prev.filter(c => c !== col) : [...prev, col]
    )
  }

  const handleSelectAll = () => setSelectedCols([...columns])
  const handleDeselectAll = () => setSelectedCols([])

  const handleExport = () => {
    const colsToExport = exportMode === 'all' ? columns : selectedCols

    if (colsToExport.length === 0) {
      alert('Please select at least one column to export.')
      return
    }

    // Map data to chosen columns
    const exportRows = data.map(row => {
      const formattedRow = {}
      colsToExport.forEach(col => {
        let val = row[col]
        if (val === undefined || val === null) {
          formattedRow[col] = ''
        } else if (typeof val === 'object') {
          formattedRow[col] = JSON.stringify(val)
        } else {
          formattedRow[col] = val
        }
      })
      return formattedRow
    })

    const worksheet = XLSX.utils.json_to_sheet(exportRows)
    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, 'ExportData')

    const dateStr = new Date().toISOString().slice(0, 10)
    const cleanPrefix = filenamePrefix.replace(/[^a-zA-Z0-9_-]/g, '_')
    XLSX.writeFile(workbook, `${cleanPrefix}_${dateStr}.xlsx`)

    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl w-full max-w-xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/30">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                {title}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Export {data.length.toLocaleString()} records to Microsoft Excel (.xlsx)
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1">
          {/* Export Mode Selection */}
          <div className="space-y-3">
            <label className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Select Export Option
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Option 1: All columns */}
              <label
                onClick={() => setExportMode('all')}
                className={`flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition-all ${
                  exportMode === 'all'
                    ? 'border-blue-500 bg-blue-50/40 dark:bg-blue-950/20 text-blue-950 dark:text-blue-200 shadow-sm'
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800/50 text-slate-700 dark:text-slate-300'
                }`}
              >
                <input
                  type="radio"
                  name="exportMode"
                  checked={exportMode === 'all'}
                  onChange={() => setExportMode('all')}
                  className="mt-0.5 text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="text-xs font-bold">1. Export All Columns</div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                    Include all {columns.length} columns in the spreadsheet output.
                  </div>
                </div>
              </label>

              {/* Option 2: Select columns */}
              <label
                onClick={() => setExportMode('select')}
                className={`flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition-all ${
                  exportMode === 'select'
                    ? 'border-blue-500 bg-blue-50/40 dark:bg-blue-950/20 text-blue-950 dark:text-blue-200 shadow-sm'
                    : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800/50 text-slate-700 dark:text-slate-300'
                }`}
              >
                <input
                  type="radio"
                  name="exportMode"
                  checked={exportMode === 'select'}
                  onChange={() => setExportMode('select')}
                  className="mt-0.5 text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <div className="text-xs font-bold">2. Select Columns to Export</div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                    Choose specific columns to customize your export.
                  </div>
                </div>
              </label>
            </div>
          </div>

          {/* Column Selection Grid (Visible when Option 2 selected) */}
          {exportMode === 'select' && (
            <div className="space-y-3 pt-2 border-t border-slate-100 dark:border-slate-800 animate-fadeIn">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-600 dark:text-slate-300">
                  Select Columns ({selectedCols.length} of {columns.length} selected)
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleSelectAll}
                    className="text-[11px] font-semibold text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    Select All
                  </button>
                  <span className="text-slate-300 dark:text-slate-700">•</span>
                  <button
                    onClick={handleDeselectAll}
                    className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 hover:underline"
                  >
                    Deselect All
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200/80 dark:border-slate-800">
                {columns.map(col => {
                  const isChecked = selectedCols.includes(col)
                  return (
                    <label
                      key={col}
                      className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300 cursor-pointer hover:text-blue-600 dark:hover:text-blue-400 select-none p-1 rounded hover:bg-slate-200/50 dark:hover:bg-slate-800/50 transition"
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => handleToggleCol(col)}
                        className="rounded text-blue-600 focus:ring-blue-500"
                      />
                      <span className="truncate">{col}</span>
                    </label>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-200/60 dark:hover:bg-slate-800 transition"
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-5 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 rounded-xl shadow-md transition-all active:scale-[0.98]"
          >
            <Download className="w-4 h-4" />
            Download Excel (.xlsx)
          </button>
        </div>
      </div>
    </div>
  )
}
