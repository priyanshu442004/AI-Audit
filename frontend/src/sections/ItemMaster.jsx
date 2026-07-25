import React, { useState, useMemo } from 'react'
import AiInsightBox from '../components/AiInsightBox'
import TruncatedCell from '../components/TruncatedCell'
import useColumnOrder from '../hooks/useColumnOrder'

const ROWS_PER_PAGE = 100

export default function ItemMaster({ data }) {
  const kpis   = data?.kpis   || {}
  const tables = data?.tables || []
  const [currentPage, setCurrentPage] = useState(0)

  // Transform table data for display
  const tableRows = tables[0]?.data || []
  const totalRows = tables[0]?.total_rows || tableRows.length
  
  // Memoize pagination calculations for performance
  const paginationData = useMemo(() => {
    const totalPages = Math.ceil(tableRows.length / ROWS_PER_PAGE)
    const startIdx = currentPage * ROWS_PER_PAGE
    const endIdx = Math.min(startIdx + ROWS_PER_PAGE, tableRows.length)
    const currentRows = tableRows.slice(startIdx, endIdx)
    
    return {
      totalPages,
      startIdx,
      endIdx,
      currentRows,
    }
  }, [tableRows, currentPage])

  // Determine which columns to show (all except the excluded ones)
  const allColumns = useMemo(() => {
    return tableRows.length > 0 ? Object.keys(tableRows[0]) : []
  }, [tableRows])
  
  const displayColumns = useMemo(() => {
    return allColumns.filter(col => {
      const colLower = col.toLowerCase()
      return !colLower.includes('g/l') && !colLower.includes('wtax')
    })
  }, [allColumns])

  const { order: colOrder, moveColumn } = useColumnOrder('item-master', displayColumns)
  const [dragCol, setDragCol]     = useState(null)
  const [dragOverCol, setDragOverCol] = useState(null)

  const visibleCols = colOrder

  const handleNextPage = () => {
    if (paginationData.totalPages > 0 && currentPage < paginationData.totalPages - 1) {
      setCurrentPage(currentPage + 1)
    }
  }

  const handlePrevPage = () => {
    if (currentPage > 0) {
      setCurrentPage(currentPage - 1)
    }
  }

  const handleGoToPage = (e) => {
    const page = parseInt(e.target.value) - 1
    if (page >= 0 && page < paginationData.totalPages) {
      setCurrentPage(page)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
          Item Master Analysis
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Comprehensive item master validation with purchase order integration and inventory tracking.
        </p>
      </div>

      <AiInsightBox section="itemmaster" kpis={kpis} />

      {/* KPIs Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { 
            label: 'Distinct Item Codes', 
            value: kpis.distinct_item_codes, 
            desc: 'Total unique items in master' 
          },
          { 
            label: 'Items Purchased', 
            value: kpis.items_with_pos, 
            color: 'text-emerald-600 dark:text-emerald-400',
            desc: 'Items with active POs' 
          },
          { 
            label: 'Unique POs', 
            value: kpis.unique_pos, 
            color: 'text-blue-600 dark:text-blue-400',
            desc: 'Total unique purchase orders' 
          }
        ].map(k => (
          <div key={k.label} className="group relative overflow-hidden rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">{k.label}</div>
            <div className={`text-3xl font-black tracking-tight ${k.color || 'text-slate-900 dark:text-white'}`}>
              {(k.value ?? '—').toLocaleString()}
            </div>
            {k.desc && <div className="text-[10px] text-slate-400 mt-1">{k.desc}</div>}
          </div>
        ))}
      </div>

      {/* Data Table */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-slate-200/80 dark:border-slate-800/80">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Item Master with PO Details
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">All {totalRows.toLocaleString()} items with associated purchase order information</p>
            </div>
          </div>
        </div>
        
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200/80 dark:border-slate-800/80 sticky top-0">
              <tr>
                {visibleCols.map(col => (
                  <th
                    key={col}
                    draggable
                    onDragStart={(e) => { e.dataTransfer.effectAllowed = 'move'; setDragCol(col) }}
                    onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; if (dragOverCol !== col) setDragOverCol(col) }}
                    onDragLeave={() => setDragOverCol(prev => (prev === col ? null : prev))}
                    onDrop={(e) => { e.preventDefault(); if (dragCol && dragCol !== col) moveColumn(dragCol, col); setDragCol(null); setDragOverCol(null) }}
                    onDragEnd={() => { setDragCol(null); setDragOverCol(null) }}
                    title="Drag to reorder"
                    className={`px-4 py-3 text-left font-semibold text-slate-600 dark:text-slate-300 whitespace-nowrap cursor-grab active:cursor-grabbing select-none${dragCol === col ? ' opacity-40' : ''}${dragOverCol === col && dragCol !== col ? ' bg-blue-100/70 dark:bg-blue-900/30 border-l-2 border-l-blue-500' : ''}`}
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200/80 dark:divide-slate-800/80">
              {paginationData.currentRows.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                  {visibleCols.map(col => {
                    const value = row[col] || '—'
                    const isNumeric = col === 'PO Qty' || col === 'Rate' || col === 'Price' || col === 'Items per Purchasing Unit' || col === 'No. of Items per Sales Unit'

                    return (
                      <td
                        key={`${idx}-${col}`}
                        className={`px-4 py-3 ${
                          isNumeric ? 'text-right font-mono' : 'text-slate-600 dark:text-slate-300'
                        }`}
                      >
                        <TruncatedCell value={value} />
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <div className="px-6 py-4 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200/80 dark:border-slate-800/80">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="text-xs text-slate-600 dark:text-slate-300">
              Showing <span className="font-semibold">{(paginationData.startIdx + 1).toLocaleString()}</span> to <span className="font-semibold">{paginationData.endIdx.toLocaleString()}</span> of <span className="font-semibold">{tableRows.length.toLocaleString()}</span> items
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handlePrevPage}
                disabled={currentPage === 0}
                className="px-3 py-1 rounded-md text-sm font-medium text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                ← Previous
              </button>

              <div className="flex items-center gap-1">
                <label htmlFor="page-input" className="text-xs text-slate-600 dark:text-slate-400">Page:</label>
                <input
                  id="page-input"
                  type="number"
                  min="1"
                  max={paginationData.totalPages}
                  value={currentPage + 1}
                  onChange={handleGoToPage}
                  className="w-12 px-2 py-1 rounded-md text-xs text-center border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
                />
                <span className="text-xs text-slate-600 dark:text-slate-400">of {paginationData.totalPages}</span>
              </div>

              <button
                onClick={handleNextPage}
                disabled={currentPage >= paginationData.totalPages - 1}
                className="px-3 py-1 rounded-md text-sm font-medium text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next →
              </button>
            </div>

            <div className="text-xs text-slate-500 dark:text-slate-400">
              {displayColumns.length} columns • {ROWS_PER_PAGE} rows per page
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
