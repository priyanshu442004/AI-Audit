import React, { useState, useEffect, useMemo } from 'react'
import { useStore } from '../store'
import { fetchThreeWayMatching } from '../api'
import TruncatedCell from '../components/TruncatedCell'
import useColumnOrder from '../hooks/useColumnOrder'
import ExceptionModal from '../components/ExceptionModal'

const COLUMNS = [
  { id: 'grn_number',         label: 'GRN Number',        align: 'left',   sortable: true  },
  { id: 'grpo_date',          label: 'GRPO Date',         align: 'left',   sortable: false },
  { id: 'po_number',          label: 'PO Number',         align: 'left',   sortable: true  },
  { id: 'po_date',            label: 'PO Date',           align: 'left',   sortable: false },
  { id: 'gate_entry_date',    label: 'Gate Entry Date',   align: 'left',   sortable: false },
  { id: 'invoice_date',       label: 'Invoice Date',      align: 'left',   sortable: false },
  { id: 'ap_invoice_number',  label: 'AP Invoice Number', align: 'left',   sortable: false },
  { id: 'ap_credit_note',     label: 'AP Credit Note',    align: 'left',   sortable: false },
  { id: 'remarks',            label: 'Remarks',           align: 'left',   sortable: false },
  { id: 'vendor_code',        label: 'Vendo Code',        align: 'left',   sortable: false },
  { id: 'vendor_name',        label: 'Vendo Name',        align: 'left',   sortable: true  },
  { id: 'vendor_country',     label: 'Vendor Country',    align: 'left',   sortable: false },
  { id: 'item_code',          label: 'Item code',         align: 'left',   sortable: false },
  { id: 'item_description',   label: 'Item description',  align: 'left',   sortable: false },
  { id: 'item_group',         label: 'Item group',        align: 'left',   sortable: false },
  { id: 'po_qty',             label: 'PO qty',            align: 'right',  sortable: true  },
  { id: 'grpo_qty',           label: 'GRPO qty',          align: 'right',  sortable: false },
  { id: 'inv_qty',            label: 'Inv qty',           align: 'right',  sortable: false },
  { id: 'qty_po_gt_grpo',     label: 'Qty PO > GRPO',     align: 'center', sortable: false },
  { id: 'qty_grpo_gt_inv',    label: 'Qty GRPO > Inv',    align: 'center', sortable: false },
  { id: 'po_rate',            label: 'PO Rate (INR)',     align: 'right',  sortable: false },
  { id: 'grpo_rate',          label: 'GRPO Rate(INR)',    align: 'right',  sortable: false },
  { id: 'inv_rate',           label: 'INV Rate(INR)',     align: 'right',  sortable: false },
  { id: 'excess_over_5',      label: 'Excess over 5%',    align: 'center', sortable: false },
  { id: 'match_status',       label: 'Match Status',      align: 'center', sortable: true  },
]
const ALL_COLS = COLUMNS.map(c => c.id)
const COL_META = Object.fromEntries(COLUMNS.map(c => [c.id, c]))

export default function ThreeWayMatching() {
  const { threeWayMatching, setThreeWayMatching } = useStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Modal State
  const [showExceptionModal, setShowExceptionModal] = useState(false)
  const [exceptionTitle, setExceptionTitle] = useState('')
  const [exceptionModalRows, setExceptionModalRows] = useState([])
  const [isModalException, setIsModalException] = useState(true)

  // Filters & Search State
  const [searchQuery, setSearchQuery] = useState('')
  const [matchStatusFilter, setMatchStatusFilter] = useState('ALL') // 'ALL' | 'Perfect match' | 'Variance'
  const [excessFilter, setExcessFilter] = useState('ALL') // 'ALL' | 'FLAGGED' | 'OK'
  const [countryFilter, setCountryFilter] = useState('ALL') // 'ALL' | 'India' | 'USA'
  
  // Sorting State
  const [sortField, setSortField] = useState('grn_number')
  const [sortAsc, setSortAsc] = useState(true)

  // Pagination State
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)

  const { order: colOrder, moveColumn } = useColumnOrder('three-way-matching', ALL_COLS)
  const [dragCol, setDragCol]     = useState(null)
  const [dragOverCol, setDragOverCol] = useState(null)
  const visibleCols = colOrder

  const openExceptionModal = (titleStr, filterFn, dedupeKey, isExc = true) => {
    setExceptionTitle(titleStr)
    setIsModalException(isExc)
    let res = rows.filter(filterFn)
    if (dedupeKey) {
      const seen = new Set()
      res = res.filter(r => {
        const kVal = r[dedupeKey]
        if (!kVal || kVal === '—' || seen.has(kVal)) return false
        seen.add(kVal)
        return true
      })
    }
    setExceptionModalRows(res)
    setShowExceptionModal(true)
  }

  // Load data if not cached
  useEffect(() => {
    if (threeWayMatching) return
    setLoading(true)
    setError(null)
    fetchThreeWayMatching()
      .then(res => {
        setThreeWayMatching(res)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message || 'Failed to load 3-way matching analysis')
        setLoading(false)
      })
  }, [threeWayMatching, setThreeWayMatching])

  // Extract raw rows and KPIs
  const { rows = [], kpis = {} } = threeWayMatching || {}

  // Filter logic
  const filteredRows = useMemo(() => {
    return rows.filter(row => {
      // 1. Text Search
      const searchLower = searchQuery.toLowerCase().trim()
      const matchesSearch = !searchLower || 
        String(row.grn_number || '').toLowerCase().includes(searchLower) ||
        String(row.po_number || '').toLowerCase().includes(searchLower) ||
        String(row.ap_invoice_number || '').toLowerCase().includes(searchLower) ||
        String(row.vendor_name || '').toLowerCase().includes(searchLower) ||
        String(row.vendor_code || '').toLowerCase().includes(searchLower) ||
        String(row.item_code || '').toLowerCase().includes(searchLower)

      // 2. Match Status Filter
      const matchesStatus = matchStatusFilter === 'ALL' || row.match_status === matchStatusFilter

      // 3. Excess over 5% filter
      const matchesExcess = excessFilter === 'ALL' || 
        (excessFilter === 'FLAGGED' && row.excess_over_5 === 1) ||
        (excessFilter === 'OK' && row.excess_over_5 === 0)

      // 4. Country filter
      const matchesCountry = countryFilter === 'ALL' || row.vendor_country === countryFilter

      return matchesSearch && matchesStatus && matchesExcess && matchesCountry
    })
  }, [rows, searchQuery, matchStatusFilter, excessFilter, countryFilter])

  // Sorting logic
  const sortedRows = useMemo(() => {
    const sorted = [...filteredRows]
    if (!sortField) return sorted

    sorted.sort((a, b) => {
      let valA = a[sortField]
      let valB = b[sortField]

      // Coerce to appropriate types
      if (typeof valA === 'string') {
        valA = valA.trim().toLowerCase()
        valB = String(valB || '').trim().toLowerCase()
      } else {
        valA = valA ?? 0
        valB = valB ?? 0
      }

      if (valA < valB) return sortAsc ? -1 : 1
      if (valA > valB) return sortAsc ? 1 : -1
      return 0
    })
    return sorted
  }, [filteredRows, sortField, sortAsc])

  // Pagination logic
  const paginatedRows = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize
    return sortedRows.slice(startIndex, startIndex + pageSize)
  }, [sortedRows, currentPage, pageSize])

  const totalPages = Math.max(1, Math.ceil(sortedRows.length / pageSize))

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery, matchStatusFilter, excessFilter, countryFilter, pageSize])

  // Export to CSV helper
  const handleDownloadCSV = () => {
    if (sortedRows.length === 0) return

    const headers = [
      'GRN Number', 'GRPO Date', 'PO Number', 'PO Date', 'Gate Entry Date', 
      'Invoice Date', 'AP Invoice Number', 'AP Credit Note', 'Vendo Code', 
      'Vendo Name', 'Vendor Country', 'Item code', 'Item description', 
      'Item group', 'PO qty', 'GRPO qty', 'Inv qty', 'Qty PO > GRPO', 
      'Qty GRPO > Inv', 'PO Rate (INR)', 'GRPO Rate(INR)', 'INV Rate(INR)', 'Excess over 5%', 
      'Match Status'
    ]

    const csvRows = [
      headers.join(','),
      ...sortedRows.map(row => {
        return [
          `"${row.grn_number || ''}"`,
          `"${row.grpo_date || ''}"`,
          `"${row.po_number || ''}"`,
          `"${row.po_date || ''}"`,
          `"${row.gate_entry_date || ''}"`,
          `"${row.invoice_date || ''}"`,
          `"${row.ap_invoice_number || ''}"`,
          `"${row.ap_credit_note || ''}"`,
          `"${row.vendor_code || ''}"`,
          `"${row.vendor_name || ''}"`,
          `"${row.vendor_country || ''}"`,
          `"${row.item_code || ''}"`,
          `"${(row.item_description || '').replace(/"/g, '""')}"`,
          `"${row.item_group || ''}"`,
          row.po_qty ?? 0,
          row.grpo_qty ?? 0,
          row.inv_qty ?? 0,
          row.qty_po_gt_grpo ?? 0,
          row.qty_grpo_gt_inv ?? 0,
          row.po_rate ?? 0,
          row.grpo_rate ?? 0,
          row.inv_rate ?? 0,
          row.excess_over_5 ?? 0,
          `"${row.match_status || ''}"`
        ].join(',')
      })
    ]

    const blob = new Blob([csvRows.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.setAttribute('href', url)
    link.setAttribute('download', '3_way_matching_report.csv')
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Handle header sorting click
  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc)
    } else {
      setSortField(field)
      setSortAsc(true)
    }
  }

  const formatNumber = (num, decimals = 0) => {
    if (num == null || isNaN(num)) return '0'
    return Number(num).toLocaleString('en-IN', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    })
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400"></div>
        <p className="mt-4 text-slate-500 dark:text-slate-400 font-medium">Computing 3-Way Matching Analytics...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 rounded-2xl bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-800/30 text-rose-800 dark:text-rose-300">
        <h3 className="text-lg font-bold">Analysis Failed</h3>
        <p className="mt-2 text-sm">{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Title block */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Comprehensive audit comparing Purchase Orders (PO), Goods Receipts (GRPO), and AP Invoices to verify rate and quantity integrity.
          </p>
        </div>
        <button
          onClick={handleDownloadCSV}
          disabled={sortedRows.length === 0}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:hover:bg-blue-600 text-white rounded-xl text-sm font-bold shadow-md transition duration-200"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
          </svg>
          Export CSV ({formatNumber(sortedRows.length)} rows)
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-4">
        <div 
          onClick={() => openExceptionModal('Total GRPO Lines', r => true, null, false)}
          className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between cursor-pointer hover:border-blue-500/50 hover:shadow-md active:scale-[0.98] transition-all"
        >
          <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider leading-none">Total GRPO Lines</span>
          <span className="text-xl font-extrabold text-slate-950 dark:text-white mt-2">{formatNumber(kpis.total_grpo_lines)}</span>
        </div>
        
        <div 
          onClick={() => openExceptionModal('Perfect Match Lines', r => r.match_status === 'Perfect match' || r.match_status === 'Matched', null, false)}
          className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between cursor-pointer hover:border-emerald-500/50 hover:shadow-md active:scale-[0.98] transition-all"
        >
          <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider leading-none">Perfect Match QTY</span>
          <span className="text-xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-2">{formatNumber(kpis.perfect_match_qty, 2)}</span>
        </div>

        <div 
          onClick={() => openExceptionModal('Unique Purchase Orders', r => r.po_number && r.po_number !== '—', 'po_number', false)}
          className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between cursor-pointer hover:border-blue-500/50 hover:shadow-md active:scale-[0.98] transition-all"
        >
          <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider leading-none">Unique POs</span>
          <span className="text-xl font-extrabold text-slate-950 dark:text-white mt-2">{formatNumber(kpis.unique_po_numbers)}</span>
        </div>

        <div 
          onClick={() => openExceptionModal('Unique Goods Receipts (GRPO)', r => r.grn_number && r.grn_number !== '—', 'grn_number', false)}
          className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between cursor-pointer hover:border-blue-500/50 hover:shadow-md active:scale-[0.98] transition-all"
        >
          <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider leading-none">Unique GRNs</span>
          <span className="text-xl font-extrabold text-slate-950 dark:text-white mt-2">{formatNumber(kpis.unique_grpo_numbers)}</span>
        </div>

        <div 
          onClick={() => openExceptionModal('AP Credit Notes', r => r.ap_credit_note && r.ap_credit_note !== '—', 'ap_credit_note', false)}
          className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between cursor-pointer hover:border-blue-500/50 hover:shadow-md active:scale-[0.98] transition-all"
        >
          <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider leading-none">AP Credit Notes</span>
          <span className="text-xl font-extrabold text-slate-950 dark:text-white mt-2">{formatNumber(kpis.unique_credit_notes)}</span>
        </div>

        <div 
          onClick={() => openExceptionModal('Unique POs with Matching Variances', r => r.qty_po_gt_grpo === 1 || r.qty_grpo_gt_inv === 1 || r.excess_over_5 === 1 || r.match_status === 'Variance', 'po_number', true)}
          className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between cursor-pointer hover:border-rose-500/50 hover:shadow-md active:scale-[0.98] transition-all"
        >
          <span className="text-[11px] font-bold text-rose-500 dark:text-rose-400 uppercase tracking-wider leading-none">Unique PO Flagged</span>
          <span className="text-xl font-extrabold text-rose-600 dark:text-rose-400 mt-2">{formatNumber(kpis.unique_po_flagged)}</span>
        </div>

        <div 
          onClick={() => openExceptionModal('Unique GRNs with Matching Variances', r => r.qty_po_gt_grpo === 1 || r.qty_grpo_gt_inv === 1 || r.excess_over_5 === 1 || r.match_status === 'Variance', 'grn_number', true)}
          className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between cursor-pointer hover:border-rose-500/50 hover:shadow-md active:scale-[0.98] transition-all"
        >
          <span className="text-[11px] font-bold text-rose-500 dark:text-rose-400 uppercase tracking-wider leading-none">Unique GRN Flagged</span>
          <span className="text-xl font-extrabold text-rose-600 dark:text-rose-400 mt-2">{formatNumber(kpis.unique_grn_flagged)}</span>
        </div>
      </div>

      {/* Filter and Search controls */}
      <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search bar */}
          <div className="relative">
            <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-400 pointer-events-none">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </span>
            <input
              type="text"
              placeholder="Search PO, GRN, Inv or Vendor..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm transition-all"
            />
          </div>

          {/* Match Status Filter */}
          <div className="flex flex-col gap-1">
            <select
              value={matchStatusFilter}
              onChange={e => setMatchStatusFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm transition-all"
            >
              <option value="ALL">All Match Statuses</option>
              <option value="Perfect match">Perfect Match</option>
              <option value="Variance">Variance</option>
            </select>
          </div>

          {/* Excess rate Filter */}
          <div className="flex flex-col gap-1">
            <select
              value={excessFilter}
              onChange={e => setExcessFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm transition-all"
            >
              <option value="ALL">All Rates Variance</option>
              <option value="FLAGGED">Excess Price &gt; 5% Flagged</option>
              <option value="OK">Rate Normal (OK)</option>
            </select>
          </div>

          {/* Country Filter */}
          <div className="flex flex-col gap-1">
            <select
              value={countryFilter}
              onChange={e => setCountryFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm transition-all"
            >
              <option value="ALL">All Countries</option>
              <option value="India">India</option>
              <option value="USA">USA</option>
            </select>
          </div>
        </div>

        {/* Info of current filter counts */}
        <div className="text-xs text-slate-400 dark:text-slate-500 flex justify-between">
          <span>Showing {formatNumber(sortedRows.length)} of {formatNumber(rows.length)} records</span>
          {sortedRows.length > 0 && <span>Page {currentPage} of {totalPages}</span>}
        </div>
      </div>

      {/* Audit Log Data Table */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="overflow-x-auto max-h-[600px] scrollbar-thin">
          <table className="w-full text-left border-collapse text-xs">
            <thead className="bg-slate-50 dark:bg-slate-950 sticky top-0 z-10 border-b border-slate-200 dark:border-slate-800">
              <tr>
                {visibleCols.map(c => {
                  const meta = COL_META[c]
                  const alignClass = meta.align === 'right' ? ' text-right' : meta.align === 'center' ? ' text-center' : ''
                  const sortHoverClass = meta.sortable ? ' hover:bg-slate-100 dark:hover:bg-slate-800' : ''
                  return (
                    <th
                      key={c}
                      draggable
                      onDragStart={(e) => { e.dataTransfer.effectAllowed = 'move'; setDragCol(c) }}
                      onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; if (dragOverCol !== c) setDragOverCol(c) }}
                      onDragLeave={() => setDragOverCol(prev => (prev === c ? null : prev))}
                      onDrop={(e) => { e.preventDefault(); if (dragCol && dragCol !== c) moveColumn(dragCol, c); setDragCol(null); setDragOverCol(null) }}
                      onDragEnd={() => { setDragCol(null); setDragOverCol(null) }}
                      onClick={meta.sortable ? () => handleSort(c) : undefined}
                      title={meta.sortable ? 'Click to sort · Drag to reorder' : 'Drag to reorder'}
                      className={`px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400 cursor-grab active:cursor-grabbing select-none${alignClass}${sortHoverClass}${dragCol === c ? ' opacity-40' : ''}${dragOverCol === c && dragCol !== c ? ' bg-blue-100/70 dark:bg-blue-900/30 border-l-2 border-l-blue-500' : ''}`}
                    >
                      {meta.label} {meta.sortable && sortField === c ? (sortAsc ? '↑' : '↓') : ''}
                    </th>
                  )
                })}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {paginatedRows.length > 0 ? (
                paginatedRows.map((row, idx) => {
                  const isPriceFlagged = row.excess_over_5 === 1
                  return (
                    <tr
                      key={`${row.grn_number}_${row.item_code}_${idx}`}
                      className={`hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors ${
                        isPriceFlagged ? 'bg-amber-50/20 dark:bg-amber-950/5' : ''
                      }`}
                    >
                      {visibleCols.map(c => {
                        if (c === 'grn_number') return (
                          <td key={c} className="px-4 py-3 font-semibold text-slate-900 dark:text-slate-100">
                            <TruncatedCell value={row.grn_number} />
                          </td>
                        )
                        if (c === 'grpo_date') return (
                          <td key={c} className="px-4 py-3 text-slate-500 dark:text-slate-400">
                            <TruncatedCell value={row.grpo_date} />
                          </td>
                        )
                        if (c === 'po_number') return (
                          <td key={c} className="px-4 py-3 text-slate-700 dark:text-slate-300 font-medium">
                            <TruncatedCell value={row.po_number} />
                          </td>
                        )
                        if (c === 'po_date') return (
                          <td key={c} className="px-4 py-3 text-slate-500 dark:text-slate-400">
                            <TruncatedCell value={row.po_date} />
                          </td>
                        )
                        if (c === 'gate_entry_date') return (
                          <td key={c} className="px-4 py-3 text-slate-500 dark:text-slate-400">
                            <TruncatedCell value={row.gate_entry_date} />
                          </td>
                        )
                        if (c === 'invoice_date') return (
                          <td key={c} className="px-4 py-3 text-slate-500 dark:text-slate-400">
                            <TruncatedCell value={row.invoice_date} />
                          </td>
                        )
                        if (c === 'ap_invoice_number') return (
                          <td key={c} className="px-4 py-3 text-slate-700 dark:text-slate-300">
                            <TruncatedCell value={row.ap_invoice_number} />
                          </td>
                        )
                        if (c === 'ap_credit_note') return (
                          <td key={c} className="px-4 py-3 text-slate-700 dark:text-slate-300 font-medium">
                            <TruncatedCell value={row.ap_credit_note} />
                          </td>
                        )
                        if (c === 'vendor_code') return (
                          <td key={c} className="px-4 py-3 text-slate-600 dark:text-slate-400 font-mono">
                            <TruncatedCell value={row.vendor_code} />
                          </td>
                        )
                        if (c === 'vendor_name') return (
                          <td key={c} className="px-4 py-3 text-slate-700 dark:text-slate-300 max-w-[200px]">
                            <TruncatedCell value={row.vendor_name} />
                          </td>
                        )
                        if (c === 'vendor_country') return (
                          <td key={c} className="px-4 py-3 text-slate-600 dark:text-slate-400">
                            <TruncatedCell value={row.vendor_country} />
                          </td>
                        )
                        if (c === 'item_code') return (
                          <td key={c} className="px-4 py-3 text-slate-700 dark:text-slate-300 font-mono">
                            <TruncatedCell value={row.item_code} />
                          </td>
                        )
                        if (c === 'item_description') return (
                          <td key={c} className="px-4 py-3 text-slate-500 dark:text-slate-400 max-w-[250px]">
                            <TruncatedCell value={row.item_description} />
                          </td>
                        )
                        if (c === 'item_group') return (
                          <td key={c} className="px-4 py-3 text-slate-600 dark:text-slate-400">
                            <TruncatedCell value={row.item_group} />
                          </td>
                        )
                        if (c === 'po_qty') return (
                          <td key={c} className="px-4 py-3 text-right font-medium text-slate-700 dark:text-slate-300">
                            <TruncatedCell value={formatNumber(row.po_qty)} />
                          </td>
                        )
                        if (c === 'grpo_qty') return (
                          <td key={c} className="px-4 py-3 text-right font-medium text-slate-700 dark:text-slate-300">
                            <TruncatedCell value={formatNumber(row.grpo_qty)} />
                          </td>
                        )
                        if (c === 'inv_qty') return (
                          <td key={c} className="px-4 py-3 text-right font-medium text-slate-700 dark:text-slate-300">
                            <TruncatedCell value={formatNumber(row.inv_qty)} />
                          </td>
                        )
                        if (c === 'qty_po_gt_grpo') return (
                          <td key={c} className="px-4 py-3 text-center">
                            {row.qty_po_gt_grpo === 1 ? (
                              <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-900/50">Yes</span>
                            ) : (
                              <span className="text-slate-400 dark:text-slate-600">—</span>
                            )}
                          </td>
                        )
                        if (c === 'qty_grpo_gt_inv') return (
                          <td key={c} className="px-4 py-3 text-center">
                            {row.qty_grpo_gt_inv === 1 ? (
                              <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-900/50">Yes</span>
                            ) : (
                              <span className="text-slate-400 dark:text-slate-600">—</span>
                            )}
                          </td>
                        )
                        if (c === 'po_rate') return (
                          <td key={c} className="px-4 py-3 text-right font-semibold text-slate-700 dark:text-slate-300">
                            <TruncatedCell value={`₹${formatNumber(row.po_rate, 2)}`} />
                          </td>
                        )
                        if (c === 'grpo_rate') return (
                          <td key={c} className="px-4 py-3 text-right font-semibold text-slate-700 dark:text-slate-300">
                            <TruncatedCell value={`₹${formatNumber(row.grpo_rate, 2)}`} />
                          </td>
                        )
                        if (c === 'inv_rate') return (
                          <td key={c} className="px-4 py-3 text-right font-semibold text-slate-700 dark:text-slate-300">
                            <TruncatedCell value={`₹${formatNumber(row.inv_rate, 2)}`} />
                          </td>
                        )
                        if (c === 'excess_over_5') return (
                          <td key={c} className="px-4 py-3 text-center">
                            {isPriceFlagged ? (
                              <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-extrabold bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300 border border-rose-200 dark:border-rose-900/50">Flagged</span>
                            ) : (
                              <span className="text-slate-400 dark:text-slate-600">—</span>
                            )}
                          </td>
                        )
                        if (c === 'match_status') return (
                          <td key={c} className="px-4 py-3 text-center">
                            {row.match_status === 'Perfect match' ? (
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-400">
                                Perfect Match
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/30 dark:text-amber-400">
                                Variance
                              </span>
                            )}
                          </td>
                        )
                        return (
                          <td key={c} className="px-4 py-3 text-slate-600 dark:text-slate-400">
                            <TruncatedCell value={row[c]} />
                          </td>
                        )
                      })}
                    </tr>
                  )
                })
              ) : (
                <tr>
                  <td colSpan={visibleCols.length} className="text-center py-10 text-slate-500 dark:text-slate-400 font-medium">
                    No rows match current search and filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination bar */}
        {sortedRows.length > 0 && (
          <div className="px-5 py-4 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-50/50 dark:bg-slate-950/20">
            <div className="flex items-center gap-2">
              <span className="text-slate-500 dark:text-slate-400 text-xs">Rows per page:</span>
              <select
                value={pageSize}
                onChange={e => {
                  setPageSize(Number(e.target.value))
                  setCurrentPage(1)
                }}
                className="px-2.5 py-1 text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300"
              >
                <option value={20}>20</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-850 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
                title="First Page"
              >
                <svg className="w-4 h-4 text-slate-600 dark:text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M18.75 19.5l-7.5-7.5 7.5-7.5m-6 15L5.25 12l7.5-7.5" />
                </svg>
              </button>
              
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-850 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
                title="Previous Page"
              >
                <svg className="w-4 h-4 text-slate-600 dark:text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
                </svg>
              </button>

              <span className="text-xs text-slate-600 dark:text-slate-300 px-2 font-medium">
                {currentPage} / {totalPages}
              </span>

              <button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-850 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
                title="Next Page"
              >
                <svg className="w-4 h-4 text-slate-600 dark:text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              </button>

              <button
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
                className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-850 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-transparent transition-colors"
                title="Last Page"
              >
                <svg className="w-4 h-4 text-slate-600 dark:text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.25l7.5 7.5-7.5 7.5m6-15l7.5 7.5-7.5 7.5" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Exception Modal */}
      <ExceptionModal
        isOpen={showExceptionModal}
        onClose={() => setShowExceptionModal(false)}
        title={exceptionTitle}
        subtitle="Detailed 3-Way Matching records for selected metric"
        columns={ALL_COLS}
        rows={exceptionModalRows}
        filenamePrefix="Three_Way_Matching_Records"
        isException={isModalException}
      />
    </div>
  )
}
