import React, { useState, useEffect, useMemo } from 'react'
import { useStore } from '../store'
import { searchAuditTrace } from '../api'
import { 
  SECTION_LABELS, 
  getSectionRows, 
  findMatchedRow, 
  getCalculatedField,
} from '../utils/auditTraceHelpers'
import CalculationDetailsView from './CalculationDetailsView'

const ROLE_LABELS = {
  vendor_master: 'BP Master',
  purchase_order: 'Purchase Order Report',
  gate_entry: 'Gate Entry Report',
  grpo: 'GRPO Report',
  purchase_register: 'Purchase Register',
  general_ledger: 'General Ledger',
  ap_credit_note: 'AP Credit Note',
  ap_invoice_report: 'AP Invoice Report',
  item_master: 'Item Master',
}

const MODAL_LABELS = {
  selectedValue: 'Selected Value',
  recordDetails: 'Details of This Record',
}

function SectionIcon({ d, className = 'w-4 h-4' }) {
  return (
    <svg className={`${className} flex-shrink-0 text-blue-500 dark:text-blue-400`} fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d={d} />
    </svg>
  )
}

export default function AuditTraceModal({ isOpen, onClose, initialData }) {
  const storeState = useStore()
  const [history, setHistory] = useState([initialData])
  const [currentIndex, setCurrentIndex] = useState(0)

  const currentTrace = history[currentIndex]

  // Real-time search state for the 9 raw source files
  const [searchResults, setSearchResults] = useState({})
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState('')

  // Pivot to a new value
  const handlePivot = (value, columnName = 'Pivoted Column', section = currentTrace.section) => {
    if (!value || value === '—' || value === 'None' || value === 'NaN') return

    const newTrace = {
      value: String(value).trim(),
      columnName,
      section,
      rowValues: null // Clear DOM row context for pivots
    }

    const newHistory = history.slice(0, currentIndex + 1).concat(newTrace)
    setHistory(newHistory)
    setCurrentIndex(newHistory.length - 1)
  }

  // Go back/forward in history
  const handleHistoryNavigate = (idx) => {
    setCurrentIndex(idx)
  }

  // Fetch search results from 9 raw source files whenever currentTrace value changes
  useEffect(() => {
    if (!currentTrace?.value) {
      setSearchResults({})
      return
    }

    setSearching(true)
    setSearchError('')
    
    searchAuditTrace(currentTrace.value)
      .then((data) => {
        setSearchResults(data)
        setSearching(false)
      })
      .catch((err) => {
        console.error(err)
        setSearchError(err.message || 'Failed to search raw source files')
        setSearching(false)
      })
  }, [currentTrace?.value])

  // Get active tabs based on matching roles
  const activeTabs = useMemo(() => {
    return Object.keys(searchResults).filter(role => searchResults[role] && searchResults[role].length > 0)
  }, [searchResults])

  const [activeTab, setActiveTab] = useState('')

  // Set first active tab when tabs load or change
  useEffect(() => {
    if (activeTabs.length > 0) {
      setActiveTab(activeTabs[0])
    } else {
      setActiveTab('')
    }
  }, [activeTabs])

  // Get active row details for the left panel
  const activeRows = getSectionRows(currentTrace.section, storeState)
  const currentMatchedRow = useMemo(() => {
    if (!currentTrace) return null
    return findMatchedRow(activeRows, currentTrace.value, currentTrace.rowValues)
  }, [currentTrace, activeRows])

  // Check if the current value is a calculated field
  const calculatedField = useMemo(() => {
    if (!currentTrace) return null
    return getCalculatedField(currentTrace.section, currentTrace.columnName, storeState)
  }, [currentTrace?.section, currentTrace?.columnName, storeState])

  const isCalculatedField = !!calculatedField

  if (!isOpen || !currentTrace) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-md bg-slate-900/60 dark:bg-slate-950/70 transition-all duration-200">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl w-[95vw] max-w-7xl h-[85vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Modal Header */}
        <div className="px-6 py-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-gradient-to-r from-slate-50 to-blue-50/30 dark:from-slate-900/50 dark:to-blue-950/20">
          <div className="flex items-center space-x-3 min-w-0">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-100 to-blue-50 dark:from-blue-950/80 dark:to-blue-900/40 flex items-center justify-center text-blue-600 dark:text-blue-400 flex-shrink-0">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div className="min-w-0">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">Audit Trace &amp; Source Explorer</h3>
              {/* Breadcrumb Trail */}
              <div className="flex items-center space-x-1.5 mt-1.5 overflow-x-auto no-scrollbar py-0.5">
                {history.map((h, idx) => (
                  <React.Fragment key={idx}>
                    {idx > 0 && <span className="text-slate-300 dark:text-slate-600 text-xs">/</span>}
                    <button
                      onClick={() => handleHistoryNavigate(idx)}
                      className={`text-xs font-semibold whitespace-nowrap px-2.5 py-1 rounded-md transition-all ${
                        idx === currentIndex
                          ? 'bg-blue-600 text-white shadow-md'
                          : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700'
                      }`}
                    >
                      {h.value}
                    </button>
                  </React.Fragment>
                ))}
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition flex-shrink-0"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Content Grid */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 min-h-0 overflow-hidden">
          
          {/* Left Panel: Record Details (Takes 4 cols out of 12) */}
          <div className="lg:col-span-4 border-r border-slate-200 dark:border-slate-800 p-6 flex flex-col min-h-0 bg-slate-50/40 dark:bg-slate-900/20 justify-between">
            <div className="flex-1 flex flex-col min-h-0">
              {isCalculatedField ? (
                <CalculationDetailsView
                  value={currentTrace.value}
                  columnName={currentTrace.columnName}
                  section={currentTrace.section}
                  sectionLabel={SECTION_LABELS[currentTrace.section] || currentTrace.section}
                  calculatedField={calculatedField}
                  currentMatchedRow={currentMatchedRow}
                  onPivot={handlePivot}
                />
              ) : (
                <>
                  <div className="mb-6">
                    <div className="flex items-center gap-2 mb-2">
                      <SectionIcon d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                      <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                        {MODAL_LABELS.selectedValue} ({currentTrace.columnName})
                      </span>
                    </div>
                    <div className="text-2xl font-black text-blue-600 dark:text-blue-400 break-all leading-tight">
                      {currentTrace.value}
                    </div>
                    {String(currentTrace.value).includes(',') && (
                      <div className="mt-3 p-2.5 rounded-lg bg-blue-50/60 dark:bg-blue-950/40 border border-blue-200/80 dark:border-blue-800/60">
                        <span className="text-[10px] font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider block mb-1.5">
                          Multiple Values ({String(currentTrace.value).split(',').filter(Boolean).length}) — Click to pivot single item:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {String(currentTrace.value)
                            .split(',')
                            .map(item => item.trim())
                            .filter(item => item && item !== '—' && item !== 'None' && item !== 'NaN')
                            .map((item, idx) => (
                              <button
                                key={idx}
                                onClick={() => handlePivot(item, currentTrace.columnName)}
                                className="px-2.5 py-1 text-xs font-bold rounded-md bg-white dark:bg-slate-800 text-blue-600 dark:text-blue-300 hover:bg-blue-600 hover:text-white dark:hover:bg-blue-600 dark:hover:text-white border border-blue-200 dark:border-blue-700 shadow-xs transition-all flex items-center gap-1"
                              >
                                <span>{item}</span>
                                <svg className="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 9l3 3m0 0l-3 3m3-3H8" />
                                </svg>
                              </button>
                            ))}
                        </div>
                      </div>
                    )}
                    <span className="text-xs text-slate-500/80 dark:text-slate-500 mt-2 block">
                      Source: <span className="font-medium text-slate-600 dark:text-slate-400">{SECTION_LABELS[currentTrace.section] || currentTrace.section}</span>
                    </span>
                  </div>

                  <div className="flex-1 flex flex-col min-h-0">
                    <div className="flex items-center gap-2 mb-3">
                      <SectionIcon d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100">{MODAL_LABELS.recordDetails}</h4>
                    </div>
                    {currentMatchedRow ? (
                      <div className="flex-1 overflow-y-auto border border-slate-200 dark:border-slate-800 rounded-lg bg-white dark:bg-slate-950/30 divide-y divide-slate-100 dark:divide-slate-800">
                        {Object.entries(currentMatchedRow).map(([key, val]) => {
                          const strVal = String(val ?? '').trim()
                          const isClickable = strVal !== '' && strVal !== '—' && strVal !== 'None' && strVal !== 'NaN' && strVal !== 'null'
                          const isCommaSeparated = isClickable && strVal.includes(',')

                          return (
                            <div key={key} className="px-4 py-3 hover:bg-blue-50/45 dark:hover:bg-blue-950/25 transition-colors">
                              <div className="flex items-start justify-between gap-2">
                                <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex-shrink-0">
                                  {key}
                                </span>
                                {isClickable && (
                                  <svg className="w-3 h-3 text-blue-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 9l3 3m0 0l-3 3m3-3H8" />
                                  </svg>
                                )}
                              </div>
                              {isCommaSeparated ? (
                                <div className="mt-1.5 flex flex-wrap gap-1.5">
                                  {strVal
                                    .split(',')
                                    .map(item => item.trim())
                                    .filter(item => item && item !== '—' && item !== 'None' && item !== 'NaN')
                                    .map((item, idx) => (
                                      <button
                                        key={idx}
                                        onClick={(e) => {
                                          e.stopPropagation()
                                          handlePivot(item, key)
                                        }}
                                        className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 hover:text-white hover:bg-blue-600 dark:hover:bg-blue-600 cursor-pointer border border-blue-200/60 dark:border-blue-800/60 transition-colors flex items-center gap-1"
                                      >
                                        <span>{item}</span>
                                        <svg className="w-3 h-3 flex-shrink-0 opacity-70" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                                          <path strokeLinecap="round" strokeLinejoin="round" d="M13 9l3 3m0 0l-3 3m3-3H8" />
                                        </svg>
                                      </button>
                                    ))}
                                </div>
                              ) : (
                                <span
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    if (isClickable) handlePivot(val, key)
                                  }}
                                  className={`text-xs font-semibold mt-1.5 block break-all leading-relaxed ${
                                    isClickable
                                      ? 'text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 cursor-pointer hover:underline decoration-dotted underline-offset-2'
                                      : 'text-slate-500 dark:text-slate-600'
                                  }`}
                                >
                                  {val === null || val === undefined || val === '' ? '—' : String(val)}
                                </span>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    ) : (
                      <div className="flex-1 flex items-center justify-center border border-dashed border-slate-300 dark:border-slate-700 rounded-lg p-6 text-center bg-slate-50/50 dark:bg-slate-900/20">
                        <p className="text-sm text-slate-500 dark:text-slate-400">Row matching current filters was not loaded.</p>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>

            {/* Action buttons (Close) */}
            <button
              onClick={onClose}
              className="w-full mt-6 py-3 px-4 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-bold rounded-xl transition duration-200 border border-slate-200 dark:border-slate-700 shadow-sm"
            >
              Close
            </button>
          </div>

          {/* Right Panel: Raw Source File Tabs and Tables (Takes 8 cols out of 12) */}
          <div className="lg:col-span-8 p-6 flex flex-col min-h-0 bg-white dark:bg-slate-900">
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-1">
                <SectionIcon d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                  Raw Source File Reference (Cross-Analysis)
                </h4>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed pl-6">
                Direct matching records from the 9 raw source files. Click any cell to pivot trace.
              </p>
            </div>

            {searching ? (
              <div className="flex-1 flex flex-col items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4" />
                <p className="text-sm text-slate-400 font-medium">Scanning raw source files...</p>
              </div>
            ) : searchError ? (
              <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
                <p className="text-sm text-rose-500 font-semibold mb-2">Error</p>
                <p className="text-xs text-slate-400">{searchError}</p>
              </div>
            ) : activeTabs.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center border border-dashed border-slate-250 dark:border-slate-750 rounded-xl p-6 text-center bg-slate-50/20 dark:bg-slate-950/10">
                <svg className="w-10 h-10 text-slate-300 dark:text-slate-700 mb-2" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <p className="text-sm text-slate-400 font-medium">No matching records found in the 9 raw source files.</p>
              </div>
            ) : (
              <div className="flex-1 flex flex-col min-h-0">
                {/* File Role Tabs */}
                <div className="flex space-x-1 overflow-x-auto py-1 border-b border-slate-200 dark:border-slate-800 no-scrollbar mb-4 flex-shrink-0">
                  {activeTabs.map(role => (
                    <button
                      key={role}
                      onClick={() => setActiveTab(role)}
                      className={`px-3 py-2 text-xs font-bold rounded-lg whitespace-nowrap transition-all ${
                        activeTab === role
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700'
                      }`}
                    >
                      {ROLE_LABELS[role] || role} ({searchResults[role].length})
                    </button>
                  ))}
                </div>

                {/* Raw data rows table */}
                {activeTab && searchResults[activeTab] && (
                  <div className="flex-1 overflow-hidden border border-slate-200 dark:border-slate-800 rounded-xl bg-slate-50/30 dark:bg-slate-950/10 flex flex-col min-h-0">
                    <div className="overflow-auto flex-1 text-xs">
                      <table className="w-full border-collapse">
                        <thead className="sticky top-0 bg-slate-100 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 z-10">
                          <tr>
                            {Object.keys(searchResults[activeTab][0]).map(h => (
                              <th key={h} className="px-3 py-2.5 text-left font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider whitespace-nowrap">
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200/60 dark:divide-slate-800/80">
                          {searchResults[activeTab].map((row, rIdx) => (
                            <tr key={rIdx} className="hover:bg-blue-50/20 dark:hover:bg-blue-950/15 bg-white dark:bg-slate-900/40 transition-colors">
                              {Object.entries(row).map(([colName, cellVal]) => {
                                const isClickable = cellVal !== null && cellVal !== undefined && cellVal !== '' && cellVal !== '—' && cellVal !== 'None' && cellVal !== 'NaN'
                                return (
                                  <td
                                    key={colName}
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      if (isClickable) handlePivot(cellVal, colName, activeTab)
                                    }}
                                    className={`px-3 py-2.5 whitespace-nowrap font-semibold ${
                                      isClickable
                                        ? 'text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 cursor-pointer hover:underline decoration-dotted underline-offset-2'
                                        : 'text-slate-500 dark:text-slate-500'
                                    }`}
                                  >
                                    {cellVal === null || cellVal === undefined || cellVal === '' ? '—' : String(cellVal)}
                                  </td>
                                )
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  )
}
