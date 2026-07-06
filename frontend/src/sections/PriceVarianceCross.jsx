import React, { useState, useEffect, useMemo } from 'react'
import { fetchPriceVarianceCross } from '../api'
import AiInsightBox from '../components/AiInsightBox'
import { useStore } from '../store'

const formatCurrency = (val) => {
  if (val === null || val === undefined) return '—'
  const num = parseFloat(val)
  if (isNaN(num)) return val
  if (num >= 10000000) return `₹${(num / 10000000).toFixed(2)} Cr`
  if (num >= 100000) return `₹${(num / 100000).toFixed(2)} L`
  return `₹${num.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
}

const parseDate = (dateStr) => {
  if (!dateStr || dateStr === '—') return null
  if (dateStr instanceof Date) return dateStr
  const s = String(dateStr).trim()
  if (!s || s.toLowerCase() === 'nan' || s.toLowerCase() === 'none') return null
  
  // Try YYYY-MM-DD
  const isoMatch = s.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/)
  if (isoMatch) {
    return new Date(parseInt(isoMatch[1], 10), parseInt(isoMatch[2], 10) - 1, parseInt(isoMatch[3], 10))
  }
  
  // Try DD-MM-YYYY
  const dmyMatch = s.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})/)
  if (dmyMatch) {
    let year = parseInt(dmyMatch[3], 10)
    if (year < 100) year += 2000
    return new Date(year, parseInt(dmyMatch[2], 10) - 1, parseInt(dmyMatch[1], 10))
  }
  
  const parsed = Date.parse(s)
  return isNaN(parsed) ? null : new Date(parsed)
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

export default function PriceVarianceCross() {
  const { priceVarianceCross, setPriceVarianceCross } = useStore()
  const [loading, setLoading] = useState(!priceVarianceCross)
  const [error, setError] = useState(null)

  // Filters and pagination state
  const [searchTerm, setSearchTerm] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [sortCol, setSortCol] = useState('item_description')
  const [sortDir, setSortDir] = useState('asc')
  const [currentPage, setCurrentPage] = useState(1)
  const ITEMS_PER_PAGE = 25

  useEffect(() => {
    if (priceVarianceCross) {
      setLoading(false)
      return
    }
    setLoading(true)
    fetchPriceVarianceCross()
      .then(res => {
        setPriceVarianceCross(res)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [priceVarianceCross, setPriceVarianceCross])

  const handleSearch = (e) => {
    setSearchTerm(e.target.value)
    setCurrentPage(1)
  }

  const handleSort = (col) => {
    if (sortCol === col) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortCol(col)
      setSortDir('asc')
    }
    setCurrentPage(1)
  }

  const rows = priceVarianceCross?.rows || []

  // Filtered rows
  const filtered = useMemo(() => {
    let out = [...rows]
    const term = searchTerm.trim().toLowerCase()

    // 1. Search filter
    if (term) {
      out = out.filter(r => 
        String(r.vendor_code ?? '').toLowerCase().includes(term) ||
        String(r.vendor_name ?? '').toLowerCase().includes(term) ||
        String(r.vendor_country ?? '').toLowerCase().includes(term) ||
        String(r.vendor_group ?? '').toLowerCase().includes(term) ||
        String(r.item_code ?? '').toLowerCase().includes(term) ||
        String(r.item_description ?? '').toLowerCase().includes(term) ||
        String(r.item_group ?? '').toLowerCase().includes(term) ||
        String(r.grn_number ?? '').toLowerCase().includes(term)
      )
    }

    // 2. Date filter (ranges over posting_date or document_date)
    if (startDate || endDate) {
      const start = startDate ? new Date(startDate) : null
      if (start) start.setHours(0, 0, 0, 0)
      const end = endDate ? new Date(endDate) : null
      if (end) end.setHours(23, 59, 59, 999)

      out = out.filter(r => {
        const postDate = parseDate(r.posting_date)
        if (!postDate) return false
        if (start && postDate < start) return false
        if (end && postDate > end) return false
        return true
      })
    }

    // 3. Sorting
    if (sortCol) {
      out.sort((a, b) => {
        const av = a[sortCol] ?? ''
        const bv = b[sortCol] ?? ''
        const an = parseFloat(av)
        const bn = parseFloat(bv)

        let cmp = 0
        if (!isNaN(an) && !isNaN(bn)) {
          cmp = an - bn
        } else {
          cmp = String(av).localeCompare(String(bv), undefined, { numeric: true, sensitivity: 'base' })
        }
        return sortDir === 'asc' ? cmp : -cmp
      })
    }

    return out
  }, [rows, searchTerm, startDate, endDate, sortCol, sortDir])

  // Calculated metrics for top of page (KPI Cards)
  const metrics = useMemo(() => {
    const totalItems = filtered.length
    
    // Count distinct vendor codes with inconsistent UOM
    const uomInconsistent = new Set(
      filtered.filter(r => r.uom_consistent === 0).map(r => r.vendor_code)
    ).size

    // Extract unique GRNs
    const grnSet = new Set()
    filtered.forEach(r => {
      if (r.grn_number && r.grn_number !== '—') {
        r.grn_number.split(',').forEach(g => {
          const clean = g.trim()
          if (clean && clean.toLowerCase() !== 'nan' && clean.toLowerCase() !== 'none') {
            grnSet.add(clean)
          }
        })
      }
    })
    const uniqueGrns = grnSet.size

    // High price variance rows count (variance flag is 1)
    const varianceCount = filtered.filter(r => r.variance_flag === 1).length

    // Count of rows in column "higher>5%" where value is 1
    const higherGt5Count = filtered.filter(r => r.higher_gt_5 === 1).length

    // Count of unique item descriptions
    const uniqueDescriptions = new Set(
      filtered.map(r => String(r.item_description || '').trim().toUpperCase()).filter(d => d && d !== '—')
    ).size

    return {
      totalItems,
      uomInconsistent,
      uniqueGrns,
      varianceCount,
      higherGt5Count,
      uniqueDescriptions
    }
  }, [filtered])

  const totalPages = Math.max(1, Math.ceil(filtered.length / ITEMS_PER_PAGE))
  const paginated = filtered.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE)
  const startRec = filtered.length === 0 ? 0 : (currentPage - 1) * ITEMS_PER_PAGE + 1
  const endRec = Math.min(currentPage * ITEMS_PER_PAGE, filtered.length)

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">
          Processing cross-vendor price variance analysis...
        </p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-800 rounded-xl">
        <h3 className="text-base font-bold text-rose-800 dark:text-rose-400 mb-1">Error Loading Data</h3>
        <p className="text-sm text-rose-700 dark:text-rose-400/80">{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Price Variance (Cross Vendor)
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Compare unit rates of the same item across different vendors to check for pricing inconsistencies.
          </p>
        </div>
        <span className="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800 text-[11px] font-semibold text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          Live Calculations
        </span>
      </div>

      {/* AI Insight Box */}
      <AiInsightBox section="pricevariancecross" kpis={{
        vendor_items: metrics.totalItems,
        uom_inconsistent: metrics.uomInconsistent,
        unique_grns: metrics.uniqueGrns,
        variance_lines: metrics.varianceCount,
        higher_gt_5: metrics.higherGt5Count,
        unique_descriptions: metrics.uniqueDescriptions
      }} />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'Vendor Items Evaluated', value: metrics.totalItems, accent: 'blue', desc: 'Total line items evaluated' },
          { label: 'Unique GRN(GRPO) Nos.', value: metrics.uniqueGrns, accent: 'blue', desc: 'Distinct goods receipt files matched' },
          { label: 'Total Variance Lines', value: metrics.varianceCount, accent: metrics.varianceCount > 0 ? 'rose' : 'blue', desc: 'Lines with pricing variance > 5%' },
          { label: 'Vendor Rows Above Lowest >5%', value: metrics.higherGt5Count, accent: metrics.higherGt5Count > 0 ? 'rose' : 'blue', desc: 'Rows in column higher>5% equal to 1' },
          { label: 'Rows (Intercompany Excluded)', value: metrics.uniqueDescriptions, accent: 'blue', desc: 'Count of unique item descriptions' },
          { label: 'Vendors with Inconsistent UOM', value: metrics.uomInconsistent, accent: metrics.uomInconsistent > 0 ? 'amber' : 'blue', desc: 'Vendors with non-uniform UOMs' }
        ].map(card => {
          const isRose = card.accent === 'rose'
          const isAmber = card.accent === 'amber'
          const barColor = isRose ? 'bg-rose-500' : (isAmber ? 'bg-amber-500' : 'bg-blue-500')
          const textColor = isRose ? 'text-rose-600 dark:text-rose-400' : (isAmber ? 'text-amber-600 dark:text-amber-400' : 'text-blue-600 dark:text-blue-400')
          
          return (
            <div key={card.label} className="relative bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden">
              <div className={`absolute top-0 left-0 right-0 h-0.5 ${barColor}`} />
              <p className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest leading-tight mb-2">
                {card.label}
              </p>
              <p className={`text-xl font-black tracking-tight leading-none ${textColor}`}>
                {card.value.toLocaleString()}
              </p>
              {card.desc && <p className="text-[9px] text-slate-400 dark:text-slate-500 mt-2">{card.desc}</p>}
            </div>
          )
        })}
      </div>

      {/* Bottom Table Section */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        {/* Table Toolbar */}
        <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800 flex flex-col gap-3">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Cross-Vendor Pricing Inconsistencies</h3>
              <p className="text-xs text-slate-400 mt-0.5">Lines grouped by item code, showcasing PO, GRN, and Unit Rate stats</p>
            </div>

            <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
              {/* Search input */}
              <div className="relative">
                <svg className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  placeholder="Search table..."
                  value={searchTerm}
                  onChange={handleSearch}
                  className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 w-44 transition"
                />
              </div>

              {/* Date Filters */}
              <div className="flex items-center gap-1.5 text-xs">
                <input
                  type="date"
                  value={startDate}
                  onChange={e => { setStartDate(e.target.value); setCurrentPage(1) }}
                  className="px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <span className="text-slate-400">to</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={e => { setEndDate(e.target.value); setCurrentPage(1) }}
                  className="px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                {(startDate || endDate) && (
                  <button
                    onClick={() => { setStartDate(''); setEndDate(''); setCurrentPage(1) }}
                    className="text-xs text-rose-500 hover:underline font-bold"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Responsive Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[2000px]">
            <thead>
              <tr className="bg-slate-50/50 dark:bg-slate-800/40 border-b border-slate-100 dark:border-slate-800">
                {[
                  { id: 'item_code', label: 'Item Code' },
                  { id: 'item_description', label: 'Item Description' },
                  { id: 'item_group', label: 'Item Group' },
                  { id: 'vendor_code', label: 'Vendor Code' },
                  { id: 'vendor_name', label: 'Vendor Name' },
                  { id: 'vendor_country', label: 'Vendor Country' },
                  { id: 'po_numbers', label: 'PO Numbers' },
                  { id: 'grn_number', label: 'GRN No' },
                  { id: 'uom', label: 'UOM' },
                  { id: 'ordered_qty', label: 'Ordered Quantity' },
                  { id: 'received_qty', label: 'Received quantiti' },
                  { id: 'rate_inr', label: 'Rate(INR)' },
                  { id: 'item_min_rate', label: 'Item Min. Rate(INR)' },
                  { id: 'item_max_rate', label: 'Item Max. Rate(INR)' },
                  { id: 'vendor_position', label: 'Vendor Position' },
                  { id: 'pct_above_lowest', label: '%age above lowest' },
                  { id: 'higher_gt_5', label: 'Higher>5%' },
                  { id: 'uom_consistency', label: 'UOM consistency' }
                ].map(col => (
                  <th
                    key={col.id}
                    onClick={() => handleSort(col.id)}
                    className="px-4 py-3 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100/50 dark:hover:bg-slate-800/60 select-none transition-colors"
                  >
                    <div className="flex items-center">
                      {col.label}
                      <SortIcon dir={sortCol === col.id ? sortDir : null} />
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {paginated.map((row, i) => (
                <tr key={i} className="hover:bg-slate-50/40 dark:hover:bg-slate-800/20 transition-colors duration-150">
                  {/* 1. Item Code */}
                  <td className="px-4 py-3 text-xs font-mono font-bold text-slate-900 dark:text-white">
                    {row.item_code || '—'}
                  </td>
                  {/* 2. Item Description */}
                  <td className="px-4 py-3 text-xs font-medium text-slate-700 dark:text-slate-300 max-w-[250px] truncate" title={row.item_description}>
                    {row.item_description || '—'}
                  </td>
                  {/* 3. Item Group */}
                  <td className="px-4 py-3 text-xs text-slate-600 dark:text-slate-400">
                    {row.item_group || '—'}
                  </td>
                  {/* 4. Vendor Code */}
                  <td className="px-4 py-3 text-xs font-mono font-bold text-slate-900 dark:text-white">
                    {row.vendor_code || '—'}
                  </td>
                  {/* 5. Vendor Name */}
                  <td className="px-4 py-3 text-xs font-medium text-slate-700 dark:text-slate-300 max-w-[200px] truncate" title={row.vendor_name}>
                    {row.vendor_name || '—'}
                  </td>
                  {/* 6. Vendor Country */}
                  <td className="px-4 py-3 text-xs text-slate-600 dark:text-slate-400">
                    {row.vendor_country || '—'}
                  </td>
                  {/* 7. PO Numbers */}
                  <td className="px-4 py-3 text-xs font-mono text-slate-600 dark:text-slate-400">
                    {row.po_numbers || '—'}
                  </td>
                  {/* 8. GRN No */}
                  <td className="px-4 py-3 text-xs font-mono text-slate-600 dark:text-slate-400 max-w-[150px] truncate" title={row.grn_number}>
                    {row.grn_number || '—'}
                  </td>
                  {/* 9. UOM */}
                  <td className="px-4 py-3 text-xs text-slate-600 dark:text-slate-400">
                    {row.uom || '—'}
                  </td>
                  {/* 10. Ordered Quantity */}
                  <td className="px-4 py-3 text-xs font-mono text-right text-slate-900 dark:text-white">
                    {row.ordered_qty !== undefined && row.ordered_qty !== null ? row.ordered_qty.toLocaleString() : '—'}
                  </td>
                  {/* 11. Received Quantity */}
                  <td className="px-4 py-3 text-xs font-mono text-right text-slate-900 dark:text-white">
                    {row.received_qty !== undefined && row.received_qty !== null ? row.received_qty.toLocaleString() : '—'}
                  </td>
                  {/* 12. Rate(INR) */}
                  <td className="px-4 py-3 text-xs font-mono text-right text-slate-900 dark:text-white">
                    {formatCurrency(row.rate_inr)}
                  </td>
                  {/* 13. Item Min. Rate(INR) */}
                  <td className="px-4 py-3 text-xs font-mono text-right text-slate-600 dark:text-slate-400">
                    {formatCurrency(row.item_min_rate)}
                  </td>
                  {/* 14. Item Max. Rate(INR) */}
                  <td className="px-4 py-3 text-xs font-mono text-right text-slate-600 dark:text-slate-400">
                    {formatCurrency(row.item_max_rate)}
                  </td>
                  {/* 15. Vendor Position */}
                  <td className="px-4 py-3 text-xs text-center">
                    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                      row.vendor_position === 'Highest'
                        ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/40 dark:text-rose-400'
                        : row.vendor_position === 'Lowest'
                        ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400'
                        : 'text-slate-400 dark:text-slate-500'
                    }`}>
                      {row.vendor_position}
                    </span>
                  </td>
                  {/* 16. %age above lowest */}
                  <td className="px-4 py-3 text-xs text-right font-mono font-bold text-slate-700 dark:text-slate-300">
                    {row.pct_above_lowest !== undefined && row.pct_above_lowest !== null ? `${parseFloat(row.pct_above_lowest).toFixed(2)}%` : '—'}
                  </td>
                  {/* 17. Higher>5% */}
                  <td className={`px-4 py-3 text-xs text-center font-mono font-bold transition-colors ${
                    row.higher_gt_5 === 1
                      ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 font-extrabold border-l border-r border-yellow-200 dark:border-yellow-900/40'
                      : 'bg-white dark:bg-slate-900'
                  }`}>
                    {row.higher_gt_5}
                  </td>
                  {/* 18. UOM consistency */}
                  <td className={`px-4 py-3 text-xs text-center font-mono font-bold transition-colors ${
                    row.uom_consistency === 1
                      ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 font-extrabold border-l border-r border-green-200 dark:border-green-900/40'
                      : 'bg-white dark:bg-slate-900'
                  }`}>
                    {row.uom_consistency}
                  </td>
                </tr>
              ))}
              {paginated.length === 0 && (
                <tr>
                  <td colSpan={20} className="px-6 py-10 text-center text-sm text-slate-400 dark:text-slate-500">
                    No matching records found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Toolbar */}
        <div className="px-5 py-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <div>
            Showing <span className="font-semibold text-slate-700 dark:text-white">{startRec}</span> to{' '}
            <span className="font-semibold text-slate-700 dark:text-white">{endRec}</span> of{' '}
            <span className="font-semibold text-slate-700 dark:text-white">{filtered.length}</span> entries
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage(1)}
              disabled={currentPage === 1}
              className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40"
            >
              First
            </button>
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40"
            >
              Prev
            </button>
            <span className="px-2 py-1">
              Page <span className="font-semibold text-slate-700 dark:text-white">{currentPage}</span> of{' '}
              <span className="font-semibold text-slate-700 dark:text-white">{totalPages}</span>
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40"
            >
              Next
            </button>
            <button
              onClick={() => setCurrentPage(totalPages)}
              disabled={currentPage === totalPages}
              className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40"
            >
              Last
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
