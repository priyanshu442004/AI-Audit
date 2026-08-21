import React, { useState, useMemo } from 'react'
import AiInsightBox from '../components/AiInsightBox'
import TruncatedCell from '../components/TruncatedCell'
import useColumnOrder from '../hooks/useColumnOrder'
import ExportModal from '../components/ExportModal'
import ExceptionModal from '../components/ExceptionModal'
import LineItemSourceTraceModal from '../components/LineItemSourceTraceModal'
import PoMissingView from './PoMissingView'
import { RefreshCw, FileSpreadsheet, AlertTriangle, Filter, Layers, FileWarning } from 'lucide-react'

const COL_GROUPS = [
  {
    label: 'PO Details',
    cols: ['PO No', 'PO Series', 'Posting Date', 'Delivery Date', 'Document Date', 'Branch', 'Document Status', 'Canceled Status']
  },
  {
    label: 'Vendor & Item',
    cols: ['Vendor Group', 'Vendor Code', 'Vendor Name', 'Item Group', 'Item Code', 'Item Description', 'UOM']
  },
  {
    label: 'Quantities & Rates',
    cols: ['PO Qty', 'Open Qty', 'GRN Qty', 'PO Price', 'GRN Price', 'Excess Rate', 'Excess Rate Variation %', 'Rate Difference']
  },
  {
    label: 'Values & Totals',
    cols: ['Document Currency', 'Document Rate', 'Line Total', 'GRN Line Total', 'Excess Price', 'Excess Price Variation %', 'Line Total Difference', 'Document Total']
  },
  {
    label: 'Audit Flags',
    cols: ['GRN No', 'PO Monitoring Status', 'Holiday & Sunday Exception', 'Excess QTY', 'Excess Qty Variation %', 'QTY Difference']
  }
]

// Note: 'Key' is omitted from ALL_COLS to hide it from the UI while keeping it in the underlying data objects
const ALL_COLS = [
  'PO No', 'GRN No', 'PO Series', 'Posting Date', 'Delivery Date',
  'Document Date', 'Branch', 'Document Status', 'Canceled Status',
  'Vendor Group', 'Vendor Code', 'Vendor Name', 'Item Group', 'Item Code',
  'Item Description', 'UOM', 'PO Qty', 'Open Qty', 'PO Monitoring Status',
  'Holiday & Sunday Exception', 'GRN Qty', 'Excess QTY', 'Excess Qty Variation %',
  'QTY Difference', 'PO Price', 'GRN Price', 'Excess Rate', 'Excess Rate Variation %',
  'Rate Difference', 'Document Currency', 'Document Rate', 'Line Total',
  'GRN Line Total', 'Excess Price', 'Excess Price Variation %',
  'Line Total Difference', 'Document Total'
]

const NUMERIC_COLS = [
  'PO Qty', 'Open Qty', 'GRN Qty', 'Excess QTY', 'Excess Qty Variation %',
  'PO Price', 'GRN Price', 'Excess Rate', 'Excess Rate Variation %',
  'Document Rate', 'Line Total', 'GRN Line Total', 'Excess Price',
  'Excess Price Variation %', 'Document Total'
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

export default function PoStatus({ data }) {
  const kpis   = data?.kpis   || {}
  const tables = data?.tables || []

  const mainTable = tables.find(t => t.title === 'Purchase Order Status — Full Audit Detail') || tables[0]
  const rows = mainTable?.rows || []

  // Interactive Header Filters State
  const [viewMode, setViewMode]                 = useState('main') // 'main' | 'po_missing'
  const [vendorTypeFilter, setVendorTypeFilter] = useState('all') // 'all' | 'indian' | 'foreign'
  const [holidayFilter, setHolidayFilter]       = useState('all') // 'all' | 'holiday_only'
  const [excess5PctFilter, setExcess5PctFilter] = useState('all') // 'all' | 'qty' | 'rate' | 'price'

  const [searchTerm, setSearchTerm]         = useState('')
  const [currentPage, setCurrentPage]       = useState(1)
  const [sortCol, setSortCol]               = useState(null)
  const [sortDir, setSortDir]               = useState('asc')
  const [activeGroup, setActiveGroup]       = useState('All')
  const [showColFilters, setShowColFilters] = useState(false)
  const [colFilters, setColFilters]         = useState({})
  const [startDate, setStartDate]           = useState('')
  const [endDate, setEndDate]               = useState('')
  const [refreshing, setRefreshing]         = useState(false)
  
  // Modals state
  const [showExportModal, setShowExportModal]       = useState(false)
  const [showExceptionModal, setShowExceptionModal] = useState(false)
  const [exceptionTitle, setExceptionTitle]         = useState('')
  const [exceptionModalRows, setExceptionModalRows] = useState([])
  const [isModalException, setIsModalException]     = useState(true)

  // 3-Sheet Line Item Source Trace Modal
  const [showTraceModal, setShowTraceModal] = useState(false)
  const [selectedTraceRow, setSelectedTraceRow] = useState(null)

  const ITEMS_PER_PAGE = 25

  const { order: colOrder, moveColumn } = useColumnOrder('po-status-v2', ALL_COLS)
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

  const handleRefresh = async () => {
    setRefreshing(true)
    await new Promise(r => setTimeout(r, 600))
    setRefreshing(false)
  }

  // Reactive Multi-Filter Pipeline
  const filtered = useMemo(() => {
    let out = rows

    // 1. Vendor Type Filter
    if (vendorTypeFilter === 'indian') {
      out = out.filter(r => (r['Document Currency'] || 'INR') === 'INR')
    } else if (vendorTypeFilter === 'foreign') {
      out = out.filter(r => (r['Document Currency'] || 'INR') !== 'INR')
    }

    // 2. Holiday Exception Filter
    if (holidayFilter === 'holiday_only') {
      out = out.filter(r => (r['Holiday & Sunday Exception'] || '').startsWith('Holiday'))
    }

    // 3. 5% Financial Exception Filter
    if (excess5PctFilter === 'qty') {
      out = out.filter(r => r['QTY Difference'] === 'Exception' || (parseFloat(String(r['Excess Qty Variation %']).replace(/,/g, '')) > 5))
    } else if (excess5PctFilter === 'rate') {
      out = out.filter(r => r['Rate Difference'] === 'Exception' || (parseFloat(String(r['Excess Rate Variation %']).replace(/,/g, '')) > 5))
    } else if (excess5PctFilter === 'price') {
      out = out.filter(r => r['Line Total Difference'] === 'Exception' || (parseFloat(String(r['Excess Price Variation %']).replace(/,/g, '')) > 5))
    }

    // Search term filter
    const term = searchTerm.trim().toLowerCase()
    if (term) {
      out = out.filter(r => Object.entries(r).some(([k, v]) => k !== 'Key' && String(v).toLowerCase().includes(term)))
    }

    // Date range filter
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

    // Column filters
    const activeFilters = Object.entries(colFilters).filter(([, v]) => v.trim())
    if (activeFilters.length > 0) {
      out = out.filter(r =>
        activeFilters.every(([col, val]) =>
          String(r[col] ?? '').toLowerCase().includes(val.trim().toLowerCase())
        )
      )
    }

    // Sorting
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
  }, [rows, vendorTypeFilter, holidayFilter, excess5PctFilter, searchTerm, colFilters, sortCol, sortDir, startDate, endDate])

  // Reactive Dynamic KPI Recalculation based on filtered rows
  const dynamicKpis = useMemo(() => {
    const uniquePos = new Set(filtered.map(r => r['PO No']).filter(p => p && p !== '0' && p !== '—')).size
    const totalPoVal = filtered.reduce((acc, r) => acc + (parseFloat(String(r['Line Total']).replace(/,/g, '')) || 0), 0)
    const canceledCount = filtered.filter(r => r['Canceled Status'] === 'Yes').length
    const holidayCount = filtered.filter(r => (r['Holiday & Sunday Exception'] || '').startsWith('Holiday')).length
    const sundayCount = filtered.filter(r => r['Holiday & Sunday Exception'] === 'Sunday').length
    
    const cntExcessQty = filtered.filter(r => r['QTY Difference'] === 'Exception').length
    const sumExcessQty = filtered.reduce((acc, r) => acc + (parseFloat(String(r['Excess QTY']).replace(/,/g, '')) || 0), 0)
    
    const cntExcessRate = filtered.filter(r => r['Rate Difference'] === 'Exception').length
    const sumExcessRate = filtered.reduce((acc, r) => acc + (parseFloat(String(r['Excess Rate']).replace(/,/g, '')) || 0), 0)
    
    const cntExcessPrice = filtered.filter(r => r['Line Total Difference'] === 'Exception').length
    const sumExcessPrice = filtered.reduce((acc, r) => acc + (parseFloat(String(r['Excess Price']).replace(/,/g, '')) || 0), 0)

    return {
      unique_po_raise: uniquePos,
      total_po_value: `${(totalPoVal / 1e7).toFixed(2)} Cr`,
      canceled_po_count: canceledCount,
      holiday_exception: holidayCount,
      sunday_exception: sundayCount,
      count_of_excess_qty: cntExcessQty,
      sum_of_excess_qty: `${(sumExcessQty / 1e5).toFixed(2)} Lakh`,
      count_of_excess_rate: cntExcessRate,
      sum_of_excess_rate: sumExcessRate,
      count_of_excess_price: cntExcessPrice,
      sum_of_excess_price: `${(sumExcessPrice / 1e5).toFixed(2)} Lakh`,
    }
  }, [filtered])

  // Dynamic Chart Calculations based on filtered rows
  const dynamicCharts = useMemo(() => {
    const totalLines = filtered.length
    const openLines = filtered.filter(r => String(r['Document Status']).toLowerCase() === 'open').length
    const closedLines = totalLines - openLines

    const openPct = totalLines ? Math.round((openLines / totalLines) * 1000) / 10 : 0
    const closedPct = totalLines ? Math.round((closedLines / totalLines) * 1000) / 10 : 0

    const totalVal = filtered.reduce((acc, r) => acc + (parseFloat(String(r['Line Total']).replace(/,/g, '')) || 0), 0)
    const openVal = filtered.filter(r => String(r['Document Status']).toLowerCase() === 'open').reduce((acc, r) => acc + (parseFloat(String(r['Line Total']).replace(/,/g, '')) || 0), 0)
    const closedVal = totalVal - openVal

    const closedValCr = (closedVal / 1e7).toFixed(2)
    const openValCr = (openVal / 1e7).toFixed(2)

    const closedValPct = totalVal ? Math.round((closedVal / totalVal) * 100) : 0
    const openValPct = totalVal ? Math.round((openVal / totalVal) * 100) : 0

    return {
      totalLines,
      openLines,
      closedLines,
      openPct,
      closedPct,
      closedValCr,
      openValCr,
      closedValPct,
      openValPct
    }
  }, [filtered])

  const openExceptionModal = (titleStr, filterFn, dedupeKey, isExc = true) => {
    setExceptionTitle(titleStr)
    setIsModalException(isExc)
    let res = filtered.filter(filterFn)
    if (dedupeKey) {
      const seen = new Set()
      res = res.filter(r => {
        const kVal = r[dedupeKey]
        if (!kVal || kVal === '—' || kVal === '0' || seen.has(kVal)) return false
        seen.add(kVal)
        return true
      })
    }
    setExceptionModalRows(res)
    setShowExceptionModal(true)
  }

  const totalPages  = Math.max(1, Math.ceil(filtered.length / ITEMS_PER_PAGE))
  const paginated   = filtered.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE)
  const startRec    = filtered.length === 0 ? 0 : (currentPage - 1) * ITEMS_PER_PAGE + 1
  const endRec      = Math.min(currentPage * ITEMS_PER_PAGE, filtered.length)

  // 11 Verified KPI Cards (Removed Foreign Vendor KPI as requested)
  const kpiCards = [
    {
      label: 'Unique PO Raise',
      value: dynamicKpis.unique_po_raise,
      fmt: 'int',
      accent: 'blue',
      isException: false,
      onCardClick: () => openExceptionModal('Unique Purchase Orders', r => r['PO No'] && r['PO No'] !== '0', 'PO No', false)
    },
    {
      label: 'Total PO Value',
      value: dynamicKpis.total_po_value,
      fmt: 'text',
      accent: 'blue',
      isException: false,
      onCardClick: () => openExceptionModal('All PO Value Records', r => true, null, false)
    },
    {
      label: 'Cancled PO Count',
      value: dynamicKpis.canceled_po_count,
      fmt: 'int',
      accent: 'amber',
      isException: true,
      onCardClick: () => openExceptionModal('Canceled Purchase Orders', r => r['Canceled Status'] === 'Yes', 'PO No', true)
    },
    {
      label: 'Holiday Exception',
      value: dynamicKpis.holiday_exception,
      fmt: 'int',
      accent: 'rose',
      isException: true,
      onCardClick: () => openExceptionModal('Holiday Exception POs', r => (r['Holiday & Sunday Exception'] || '').startsWith('Holiday'), 'PO No', true)
    },
    {
      label: 'Sunday Exception',
      value: dynamicKpis.sunday_exception,
      fmt: 'int',
      accent: 'rose',
      isException: true,
      onCardClick: () => openExceptionModal('Sunday Exception POs', r => r['Holiday & Sunday Exception'] === 'Sunday', 'PO No', true)
    },
    {
      label: 'Count of Excess QTY',
      value: dynamicKpis.count_of_excess_qty,
      fmt: 'int',
      accent: 'rose',
      isException: true,
      onCardClick: () => openExceptionModal('Count of Excess QTY Exceptions', r => r['QTY Difference'] === 'Exception', null, true)
    },
    {
      label: 'Sum of Excess QTY',
      value: dynamicKpis.sum_of_excess_qty,
      fmt: 'text',
      accent: 'rose',
      isException: true,
      onCardClick: () => openExceptionModal('Sum of Excess QTY Exceptions', r => r['QTY Difference'] === 'Exception', null, true)
    },
    {
      label: 'Count of Excess Rate',
      value: dynamicKpis.count_of_excess_rate,
      fmt: 'int',
      accent: 'rose',
      isException: true,
      onCardClick: () => openExceptionModal('Count of Excess Rate Exceptions', r => r['Rate Difference'] === 'Exception', null, true)
    },
    {
      label: 'Sum of Excess Rate',
      value: dynamicKpis.sum_of_excess_rate,
      fmt: 'number',
      accent: 'rose',
      isException: true,
      onCardClick: () => openExceptionModal('Sum of Excess Rate Exceptions', r => r['Rate Difference'] === 'Exception', null, true)
    },
    {
      label: 'Count of Excess Price',
      value: dynamicKpis.count_of_excess_price,
      fmt: 'int',
      accent: 'rose',
      isException: true,
      onCardClick: () => openExceptionModal('Count of Excess Price Exceptions', r => r['Line Total Difference'] === 'Exception', null, true)
    },
    {
      label: 'Sum of Excess Price',
      value: dynamicKpis.sum_of_excess_price,
      fmt: 'text',
      accent: 'rose',
      isException: true,
      onCardClick: () => openExceptionModal('Sum of Excess Price Exceptions', r => r['Line Total Difference'] === 'Exception', null, true)
    },
  ]

  const accentMap = {
    blue:  { bar: 'bg-blue-500',  text: 'text-blue-600 dark:text-blue-400'  },
    amber: { bar: 'bg-amber-500', text: 'text-amber-600 dark:text-amber-400' },
    rose:  { bar: 'bg-rose-500',  text: 'text-rose-600 dark:text-rose-400'   },
  }

  const fmtVal = (fmt, val) => {
    if (val === null || val === undefined) return '—'
    if (fmt === 'int') return typeof val === 'number' ? val.toLocaleString() : val
    if (fmt === 'number') return typeof val === 'number' ? val.toFixed(2) : val
    return String(val)
  }

  if (viewMode === 'po_missing') {
    return <PoMissingView data={data} onBack={() => setViewMode('main')} />
  }

  return (
    <div className="space-y-6">
      {/* Header Action Bar */}
      <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-4 pb-2 border-b border-slate-200/60 dark:border-slate-800/60">
        <div>
          <h2 className="text-xl font-black text-slate-900 dark:text-white tracking-tight">Procurement Transaction Compliance Review</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Real-time audit analytics & S3 sheet trace inspection for purchase order lifecycle compliance.
          </p>
        </div>

        {/* 3 Header Filters + Actions (Placed left of Export to Excel) */}
        <div className="flex items-center gap-2.5 flex-wrap">
          
          {/* Filter 1: Vendor Type */}
          <div className="flex items-center gap-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-1.5 shadow-sm">
            <Filter className="w-3.5 h-3.5 text-blue-500" />
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Vendor:</span>
            <select
              value={vendorTypeFilter}
              onChange={(e) => { setVendorTypeFilter(e.target.value); setCurrentPage(1); }}
              className="text-xs font-bold bg-transparent text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="all">All Vendors</option>
              <option value="indian">Indian Vendors (INR)</option>
              <option value="foreign">Foreign Vendors</option>
            </select>
          </div>

          {/* Filter 2: Holiday Exception */}
          <div className="flex items-center gap-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-1.5 shadow-sm">
            <Filter className="w-3.5 h-3.5 text-amber-500" />
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Holiday:</span>
            <select
              value={holidayFilter}
              onChange={(e) => { setHolidayFilter(e.target.value); setCurrentPage(1); }}
              className="text-xs font-bold bg-transparent text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="all">All POs</option>
              <option value="holiday_only">Holiday Exceptions Only</option>
            </select>
          </div>

          {/* Filter 3: 5% Financial Exception */}
          <div className="flex items-center gap-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl px-3 py-1.5 shadow-sm">
            <Filter className="w-3.5 h-3.5 text-rose-500" />
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">5% Exception:</span>
            <select
              value={excess5PctFilter}
              onChange={(e) => { setExcess5PctFilter(e.target.value); setCurrentPage(1); }}
              className="text-xs font-bold bg-transparent text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="all">All Items</option>
              <option value="qty">Qty Excess (&gt;5%)</option>
              <option value="rate">Rate Excess (&gt;5%)</option>
              <option value="price">Price Excess (&gt;5%)</option>
            </select>
          </div>

          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 shadow-sm transition-all active:scale-95 disabled:opacity-50"
            title="Refresh page data"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-blue-500 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
          </button>

          {/* Export to Excel Button */}
          <button
            onClick={() => setShowExportModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm transition-all active:scale-95"
            title="Export page data to Excel"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>Export to Excel</span>
          </button>
        </div>
      </div>

      <AiInsightBox section="postatus" kpis={dynamicKpis} />

      {/* 11 KPI Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {kpiCards.map((k) => {
          const ac = accentMap[k.accent] || accentMap.blue
          return (
            <div
              key={k.label}
              onClick={k.onCardClick}
              className={`relative bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-3.5 shadow-sm transition-all duration-200 overflow-hidden flex flex-col justify-between cursor-pointer hover:shadow-md active:scale-[0.98] ${
                k.isException ? 'hover:border-rose-500/50' : 'hover:border-blue-500/50'
              }`}
            >
              <div className={`absolute top-0 left-0 right-0 h-0.5 ${ac.bar}`} />
              <div>
                <div className="flex items-center justify-between gap-1 mb-2">
                  <p className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider leading-tight">
                    {k.label}
                  </p>
                  {k.isException && (
                    <span className="flex items-center gap-0.5 text-[8px] font-extrabold text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 px-1 py-0.5 rounded-md border border-rose-200 dark:border-rose-800/40">
                      <AlertTriangle className="w-2.5 h-2.5" /> Exception
                    </span>
                  )}
                </div>
                <p className={`text-lg font-black tracking-tight leading-none ${ac.text}`}>
                  {fmtVal(k.fmt, k.value)}
                </p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Visual Analytics / Chart Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* PO Status Distribution Card */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white tracking-tight">PO Status Distribution</h3>
            <p className="text-xs text-slate-400 mt-0.5 font-medium">Open vs Closed line items</p>
          </div>

          <div className="my-5 flex flex-col sm:flex-row items-center justify-between gap-6">
            {/* Donut Chart */}
            <div className="relative w-36 h-36 flex items-center justify-center shrink-0">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                {/* Background Ring */}
                <path
                  className="text-slate-100 dark:text-slate-800"
                  strokeWidth="3.8"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                {/* Green (Closed) Segment */}
                <path
                  className="text-emerald-600 transition-all duration-1000 ease-out"
                  strokeDasharray={`${dynamicCharts.closedPct}, 100`}
                  strokeWidth="3.8"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                {/* Amber (Open) Segment */}
                <path
                  className="text-amber-500 transition-all duration-1000 ease-out"
                  strokeDasharray={`${dynamicCharts.openPct}, 100`}
                  strokeDashoffset={`-${dynamicCharts.closedPct}`}
                  strokeWidth="3.8"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                <span className="text-xl font-black text-slate-900 dark:text-white tracking-tight leading-none">
                  {dynamicCharts.totalLines.toLocaleString()}
                </span>
                <span className="text-[10px] font-semibold text-slate-400 mt-1 uppercase tracking-wider">
                  Total Lines
                </span>
              </div>
            </div>

            {/* Right Legend & Progress */}
            <div className="w-full space-y-4">
              {/* Open Item */}
              <div>
                <div className="flex items-center justify-between text-xs font-semibold mb-1.5">
                  <span className="flex items-center gap-2 text-slate-700 dark:text-slate-200">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
                    Open
                  </span>
                  <span className="text-slate-500 dark:text-slate-400 font-bold">
                    {dynamicCharts.openLines.toLocaleString()} <span className="text-slate-400 dark:text-slate-500 font-normal">({dynamicCharts.openPct}%)</span>
                  </span>
                </div>
                <div className="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500 rounded-full transition-all duration-500" style={{ width: `${dynamicCharts.openPct}%` }} />
                </div>
              </div>

              {/* Closed Item */}
              <div>
                <div className="flex items-center justify-between text-xs font-semibold mb-1.5">
                  <span className="flex items-center gap-2 text-slate-700 dark:text-slate-200">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 inline-block" />
                    Closed
                  </span>
                  <span className="text-slate-500 dark:text-slate-400 font-bold">
                    {dynamicCharts.closedLines.toLocaleString()} <span className="text-slate-400 dark:text-slate-500 font-normal">({dynamicCharts.closedPct}%)</span>
                  </span>
                </div>
                <div className="h-2 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-600 rounded-full transition-all duration-500" style={{ width: `${dynamicCharts.closedPct}%` }} />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* PO Value Exposure Card */}
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white tracking-tight">PO Value Exposure</h3>
            <p className="text-xs text-slate-400 mt-0.5 font-medium">Financial commitment split – Closed vs Open</p>
          </div>

          <div className="my-5 space-y-6">
            {/* Closed Value */}
            <div>
              <div className="flex items-center justify-between text-xs font-bold mb-2">
                <span className="text-slate-700 dark:text-slate-200 font-extrabold">Closed Value</span>
                <span className="text-slate-900 dark:text-white font-black text-sm">₹{dynamicCharts.closedValCr} Cr</span>
              </div>
              <div className="h-7 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden relative flex items-center">
                <div
                  className="h-full bg-emerald-500 rounded-full flex items-center justify-center transition-all duration-500 shadow-sm"
                  style={{ width: `${dynamicCharts.closedValPct}%` }}
                >
                  {dynamicCharts.closedValPct > 10 && (
                    <span className="text-xs font-black text-white px-2 tracking-wider">{dynamicCharts.closedValPct}%</span>
                  )}
                </div>
              </div>
            </div>

            {/* Open Value */}
            <div>
              <div className="flex items-center justify-between text-xs font-bold mb-2">
                <span className="text-slate-700 dark:text-slate-200 font-extrabold">Open Value</span>
                <span className="text-slate-900 dark:text-white font-black text-sm">₹{dynamicCharts.openValCr} Cr</span>
              </div>
              <div className="h-7 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden relative flex items-center">
                <div
                  className="h-full bg-amber-500 rounded-full flex items-center justify-center transition-all duration-500 shadow-sm"
                  style={{ width: `${dynamicCharts.openValPct}%` }}
                >
                  {dynamicCharts.openValPct > 10 && (
                    <span className="text-xs font-black text-white px-2 tracking-wider">{dynamicCharts.openValPct}%</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          <p className="text-[11px] text-slate-400 dark:text-slate-500 text-center font-medium border-t border-slate-100 dark:border-slate-800/80 pt-3">
            Open PO value represents uncommitted cash and pending material deliveries.
          </p>
        </div>
      </div>

      {/* Main Audit Detail Table */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800 flex flex-col gap-3">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3 flex-wrap">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <span>Purchase Order Status — Full Audit Detail</span>
                  <span className="text-[10px] font-normal text-blue-600 bg-blue-50 dark:bg-blue-950/40 px-2 py-0.5 rounded-full border border-blue-200 dark:border-blue-800/40">
                    Click any row to inspect 3 S3 source sheets
                  </span>
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">38 Verified Audit Columns from Purchase Status Report</p>
              </div>

              {/* PO Missing Button */}
              <button
                onClick={() => setViewMode('po_missing')}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white text-xs font-bold shadow-sm transition-all active:scale-95 shrink-0"
                title="Inspect 3 PO Missing Sub-Sheets (FOC, Job Work, Repair & Maintenance)"
              >
                <FileWarning className="w-3.5 h-3.5" />
                <span>PO Missing Audit</span>
                <span className="ml-1 text-[10px] bg-amber-950/50 px-2 py-0.5 rounded-full font-extrabold border border-amber-300/40">
                  {((data?.po_missing?.foc_items?.rows?.length || 0) + (data?.po_missing?.job_work?.rows?.length || 0) + (data?.po_missing?.repair_maintenance?.rows?.length || 0)).toLocaleString()}
                </span>
              </button>
            </div>

            <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
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

              <div className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-800/60 p-1.5 rounded-lg border border-slate-200 dark:border-slate-700">
                <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 px-1 flex items-center gap-1">
                  <svg className="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  Date Range:
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

          <div className="flex items-center gap-1.5 flex-wrap">
            {['All', ...COL_GROUPS.map(g => g.label)].map(g => (
              <button
                key={g}
                onClick={() => { setActiveGroup(g); setCurrentPage(1); }}
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
                    title="Click to sort · Drag to reorder"
                    className={`px-4 py-2.5 text-[10px] font-bold uppercase tracking-wider whitespace-nowrap cursor-pointer select-none border-b border-slate-200 dark:border-slate-700 hover:text-blue-600 dark:hover:text-blue-400 transition-colors ${
                      colFilters[c]?.trim()
                        ? 'text-blue-600 dark:text-blue-400 bg-blue-50/60 dark:bg-blue-950/20'
                        : 'text-slate-500 dark:text-slate-400'
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
                    {rows.length === 0 ? 'Upload files to populate this table.' : 'No records match your search or active filters.'}
                  </td>
                </tr>
              ) : paginated.map((r, i) => (
                <tr
                  key={i}
                  onClick={() => { setSelectedTraceRow(r); setShowTraceModal(true); }}
                  className="hover:bg-blue-50/50 dark:hover:bg-blue-950/30 cursor-pointer transition-colors duration-100"
                  title="Click to inspect 3 S3 source input sheets for this line item"
                >
                  {visibleCols.map(c => {
                    const val = r[c]

                    if (c === 'QTY Difference' || c === 'Rate Difference' || c === 'Line Total Difference') return (
                      <td key={c} className="px-4 py-2 font-mono text-center">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          val === 'Exception'
                            ? 'bg-rose-100 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-800/40'
                            : val === 'Tolerable'
                            ? 'bg-amber-50 dark:bg-amber-950/30 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800/40'
                            : 'bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/40'
                        }`}>
                          {val || '—'}
                        </span>
                      </td>
                    )

                    if (c === 'Document Status' || c === 'Canceled Status') return (
                      <td key={c} className="px-4 py-2 font-mono text-center">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          val === 'Yes' || val === 'Closed'
                            ? 'bg-rose-50 dark:bg-rose-950/30 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-800/40'
                            : 'bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/40'
                        }`}>
                          {val || '—'}
                        </span>
                      </td>
                    )

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

      {/* Export Modal */}
      <ExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        title="Export Purchase Order Status Data"
        columns={ALL_COLS}
        data={filtered}
        filenamePrefix="PO_Status_Audit"
      />

      {/* Exception Modal */}
      <ExceptionModal
        isOpen={showExceptionModal}
        onClose={() => setShowExceptionModal(false)}
        title={exceptionTitle}
        subtitle="Purchase Order line items matching selected audit criteria"
        columns={ALL_COLS}
        rows={exceptionModalRows}
        filenamePrefix="PO_Status_Records"
        isException={isModalException}
      />

      {/* 3-Sheet Line Item Source Trace Modal */}
      <LineItemSourceTraceModal
        isOpen={showTraceModal}
        onClose={() => setShowTraceModal(false)}
        selectedRow={selectedTraceRow}
      />
    </div>
  )
}
