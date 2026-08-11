import React, { useState, useEffect, useMemo } from 'react'
import { fetchVendorMasterNew } from '../api'
import AiInsightBox from '../components/AiInsightBox'
import { useStore } from '../store'
import TruncatedCell from '../components/TruncatedCell'
import useColumnOrder from '../hooks/useColumnOrder'

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

const COLS = [
  { id: 'vendor_code', label: 'Vendor Code' },
  { id: 'vendor_name', label: 'Vendor Name' },
  { id: 'vendor_country', label: 'Vendor Country' },
  { id: 'vendor_group', label: 'Vendor Group' },
  { id: 'region', label: 'Region' },
  { id: 'currency', label: 'Currency' },
  { id: 'gstin', label: 'GSTIN' },
  { id: 'msme_registration', label: 'MSME Registration' },
  { id: 'payment_terms', label: 'Payment Terms' },
  { id: 'active', label: 'Active' },
  { id: 'same_gst_multi_code', label: 'Same GST Multi-Code' },
  { id: 'missing_gstin', label: 'Missing GSTIN (Dom)' },
  { id: 'foreign_w_gstin', label: 'Missing GSTIN (For)' },
  { id: 'related_party', label: 'Related Party' },
]
const ALL_COLS = COLS.map(c => c.id)
const COL_LABEL = Object.fromEntries(COLS.map(c => [c.id, c.label]))

const CELL_CLASS = {
  vendor_code: 'px-4 py-3 font-mono font-bold text-slate-900 dark:text-white',
  vendor_name: 'px-4 py-3 text-slate-700 dark:text-slate-300 font-semibold',
  vendor_country: 'px-4 py-3 text-slate-600 dark:text-slate-400',
  vendor_group: 'px-4 py-3 text-slate-600 dark:text-slate-400',
  region: 'px-4 py-3 text-slate-700 dark:text-slate-300',
  currency: 'px-4 py-3 font-mono text-slate-600 dark:text-slate-400',
  gstin: 'px-4 py-3 font-mono text-slate-600 dark:text-slate-400',
  msme_registration: 'px-4 py-3 text-center text-slate-700 dark:text-slate-300',
  payment_terms: 'px-4 py-3 text-slate-600 dark:text-slate-400',
  active: 'px-4 py-3',
  same_gst_multi_code: 'px-4 py-3 text-center',
  missing_gstin: 'px-4 py-3 text-center',
  foreign_w_gstin: 'px-4 py-3 text-center',
  related_party: 'px-4 py-3 text-center',
}

function renderCell(colId, row) {
  switch (colId) {
    case 'active':
      return (
        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
          row.active === 'Active'
            ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400'
            : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400'
        }`}>
          {row.active}
        </span>
      )
    case 'same_gst_multi_code':
      return (
        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
          row.same_gst_multi_code === 1
            ? 'bg-rose-100 text-rose-700 dark:bg-rose-950/40 dark:text-rose-450'
            : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-500'
        }`}>
          {row.same_gst_multi_code}
        </span>
      )
    case 'missing_gstin':
      return (
        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
          row.missing_gstin === 1
            ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-450'
            : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-500'
        }`}>
          {row.missing_gstin}
        </span>
      )
    case 'foreign_w_gstin':
      return (
        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
          row.foreign_w_gstin === 1
            ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-450'
            : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-500'
        }`}>
          {row.foreign_w_gstin}
        </span>
      )
    case 'related_party':
      return (
        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
          row.related_party === 1
            ? 'bg-rose-100 text-rose-750 dark:bg-rose-950/50 dark:text-rose-400'
            : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-500'
        }`}>
          {row.related_party}
        </span>
      )
    default:
      return <TruncatedCell value={row[colId]} />
  }
}

export default function VendorMasterNew() {
  const { vendorMasterNew, setVendorMasterNew } = useStore()
  const [loading, setLoading] = useState(!vendorMasterNew)
  const [error, setError] = useState(null)

  // Filters and pagination state
  const [searchTerm, setSearchTerm] = useState('')
  const [regionFilter, setRegionFilter] = useState('All')
  const [statusFilter, setStatusFilter] = useState('All')
  const [onlyRelated, setOnlyRelated] = useState(false)
  const [onlyMissingGst, setOnlyMissingGst] = useState(false)
  const [onlyMultiGst, setOnlyMultiGst] = useState(false)

  const [sortCol, setSortCol] = useState('vendor_code')
  const [sortDir, setSortDir] = useState('asc')
  const [currentPage, setCurrentPage] = useState(1)
  const ITEMS_PER_PAGE = 25

  const { order: colOrder, moveColumn } = useColumnOrder('vendor-master', ALL_COLS)
  const [dragCol, setDragCol] = useState(null)
  const [dragOverCol, setDragOverCol] = useState(null)

  useEffect(() => {
    if (vendorMasterNew) {
      setLoading(false)
      return
    }
    setLoading(true)
    fetchVendorMasterNew()
      .then(res => {
        setVendorMasterNew(res)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [vendorMasterNew, setVendorMasterNew])

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

  const rows = vendorMasterNew?.rows || []

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
        String(r.region ?? '').toLowerCase().includes(term) ||
        String(r.currency ?? '').toLowerCase().includes(term) ||
        String(r.gstin ?? '').toLowerCase().includes(term) ||
        String(r.msme_registration ?? '').toLowerCase().includes(term) ||
        String(r.payment_terms ?? '').toLowerCase().includes(term) ||
        String(r.active ?? '').toLowerCase().includes(term)
      )
    }

    // 2. Region filter
    if (regionFilter !== 'All') {
      out = out.filter(r => r.region === regionFilter)
    }

    // 3. Status filter
    if (statusFilter !== 'All') {
      out = out.filter(r => r.active === statusFilter)
    }

    // 4. Related party toggle
    if (onlyRelated) {
      out = out.filter(r => r.related_party === 1)
    }

    // 5. Missing GSTIN toggle (missing_gstin is domestic missing, foreign_w_gstin is foreign missing)
    if (onlyMissingGst) {
      out = out.filter(r => r.missing_gstin === 1 || r.foreign_w_gstin === 1)
    }

    // 6. Same GST multi code toggle
    if (onlyMultiGst) {
      out = out.filter(r => r.same_gst_multi_code === 1)
    }

    // 7. Sorting
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
  }, [rows, searchTerm, regionFilter, statusFilter, onlyRelated, onlyMissingGst, onlyMultiGst, sortCol, sortDir])

  // Top Items metrics calculated from resultant table at bottom (filtered)
  const kpiMetrics = useMemo(() => {
    const uniqueVendors = new Set()
    let sameGstMulti = 0
    let dormantDuplicates = 0
    let missingGstDom = 0
    let missingGstFor = 0
    let rowsFlagged = 0

    filtered.forEach(r => {
      if (r.vendor_code) {
        uniqueVendors.add(r.vendor_code)
      }
      if (r.same_gst_multi_code === 1) {
        sameGstMulti++
        if (r.active === 'Dormant') {
          dormantDuplicates++
        }
      }
      if (r.missing_gstin === 1) {
        missingGstDom++
      }
      if (r.foreign_w_gstin === 1) {
        missingGstFor++
      }
      if (r.missing_gstin === 1 || r.foreign_w_gstin === 1) {
        rowsFlagged++
      }
    })

    return {
      totalSuppliers: uniqueVendors.size,
      sameGstMulti,
      dormantDuplicates,
      missingGstDom,
      missingGstFor,
      rowsFlagged
    }
  }, [filtered])

  // Top Items: Related Parties list
  const relatedParties = useMemo(() => {
    return rows.filter(r => r.related_party === 1)
  }, [rows])

  // Region breakdown
  const regionBreakdown = useMemo(() => {
    const domestic = rows.filter(r => r.region === 'Domestic').length
    const foreign = rows.filter(r => r.region === 'Foreign').length
    const total = rows.length
    return {
      domestic,
      foreign,
      domesticPct: total > 0 ? ((domestic / total) * 100).toFixed(1) : '0',
      foreignPct: total > 0 ? ((foreign / total) * 100).toFixed(1) : '0',
    }
  }, [rows])

  const totalPages = Math.max(1, Math.ceil(filtered.length / ITEMS_PER_PAGE))
  const paginated = filtered.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE)
  const startRec = filtered.length === 0 ? 0 : (currentPage - 1) * ITEMS_PER_PAGE + 1
  const endRec = Math.min(currentPage * ITEMS_PER_PAGE, filtered.length)

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">
          Processing Vendor Master Validation analysis...
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

  // Get raw KPIs computed by backend
  const rawKpis = vendorMasterNew?.kpis || {}
  const aiKpis = {
    ...rawKpis,
    total_suppliers: kpiMetrics.totalSuppliers,
    same_gstin_multi_codes: kpiMetrics.sameGstMulti,
    dormant_duplicate_codes: kpiMetrics.dormantDuplicates,
    missing_gstin_domestic: kpiMetrics.missingGstDom,
    missing_gstin_foreign: kpiMetrics.missingGstFor,
    rows_flagged: kpiMetrics.rowsFlagged
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Vendor Master Validation
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Audit register consistency of Business Partners, highlighting GSTIN duplicates, missing tax details, and related party mappings.
          </p>
        </div>
        <span className="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800 text-[11px] font-semibold text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          BP Master Validation
        </span>
      </div>

      {/* AI Insight Box */}
      <AiInsightBox section="vendormaster" kpis={aiKpis} />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'Total Suppliers', value: kpiMetrics.totalSuppliers, accent: 'blue', desc: 'Unique vendor codes in result' },
          { label: 'Same GSTIN on Multiple codes', value: kpiMetrics.sameGstMulti, accent: 'rose', desc: 'GSTINs registered to multiple codes' },
          { label: 'Dormant duplicate codes', value: kpiMetrics.dormantDuplicates, accent: 'slate', desc: 'Same GSTIN multi code and dormant status' },
          { label: 'Missing GSTIN(domestic)', value: kpiMetrics.missingGstDom, accent: 'amber', desc: 'Domestic vendors without GSTIN' },
          { label: 'Missing GSTIN(foreign)', value: kpiMetrics.missingGstFor, accent: 'amber', desc: 'Foreign vendors without GSTIN' },
          { label: 'Rows flagged', value: kpiMetrics.rowsFlagged, accent: 'rose', desc: 'Flagged for missing domestic/foreign GSTIN' }
        ].map(card => {
          const isRose = card.accent === 'rose'
          const isAmber = card.accent === 'amber'
          const isGreen = card.accent === 'green'
          const isSlate = card.accent === 'slate'
          const barColor = isRose ? 'bg-rose-500' : (isAmber ? 'bg-amber-500' : (isGreen ? 'bg-emerald-500' : (isSlate ? 'bg-slate-500' : 'bg-blue-500')))
          const textColor = isRose ? 'text-rose-600 dark:text-rose-400' : (isAmber ? 'text-amber-600 dark:text-amber-400' : (isGreen ? 'text-emerald-600 dark:text-emerald-400' : (isSlate ? 'text-slate-600 dark:text-slate-400' : 'text-blue-600 dark:text-blue-400')))
          
          return (
            <div key={card.label} className="relative bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden">
              <div className={`absolute top-0 left-0 right-0 h-0.5 ${barColor}`} />
              <p className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest leading-tight mb-2">
                {card.label}
              </p>
              <p className={`text-xl font-black tracking-tight leading-none ${textColor}`}>
                {typeof card.value === 'number' ? card.value.toLocaleString() : card.value}
              </p>
              {card.desc && <p className="text-[9px] text-slate-400 dark:text-slate-500 mt-2">{card.desc}</p>}
            </div>
          )
        })}
      </div>

      {/* Side Highlights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Related Party Vendors */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm">
          <div className="flex justify-between items-center mb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Identified Related Parties</h3>
              <p className="text-xs text-slate-400 mt-0.5">Audited records mapped to related business units</p>
            </div>
            <span className="px-2 py-0.5 rounded bg-rose-100 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 text-[10px] font-mono font-bold">
              {relatedParties.length} Found
            </span>
          </div>
          <div className="overflow-x-auto max-h-[350px] overflow-y-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="sticky top-0 z-20 bg-white dark:bg-slate-900">
                <tr className="border-b border-slate-100 dark:border-slate-800 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  <th className="py-2">Vendor Code</th>
                  <th className="py-2">Vendor Name</th>
                  <th className="py-2">Country / Region</th>
                  <th className="py-2">GSTIN</th>
                  <th className="py-2 text-right">Active Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-medium">
                {relatedParties.map((v, i) => (
                  <tr key={i} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 font-mono font-bold text-slate-950 dark:text-white"><TruncatedCell value={v.vendor_code} /></td>
                    <td className="py-2.5 text-slate-700 dark:text-slate-300 font-semibold">
                      <TruncatedCell value={v.vendor_name} />
                    </td>
                    <td className="py-2.5 text-slate-500 dark:text-slate-500"><TruncatedCell value={`${v.vendor_country} (${v.region})`} /></td>
                    <td className="py-2.5 font-mono text-slate-600 dark:text-slate-400"><TruncatedCell value={v.gstin} /></td>
                    <td className="py-2.5 text-right">
                      <span className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-mono font-bold ${
                        v.active === 'Active' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400' : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400'
                      }`}>
                        {v.active}
                      </span>
                    </td>
                  </tr>
                ))}
                {relatedParties.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-4 text-center text-slate-400">No related party vendors found</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Region & Active Status Breakdown */}
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Vendor Base Distribution</h3>
            <p className="text-xs text-slate-400 mt-0.5">Demographics and operational registry metrics</p>
          </div>

          <div className="space-y-4 my-4 flex-1 flex flex-col justify-center">
            {/* Region */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold text-slate-600 dark:text-slate-300">
                <span>Domestic vs. Foreign</span>
                <span className="font-bold text-slate-950 dark:text-white">{regionBreakdown.domestic} vs {regionBreakdown.foreign}</span>
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 rounded-full h-4 overflow-hidden relative flex shadow-inner">
                <div 
                  className="h-full bg-blue-500 flex items-center justify-center text-[9px] font-bold text-white transition-all duration-500"
                  style={{ width: `${regionBreakdown.domesticPct}%` }}
                >
                  {regionBreakdown.domesticPct > 15 && `Dom: ${regionBreakdown.domesticPct}%`}
                </div>
                <div 
                  className="h-full bg-indigo-600 flex items-center justify-center text-[9px] font-bold text-white transition-all duration-500"
                  style={{ width: `${regionBreakdown.foreignPct}%` }}
                >
                  {regionBreakdown.foreignPct > 15 && `For: ${regionBreakdown.foreignPct}%`}
                </div>
              </div>
            </div>

            {/* Active / Dormant */}
            <div className="space-y-1.5 pt-2">
              <div className="flex justify-between text-xs font-semibold text-slate-600 dark:text-slate-300">
                <span>Status Ratio</span>
                <span className="font-bold text-slate-950 dark:text-white">
                  Active: {rows.filter(r => r.active === 'Active').length} | Dormant: {rows.filter(r => r.active === 'Dormant').length}
                </span>
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 rounded-full h-4 overflow-hidden relative flex shadow-inner">
                {(() => {
                  const activeCount = rows.filter(r => r.active === 'Active').length
                  const dormantCount = rows.filter(r => r.active === 'Dormant').length
                  const tot = rows.length
                  const activePct = tot > 0 ? ((activeCount / tot) * 100).toFixed(1) : '0'
                  const dormantPct = tot > 0 ? ((dormantCount / tot) * 100).toFixed(1) : '0'
                  return (
                    <>
                      <div 
                        className="h-full bg-emerald-500 flex items-center justify-center text-[9px] font-bold text-white transition-all duration-500"
                        style={{ width: `${activePct}%` }}
                      >
                        {activePct > 15 && `Active: ${activePct}%`}
                      </div>
                      <div 
                        className="h-full bg-slate-500 flex items-center justify-center text-[9px] font-bold text-white transition-all duration-500"
                        style={{ width: `${dormantPct}%` }}
                      >
                        {dormantPct > 15 && `Dormant: ${dormantPct}%`}
                      </div>
                    </>
                  )
                })()}
              </div>
            </div>
          </div>
          <div className="text-[10px] text-slate-400 border-t border-slate-100 dark:border-slate-800/80 pt-3 text-center">
            Dormant vendors are flagged when Active value is not 'Y' in SAP.
          </div>
        </div>
      </div>

      {/* Table Section */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        {/* Table Toolbar */}
        <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800 flex flex-col gap-3">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">BP Master Registry Records</h3>
              <p className="text-xs text-slate-400 mt-0.5">Detail view of all Business Partners starting with code prefix V</p>
            </div>

            <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
              {/* Search input */}
              <div className="relative">
                <svg className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  placeholder="Search vendor base..."
                  value={searchTerm}
                  onChange={handleSearch}
                  className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 w-48 transition"
                />
              </div>

              {/* Region Filter */}
              <select
                value={regionFilter}
                onChange={e => { setRegionFilter(e.target.value); setCurrentPage(1) }}
                className="px-2 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
              >
                <option value="All">All Regions</option>
                <option value="Domestic">Domestic</option>
                <option value="Foreign">Foreign</option>
              </select>

              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={e => { setStatusFilter(e.target.value); setCurrentPage(1) }}
                className="px-2 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 cursor-pointer"
              >
                <option value="All">All Statuses</option>
                <option value="Active">Active</option>
                <option value="Dormant">Dormant</option>
              </select>
            </div>
          </div>

          {/* Quick Filters */}
          <div className="flex items-center gap-4 flex-wrap text-xs text-slate-600 dark:text-slate-400 font-medium bg-slate-50 dark:bg-slate-800/40 p-2 rounded-lg border border-slate-100 dark:border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider font-bold">Quick Filters:</span>
            <label className="flex items-center gap-1.5 cursor-pointer hover:text-slate-900 dark:hover:text-white select-none">
              <input
                type="checkbox"
                checked={onlyRelated}
                onChange={e => { setOnlyRelated(e.target.checked); setCurrentPage(1) }}
                className="rounded border-slate-300 dark:border-slate-750 text-blue-500 focus:ring-blue-500/20"
              />
              Related Party
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer hover:text-slate-900 dark:hover:text-white select-none">
              <input
                type="checkbox"
                checked={onlyMissingGst}
                onChange={e => { setOnlyMissingGst(e.target.checked); setCurrentPage(1) }}
                className="rounded border-slate-300 dark:border-slate-750 text-blue-500 focus:ring-blue-500/20"
              />
              Missing GSTIN
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer hover:text-slate-900 dark:hover:text-white select-none">
              <input
                type="checkbox"
                checked={onlyMultiGst}
                onChange={e => { setOnlyMultiGst(e.target.checked); setCurrentPage(1) }}
                className="rounded border-slate-300 dark:border-slate-750 text-blue-500 focus:ring-blue-500/20"
              />
              Same GST Multi-Code
            </label>
            {(onlyRelated || onlyMissingGst || onlyMultiGst || searchTerm || regionFilter !== 'All' || statusFilter !== 'All') && (
              <button
                onClick={() => {
                  setOnlyRelated(false);
                  setOnlyMissingGst(false);
                  setOnlyMultiGst(false);
                  setSearchTerm('');
                  setRegionFilter('All');
                  setStatusFilter('All');
                  setCurrentPage(1);
                }}
                className="text-xs font-bold text-rose-500 hover:text-rose-600 ml-auto"
              >
                Reset All Filters
              </button>
            )}
          </div>
        </div>

        {/* Responsive Table */}
        <div className="overflow-x-auto" style={{ maxHeight: '520px', overflowY: 'auto' }}>
          <table className="w-full text-left border-collapse min-w-[1800px]">
            <thead className="sticky top-0 z-20 bg-slate-50 dark:bg-slate-800/95 backdrop-blur-sm">
              <tr className="bg-slate-50/50 dark:bg-slate-800/40 border-b border-slate-100 dark:border-slate-800">
                {colOrder.map(colId => (
                  <th
                    key={colId}
                    draggable
                    onDragStart={(e) => { e.dataTransfer.effectAllowed = 'move'; setDragCol(colId) }}
                    onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; if (dragOverCol !== colId) setDragOverCol(colId) }}
                    onDragLeave={() => setDragOverCol(prev => (prev === colId ? null : prev))}
                    onDrop={(e) => { e.preventDefault(); if (dragCol && dragCol !== colId) moveColumn(dragCol, colId); setDragCol(null); setDragOverCol(null) }}
                    onDragEnd={() => { setDragCol(null); setDragOverCol(null) }}
                    onClick={() => handleSort(colId)}
                    title="Click to sort · Drag to reorder"
                    className={`px-4 py-3 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider cursor-grab active:cursor-grabbing select-none transition-colors hover:bg-slate-100/50 dark:hover:bg-slate-800/60 ${dragCol === colId ? 'opacity-40' : ''} ${dragOverCol === colId && dragCol !== colId ? 'bg-blue-100/70 dark:bg-blue-900/30 border-l-2 border-l-blue-500' : ''}`}
                  >
                    <div className="flex items-center font-bold">
                      {COL_LABEL[colId]}
                      <SortIcon dir={sortCol === colId ? sortDir : null} />
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-medium text-xs">
              {paginated.map((row, i) => {
                const isRP = row.related_party === 1
                return (
                  <tr
                    key={i}
                    className={`transition-colors duration-150 ${
                      isRP
                        ? 'bg-rose-50/20 dark:bg-rose-950/10 hover:bg-rose-50/40 dark:hover:bg-rose-950/20'
                        : 'hover:bg-slate-50/40 dark:hover:bg-slate-800/20'
                    }`}
                  >
                    {colOrder.map(colId => (
                      <td key={colId} className={CELL_CLASS[colId] || 'px-4 py-3 text-slate-700 dark:text-slate-300'}>
                        {renderCell(colId, row)}
                      </td>
                    ))}
                  </tr>
                )
              })}
              {paginated.length === 0 && (
                <tr>
                  <td colSpan={colOrder.length} className="px-6 py-10 text-center text-sm text-slate-400 dark:text-slate-500">
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
