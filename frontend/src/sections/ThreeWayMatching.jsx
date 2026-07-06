import React, { useState, useEffect, useMemo } from 'react'
import { useStore } from '../store'
import { fetchThreeWayMatching } from '../api'

export default function ThreeWayMatching() {
  const { threeWayMatching, setThreeWayMatching } = useStore()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

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
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">3-Way Matching Dashboard</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
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
        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider leading-none">Total GRPO Lines</span>
          <span className="text-xl font-extrabold text-slate-950 dark:text-white mt-2">{formatNumber(kpis.total_grpo_lines)}</span>
        </div>
        
        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider leading-none">Perfect Match QTY</span>
          <span className="text-xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-2">{formatNumber(kpis.perfect_match_qty, 2)}</span>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider leading-none">Unique POs</span>
          <span className="text-xl font-extrabold text-slate-950 dark:text-white mt-2">{formatNumber(kpis.unique_po_numbers)}</span>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider leading-none">Unique GRNs</span>
          <span className="text-xl font-extrabold text-slate-950 dark:text-white mt-2">{formatNumber(kpis.unique_grpo_numbers)}</span>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <span className="text-[11px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider leading-none">AP Credit Notes</span>
          <span className="text-xl font-extrabold text-slate-950 dark:text-white mt-2">{formatNumber(kpis.unique_credit_notes)}</span>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <span className="text-[11px] font-bold text-rose-500 dark:text-rose-400 uppercase tracking-wider leading-none">Unique PO Flagged</span>
          <span className="text-xl font-extrabold text-rose-600 dark:text-rose-400 mt-2">{formatNumber(kpis.unique_po_flagged)}</span>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between">
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
                <th onClick={() => handleSort('grn_number')} className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 select-none">
                  GRN Number {sortField === 'grn_number' ? (sortAsc ? '↑' : '↓') : ''}
                </th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400">GRPO Date</th>
                <th onClick={() => handleSort('po_number')} className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 select-none">
                  PO Number {sortField === 'po_number' ? (sortAsc ? '↑' : '↓') : ''}
                </th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400">PO Date</th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400">Gate Entry Date</th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400">Invoice Date</th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400">AP Invoice Number</th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400">AP Credit Note</th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400">Vendo Code</th>
                <th onClick={() => handleSort('vendor_name')} className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 select-none">
                  Vendo Name {sortField === 'vendor_name' ? (sortAsc ? '↑' : '↓') : ''}
                </th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400">Vendor Country</th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400">Item code</th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400">Item description</th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400">Item group</th>
                <th onClick={() => handleSort('po_qty')} className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400 text-right cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 select-none">
                  PO qty {sortField === 'po_qty' ? (sortAsc ? '↑' : '↓') : ''}
                </th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400 text-right">GRPO qty</th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400 text-right">Inv qty</th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400 text-center">Qty PO &gt; GRPO</th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400 text-center">Qty GRPO &gt; Inv</th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400 text-right">PO Rate (INR)</th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400 text-right">GRPO Rate(INR)</th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400 text-right">INV Rate(INR)</th>
                <th className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400 text-center">Excess over 5%</th>
                <th onClick={() => handleSort('match_status')} className="px-4 py-3.5 font-semibold text-slate-500 dark:text-slate-400 text-center cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 select-none">
                  Match Status {sortField === 'match_status' ? (sortAsc ? '↑' : '↓') : ''}
                </th>
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
                      <td className="px-4 py-3 font-semibold text-slate-900 dark:text-slate-100">{row.grn_number}</td>
                      <td className="px-4 py-3 text-slate-500 dark:text-slate-400 whitespace-nowrap">{row.grpo_date || '—'}</td>
                      <td className="px-4 py-3 text-slate-700 dark:text-slate-300 font-medium">{row.po_number || '—'}</td>
                      <td className="px-4 py-3 text-slate-500 dark:text-slate-400 whitespace-nowrap">{row.po_date || '—'}</td>
                      <td className="px-4 py-3 text-slate-500 dark:text-slate-400 whitespace-nowrap">{row.gate_entry_date || '—'}</td>
                      <td className="px-4 py-3 text-slate-500 dark:text-slate-400 whitespace-nowrap">{row.invoice_date || '—'}</td>
                      <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{row.ap_invoice_number || '—'}</td>
                      <td className="px-4 py-3 text-slate-700 dark:text-slate-300 font-medium">{row.ap_credit_note || '—'}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-400 font-mono">{row.vendor_code || '—'}</td>
                      <td className="px-4 py-3 text-slate-700 dark:text-slate-300 max-w-[200px] truncate" title={row.vendor_name}>{row.vendor_name || '—'}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{row.vendor_country || '—'}</td>
                      <td className="px-4 py-3 text-slate-700 dark:text-slate-300 font-mono">{row.item_code || '—'}</td>
                      <td className="px-4 py-3 text-slate-500 dark:text-slate-400 max-w-[250px] truncate" title={row.item_description}>{row.item_description || '—'}</td>
                      <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{row.item_group || '—'}</td>
                      <td className="px-4 py-3 text-right font-medium text-slate-700 dark:text-slate-300">{formatNumber(row.po_qty)}</td>
                      <td className="px-4 py-3 text-right font-medium text-slate-700 dark:text-slate-300">{formatNumber(row.grpo_qty)}</td>
                      <td className="px-4 py-3 text-right font-medium text-slate-700 dark:text-slate-300">{formatNumber(row.inv_qty)}</td>
                      
                      <td className="px-4 py-3 text-center">
                        {row.qty_po_gt_grpo === 1 ? (
                          <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-900/50">Yes</span>
                        ) : (
                          <span className="text-slate-400 dark:text-slate-600">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {row.qty_grpo_gt_inv === 1 ? (
                          <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-200 dark:border-amber-900/50">Yes</span>
                        ) : (
                          <span className="text-slate-400 dark:text-slate-600">—</span>
                        )}
                      </td>

                      <td className="px-4 py-3 text-right font-semibold text-slate-700 dark:text-slate-300">₹{formatNumber(row.po_rate, 2)}</td>
                      <td className="px-4 py-3 text-right font-semibold text-slate-700 dark:text-slate-300">₹{formatNumber(row.grpo_rate, 2)}</td>
                      <td className="px-4 py-3 text-right font-semibold text-slate-700 dark:text-slate-300">₹{formatNumber(row.inv_rate, 2)}</td>
                      
                      <td className="px-4 py-3 text-center">
                        {isPriceFlagged ? (
                          <span className="inline-flex px-2 py-0.5 rounded text-[10px] font-extrabold bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300 border border-rose-200 dark:border-rose-900/50">Flagged</span>
                        ) : (
                          <span className="text-slate-400 dark:text-slate-600">—</span>
                        )}
                      </td>

                      <td className="px-4 py-3 text-center">
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
                    </tr>
                  )
                })
              ) : (
                <tr>
                  <td colSpan="24" className="text-center py-10 text-slate-500 dark:text-slate-400 font-medium">
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
    </div>
  )
}
