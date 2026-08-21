import React, { useState, useMemo } from 'react'
import TruncatedCell from '../components/TruncatedCell'
import useColumnOrder from '../hooks/useColumnOrder'
import ExportModal from '../components/ExportModal'
import { ArrowLeft, Gift, Wrench, Hammer, RefreshCw, FileSpreadsheet, Filter, AlertTriangle, Layers } from 'lucide-react'

const DEFAULT_COLS = [
  'Gate Entry No', 'PO Number', 'GRPO No', 'Series Name', 'Posting Date',
  'Delivery Date', 'Document Date', 'Vendor Ref No', 'Branch', 'Document Status',
  'Canceled Status', 'Group Name', 'Vendor Code', 'Vendor Name', 'Item Group',
  'Item Code', 'Item Description', 'UOM', 'GRPO Qty', 'GRPO Price',
  'Document Currency', 'Document Rate', 'Line Total', 'Document Total',
  'Warehouse Code', 'Account Code'
]

const NUMERIC_COLS = [
  'GRPO Qty', 'GRPO Price', 'Document Rate', 'Line Total', 'Document Total'
]

function SortIcon({ dir }) {
  if (!dir) return (
    <svg className="w-3 h-3 text-slate-300 dark:text-slate-600 ml-1 inline" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4" />
    </svg>
  )
  return (
    <svg className="w-3 h-3 text-blue-500 ml-1 inline" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
      {dir === 'asc'
        ? <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
        : <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />}
    </svg>
  )
}

const parseDate = (dateStr) => {
  if (!dateStr || dateStr === '—') return null
  if (dateStr instanceof Date) return dateStr
  const s = String(dateStr).trim()
  if (!s || s.toLowerCase() === 'nan' || s.toLowerCase() === 'none') return null
  const isoMatch = s.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/)
  if (isoMatch) {
    return new Date(parseInt(isoMatch[1], 10), parseInt(isoMatch[2], 10) - 1, parseInt(isoMatch[3], 10))
  }
  const dmyMatch = s.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})/)
  if (dmyMatch) {
    let year = parseInt(dmyMatch[3], 10)
    if (year < 100) year += 2000
    return new Date(year, parseInt(dmyMatch[2], 10) - 1, parseInt(dmyMatch[1], 10))
  }
  const parsed = Date.parse(s)
  return isNaN(parsed) ? null : new Date(parsed)
}

export default function PoMissingView({ data, onBack }) {
  const poMissing = data?.po_missing || {}
  
  const [activeTab, setActiveTab] = useState('foc') // 'foc' | 'jobwork' | 'repair'

  const activeSheetData = useMemo(() => {
    if (activeTab === 'foc') return poMissing.foc_items || { title: 'FOC Items', kpis: {}, rows: [] }
    if (activeTab === 'jobwork') return poMissing.job_work || { title: 'Job Work Items', kpis: {}, rows: [] }
    return poMissing.repair_maintenance || { title: 'Repair & Maintenance Items', kpis: {}, rows: [] }
  }, [poMissing, activeTab])

  const rows = activeSheetData.rows || []
  const kpis = activeSheetData.kpis || {}

  const dynamicColumns = useMemo(() => {
    if (rows.length === 0) return DEFAULT_COLS
    const keys = Object.keys(rows[0]).filter(k => k !== 'Line Total Num' && k !== 'PO Number Str')
    return keys.length > 0 ? keys : DEFAULT_COLS
  }, [rows])

  const [searchTerm, setSearchTerm]         = useState('')
  const [currentPage, setCurrentPage]       = useState(1)
  const [sortCol, setSortCol]               = useState(null)
  const [sortDir, setSortDir]               = useState('asc')
  const [showColFilters, setShowColFilters] = useState(false)
  const [colFilters, setColFilters]         = useState({})
  const [startDate, setStartDate]           = useState('')
  const [endDate, setEndDate]               = useState('')
  const [refreshing, setRefreshing]         = useState(false)
  const [showExportModal, setShowExportModal] = useState(false)

  const ITEMS_PER_PAGE = 25

  const { order: colOrder, moveColumn } = useColumnOrder(`po-missing-${activeTab}`, dynamicColumns)
  const [dragCol, setDragCol]     = useState(null)
  const [dragOverCol, setDragOverCol] = useState(null)

  const handleColFilter = (col, val) => {
    setColFilters(prev => ({ ...prev, [col]: val }))
    setCurrentPage(1)
  }
  const clearColFilters = () => { setColFilters({}); setCurrentPage(1) }
  const activeColFilterCount = Object.values(colFilters).filter(v => v.trim()).length

  const visibleCols = useMemo(() => {
    const baseSet = new Set(dynamicColumns)
    return colOrder.filter(c => baseSet.has(c))
  }, [dynamicColumns, colOrder])

  const handleSort = (col) => {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortCol(col); setSortDir('asc') }
    setCurrentPage(1)
  }

  const handleSearch = (e) => { setSearchTerm(e.target.value); setCurrentPage(1) }

  const handleTabChange = (tabKey) => {
    setActiveTab(tabKey)
    setCurrentPage(1)
    setSearchTerm('')
    setColFilters({})
    setSortCol(null)
  }

  const filtered = useMemo(() => {
    let out = rows

    const term = searchTerm.trim().toLowerCase()
    if (term) {
      out = out.filter(r => Object.values(r).some(v => String(v).toLowerCase().includes(term)))
    }

    if (startDate || endDate) {
      const start = startDate ? new Date(startDate) : null
      if (start) start.setHours(0, 0, 0, 0)
      const end = endDate ? new Date(endDate) : null
      if (end) end.setHours(23, 59, 59, 999)
      out = out.filter(r => {
        const dateVal = parseDate(r['Posting Date'] || r['Document Date'])
        if (!dateVal) return false
        if (start && dateVal < start) return false
        if (end && dateVal > end) return false
        return true
      })
    }

    const activeFilters = Object.entries(colFilters).filter(([, v]) => v.trim())
    if (activeFilters.length > 0) {
      out = out.filter(r =>
        activeFilters.every(([col, val]) =>
          String(r[col] ?? '').toLowerCase().includes(val.trim().toLowerCase())
        )
      )
    }

    if (sortCol) {
      out = [...out].sort((a, b) => {
        const av = a[sortCol] ?? ''
        const bv = b[sortCol] ?? ''
        const an = parseFloat(String(av).replace(/,/g, '')), bn = parseFloat(String(bv).replace(/,/g, ''))
        const cmp = (!isNaN(an) && !isNaN(bn)) ? an - bn : String(av).localeCompare(String(bv))
        return sortDir === 'asc' ? cmp : -cmp
      })
    }
    return out
  }, [rows, searchTerm, colFilters, sortCol, sortDir, startDate, endDate])

  const totalPages  = Math.max(1, Math.ceil(filtered.length / ITEMS_PER_PAGE))
  const paginated   = filtered.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE)
  const startRec    = filtered.length === 0 ? 0 : (currentPage - 1) * ITEMS_PER_PAGE + 1
  const endRec      = Math.min(currentPage * ITEMS_PER_PAGE, filtered.length)

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      
      {/* Top Navigation Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-3 border-b border-slate-200/80 dark:border-slate-800">
        <div>
          <button
            onClick={onBack}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 text-xs font-bold transition mb-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Procurement Transaction Review</span>
          </button>
          <h2 className="text-xl font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
            <span>PO Missing Receipts Audit</span>
            <span className="text-xs font-bold text-amber-700 bg-amber-100 dark:bg-amber-950/60 dark:text-amber-400 px-2.5 py-0.5 rounded-full border border-amber-300 dark:border-amber-800/60">
              GRPO S3 Input Exception
            </span>
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Detailed reconciliation of GRPO line items received without an associated Purchase Order reference.
          </p>
        </div>

        {/* Action Export Button */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowExportModal(true)}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm transition-all active:scale-95"
          >
            <FileSpreadsheet className="w-4 h-4" />
            <span>Export Active Sheet ({activeSheetData.title || 'Data'})</span>
          </button>
        </div>
      </div>

      {/* 3 Sub-Sheet Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 bg-slate-100/60 dark:bg-slate-900/60 p-1.5 rounded-2xl overflow-x-auto">
        <button
          onClick={() => handleTabChange('foc')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
            activeTab === 'foc'
              ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm border border-slate-200/80 dark:border-slate-700'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-white/50 dark:hover:bg-slate-800/50'
          }`}
        >
          <Gift className="w-4 h-4 text-purple-500" />
          <span>FOC Items Sheet</span>
          <span className="ml-1 text-[10px] bg-purple-100 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded-full font-extrabold">
            {poMissing.foc_items?.kpis?.total_count || 0}
          </span>
        </button>

        <button
          onClick={() => handleTabChange('jobwork')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
            activeTab === 'jobwork'
              ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm border border-slate-200/80 dark:border-slate-700'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-white/50 dark:hover:bg-slate-800/50'
          }`}
        >
          <Hammer className="w-4 h-4 text-amber-500" />
          <span>Job Work Items Sheet</span>
          <span className="ml-1 text-[10px] bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 px-2 py-0.5 rounded-full font-extrabold">
            {poMissing.job_work?.kpis?.total_count || 0}
          </span>
        </button>

        <button
          onClick={() => handleTabChange('repair')}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
            activeTab === 'repair'
              ? 'bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-400 shadow-sm border border-slate-200/80 dark:border-slate-700'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-white/50 dark:hover:bg-slate-800/50'
          }`}
        >
          <Wrench className="w-4 h-4 text-rose-500" />
          <span>Repair & Maintenance Sheet</span>
          <span className="ml-1 text-[10px] bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 px-2 py-0.5 rounded-full font-extrabold">
            {poMissing.repair_maintenance?.kpis?.total_count || 0}
          </span>
        </button>
      </div>

      {/* KPI Cards for Active Sheet */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Count</span>
          <div className="text-xl font-black text-slate-900 dark:text-white mt-1">
            {(kpis.total_count || 0).toLocaleString()}
          </div>
        </div>
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Unique GRPO</span>
          <div className="text-xl font-black text-slate-900 dark:text-white mt-1">
            {(kpis.unique_grpo || 0).toLocaleString()}
          </div>
        </div>
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Sum of GRPO QTY</span>
          <div className="text-xl font-black text-slate-900 dark:text-white mt-1">
            {kpis.sum_grpo_qty || '0.00'}
          </div>
        </div>
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Sum of GRPO Value</span>
          <div className="text-xl font-black text-blue-600 dark:text-blue-400 mt-1">
            {kpis.sum_grpo_value || '₹0.00'}
          </div>
        </div>
      </div>

      {/* Main Table for Active Sheet */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800 flex flex-col gap-3">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                {activeSheetData.title || 'PO Missing Records'}
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">Filtered from uploaded S3 GRPO dataset</p>
            </div>

            <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
              <div className="relative">
                <svg className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none"
                  fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  placeholder="Search active sheet…"
                  value={searchTerm}
                  onChange={handleSearch}
                  className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 w-44 transition"
                />
              </div>

              <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-800/60 p-1.5 rounded-lg border border-slate-200 dark:border-slate-700">
                <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 px-1">Date Range:</span>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => { setStartDate(e.target.value); setCurrentPage(1); }}
                  className="px-1.5 py-0.5 text-[10px] font-medium rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-750 dark:text-slate-250 focus:outline-none"
                />
                <span className="text-[10px] text-slate-400">—</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => { setEndDate(e.target.value); setCurrentPage(1); }}
                  className="px-1.5 py-0.5 text-[10px] font-medium rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-750 dark:text-slate-250 focus:outline-none"
                />
                {(startDate || endDate) && (
                  <button
                    onClick={() => { setStartDate(''); setEndDate(''); setCurrentPage(1); }}
                    className="p-0.5 hover:bg-slate-200 dark:hover:bg-slate-700 rounded text-slate-400 transition"
                  >✕</button>
                )}
              </div>

              <button
                onClick={() => setShowColFilters(v => !v)}
                className={`relative inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold rounded-lg border transition ${
                  showColFilters
                    ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                    : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-50'
                }`}
              >
                <Filter className="w-3 h-3" />
                Column Filters
                {activeColFilterCount > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-rose-500 text-white text-[9px] font-bold flex items-center justify-center">
                    {activeColFilterCount}
                  </span>
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto" style={{ maxHeight: '540px', overflowY: 'auto' }}>
          <table className="w-full text-left border-collapse text-xs">
            <thead className="sticky top-0 z-20 bg-slate-50 dark:bg-slate-800/95 backdrop-blur-sm">
              <tr>
                {visibleCols.map(c => (
                  <th
                    key={c}
                    draggable
                    onDragStart={(e) => { e.dataTransfer.effectAllowed = 'move'; setDragCol(c); }}
                    onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; if (dragOverCol !== c) setDragOverCol(c); }}
                    onDragLeave={() => setDragOverCol(prev => (prev === c ? null : prev))}
                    onDrop={(e) => { e.preventDefault(); if (dragCol && dragCol !== c) moveColumn(dragCol, c); setDragCol(null); setDragOverCol(null); }}
                    onDragEnd={() => { setDragCol(null); setDragOverCol(null); }}
                    onClick={() => handleSort(c)}
                    className="px-4 py-2.5 text-[10px] font-bold uppercase tracking-wider whitespace-nowrap cursor-pointer select-none border-b border-slate-200 dark:border-slate-700 hover:text-blue-600 transition-colors text-slate-500 dark:text-slate-400"
                  >
                    {c}
                    <SortIcon dir={sortCol === c ? sortDir : null} />
                  </th>
                ))}
              </tr>
              {showColFilters && (
                <tr className="bg-slate-100/80 dark:bg-slate-800/80">
                  {visibleCols.map(c => (
                    <th key={c} className="px-2 py-1.5 border-b border-slate-200 dark:border-slate-700 font-normal">
                      <input
                        type="text"
                        value={colFilters[c] || ''}
                        onChange={e => handleColFilter(c, e.target.value)}
                        placeholder="Filter…"
                        className="w-full min-w-[80px] px-2 py-1 text-[11px] rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 focus:outline-none"
                      />
                    </th>
                  ))}
                </tr>
              )}
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {paginated.length === 0 ? (
                <tr>
                  <td colSpan={visibleCols.length} className="px-6 py-12 text-center text-sm text-slate-400">
                    No records found in this category.
                  </td>
                </tr>
              ) : paginated.map((r, i) => (
                <tr key={i} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
                  {visibleCols.map(c => {
                    const val = r[c]

                    if (NUMERIC_COLS.includes(c)) return (
                      <td key={c} className="px-4 py-2 whitespace-nowrap font-mono text-slate-700 dark:text-slate-300 text-right">
                        {typeof val === 'number' ? val.toLocaleString(undefined, { maximumFractionDigits: 2 }) : String(val ?? '—')}
                      </td>
                    )

                    return (
                      <td key={c} className="px-4 py-2 text-slate-700 dark:text-slate-300">
                        {val === null || val === undefined || val === '' ? '—' : <TruncatedCell value={val} />}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="px-5 py-3.5 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/20 flex items-center justify-between gap-4 flex-wrap">
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Showing <span className="font-semibold text-slate-800 dark:text-white">{startRec}</span>–<span className="font-semibold text-slate-800 dark:text-white">{endRec}</span> of <span className="font-semibold text-slate-800 dark:text-white">{filtered.length.toLocaleString()}</span> records
          </span>
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setCurrentPage(1)}
              disabled={currentPage === 1}
              className="px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-[11px] font-semibold text-slate-500 disabled:opacity-40"
            >«</button>
            <button
              onClick={() => setCurrentPage(p => Math.max(p - 1, 1))}
              disabled={currentPage === 1}
              className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-[11px] font-semibold text-slate-600 disabled:opacity-40"
            >Prev</button>
            <span className="px-3 py-1.5 text-[11px] font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800/40">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-[11px] font-semibold text-slate-600 disabled:opacity-40"
            >Next</button>
            <button
              onClick={() => setCurrentPage(totalPages)}
              disabled={currentPage === totalPages}
              className="px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-[11px] font-semibold text-slate-500 disabled:opacity-40"
            >»</button>
          </div>
        </div>
      </div>

      {/* Export Modal */}
      <ExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        title={`Export ${activeSheetData.title || 'PO Missing Data'}`}
        columns={visibleCols}
        data={filtered}
        filenamePrefix={`PO_Missing_${activeTab.toUpperCase()}`}
      />

    </div>
  )
}
