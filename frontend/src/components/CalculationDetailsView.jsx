import React from 'react'

/**
 * CalculationDetailsView
 *
 * Renders a "Calculation Details" view for calculated fields.
 * Shows:
 *   - Selected Value (header consistent with normal trace modal)
 *   - Heading & subtitle
 *   - Formula (business-friendly explanation, then technical expression)
 *   - Input values with Field Name, Current Value, Source File, Source Record
 *   - Each input value is clickable → opens its own trace via onPivot
 */
export default function CalculationDetailsView({
  value,
  columnName,
  section,
  sectionLabel,
  calculatedField,
  currentMatchedRow,
  onPivot,
}) {
  if (!calculatedField) return null

  const { formula, expression, inputs } = calculatedField

  // Resolve the actual value for each input from the current row
  const resolvedInputs = (inputs || []).map((input) => {
    const fieldValue = currentMatchedRow?.[input.field] ?? '—'
    return {
      ...input,
      currentValue: fieldValue,
    }
  })

  return (
    <div className="flex flex-col min-h-0 overflow-hidden">
      {/* Selected Value (consistent with normal trace modal) */}
      <div className="mb-5 pb-4 border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-950/40 flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <span className="text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-tight">
            Selected Value ({columnName})
          </span>
        </div>
        <div className="text-3xl font-black text-blue-600 dark:text-blue-400 break-all leading-tight mb-2">
          {value}
        </div>
        <span className="text-xs text-slate-500 dark:text-slate-500">
          Source: <span className="font-semibold text-slate-700 dark:text-slate-300">{sectionLabel || section}</span>
        </span>
      </div>

      {/* Main Content Grid: Two Columns */}
      <div className="flex-1 min-h-0 grid grid-cols-2 gap-4">
        {/* Left Column: Calculation Logic Widget */}
        <div className="flex flex-col min-h-0 overflow-hidden">
          {/* Widget Title */}
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-950/40 flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100">
              Calculation Logic
            </h4>
          </div>

          {/* Widget Box */}
          <div className="flex-1 min-h-0 overflow-hidden flex flex-col p-4 rounded-lg bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-950/20 dark:to-orange-950/10 border border-amber-200 dark:border-amber-900/40 shadow-sm">
            <div className="flex-1 min-h-0 overflow-y-auto pr-2">
              <div className="text-[11px] font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider mb-2.5 flex items-center gap-2">
                <svg className="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                Formula
              </div>
              <div className="text-sm font-bold text-slate-800 dark:text-slate-100 leading-relaxed mb-4">
                {formula}
              </div>
              {expression && expression !== formula && (
                <div>
                  <div className="text-[10px] font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider mb-1.5 flex items-center gap-2">
                    <svg className="w-3 h-3 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                    </svg>
                    Expression
                  </div>
                  <div className="text-xs font-mono text-slate-600 dark:text-slate-400 leading-relaxed bg-white/40 dark:bg-slate-950/30 p-2.5 rounded border border-amber-100 dark:border-amber-900/20 break-all">
                    {expression}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Input Values Widget */}
        <div className="flex flex-col min-h-0 overflow-hidden">
          {/* Widget Title */}
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-950/40 flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100">
              Input Values ({resolvedInputs.length})
            </h4>
          </div>

          {/* Widget Box */}
          <div className="flex-1 min-h-0 overflow-hidden flex flex-col p-4 rounded-lg border border-blue-200 dark:border-blue-900/40 bg-gradient-to-br from-blue-50/40 to-cyan-50/30 dark:from-blue-950/10 dark:to-cyan-950/10 shadow-sm">
            <div className="flex-1 min-h-0 overflow-y-auto space-y-3 pr-2">
              {resolvedInputs.map((input, idx) => {
                const isClickable =
                  input.currentValue &&
                  input.currentValue !== '—' &&
                  input.currentValue !== 'None' &&
                  input.currentValue !== 'NaN'

                return (
                  <div
                    key={idx}
                    className="p-3.5 rounded-lg border border-blue-150 dark:border-blue-800/30 bg-white dark:bg-slate-950/40 hover:border-blue-300 dark:hover:border-blue-700/50 hover:bg-blue-50/50 dark:hover:bg-blue-950/20 transition-all duration-150 shadow-xs"
                  >
                    {/* Field Name */}
                    <div className="flex items-start justify-between mb-2.5">
                      <span
                        onClick={() =>
                          isClickable &&
                          onPivot(input.currentValue, input.field, section)
                        }
                        className={`text-xs font-bold ${
                          isClickable
                            ? 'text-blue-600 dark:text-blue-400 cursor-pointer hover:underline'
                            : 'text-slate-700 dark:text-slate-300'
                        }`}
                      >
                        {input.field}
                      </span>
                      {isClickable && (
                        <svg className="w-3.5 h-3.5 text-blue-400 flex-shrink-0 ml-1.5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M13 9l3 3m0 0l-3 3m3-3H8" />
                        </svg>
                      )}
                    </div>

                    {/* Current Value */}
                    <div className="mb-2.5">
                      <span className="text-[9px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-1">
                        💾 Value
                      </span>
                      <div
                        onClick={() =>
                          isClickable &&
                          onPivot(input.currentValue, input.field, section)
                        }
                        className={`text-sm font-black break-all leading-tight ${
                          isClickable
                            ? 'text-slate-900 dark:text-slate-100 cursor-pointer hover:text-blue-600 dark:hover:text-blue-400'
                            : 'text-slate-600 dark:text-slate-400'
                        }`}
                      >
                        {input.currentValue}
                      </div>
                    </div>

                    {/* Source File */}
                    <div className="mb-2">
                      <span className="text-[9px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-0.5">
                        📁 File
                      </span>
                      <div className="text-xs text-slate-600 dark:text-slate-400 font-semibold break-words line-clamp-1">
                        {input.source_file || '—'}
                      </div>
                    </div>

                    {/* Source Record */}
                    <div>
                      <span className="text-[9px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block mb-0.5">
                        📋 Record
                      </span>
                      <div className="text-xs text-slate-600 dark:text-slate-400 font-semibold break-words line-clamp-2">
                        {input.source_record || '—'}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}