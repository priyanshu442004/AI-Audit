import React, { useState, useEffect, useMemo } from 'react'
import { fetchStockVerifiedReport } from '../api'
import { useStore } from '../store'
import PageActionBar from '../components/PageActionBar'
import useColumnOrder from '../hooks/useColumnOrder'

// Show quantities exactly as in the Inventory Report (no rounding)
const MAX_DECIMALS = 6

const ITEMS_PER_PAGE = 50

// Suggestions shown in the Item_Code / Item_Name drop-downs while typing
const MAX_SUGGESTIONS = 200

const WIDE_TEXT_COLS = new Set(['item_name'])
const REMARK_COLS = new Set(['remark_pr', 'remark'])

const REMARK_FILTERS = [
  { id: 'all',       label: 'All items' },
  { id: 'any',       label: 'Any exception' },
  { id: 'remark_pr', label: 'Remark(PR) exception' },
  { id: 'remark',    label: 'Remark (closing) exception' },
]

const formatNumber = (val) => {
  if (val === null || val === undefined || val === '') return '—'
  const num = Number(val)
  if (Number.isNaN(num)) return String(val)
  return num.toLocaleString('en-IN', { maximumFractionDigits: MAX_DECIMALS })
}

const formatDate = (s) => {
  const m = s ? String(s).match(/^(\d{4})-(\d{2})-(\d{2})/) : null
  return m ? `${m[3]}-${m[2]}-${m[1]}` : '—'
}

const isException = (row, filter) => {
  if (filter === 'remark_pr') return row.remark_pr === 'Exception'
  if (filter === 'remark') return row.remark === 'Exception'
  if (filter === 'any') return row.remark_pr === 'Exception' || row.remark === 'Exception'
  return true
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

function KpiCard({ label, value, desc, tone, active, onClick }) {
  const tones = {
    slate: 'text-slate-900 dark:text-white',
    rose:  'text-rose-600 dark:text-rose-400',
    emerald: 'text-emerald-600 dark:text-emerald-400',
  }
  return (
    <button
      onClick={onClick}
      disabled={!onClick}
      className={`text-left p-4 rounded-xl border bg-white dark:bg-slate-900 shadow-sm transition-colors ${
        active
          ? 'border-blue-500 ring-1 ring-blue-500'
          : 'border-slate-200 dark:border-slate-800'
      } ${onClick ? 'hover:border-blue-300 dark:hover:border-blue-700 cursor-pointer' : 'cursor-default'}`}
    >
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">{label}</p>
      <p className={`text-2xl font-bold mt-1 font-mono ${tones[tone] || tones.slate}`}>{(value ?? 0).toLocaleString()}</p>
      <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">{desc}</p>
    </button>
  )
}

function SuggestInput({ id, placeholder, value, onChange, options }) {
  const term = value.trim().toLowerCase()
  const suggestions = useMemo(() => {
    const out = []
    for (const o of options) {
      if (!term || o.toLowerCase().includes(term)) {
        out.push(o)
        if (out.length >= MAX_SUGGESTIONS) break
      }
    }
    return out
  }, [options, term])

  return (
    <div className="relative">
      <input
        type="text"
        list={id}
        placeholder={placeholder}
        value={value}
        onChange={e => onChange(e.target.value)}
        className="pl-3 pr-7 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 w-48 transition"
      />
      {value && (
        <button
          onClick={() => onChange('')}
          title="Clear"
          className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-rose-500 text-xs font-bold"
        >
          ×
        </button>
      )}
      <datalist id={id}>
        {suggestions.map(o => <option key={o} value={o} />)}
      </datalist>
    </div>
  )
}

function ReportTable({ columns, rows, filterKey }) {
  const [sortCol, setSortCol] = useState(null)
  const [sortDir, setSortDir] = useState('asc')
  const [currentPage, setCurrentPage] = useState(1)
  const [dragCol, setDragCol] = useState(null)
  const [dragOverCol, setDragOverCol] = useState(null)

  const colMeta = useMemo(() => Object.fromEntries(columns.map(c => [c.id, c])), [columns])
  const allColIds = useMemo(() => columns.map(c => c.id), [columns])
  const { order: colOrder, moveColumn, resetOrder, isCustomOrder } = useColumnOrder('stock-verified-report', allColIds)

  useEffect(() => { setCurrentPage(1) }, [filterKey])

  const handleSort = (col) => {
    if (sortCol !== col) {
      setSortCol(col)
      setSortDir('asc')
    } else if (sortDir === 'asc') {
      setSortDir('desc')
    } else {
      // third click restores the report order (as in the Inventory Report)
      setSortCol(null)
      setSortDir('asc')
    }
    setCurrentPage(1)
  }

  const sorted = useMemo(() => {
    if (!sortCol) return rows
    const isNum = colMeta[sortCol]?.type === 'num'
    return [...rows].sort((a, b) => {
      const av = a[sortCol]
      const bv = b[sortCol]
      if (av === null || av === undefined || av === '') return 1
      if (bv === null || bv === undefined || bv === '') return -1
      const cmp = isNum
        ? Number(av) - Number(bv)
        : String(av).localeCompare(String(bv), undefined, { numeric: true, sensitivity: 'base' })
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [rows, sortCol, sortDir, colMeta])

  const totalPages = Math.max(1, Math.ceil(sorted.length / ITEMS_PER_PAGE))
  const page = Math.min(currentPage, totalPages)
  const paginated = sorted.slice((page - 1) * ITEMS_PER_PAGE, page * ITEMS_PER_PAGE)
  const startRec = sorted.length === 0 ? 0 : (page - 1) * ITEMS_PER_PAGE + 1
  const endRec = Math.min(page * ITEMS_PER_PAGE, sorted.length)

  const renderCell = (row, c) => {
    const meta = colMeta[c]
    const val = row[c]
    if (REMARK_COLS.has(c)) {
      return (
        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
          val === 'Exception'
            ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/40 dark:text-rose-400'
            : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400'
        }`}>
          {val ?? '—'}
        </span>
      )
    }
    if (c === 'variation' && Number(val) < 0) {
      return <span className="text-rose-600 dark:text-rose-400 font-semibold">{formatNumber(val)}</span>
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
    if (c === 'item_code') return 'font-mono font-semibold text-slate-900 dark:text-white whitespace-pre'
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
                key={`${row.item_code}-${i}`}
                className={`transition-colors duration-150 hover:bg-blue-50/40 dark:hover:bg-slate-800/40 ${
                  row.remark_pr === 'Exception' || row.remark === 'Exception' ? 'bg-rose-50/50 dark:bg-rose-950/10' : ''
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
                  No matching items found
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
          <span className="font-semibold text-slate-700 dark:text-white">{sorted.length.toLocaleString()}</span> items
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

export default function StockVerifiedReport() {
  const { stockVerifiedReport, setStockVerifiedReport } = useStore()
  const [loading, setLoading] = useState(!stockVerifiedReport)
  const [error, setError] = useState(null)
  const [refreshing, setRefreshing] = useState(false)
  const [itemCode, setItemCode] = useState('')
  const [itemName, setItemName] = useState('')
  const [itemGroup, setItemGroup] = useState('')
  const [remarkFilter, setRemarkFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [showUnmatched, setShowUnmatched] = useState(false)

  useEffect(() => {
    if (stockVerifiedReport) {
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    fetchStockVerifiedReport()
      .then(res => {
        setStockVerifiedReport(res)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [stockVerifiedReport, setStockVerifiedReport])

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      const res = await fetchStockVerifiedReport()
      setStockVerifiedReport(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setRefreshing(false)
    }
  }

  const columns = stockVerifiedReport?.columns || []
  const rows = stockVerifiedReport?.rows || []
  const kpis = stockVerifiedReport?.kpis || {}
  const warnings = stockVerifiedReport?.warnings || []
  const unmatched = stockVerifiedReport?.pr_not_in_inventory || []

  const codeOptions = useMemo(() => rows.map(r => r.item_code), [rows])
  const nameOptions = useMemo(() => [...new Set(rows.map(r => r.item_name).filter(Boolean))], [rows])
  const groupOptions = useMemo(() => [...new Set(rows.map(r => r.item_group).filter(Boolean))].sort(), [rows])

  const filtered = useMemo(() => {
    const code = itemCode.trim().toLowerCase()
    const name = itemName.trim().toLowerCase()
    const term = searchTerm.trim().toLowerCase()
    return rows.filter(r =>
      (!code || String(r.item_code ?? '').toLowerCase().includes(code)) &&
      (!name || String(r.item_name ?? '').toLowerCase().includes(name)) &&
      (!itemGroup || r.item_group === itemGroup) &&
      isException(r, remarkFilter) &&
      (!term || columns.some(c => String(r[c.id] ?? '').toLowerCase().includes(term)))
    )
  }, [rows, columns, itemCode, itemName, itemGroup, remarkFilter, searchTerm])

  const filterKey = `${itemCode}|${itemName}|${itemGroup}|${remarkFilter}|${searchTerm}`
  const hasFilters = itemCode || itemName || itemGroup || remarkFilter !== 'all' || searchTerm

  // Export uses the Excel column headings and the current filters
  const exportColumns = useMemo(() => columns.map(c => c.label), [columns])
  const exportRows = useMemo(
    () => filtered.map(r => Object.fromEntries(columns.map(c => [c.label, r[c.id]]))),
    [filtered, columns]
  )

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">
          Building stock verified report from the Inventory Report...
        </p>
      </div>
    )
  }

  if (error || stockVerifiedReport?.error) {
    return (
      <div className="p-6 bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-800 rounded-xl">
        <h3 className="text-base font-bold text-rose-800 dark:text-rose-400 mb-1">Error Loading Data</h3>
        <p className="text-sm text-rose-700 dark:text-rose-400/80">{error || stockVerifiedReport.error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageActionBar
        title="Stock Verified Report"
        subtitle="Item-wise stock movement from the Inventory Report, with GRPO receipts checked against the Purchase Register and closing stock re-computed."
        badgeText="Live Calculations"
        onRefresh={handleRefresh}
        refreshing={refreshing}
        columns={exportColumns}
        data={exportRows}
        filenamePrefix="Stock_Verified_Report"
      />

      {warnings.length > 0 && (
        <div className="p-4 rounded-xl border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/20 text-xs text-amber-800 dark:text-amber-300 space-y-1">
          {warnings.map(w => <p key={w}>{w}</p>)}
          {unmatched.length > 0 && (
            <button onClick={() => setShowUnmatched(v => !v)} className="font-bold hover:underline">
              {showUnmatched ? 'Hide' : 'Show'} Purchase Register items not in the Inventory Report
            </button>
          )}
          {showUnmatched && (
            <div className="mt-2 max-h-56 overflow-y-auto rounded-lg border border-amber-200 dark:border-amber-800 bg-white dark:bg-slate-900">
              <table className="w-full text-left">
                <thead className="sticky top-0 bg-amber-50 dark:bg-slate-800">
                  <tr>
                    <th className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider">Item Code</th>
                    <th className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-right">RecQty PR(GRPO)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-amber-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                  {unmatched.map(u => (
                    <tr key={u.item_code}>
                      <td className="px-3 py-1.5 font-mono whitespace-pre">{u.item_code}</td>
                      <td className="px-3 py-1.5 font-mono text-right">{formatNumber(u.pr_rec_qty)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Items Verified"
          value={kpis.total_items}
          desc={`${(kpis.inventory_lines ?? 0).toLocaleString()} warehouse lines rolled up by Item_Code`}
          active={remarkFilter === 'all'}
          onClick={() => setRemarkFilter('all')}
        />
        <KpiCard
          label="Remark(PR) Exceptions"
          value={kpis.pr_exceptions}
          desc="Purchase Register quantity exceeds GRPO stock receipt"
          tone={kpis.pr_exceptions ? 'rose' : 'emerald'}
          active={remarkFilter === 'remark_pr'}
          onClick={() => setRemarkFilter('remark_pr')}
        />
        <KpiCard
          label="Closing Stock Exceptions"
          value={kpis.closing_exceptions}
          desc="Computed ClsQty differs from ClsQty(SLR) at 2 decimals"
          tone={kpis.closing_exceptions ? 'rose' : 'emerald'}
          active={remarkFilter === 'remark'}
          onClick={() => setRemarkFilter('remark')}
        />
        <KpiCard
          label="Purchase Register Lines"
          value={kpis.pr_lines}
          desc={`${(kpis.pr_not_in_inventory ?? 0).toLocaleString()} item code(s) not in the Inventory Report`}
          tone={kpis.pr_not_in_inventory ? 'rose' : 'slate'}
        />
      </div>

      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2 flex-wrap">
          <SuggestInput id="svr-item-codes" placeholder="Item_Code" value={itemCode} onChange={setItemCode} options={codeOptions} />
          <SuggestInput id="svr-item-names" placeholder="Item_Name" value={itemName} onChange={setItemName} options={nameOptions} />
          <select
            value={itemGroup}
            onChange={e => setItemGroup(e.target.value)}
            className="px-2 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="">All item groups</option>
            {groupOptions.map(g => <option key={g} value={g}>{g}</option>)}
          </select>
          <select
            value={remarkFilter}
            onChange={e => setRemarkFilter(e.target.value)}
            className="px-2 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {REMARK_FILTERS.map(f => <option key={f.id} value={f.id}>{f.label}</option>)}
          </select>
          <div className="relative ml-auto">
            <svg className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search all columns..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 w-52 transition"
            />
          </div>
          {hasFilters && (
            <button
              onClick={() => { setItemCode(''); setItemName(''); setItemGroup(''); setRemarkFilter('all'); setSearchTerm('') }}
              className="text-xs text-rose-500 hover:underline font-bold"
            >
              Clear filters
            </button>
          )}
        </div>

        <p className="px-5 py-3 text-xs text-slate-500 dark:text-slate-400 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/20">
          One line per Item_Code with all warehouses summed. Variation = StockQty(GRPO) − RecQty PR(GRPO); Remark(PR) is an exception when the variation is negative.
          ClsQty = OBQTY + StockQty(GRPO) + RecQty(Others) − OutQty(Consumption) − Out_Qty(Others); Remark is an exception when it differs from ClsQty(SLR) at 2 decimals.
        </p>

        <ReportTable columns={columns} rows={filtered} filterKey={filterKey} />
      </div>
    </div>
  )
}
