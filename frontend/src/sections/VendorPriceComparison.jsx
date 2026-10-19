import React, { useState, useEffect, useMemo } from 'react'
import { fetchVendorPriceComparison } from '../api'
import { useStore } from '../store'
import PageActionBar from '../components/PageActionBar'
import useColumnOrder from '../hooks/useColumnOrder'

const MODULES = [
  {
    id: 'same_vendor',
    label: 'Same Vendor',
    description: 'Every distinct price at which an item was bought on closed INR POs from non-group domestic vendors — one line per Item Code & PO Price (Price Key), for items ordered more than once.',
  },
  {
    id: 'different_vendor',
    label: 'Different Vendor',
    description: 'Items bought from two or more vendors on INR POs from non-group domestic vendors — one line per vendor per item (Key), with repeated Item Code & PO Price combinations removed.',
  },
]

// Show numbers exactly as in the PO report (no rounding of totals or prices)
const MAX_DECIMALS = 6

const ITEMS_PER_PAGE = 50

// Long free-text columns are kept to one line; the full value shows on hover
const WIDE_TEXT_COLS = new Set(['branch', 'vendor_name', 'item_description'])

const formatNumber = (val) => {
  if (val === null || val === undefined || val === '') return '—'
  const num = Number(val)
  if (Number.isNaN(num)) return String(val)
  return num.toLocaleString('en-IN', { maximumFractionDigits: MAX_DECIMALS })
}

const parseIsoDate = (s) => {
  if (!s) return null
  const m = String(s).match(/^(\d{4})-(\d{2})-(\d{2})/)
  return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null
}

const formatDate = (s) => {
  const d = parseIsoDate(s)
  if (!d) return '—'
  return `${String(d.getDate()).padStart(2, '0')}-${String(d.getMonth() + 1).padStart(2, '0')}-${d.getFullYear()}`
}

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

function ModuleTable({ moduleId, columns, rows, searchTerm, startDate, endDate }) {
  const [sortCol, setSortCol] = useState(null)
  const [sortDir, setSortDir] = useState('asc')
  const [currentPage, setCurrentPage] = useState(1)
  const [dragCol, setDragCol] = useState(null)
  const [dragOverCol, setDragOverCol] = useState(null)

  const colMeta = useMemo(() => Object.fromEntries(columns.map(c => [c.id, c])), [columns])
  const allColIds = useMemo(() => columns.map(c => c.id), [columns])
  const { order: colOrder, moveColumn, resetOrder, isCustomOrder } = useColumnOrder(`vendor-price-comparison-${moduleId}`, allColIds)

  useEffect(() => { setCurrentPage(1) }, [searchTerm, startDate, endDate])

  const handleSort = (col) => {
    if (sortCol !== col) {
      setSortCol(col)
      setSortDir('asc')
    } else if (sortDir === 'asc') {
      setSortDir('desc')
    } else {
      // third click restores the analysis order (Item Code, then Posting Date)
      setSortCol(null)
      setSortDir('asc')
    }
    setCurrentPage(1)
  }

  const filtered = useMemo(() => {
    let out = rows
    const term = searchTerm.trim().toLowerCase()
    if (term) {
      out = out.filter(r => allColIds.some(c => String(r[c] ?? '').toLowerCase().includes(term)))
    }
    if (startDate || endDate) {
      const start = startDate ? parseIsoDate(startDate) : null
      const end = endDate ? parseIsoDate(endDate) : null
      out = out.filter(r => {
        const d = parseIsoDate(r.posting_date)
        if (!d) return false
        if (start && d < start) return false
        if (end && d > end) return false
        return true
      })
    }
    if (sortCol) {
      const isNum = colMeta[sortCol]?.type === 'num'
      out = [...out].sort((a, b) => {
        const av = a[sortCol]
        const bv = b[sortCol]
        if (av === null || av === undefined || av === '') return 1
        if (bv === null || bv === undefined || bv === '') return -1
        const cmp = isNum
          ? Number(av) - Number(bv)
          : String(av).localeCompare(String(bv), undefined, { numeric: true, sensitivity: 'base' })
        return sortDir === 'asc' ? cmp : -cmp
      })
    }
    return out
  }, [rows, searchTerm, startDate, endDate, sortCol, sortDir, allColIds, colMeta])

  const totalPages = Math.max(1, Math.ceil(filtered.length / ITEMS_PER_PAGE))
  const page = Math.min(currentPage, totalPages)
  const paginated = filtered.slice((page - 1) * ITEMS_PER_PAGE, page * ITEMS_PER_PAGE)
  const startRec = filtered.length === 0 ? 0 : (page - 1) * ITEMS_PER_PAGE + 1
  const endRec = Math.min(page * ITEMS_PER_PAGE, filtered.length)

  // Band rows of the same item so price comparisons read as one block (analysis order only)
  const bandByRow = useMemo(() => {
    let band = 0
    let prev = null
    return paginated.map(r => {
      if (prev !== null && r.item_code !== prev) band ^= 1
      prev = r.item_code
      return band
    })
  }, [paginated])

  const renderCell = (row, c) => {
    const meta = colMeta[c]
    const val = row[c]
    if (c === 'duplicate_vendor_code' || c === 'duplicate_item_code') {
      return (
        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
          val === 'YES'
            ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400'
            : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400'
        }`}>
          {val ?? '—'}
        </span>
      )
    }
    if (meta?.type === 'num') return formatNumber(val)
    if (meta?.type === 'date') return formatDate(val)
    if (WIDE_TEXT_COLS.has(c)) {
      return <span className="block truncate max-w-[280px]" title={val ?? ''}>{val ?? '—'}</span>
    }
    return val ?? '—'
  }

  const cellClass = (c) => {
    const meta = colMeta[c]
    if (meta?.type === 'num') return 'text-right font-mono text-slate-700 dark:text-slate-300 whitespace-nowrap'
    if (meta?.type === 'date') return 'font-mono text-slate-600 dark:text-slate-400 whitespace-nowrap'
    if (meta?.computed) return 'font-mono text-slate-700 dark:text-slate-300 whitespace-nowrap'
    if (c === 'vendor_code' || c === 'item_code') return 'font-mono font-semibold text-slate-900 dark:text-white whitespace-nowrap'
    return 'text-slate-600 dark:text-slate-400 whitespace-nowrap'
  }

  return (
    <>
      <div className="px-5 py-2 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
        <span>
          <span className="inline-block w-2.5 h-2.5 rounded-sm bg-violet-100 dark:bg-violet-900/40 border border-violet-200 dark:border-violet-800 mr-1.5 align-middle" />
          Highlighted headers are calculated columns · Click a header to sort · Drag to reorder
        </span>
        {isCustomOrder && (
          <button onClick={resetOrder} className="text-blue-600 dark:text-blue-400 font-semibold hover:underline">
            Reset column order
          </button>
        )}
      </div>

      <div className="overflow-x-auto" style={{ maxHeight: '560px', overflowY: 'auto' }}>
        <table className="w-full text-left border-collapse">
          <thead className="sticky top-0 z-20 bg-slate-50 dark:bg-slate-800/95 backdrop-blur-sm">
            <tr className="border-b border-slate-100 dark:border-slate-800">
              {colOrder.map(c => (
                <th
                  key={c}
                  draggable
                  onDragStart={(e) => { e.dataTransfer.effectAllowed = 'move'; setDragCol(c) }}
                  onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; if (dragOverCol !== c) setDragOverCol(c) }}
                  onDragLeave={() => setDragOverCol(prev => (prev === c ? null : prev))}
                  onDrop={(e) => { e.preventDefault(); if (dragCol && dragCol !== c) moveColumn(dragCol, c); setDragCol(null); setDragOverCol(null) }}
                  onDragEnd={() => { setDragCol(null); setDragOverCol(null) }}
                  onClick={() => handleSort(c)}
                  title={colMeta[c]?.computed ? 'Calculated column · Click to sort · Drag to reorder' : 'Click to sort · Drag to reorder'}
                  className={`px-4 py-3 text-[10px] font-bold uppercase tracking-wider cursor-grab active:cursor-grabbing select-none transition-colors whitespace-nowrap ${
                    colMeta[c]?.computed
                      ? 'bg-violet-50 dark:bg-violet-950/40 text-violet-600 dark:text-violet-300'
                      : 'text-slate-400 dark:text-slate-500 hover:bg-slate-100/50 dark:hover:bg-slate-800/60'
                  }${colMeta[c]?.type === 'num' ? ' text-right' : ''}${dragCol === c ? ' opacity-40' : ''}${dragOverCol === c && dragCol !== c ? ' bg-blue-100/70 dark:bg-blue-900/30 border-l-2 border-l-blue-500' : ''}`}
                >
                  <div className={`flex items-center font-bold${colMeta[c]?.type === 'num' ? ' justify-end' : ''}`}>
                    {colMeta[c]?.label ?? c}
                    <SortIcon dir={sortCol === c ? sortDir : null} />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {paginated.map((row, i) => (
              <tr
                key={`${row.numerator}-${row.vendor_code}-${row.item_code}-${row.po_price}-${i}`}
                className={`transition-colors duration-150 hover:bg-blue-50/40 dark:hover:bg-slate-800/40 ${
                  !sortCol && bandByRow[i] ? 'bg-slate-50/70 dark:bg-slate-800/20' : ''
                }`}
              >
                {colOrder.map(c => (
                  <td key={c} className={`px-4 py-2.5 text-xs ${cellClass(c)}`}>
                    {renderCell(row, c)}
                  </td>
                ))}
              </tr>
            ))}
            {paginated.length === 0 && (
              <tr>
                <td colSpan={colOrder.length} className="px-6 py-10 text-center text-sm text-slate-400 dark:text-slate-500">
                  {rows.length === 0 ? 'No lines qualify for this module in the uploaded Purchase Order Report.' : 'No matching records found'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="px-5 py-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between flex-wrap gap-3 text-xs text-slate-500 dark:text-slate-400">
        <div>
          Showing <span className="font-semibold text-slate-700 dark:text-white">{startRec.toLocaleString()}</span> to{' '}
          <span className="font-semibold text-slate-700 dark:text-white">{endRec.toLocaleString()}</span> of{' '}
          <span className="font-semibold text-slate-700 dark:text-white">{filtered.length.toLocaleString()}</span> entries
        </div>
        <div className="flex items-center gap-1">
          <button onClick={() => setCurrentPage(1)} disabled={page === 1} className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40">First</button>
          <button onClick={() => setCurrentPage(Math.max(1, page - 1))} disabled={page === 1} className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40">Prev</button>
          <span className="px-2 py-1">
            Page <span className="font-semibold text-slate-700 dark:text-white">{page}</span> of{' '}
            <span className="font-semibold text-slate-700 dark:text-white">{totalPages}</span>
          </span>
          <button onClick={() => setCurrentPage(Math.min(totalPages, page + 1))} disabled={page === totalPages} className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40">Next</button>
          <button onClick={() => setCurrentPage(totalPages)} disabled={page === totalPages} className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40">Last</button>
        </div>
      </div>
    </>
  )
}

export default function VendorPriceComparison() {
  const { vendorPriceComparison, setVendorPriceComparison } = useStore()
  const [loading, setLoading] = useState(!vendorPriceComparison)
  const [error, setError] = useState(null)
  const [refreshing, setRefreshing] = useState(false)
  const [activeModule, setActiveModule] = useState('same_vendor')
  const [searchTerm, setSearchTerm] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')

  useEffect(() => {
    if (vendorPriceComparison) {
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    fetchVendorPriceComparison()
      .then(res => {
        setVendorPriceComparison(res)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [vendorPriceComparison, setVendorPriceComparison])

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      const res = await fetchVendorPriceComparison()
      setVendorPriceComparison(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setRefreshing(false)
    }
  }

  const mod = vendorPriceComparison?.[activeModule]
  const columns = mod?.columns || []
  const rows = mod?.rows || []
  const moduleInfo = MODULES.find(m => m.id === activeModule)

  // Export uses the Excel column headings and the current search / date filters
  const exportColumns = useMemo(() => columns.map(c => c.label), [columns])
  const exportRows = useMemo(() => {
    const term = searchTerm.trim().toLowerCase()
    const start = startDate ? parseIsoDate(startDate) : null
    const end = endDate ? parseIsoDate(endDate) : null
    return rows
      .filter(r => !term || columns.some(c => String(r[c.id] ?? '').toLowerCase().includes(term)))
      .filter(r => {
        if (!start && !end) return true
        const d = parseIsoDate(r.posting_date)
        return d && (!start || d >= start) && (!end || d <= end)
      })
      .map(r => Object.fromEntries(columns.map(c => [c.label, r[c.id]])))
  }, [rows, columns, searchTerm, startDate, endDate])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">
          Building vendor price comparison from the Purchase Order Report...
        </p>
      </div>
    )
  }

  if (error || vendorPriceComparison?.error) {
    return (
      <div className="p-6 bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-800 rounded-xl">
        <h3 className="text-base font-bold text-rose-800 dark:text-rose-400 mb-1">Error Loading Data</h3>
        <p className="text-sm text-rose-700 dark:text-rose-400/80">{error || vendorPriceComparison.error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageActionBar
        title="Vendor Price Comparison Analysis"
        subtitle="Price comparison of PO lines from the Purchase Order Report — within the same vendor and across different vendors."
        badgeText="Live Calculations"
        onRefresh={handleRefresh}
        refreshing={refreshing}
        columns={exportColumns}
        data={exportRows}
        filenamePrefix={`Vendor_Price_Comparison_${moduleInfo.label.replace(/\s+/g, '_')}`}
      />

      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="px-5 pt-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-end justify-between flex-wrap gap-3">
            <div className="flex gap-1" role="tablist">
              {MODULES.map(m => {
                const count = vendorPriceComparison?.[m.id]?.rows?.length ?? 0
                const active = activeModule === m.id
                return (
                  <button
                    key={m.id}
                    role="tab"
                    aria-selected={active}
                    onClick={() => setActiveModule(m.id)}
                    className={`px-4 py-2.5 text-sm font-semibold border-b-2 -mb-px transition-colors flex items-center gap-2 ${
                      active
                        ? 'border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400'
                        : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
                    }`}
                  >
                    {m.label}
                    <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                      active ? 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300' : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400'
                    }`}>
                      {count.toLocaleString()}
                    </span>
                  </button>
                )
              })}
            </div>

            <div className="flex items-center gap-2 flex-wrap pb-3">
              <div className="relative">
                <svg className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  placeholder="Search vendor, item, PO..."
                  value={searchTerm}
                  onChange={e => setSearchTerm(e.target.value)}
                  className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 w-52 transition"
                />
              </div>
              <div className="flex items-center gap-1.5 text-xs">
                <span className="text-slate-400">Posting date</span>
                <input
                  type="date"
                  value={startDate}
                  onChange={e => setStartDate(e.target.value)}
                  className="px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <span className="text-slate-400">to</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={e => setEndDate(e.target.value)}
                  className="px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                {(startDate || endDate) && (
                  <button onClick={() => { setStartDate(''); setEndDate('') }} className="text-xs text-rose-500 hover:underline font-bold">
                    Clear
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        <p className="px-5 py-3 text-xs text-slate-500 dark:text-slate-400 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/20">
          {moduleInfo.description}
        </p>

        <ModuleTable
          key={activeModule}
          moduleId={activeModule}
          columns={columns}
          rows={rows}
          searchTerm={searchTerm}
          startDate={startDate}
          endDate={endDate}
        />
      </div>
    </div>
  )
}
