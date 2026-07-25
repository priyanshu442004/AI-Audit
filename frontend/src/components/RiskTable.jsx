import React from 'react'
import TruncatedCell from './TruncatedCell'

const SEV_CLASSES = {
  CRITICAL: 'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300',
  HIGH:     'bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300',
  MEDIUM:   'bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300',
  LOW:      'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
}

export default function RiskTable({ risks = [] }) {
  if (!risks.length) return null
  return (
    <div className="app-card rounded-lg overflow-hidden">
      <div className="px-6 py-4 border-b app-divider">
        <h3 className="text-base font-semibold app-title">
          Top 10 Risks &amp; Recommended Actions
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="app-table-head">
            <tr>
              {['ID','Risk','Magnitude','Severity','Action'].map(h => (
                <th key={h} className="text-left px-4 py-3 app-label">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {risks.map((r, i) => (
              <tr key={i} className="app-row-hover">
                <td className="px-4 py-3 font-mono text-xs font-semibold app-body">
                  <TruncatedCell value={r.id} />
                </td>
                <td className="px-4 py-3 app-title text-[11px]">
                  <TruncatedCell value={r.risk} />
                </td>
                <td className="px-4 py-3 app-muted text-[11px] hidden md:table-cell">
                  <TruncatedCell value={r.magnitude} />
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${SEV_CLASSES[r.severity] || SEV_CLASSES.LOW}`}>
                    {r.severity}
                  </span>
                </td>
                <td className="px-4 py-3 app-muted text-[11px] hidden lg:table-cell">
                  <TruncatedCell value={r.action} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
