import React from 'react'

/**
 * Renders a scrollable card table — matches original renderAuditTables behaviour.
 * title: card heading
 * rows: array of objects
 * maxRows: show scroll if rows > this (default 15)
 */
export default function DataTable({ title, rows = [], maxRows = 15 }) {
  if (!rows.length) return null

  const cols = Object.keys(rows[0])
  const scrollable = rows.length > maxRows

  // Clean columns for display (replace underscores, capitalize)
  const formatHeader = (str) => {
    return str
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase())
  }

  return (
    <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm overflow-hidden mb-6">
      <div className="px-6 py-4.5 border-b border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
        <h4 className="text-sm font-bold text-slate-900 dark:text-white">{title}</h4>
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
          {rows.length.toLocaleString()} records
        </span>
      </div>
      <div className={`overflow-x-auto ${scrollable ? 'max-h-96 overflow-y-auto' : ''}`}>
        <table className="w-full text-left border-collapse">
          <thead className="sticky top-0 z-20 bg-slate-50 dark:bg-slate-900 backdrop-blur-sm">
            <tr className="bg-slate-50/50 dark:bg-slate-800/40 border-b border-slate-100 dark:border-slate-800/80">
              {cols.map(c => (
                <th key={c} className="px-5 py-3 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider whitespace-nowrap">
                  {formatHeader(c)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {rows.map((row, i) => (
              <tr key={i} className="hover:bg-slate-50/40 dark:hover:bg-slate-800/20 transition-colors duration-150">
                {cols.map(c => {
                  const val = row[c]
                  // Check if it's a number and format or right-align if appropriate
                  const isNumeric = typeof val === 'number' || (!isNaN(parseFloat(val)) && isFinite(val) && !String(val).startsWith('0'))
                  return (
                    <td 
                      key={c} 
                      className={`px-5 py-3 text-xs text-slate-700 dark:text-slate-300 font-medium whitespace-nowrap ${isNumeric ? 'font-mono' : ''}`}
                    >
                      {val === null || val === undefined ? '—' : String(val)}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
