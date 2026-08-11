import React from 'react'
import DataTable from '../components/DataTable'
import AiInsightBox from '../components/AiInsightBox'

export default function PriceVariance({ data }) {
  const kpis   = data?.kpis   || {}
  const charts = data?.charts || {}
  const tables = data?.tables || []
  const top10  = charts.top10_savings || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
          Price Variance &amp; Potential Savings
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Identifies purchase price variance (PPV) across different vendors for the same item codes to capture savings opportunities.
        </p>
      </div>

      <AiInsightBox section="pricevariance" kpis={kpis} />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Anomalous Items (>5% PPV)', value: kpis.items_above_5pct, desc: 'Unique item codes with pricing variance' },
          { label: 'Total Estimated Savings', value: `₹${kpis.total_saving_l ?? 0} L`, color: 'text-green-600 dark:text-green-400', desc: 'Price leakage opportunity' },
          { label: 'Max Single Saving', value: kpis.biggest_saving != null ? `₹${(kpis.biggest_saving / 1e7).toFixed(2)} Cr` : '—', color: 'text-blue-600 dark:text-blue-400', desc: 'Highest impact item' },
          { label: 'Transaction Rows Audited', value: kpis.rows_reviewed, desc: 'Total line items evaluated' }
        ].map(k => (
          <div key={k.label} className="group relative overflow-hidden rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">{k.label}</div>
            <div className={`text-2xl font-black tracking-tight ${k.color || 'text-slate-900 dark:text-white'}`}>
              {typeof k.value === 'number' ? k.value.toLocaleString() : k.value}
            </div>
            {k.desc && <div className="text-[10px] text-slate-400 mt-1">{k.desc}</div>}
          </div>
        ))}
      </div>

      {/* Top 10 savings table */}
      {top10.length > 0 && (
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm overflow-hidden">
          <div className="px-6 py-4.5 border-b border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Top 10 Items by Potential Savings</h3>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400">
              Savings Focus Area
            </span>
          </div>
          <div className="overflow-x-auto max-h-[350px] overflow-y-auto">
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 z-20 bg-slate-50 dark:bg-slate-800/95 backdrop-blur-sm">
                <tr className="bg-slate-50/50 dark:bg-slate-800/40 border-b border-slate-100 dark:border-slate-800/80">
                  <th className="px-6 py-3 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider w-16">Rank</th>
                  <th className="px-6 py-3 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Item Details</th>
                  <th className="px-6 py-3 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider text-right">Potential Savings (₹)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {top10.map((row, i) => (
                  <tr key={i} className="hover:bg-slate-50/40 dark:hover:bg-slate-800/20 transition-colors duration-150">
                    <td className="px-6 py-3.5 text-xs font-mono font-bold text-slate-400 dark:text-slate-500">
                      #{(row.rank || i + 1).toString().padStart(2, '0')}
                    </td>
                    <td className="px-6 py-3.5 text-xs font-semibold text-slate-900 dark:text-white">
                      {row['Description'] || row['Item No.']}
                    </td>
                    <td className="px-6 py-3.5 text-right text-xs font-bold text-emerald-600 dark:text-emerald-400 font-mono">
                      ₹{Number(row['Potential Saving (₹)']).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detail Tables */}
      <div className="space-y-6">
        {tables.map(t => <DataTable key={t.title} title={t.title} rows={t.rows} />)}
      </div>
    </div>
  )
}
