import React, { useState, useMemo } from 'react'
import DonutChart from '../components/DonutChart'
import AiInsightBox from '../components/AiInsightBox'
import { CHART_COLORS } from '../theme'
import TruncatedCell from '../components/TruncatedCell'
import useColumnOrder from '../hooks/useColumnOrder'

const formatCurrency = (val) => {
  if (val === null || val === undefined) return '—'
  const num = parseFloat(val)
  if (isNaN(num)) return val
  if (num >= 10000000) return `₹${(num / 10000000).toFixed(2)} Cr`
  if (num >= 100000) return `₹${(num / 100000).toFixed(2)} L`
  return `₹${num.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
}

const COL_GROUPS = [
  { label: 'Gate Entry Info', cols: ['Gate Entry number', 'Gate Entry Date', 'GRPO Date', 'PO Number', 'GRN Number', 'AP Invoice Number'] },
  { label: 'Vendor Details', cols: ['Vendor Code', 'Vendor Name', 'Vendor Country', 'Vendor Bill Number'] },
  { label: 'Item Details', cols: ['Item Code', 'Item Description', 'Item Group'] },
  { label: 'Value & Qty', cols: ['Quantity', 'Rate(INR)', 'Value(INR)'] },
  { label: 'Analysis', cols: ['Days(GRPO-GE)', 'Seq Exception(GE>GRPO)', 'Exceeds 3 days'] }
]

const ALL_COLS = COL_GROUPS.flatMap(g => g.cols)

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

function FlagChip({ val }) {
  const flagged = val === 1 || val === '1' || val === true
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
      flagged
        ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/40 dark:text-rose-400'
        : 'bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-600'
    }`}>
      {flagged ? '1' : '0'}
    </span>
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

export default function GateEntry({ data }) {
  const kpis   = data?.kpis   || {}
  const charts = data?.charts || {}
  const tables = data?.tables || []

  const pve    = charts.pass_vs_exception || { total: 0, segments: [] }
  const checks = charts.detailed_checks || []

  const mainTable = tables.find(t => t.title === 'Gate Entry Full Transaction List')
  const rows = mainTable?.rows || []

  const [searchTerm, setSearchTerm]         = useState('')
  const [currentPage, setCurrentPage]       = useState(1)
  const [sortCol, setSortCol]               = useState(null)
  const [sortDir, setSortDir]               = useState('asc')
  const [activeGroup, setActiveGroup]       = useState('All')
  const [showColFilters, setShowColFilters] = useState(false)
  const [colFilters, setColFilters]         = useState({})
  const [startDate, setStartDate]           = useState('')
  const [endDate, setEndDate]               = useState('')
  const ITEMS_PER_PAGE = 25

  const { order: colOrder, moveColumn } = useColumnOrder('gate-entry', ALL_COLS)
  const [dragCol, setDragCol]     = useState(null)
  const [dragOverCol, setDragOverCol] = useState(null)

  const handleColFilter = (col, val) => {
    setColFilters(prev => ({ ...prev, [col]: val }))
    setCurrentPage(1)
  }
  const clearColFilters = () => { setColFilters({}); setCurrentPage(1) }
  const activeColFilterCount = Object.values(colFilters).filter(v => v.trim()).length

  const visibleCols = useMemo(() => {
    const base = activeGroup === 'All'
      ? ALL_COLS
      : (COL_GROUPS.find(g => g.label === activeGroup)?.cols || ALL_COLS)
    const baseSet = new Set(base)
    return colOrder.filter(c => baseSet.has(c))
  }, [activeGroup, colOrder])

  const handleSort = (col) => {
    if (sortCol === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortCol(col); setSortDir('asc') }
    setCurrentPage(1)
  }

  const handleSearch = (e) => { setSearchTerm(e.target.value); setCurrentPage(1) }

  const filtered = useMemo(() => {
    const term = searchTerm.trim().toLowerCase()
    // 1. Global search across all columns
    let out = term
      ? rows.filter(r => Object.entries(r).some(([k, v]) => String(v).toLowerCase().includes(term)))
      : rows
    // 2. Date range filter
    if (startDate || endDate) {
      const start = startDate ? new Date(startDate) : null
      if (start) start.setHours(0, 0, 0, 0)
      const end = endDate ? new Date(endDate) : null
      if (end) end.setHours(23, 59, 59, 999)
      out = out.filter(r => {
        const dateVal = parseDate(r['Gate Entry Date'])
        if (!dateVal) return false
        if (start && dateVal < start) return false
        if (end && dateVal > end) return false
        return true
      })
    }
    // 3. Per-column filters (AND logic)
    const activeFilters = Object.entries(colFilters).filter(([, v]) => v.trim())
    if (activeFilters.length > 0) {
      out = out.filter(r =>
        activeFilters.every(([col, val]) =>
          String(r[col] ?? '').toLowerCase().includes(val.trim().toLowerCase())
        )
      )
    }
    // 4. Sort
    if (sortCol) {
      out = [...out].sort((a, b) => {
        const av = a[sortCol] ?? ''
        const bv = b[sortCol] ?? ''
        const an = parseFloat(av), bn = parseFloat(bv)
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

  const kpiCards = [
    { label: 'Gate-Entry GRPO Lines', value: kpis.gate_entry_grpo_lines, accent: 'blue', desc: 'Total transaction lines' },
    { label: 'Total Value(INR)', value: formatCurrency(kpis.total_value_inr), accent: 'blue', desc: 'Sum of matched GRPO values' },
    { label: 'Sequence Exceptions', value: kpis.sequence_exceptions, accent: (kpis.sequence_exceptions ?? 0) > 0 ? 'rose' : 'blue', desc: 'GE > GRPO chronological anomalies' },
    { label: 'Exceeds 3 day window', value: kpis.exceeds_3_day_window, accent: (kpis.exceeds_3_day_window ?? 0) > 0 ? 'amber' : 'blue', desc: 'Lag > 3 days between GE and GRPO' },
    { label: 'Unique PO Numbers', value: kpis.unique_po_numbers, accent: 'blue', desc: 'Distinct purchase orders linked' },
    { label: 'Unique GRN(GRPO Nos.)', value: kpis.unique_grn_numbers, accent: 'blue', desc: 'Distinct goods receipts processed' },
    { label: 'Unique AP Invoices', value: kpis.unique_ap_invoices, accent: 'blue', desc: 'Distinct AP invoices matched' },
    { label: 'Unique PO Flagged', value: kpis.unique_po_flagged, accent: (kpis.unique_po_flagged ?? 0) > 0 ? 'rose' : 'blue', desc: 'Unique POs with date errors' },
    { label: 'Unique GRN Flagged', value: kpis.unique_grn_flagged, accent: (kpis.unique_grn_flagged ?? 0) > 0 ? 'rose' : 'blue', desc: 'Unique GRNs with date errors' },
  ]

  const accentMap = {
    blue:  { bar: 'bg-blue-500',  text: 'text-blue-600 dark:text-blue-400'  },
    amber: { bar: 'bg-amber-500', text: 'text-amber-600 dark:text-amber-400' },
    rose:  { bar: 'bg-rose-500',  text: 'text-rose-600 dark:text-rose-400'   },
    green: { bar: 'bg-green-500', text: 'text-green-600 dark:text-green-400' },
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Gate Entry Check
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Chronological validation of transaction dates: Vendor Bill Date ≤ Gate Entry Date ≤ Goods Receipt Date ≤ AP Invoice Date
          </p>
        </div>
        <span className="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800 text-[11px] font-semibold text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          Live Audit
        </span>
      </div>

      <AiInsightBox section="gateentry" kpis={kpis} />

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {kpiCards.map((k) => {
          const ac = accentMap[k.accent] || accentMap.blue
          return (
            <div key={k.label}
              className="relative bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden flex flex-col justify-between">
              <div className={`absolute top-0 left-0 right-0 h-0.5 ${ac.bar}`} />
              <div>
                <p className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest leading-tight mb-2">
                  {k.label}
                </p>
                <p className={`text-lg font-black tracking-tight leading-none ${ac.text}`}>
                  {typeof k.value === 'number' ? k.value.toLocaleString() : k.value}
                </p>
              </div>
              {k.desc && <p className="text-[9px] text-slate-400 dark:text-slate-500 mt-2 leading-tight">{k.desc}</p>}
            </div>
          )
        })}
      </div>

      {/* Charts section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-800 dark:text-white">Audit Pass vs Exception Ratio</h3>
            <p className="text-xs text-slate-400 mt-0.5">Chronology verification outcome</p>
          </div>
          <div className="flex items-center justify-center my-6">
            <DonutChart
              segments={(pve.segments || []).map(s => ({
                ...s, color: s.label === 'Pass' ? CHART_COLORS.success : CHART_COLORS.risk,
              }))}
              centerText={`${kpis.integrity_pct ?? 0}%`}
              centerSub="Valid Chronology"
            />
          </div>
          <div className="space-y-2 text-xs border-t border-slate-100 dark:border-slate-850 pt-3">
            {(pve.segments || []).map(s => (
              <div key={s.label} className="flex justify-between items-center">
                <span className="flex items-center gap-2 text-slate-600 dark:text-slate-300 font-medium">
                  <span className={`w-2.5 h-2.5 rounded-full ${s.label === 'Pass' ? 'bg-green-600' : 'bg-rose-600'}`} />
                  {s.label === 'Pass' ? 'Correct Date Sequence' : 'Sequence Discrepancy (GE > GRPO / AP)'}
                </span>
                <span className="font-semibold text-slate-950 dark:text-white">{(s.value || 0).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-800 dark:text-white">Chronological Control Checks</h3>
            <p className="text-xs text-slate-400 mt-0.5">Performance of specific chronological validation rules</p>
          </div>
          <div className="space-y-4 my-6 flex-1 flex flex-col justify-center">
            {checks.map(c => {
              const colors = {
                'Total': 'bg-slate-500', 
                'GE = GRPO (same)': 'bg-emerald-600',
                'GE < GRPO (normal)': 'bg-blue-600', 
                'GE > GRPO (error)': 'bg-rose-600',
                'Missing GRPO Date': 'bg-amber-600', 
                'Missing Bill Date': 'bg-slate-400',
              }
              const progressColor = colors[c.label] || 'bg-slate-400'
              return (
                <div key={c.label} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold text-slate-600 dark:text-slate-300">
                    <span>{c.label}</span>
                    <span className="font-bold text-slate-950 dark:text-white">{(c.value || 0).toLocaleString()}</span>
                  </div>
                  <div className="bg-slate-100 dark:bg-slate-800/80 rounded-full h-3 overflow-hidden">
                    <div 
                      className={`h-full rounded-full ${progressColor} transition-all duration-500`}
                      style={{ width: `${Math.max(c.pct, 1)}%` }} 
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Details Table */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        {/* Table toolbar */}
        <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800 flex flex-col gap-3">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Gate Entry Reconciled Transaction List</h3>
              <p className="text-xs text-slate-400 mt-0.5">Chronology checks · cross-file links · value calculations</p>
            </div>
            <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
              {/* Global search */}
              <div className="relative">
                <svg className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none"
                  fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  placeholder="Search all columns…"
                  value={searchTerm}
                  onChange={handleSearch}
                  className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 w-44 transition"
                />
              </div>

              {/* Date Range Filter */}
              <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-800/60 p-1.5 rounded-lg border border-slate-200 dark:border-slate-700">
                <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 px-1 flex items-center gap-1">
                  <svg className="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  Date:
                </span>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => { setStartDate(e.target.value); setCurrentPage(1); }}
                  className="px-1.5 py-0.5 text-[10px] font-medium rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-750 dark:text-slate-250 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <span className="text-[10px] text-slate-400">—</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => { setEndDate(e.target.value); setCurrentPage(1); }}
                  className="px-1.5 py-0.5 text-[10px] font-medium rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-750 dark:text-slate-250 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                {(startDate || endDate) && (
                  <button
                    onClick={() => { setStartDate(''); setEndDate(''); setCurrentPage(1); }}
                    className="p-0.5 hover:bg-slate-200 dark:hover:bg-slate-700 rounded text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition"
                    title="Clear Date Filter"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Column filters toggle */}
              <button
                onClick={() => setShowColFilters(v => !v)}
                className={`relative inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold rounded-lg border transition-all duration-150 ${
                  showColFilters
                    ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                    : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800'
                }`}
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 010 2H4a1 1 0 01-1-1zM6 12a1 1 0 011-1h10a1 1 0 010 2H7a1 1 0 01-1-1zM10 20a1 1 0 011-1h2a1 1 0 010 2h-2a1 1 0 01-1-1z" />
                </svg>
                Column Filters
                {activeColFilterCount > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-rose-500 text-white text-[9px] font-bold flex items-center justify-center">
                    {activeColFilterCount}
                  </span>
                )}
              </button>
              {/* Clear all column filters */}
              {activeColFilterCount > 0 && (
                <button
                  onClick={clearColFilters}
                  className="px-2.5 py-1.5 text-[11px] font-semibold rounded-lg border border-rose-200 dark:border-rose-800/40 text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/20 hover:bg-rose-100 dark:hover:bg-rose-950/40 transition"
                >
                  Clear Filters
                </button>
              )}
            </div>
          </div>

          {/* Column group tabs */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {['All', ...COL_GROUPS.map(g => g.label)].map(g => (
              <button
                key={g}
                onClick={() => { setActiveGroup(g); setCurrentPage(1) }}
                className={`px-3 py-1 text-[11px] font-semibold rounded-full border transition-all duration-150 ${
                  activeGroup === g
                    ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                    : 'bg-white dark:bg-slate-900 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800'
                }`}
              >
                {g}
              </button>
            ))}
            <span className="ml-auto text-[11px] text-slate-400 dark:text-slate-500 font-medium">
              {filtered.length.toLocaleString()} of {rows.length.toLocaleString()} records
            </span>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto" style={{ maxHeight: '520px', overflowY: 'auto' }}>
          <table className="w-full text-left border-collapse text-xs">
            <thead className="sticky top-0 z-20 bg-slate-50 dark:bg-slate-800/95 backdrop-blur-sm">
              <tr>
                {visibleCols.map(c => (
                  <th
                    key={c}
                    draggable
                    onDragStart={(e) => { e.dataTransfer.effectAllowed = 'move'; setDragCol(c) }}
                    onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; if (dragOverCol !== c) setDragOverCol(c) }}
                    onDragLeave={() => setDragOverCol(prev => (prev === c ? null : prev))}
                    onDrop={(e) => { e.preventDefault(); if (dragCol && dragCol !== c) moveColumn(dragCol, c); setDragCol(null); setDragOverCol(null) }}
                    onDragEnd={() => { setDragCol(null); setDragOverCol(null) }}
                    onClick={() => handleSort(c)}
                    title="Click to sort · Drag to reorder"
                    className={`px-4 py-2.5 text-[10px] font-bold uppercase tracking-wider whitespace-nowrap cursor-grab active:cursor-grabbing select-none border-b border-slate-200 dark:border-slate-700 hover:text-slate-600 dark:hover:text-slate-300 transition-colors ${
                      colFilters[c]?.trim()
                        ? 'text-blue-600 dark:text-blue-400 bg-blue-50/60 dark:bg-blue-950/20'
                        : 'text-slate-700 dark:text-slate-300'
                    } ${dragCol === c ? 'opacity-40' : ''} ${dragOverCol === c && dragCol !== c ? 'bg-blue-100/70 dark:bg-blue-900/30 border-l-2 border-l-blue-500' : ''}`}
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
                        className={`w-full min-w-[80px] px-2 py-1 text-[11px] rounded border transition outline-none ${
                          colFilters[c]?.trim()
                            ? 'border-blue-400 dark:border-blue-600 bg-blue-50 dark:bg-blue-950/30 text-blue-800 dark:text-blue-300 placeholder-blue-400'
                            : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 placeholder-slate-300 dark:placeholder-slate-600'
                        } focus:border-blue-500 focus:ring-1 focus:ring-blue-500`}
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
                    {rows.length === 0 ? 'Upload files to populate this table.' : 'No records match your search.'}
                  </td>
                </tr>
              ) : paginated.map((r, i) => (
                <tr key={i} className="hover:bg-blue-50/30 dark:hover:bg-blue-950/10 transition-colors duration-100">
                  {visibleCols.map(c => {
                    const val = r[c]

                    if (['Seq Exception(GE>GRPO)', 'Exceeds 3 days'].includes(c)) {
                      const flagged = val === 1 || val === '1' || val === true
                      return (
                        <td key={c} className={`px-4 py-2 whitespace-nowrap text-center ${flagged ? 'bg-rose-50/40 dark:bg-rose-950/20' : ''}`}>
                          <FlagChip val={val} />
                        </td>
                      )
                    }

                    if (c === 'Quantity') return (
                      <td key={c} className="px-4 py-2 font-mono text-slate-800 dark:text-slate-200 font-medium">
                        <TruncatedCell value={typeof val === 'number' ? val.toLocaleString() : (val ?? '—')} />
                      </td>
                    )

                    if (['Rate(INR)', 'Value(INR)'].includes(c)) return (
                      <td key={c} className="px-4 py-2 font-mono text-slate-800 dark:text-slate-200 font-medium">
                        <TruncatedCell value={typeof val === 'number' ? formatCurrency(val) : (val ?? '—')} />
                      </td>
                    )

                    if (c === 'Days(GRPO-GE)') {
                      const num = parseInt(val)
                      const isNeg = !isNaN(num) && num < 0
                      const isHi = !isNaN(num) && num > 3
                      return (
                        <td key={c} className={`px-4 py-2 font-mono text-center ${isNeg ? 'bg-rose-50/30 dark:bg-rose-950/10' : isHi ? 'bg-amber-50/30 dark:bg-amber-950/10' : ''}`}>
                          <span className={
                            isNeg
                              ? 'text-rose-600 dark:text-rose-400 font-bold'
                              : isHi
                              ? 'text-amber-600 dark:text-amber-400 font-semibold'
                              : 'text-slate-800 dark:text-slate-200'
                          }>
                            {val === '' || val === null || val === undefined ? '—' : <TruncatedCell value={val} />}
                          </span>
                        </td>
                      )
                    }

                    const isNum = typeof val === 'number' || (!isNaN(parseFloat(val)) && isFinite(val) && !String(val).startsWith('0'))
                    return (
                      <td key={c} className={`px-4 py-2 text-slate-800 dark:text-slate-200 font-medium ${isNum ? 'font-mono' : ''}`}>
                        {val === null || val === undefined || val === '' ? '—' : <TruncatedCell value={val} />}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-5 py-3.5 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/20 flex items-center justify-between gap-4 flex-wrap">
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Showing <span className="font-semibold text-slate-800 dark:text-white">{startRec}</span>–<span className="font-semibold text-slate-800 dark:text-white">{endRec}</span> of <span className="font-semibold text-slate-800 dark:text-white">{filtered.length.toLocaleString()}</span> lines
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
            <span className="px-3 py-1.5 text-[11px] font-bold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800/40">
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
  )
}
