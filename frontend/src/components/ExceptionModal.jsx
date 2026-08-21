import React, { useState, useMemo } from 'react'
import { AlertTriangle, X, Search, FileSpreadsheet, Download, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import TruncatedCell from './TruncatedCell'
import ExportModal from './ExportModal'

export default function ExceptionModal({
  isOpen,
  onClose,
  title = 'Audit Records',
  subtitle = 'Viewing rows associated with selected audit metric',
  columns = [],
  rows = [],
  filenamePrefix = 'Audit_Records',
  isException = true
}) {
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [showExportModal, setShowExportModal] = useState(false)
  const [sortCol, setSortCol] = useState(null)
  const [sortDir, setSortDir] = useState('asc')
  const ITEMS_PER_PAGE = 25

  const filteredRows = useMemo(() => {
    if (!searchTerm.trim()) return rows
    const term = searchTerm.trim().toLowerCase()
    return rows.filter(r =>
      Object.values(r).some(v => String(v ?? '').toLowerCase().includes(term))
    )
  }, [rows, searchTerm])

  const handleSort = (col) => {
    if (sortCol === col) {
      if (sortDir === 'asc') {
        setSortDir('desc')
      } else {
        setSortCol(null)
        setSortDir('asc')
      }
    } else {
      setSortCol(col)
      setSortDir('asc')
    }
    setCurrentPage(1)
  }

  const sortedRows = useMemo(() => {
    if (!sortCol) return filteredRows

    return [...filteredRows].sort((a, b) => {
      let valA = a[sortCol]
      let valB = b[sortCol]

      // Blank values to the end
      if (valA === null || valA === undefined || valA === '' || valA === '—') return 1
      if (valB === null || valB === undefined || valB === '' || valB === '—') return -1

      // Numeric check
      const parseNum = (v) => {
        if (typeof v === 'number') return v
        if (typeof v === 'string') {
          const cleaned = v.replace(/,/g, '').replace(/₹/g, '').trim()
          const n = parseFloat(cleaned)
          return isNaN(n) ? null : n
        }
        return null
      }

      const numA = parseNum(valA)
      const numB = parseNum(valB)

      let res = 0
      if (numA !== null && numB !== null) {
        res = numA - numB
      } else {
        res = String(valA).localeCompare(String(valB), undefined, { numeric: true, sensitivity: 'base' })
      }

      return sortDir === 'asc' ? res : -res
    })
  }, [filteredRows, sortCol, sortDir])

  const totalPages = Math.max(1, Math.ceil(sortedRows.length / ITEMS_PER_PAGE))
  const paginatedRows = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE
    return sortedRows.slice(start, start + ITEMS_PER_PAGE)
  }, [sortedRows, currentPage])

  if (!isOpen) return null

  const startRec = sortedRows.length === 0 ? 0 : (currentPage - 1) * ITEMS_PER_PAGE + 1
  const endRec = Math.min(currentPage * ITEMS_PER_PAGE, sortedRows.length)

  const headerBg = isException ? 'bg-rose-50/30 dark:bg-rose-950/10' : 'bg-blue-50/30 dark:bg-blue-950/10'
  const iconContainer = isException ? 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20' : 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20'
  const badgeStyle = isException ? 'bg-rose-100 dark:bg-rose-950/50 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-800/50' : 'bg-blue-100 dark:bg-blue-950/50 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-800/50'
  const searchRing = isException ? 'focus:ring-rose-500/50' : 'focus:ring-blue-500/50'
  const pageBadge = isException ? 'text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-800/40' : 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/40 border-blue-200 dark:border-blue-800/40'

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-900/70 backdrop-blur-sm animate-fadeIn">
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl w-full max-w-6xl max-h-[92vh] flex flex-col overflow-hidden">
          
          {/* Header */}
          <div className={`px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between ${headerBg}`}>
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-xl border ${iconContainer}`}>
                {isException ? <AlertTriangle className="w-6 h-6" /> : <FileSpreadsheet className="w-6 h-6" />}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                    {title}
                  </h3>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${badgeStyle}`}>
                    {rows.length.toLocaleString()} {isException ? 'Exception Rows' : 'Rows'}
                  </span>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  {subtitle}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Export Button */}
              <button
                onClick={() => setShowExportModal(true)}
                disabled={rows.length === 0}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/50 hover:bg-emerald-100 dark:hover:bg-emerald-900/60 transition disabled:opacity-40"
              >
                <FileSpreadsheet className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                {isException ? 'Export Exceptions' : 'Export'}
              </button>

              <button
                onClick={onClose}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Search Toolbar */}
          <div className="px-6 py-3 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 flex items-center justify-between gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                placeholder="Search within records..."
                value={searchTerm}
                onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
                className={`w-full pl-9 pr-4 py-1.5 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:outline-none focus:ring-2 ${searchRing}`}
              />
            </div>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Filtered: <strong className="text-slate-900 dark:text-white">{sortedRows.length.toLocaleString()}</strong> of {rows.length.toLocaleString()} rows
            </span>
          </div>

          {/* Modal Table Content */}
          <div className="flex-1 overflow-auto p-6">
            {sortedRows.length === 0 ? (
              <div className="py-16 text-center text-slate-400">
                <AlertTriangle className="w-10 h-10 mx-auto mb-2 text-slate-300 dark:text-slate-600" />
                <p className="text-sm font-semibold">No records found matching filters.</p>
              </div>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                <table className="w-full text-left border-collapse text-xs">
                  <thead className="bg-slate-100 dark:bg-slate-800/90 text-slate-700 dark:text-slate-200 sticky top-0 z-10">
                    <tr>
                      <th className="px-3 py-2.5 font-bold uppercase text-[10px] tracking-wider w-10 text-center select-none">
                        #
                      </th>
                      {columns.map(col => (
                        <th
                          key={col}
                          onClick={() => handleSort(col)}
                          title="Click to sort by this column"
                          className="px-4 py-2.5 font-bold uppercase text-[10px] tracking-wider whitespace-nowrap cursor-pointer select-none hover:bg-slate-200/70 dark:hover:bg-slate-700/70 transition-colors"
                        >
                          <div className="flex items-center gap-1.5">
                            <span>{col.includes('_') ? col.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') : col}</span>
                            {sortCol === col ? (
                              sortDir === 'asc' ? (
                                <ArrowUp className="w-3 h-3 text-blue-600 dark:text-blue-400" />
                              ) : (
                                <ArrowDown className="w-3 h-3 text-blue-600 dark:text-blue-400" />
                              )
                            ) : (
                              <ArrowUpDown className="w-3 h-3 text-slate-400 opacity-50 hover:opacity-100" />
                            )}
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800 bg-white dark:bg-slate-900">
                    {paginatedRows.map((r, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
                        <td className="px-3 py-2 font-mono text-center text-slate-400 text-[11px]">
                          {(currentPage - 1) * ITEMS_PER_PAGE + idx + 1}
                        </td>
                        {columns.map(col => {
                          const val = r[col]
                          const isFlag = val === 1 || val === '1' || val === true
                          const isExceptionCol = col.toLowerCase().includes('exception') || col.toLowerCase().includes('flag') || col.toLowerCase().includes('variance') || col.toLowerCase().includes('breach')

                          if (isExceptionCol && typeof val === 'number') {
                            return (
                              <td key={col} className="px-4 py-2 text-center whitespace-nowrap">
                                <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                                  isFlag
                                    ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200 dark:border-rose-800'
                                    : 'bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500'
                                }`}>
                                  {val}
                                </span>
                              </td>
                            )
                          }

                          return (
                            <td key={col} className="px-4 py-2 text-slate-800 dark:text-slate-200 font-medium">
                              {val === null || val === undefined || val === '' ? '—' : <TruncatedCell value={val} />}
                            </td>
                          )
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Modal Footer / Pagination */}
          <div className="px-6 py-3.5 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 flex items-center justify-between gap-4 flex-wrap">
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Showing <span className="font-semibold text-slate-800 dark:text-white">{startRec}</span>–<span className="font-semibold text-slate-800 dark:text-white">{endRec}</span> of <span className="font-semibold text-slate-800 dark:text-white">{filteredRows.length.toLocaleString()}</span> rows
            </span>
            
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                className="px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-[11px] font-semibold text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >«</button>
              <button
                onClick={() => setCurrentPage(p => Math.max(p - 1, 1))}
                disabled={currentPage === 1}
                className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-[11px] font-semibold text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-900 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >Prev</button>
              <span className={`px-3 py-1.5 text-[11px] font-bold rounded-lg border ${pageBadge}`}>
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))}
                disabled={currentPage === totalPages}
                className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-[11px] font-semibold text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-900 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >Next</button>
              <button
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
                className="px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-[11px] font-semibold text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >»</button>
            </div>
          </div>

        </div>
      </div>

      {/* Embedded Export Modal for Exception Rows */}
      <ExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        title={`Export ${title}`}
        columns={columns}
        data={filteredRows}
        filenamePrefix={filenamePrefix}
      />
    </>
  )
}
