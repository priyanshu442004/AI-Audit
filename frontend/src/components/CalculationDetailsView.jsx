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
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <svg className="w-4 h-4 flex-shrink-0 text-blue-500 dark:text-blue-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
          </svg>
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
            Selected Value ({columnName})
          </span>
        </div>
        <div className="text-2xl font-black text-blue-600 dark:text-blue-400 break-all leading-tight">
          {value}
        </div>
        <span className="text-xs text-slate-500/80 dark:text-slate-500 mt-2 block">
          Source: <span className="font-medium text-slate-600 dark:text-slate-400">{sectionLabel || section}</span>
        </span>
      </div>

      {/* Heading */}
      <div className="mb-5">
        <div className="flex items-center gap-2 mb-1.5">
          <svg className="w-4 h-4 flex-shrink-0 text-blue-500 dark:text-blue-400" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          <h4 className="text-sm font-bold text-slate-800 dark:text-slate-100">
            Calculation Details
          </h4>
        </div>
        <p className="text-xs text-slate-500/80 dark:text-slate-500 leading-relaxed pl-6">
          This value is calculated using the following information.
        </p>
      </div>

      {/* Formula Display — business formula first, technical expression below */}
      <div className="mb-6 p-4 rounded-xl bg-blue-50/60 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/30">
        <div className="text-[10px] font-semibold text-blue-500 dark:text-blue-400 uppercase tracking-wider mb-2">
          Calculation Logic
        </div>
        <div className="text-sm font-bold text-slate-800 dark:text-slate-100 leading-relaxed">
          {formula}
        </div>
        {expression && expression !== formula && (
          <div className="mt-2 pt-2 border-t border-blue-100 dark:border-blue-900/20">
            <span className="text-[10px] font-semibold text-blue-400 uppercase tracking-wider block mb-1">
              Technical Expression
            </span>
            <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400 leading-relaxed">
              {expression}
            </div>
          </div>
        )}
      </div>

      {/* Input Values */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <div className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-3">
          Input Values ({resolvedInputs.length})
        </div>
        <div className="h-full overflow-y-auto space-y-2 pr-1">
          {resolvedInputs.map((input, idx) => {
            const isClickable =
              input.currentValue &&
              input.currentValue !== '—' &&
              input.currentValue !== 'None' &&
              input.currentValue !== 'NaN'

            return (
              <div
                key={idx}
                className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950/30 hover:bg-slate-50 dark:hover:bg-slate-900/30 transition-colors"
              >
                {/* Field Name (clickable) */}
                <div className="flex items-center justify-between mb-2">
                  <span
                    onClick={() =>
                      isClickable &&
                      onPivot(input.currentValue, input.field, section)
                    }
                    className={`text-xs font-bold ${
                      isClickable
                        ? 'text-blue-600 dark:text-blue-400 cursor-pointer hover:underline'
                        : 'text-slate-500 dark:text-slate-400'
                    }`}
                  >
                    {input.field}
                  </span>
                  {isClickable && (
                    <svg className="w-3 h-3 text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  )}
                </div>

                {/* Current Value (clickable) */}
                <div className="mb-2">
                  <span className="text-[10px] font-medium text-slate-400 dark:text-slate-500 uppercase">
                    Current Value
                  </span>
                  <div
                    onClick={() =>
                      isClickable &&
                      onPivot(input.currentValue, input.field, section)
                    }
                    className={`text-sm font-semibold mt-0.5 ${
                      isClickable
                        ? 'text-slate-800 dark:text-slate-200 cursor-pointer hover:text-blue-600 dark:hover:text-blue-400 hover:underline'
                        : 'text-slate-400 dark:text-slate-600'
                    }`}
                  >
                    {input.currentValue}
                  </div>
                </div>

                {/* Source File & Source Record */}
                <div className="grid grid-cols-2 gap-3 text-[10px]">
                  <div>
                    <span className="font-medium text-slate-400 dark:text-slate-500 uppercase">
                      Source File
                    </span>
                    <div className="text-slate-600 dark:text-slate-400 font-semibold mt-0.5 truncate">
                      {input.source_file}
                    </div>
                  </div>
                  <div>
                    <span className="font-medium text-slate-400 dark:text-slate-500 uppercase">
                      Source Record
                    </span>
                    <div className="text-slate-600 dark:text-slate-400 font-semibold mt-0.5 truncate">
                      {input.source_record}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}