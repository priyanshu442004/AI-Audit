import React, { useState, useMemo } from 'react'
import { useStore } from '../store'

import { 
  SECTION_LABELS, 
  getSectionRows, 
  getCrossReferences, 
  findMatchedRow, 
  evaluateKpiContributions,
  getCalculatedField,
} from '../utils/auditTraceHelpers'
import CalculationDetailsView from './CalculationDetailsView'

const MODAL_LABELS = {
  selectedValue: 'Selected Value',
  recordDetails: 'Details of This Record',
  kpiSection: 'How This Value Affects the Report',
  kpiSubtitle: 'See whether this value is used to calculate any other values shown on this page.',
  crossRefSection: 'Where Else This Value Appears',
  crossRefSubtitle: 'This value was found in other uploaded files. Click any row to see where it came from.',
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

  // Scan cross references
  const crossRefs = useMemo(() => {
    if (!currentTrace?.value) return {}
    return getCrossReferences(currentTrace.value, storeState)
  }, [currentTrace?.value, storeState])

  const crossRefKeys = Object.keys(crossRefs)
  const [activeTab, setActiveTab] = useState(crossRefKeys[0] || '')

  // Sync active tab when scan results change
  React.useEffect(() => {
    if (crossRefKeys.length > 0) {
      setActiveTab(crossRefKeys[0])
    } else {
      setActiveTab('')
    }
  }, [currentTrace?.value, crossRefKeys.length])

  // Get active row details
  const activeRows = getSectionRows(currentTrace.section, storeState)
  const currentMatchedRow = useMemo(() => {
    if (!currentTrace) return null
    return findMatchedRow(activeRows, currentTrace.value, currentTrace.rowValues)
  }, [currentTrace, activeRows])

  // Get KPI contributions
  const kpiContributions = useMemo(() => {
    return evaluateKpiContributions(currentTrace.section, currentMatchedRow)
  }, [currentTrace.section, currentMatchedRow])

  const hasKpiData = kpiContributions.length > 0

  // Check if the current value is a calculated field
  const calculatedField = useMemo(() => {
    if (!currentTrace) return null
    return getCalculatedField(currentTrace.section, currentTrace.columnName, storeState)
  }, [currentTrace?.section, currentTrace?.columnName, currentTrace?.value, storeState])

  const isCalculatedField = !!calculatedField

  if (!isOpen || !currentTrace) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-md bg-slate-900/60 dark:bg-slate-950/70 transition-all duration-200">
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl w-[95vw] max-w-6xl h-[85vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-900/50">
          <div className="flex items-center space-x-3 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-950/60 flex items-center justify-center text-blue-600 dark:text-blue-400">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Audit Trace & KPI Explorer</h3>
              {/* Breadcrumb Trail */}
              <div className="flex items-center space-x-1.5 mt-0.5 overflow-x-auto no-scrollbar py-0.5">
                {history.map((h, idx) => (
                  <React.Fragment key={idx}>
                    {idx > 0 && <span className="text-slate-400 text-[10px]">&gt;</span>}
                    <button
                      onClick={() => handleHistoryNavigate(idx)}
                      className={`text-[10px] font-semibold whitespace-nowrap px-2 py-0.5 rounded transition ${
                        idx === currentIndex
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
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
            className="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Content Grid: single column for calculated values, multi-column otherwise */}
        <div className={`flex-1 grid grid-cols-1 min-h-0 overflow-hidden ${isCalculatedField ? '' : hasKpiData ? 'lg:grid-cols-12' : 'lg:grid-cols-2'}`}>
          
          {/* Left Panel: Calculation Details or Matched Row Fields */}
          <div className={`${isCalculatedField ? 'lg:col-span-1' : hasKpiData ? 'lg:col-span-4' : 'lg:col-span-1'} border-r border-slate-200 dark:border-slate-800 p-6 flex flex-col min-h-0 bg-slate-50/40 dark:bg-slate-900/20`}>
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
                <div className="mb-8">
                  <div className="flex items-center gap-2 mb-2">
                    <SectionIcon d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                      {MODAL_LABELS.selectedValue} ({currentTrace.columnName})
                    </span>
                  </div>
                  <div className="text-2xl font-black text-blue-600 dark:text-blue-400 break-all leading-tight">
                    {currentTrace.value}
                  </div>
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
                    <div className="flex-1 overflow-y-auto border border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-950/30 divide-y divide-slate-100 dark:divide-slate-850 p-1">
                      {Object.entries(currentMatchedRow).map(([key, val]) => {
                        const isClickable = val && val !== '—' && val !== 'None' && val !== 'NaN'
                        return (
                          <div key={key} className="p-2 flex flex-col hover:bg-slate-50 dark:hover:bg-slate-900/30 transition-colors">
                            <span className="text-[10px] font-medium text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                              {key}
                            </span>
                            <span
                              onClick={() => isClickable && handlePivot(val, key)}
                              className={`text-xs font-semibold mt-0.5 break-all ${
                                isClickable
                                  ? 'text-slate-800 dark:text-slate-200 hover:text-blue-600 dark:hover:text-blue-400 cursor-pointer hover:underline'
                                  : 'text-slate-400 dark:text-slate-600'
                              }`}
                            >
                              {val === null || val === undefined || val === '' ? '—' : String(val)}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  ) : (
                    <div className="flex-1 flex items-center justify-center border border-dashed border-slate-350 dark:border-slate-750 rounded-xl p-6 text-center">
                      <p className="text-xs text-slate-400">Row matching current filters was not loaded.</p>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

          {hasKpiData && !isCalculatedField && (
          <div className="lg:col-span-4 border-r border-slate-200 dark:border-slate-800 p-6 flex flex-col min-h-0 bg-white dark:bg-slate-900">
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-1.5">
                <SectionIcon d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                  {MODAL_LABELS.kpiSection}
                </h4>
              </div>
              <p className="text-xs text-slate-500/80 dark:text-slate-500 leading-relaxed pl-6">
                {MODAL_LABELS.kpiSubtitle}
              </p>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3">
              {kpiContributions.map((contrib, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-xl border flex items-start space-x-3 transition ${
                    contrib.matched
                      ? 'bg-emerald-50/50 dark:bg-emerald-950/10 border-emerald-200/50 dark:border-emerald-900/30'
                      : 'bg-slate-50/50 dark:bg-slate-900/30 border-slate-200/60 dark:border-slate-800/40'
                  }`}
                >
                  <div className={`mt-0.5 rounded-full p-1 ${
                    contrib.matched
                      ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400'
                      : 'bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-600'
                  }`}>
                    {contrib.matched ? (
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="3" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="3" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    )}
                  </div>
                  <div>
                    <p className={`text-xs font-bold ${
                      contrib.matched ? 'text-emerald-800 dark:text-emerald-400' : 'text-slate-600 dark:text-slate-400'
                    }`}>
                      {contrib.kpi}
                    </p>
                    <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5 leading-relaxed">
                      {contrib.detail}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          )}

          {/* Right Panel: Cross-Section Tracing & Pivots - hidden for calculated values */}
          {!isCalculatedField && (
          <div className={`${hasKpiData ? 'lg:col-span-4' : 'lg:col-span-1'} p-6 flex flex-col min-h-0 bg-slate-50/40 dark:bg-slate-900/20`}>
            <div className="mb-5">
              <div className="flex items-center gap-2 mb-1.5">
                <SectionIcon d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                  {MODAL_LABELS.crossRefSection}
                </h4>
              </div>
              <p className="text-xs text-slate-500/80 dark:text-slate-500 leading-relaxed pl-6">
                {MODAL_LABELS.crossRefSubtitle}
              </p>
            </div>

            {crossRefKeys.length > 0 ? (
              <div className="flex-1 flex flex-col min-h-0">
                {/* Horizontal tabs */}
                <div className="flex space-x-1 overflow-x-auto py-1 border-b border-slate-200 dark:border-slate-800 no-scrollbar mb-3">
                  {crossRefKeys.map(k => (
                    <button
                      key={k}
                      onClick={() => setActiveTab(k)}
                      className={`px-3 py-1.5 text-[11px] font-bold rounded-lg whitespace-nowrap transition-all ${
                        activeTab === k
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800'
                      }`}
                    >
                      {SECTION_LABELS[k] || k} ({crossRefs[k].length})
                    </button>
                  ))}
                </div>

                {/* matched rows preview */}
                {activeTab && crossRefs[activeTab] && (
                  <div className="flex-1 overflow-hidden border border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-950/30 flex flex-col min-h-0">
                    <div className="overflow-auto flex-1 text-[11px]">
                      <table className="w-full border-collapse">
                        <thead className="sticky top-0 bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 z-10">
                          <tr>
                            {Object.keys(crossRefs[activeTab][0]).map(h => (
                              <th key={h} className="px-3 py-2 text-left font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider whitespace-nowrap">
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-850">
                          {crossRefs[activeTab].map((r, rIdx) => (
                            <tr key={rIdx} className="hover:bg-blue-50/20 dark:hover:bg-blue-950/10 transition-colors">
                              {Object.entries(r).map(([k, v]) => {
                                const isClickable = v && v !== '—' && v !== 'None' && v !== 'NaN'
                                return (
                                  <td
                                    key={k}
                                    onClick={() => isClickable && handlePivot(v, k, activeTab)}
                                    className={`px-3 py-2 whitespace-nowrap ${
                                      isClickable
                                        ? 'text-slate-700 dark:text-slate-300 font-semibold cursor-pointer hover:text-blue-600 dark:hover:text-blue-400 hover:underline'
                                        : 'text-slate-400 dark:text-slate-600'
                                    }`}
                                  >
                                    {v === null || v === undefined || v === '' ? '—' : String(v)}
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
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center border border-dashed border-slate-350 dark:border-slate-750 rounded-xl p-6 text-center">
                <svg className="w-8 h-8 text-slate-300 dark:text-slate-700 mb-2" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <p className="text-xs text-slate-400">No cross-reference matches found for this value in other modules.</p>
              </div>
            )}
          </div>
          )}

        </div>

      </div>
    </div>
  )
}
