import React from 'react'
import DonutChart from '../components/DonutChart'
import DataTable from '../components/DataTable'
import AiInsightBox from '../components/AiInsightBox'

export default function GrpoExcept({ data }) {
  const kpis   = data?.kpis   || {}
  const charts = data?.charts || {}
  const tables = data?.tables || []

  const donut = charts.exceptions_donut || { total: 0, segments: [] }
  const vd    = charts.visual_distribution || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
          GRPO Linkage Exceptions
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Identifies gaps and failures in document relationships between Goods Receipts (GRPO), Gate Entries (GE), and AP Invoices.
        </p>
      </div>

      <AiInsightBox section="grpoexcept" kpis={kpis} />

      {/* KPIs Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'GRPO w/o Invoice', value: kpis.grpo_no_invoice, color: 'text-amber-600 dark:text-amber-500', desc: 'Received items not yet billed' },
          { label: 'GE w/o GRPO', value: kpis.ge_no_grpo, color: 'text-rose-600 dark:text-rose-400', desc: 'Gate entries missing physical goods receipt' },
          { label: 'Invoice w/o GE', value: kpis.invoice_no_ge, color: 'text-rose-600 dark:text-rose-400', desc: 'Billed items without recorded gate entry' },
          { label: 'Total Exceptions', value: kpis.total_exceptions, color: 'text-rose-600 dark:text-rose-400', desc: 'Linkage violations detected' }
        ].map(k => (
          <div key={k.label} className="group relative overflow-hidden rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm">
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">{k.label}</div>
            <div className={`text-2xl font-black tracking-tight ${k.color || 'text-slate-900 dark:text-white'}`}>
              {(k.value ?? '—').toLocaleString()}
            </div>
            {k.desc && <div className="text-[10px] text-slate-400 mt-1">{k.desc}</div>}
          </div>
        ))}
      </div>

      {/* Breakdown Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Exceptions by Type</h3>
            <p className="text-xs text-slate-400 mt-0.5">Distribution of document linkage errors</p>
          </div>
          <div className="flex items-center justify-center my-6">
            <DonutChart
              segments={donut.segments || []}
              centerText={(donut.total || 0).toLocaleString()}
              centerSub="Total Exceptions"
            />
          </div>
          <div className="space-y-2 text-xs border-t border-slate-100 dark:border-slate-800/80 pt-3">
            {(donut.segments || []).map(s => (
              <div key={s.label} className="flex justify-between items-center">
                <span className="flex items-center gap-2 text-slate-600 dark:text-slate-300 font-medium">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: s.color }} />
                  {s.label}
                </span>
                <span className="font-semibold text-slate-950 dark:text-white">{(s.value || 0).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Visual Distribution</h3>
            <p className="text-xs text-slate-400 mt-0.5">Exceptions scaled relative to total audit footprint</p>
          </div>
          <div className="space-y-4 my-6 flex-1 flex flex-col justify-center">
            {vd.map((item, i) => {
              const colors = ['bg-blue-600', 'bg-amber-500', 'bg-rose-600']
              return (
                <div key={item.label} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold text-slate-600 dark:text-slate-300">
                    <span>{item.label}</span>
                    <span className="font-bold text-slate-950 dark:text-white">{(item.value || 0).toLocaleString()}</span>
                  </div>
                  <div className="bg-slate-100 dark:bg-slate-800 rounded-full h-5 overflow-hidden relative shadow-inner">
                    <div 
                      className={`h-full rounded-full ${colors[i % 3]} flex items-center justify-end pr-2 transition-all duration-500`}
                      style={{ width: `${Math.max(item.pct, 1)}%` }} 
                    >
                      <span className="text-[9px] font-bold text-white leading-none z-10">{item.pct}%</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
          <div className="text-[10px] text-slate-400 border-t border-slate-100 dark:border-slate-800/80 pt-3 text-center">
            Unlinked documents indicate potential system gaps, vendor bypasses, or unrecorded material movements.
          </div>
        </div>
      </div>

      {/* Tables */}
      <div className="space-y-6">
        {tables.map(t => <DataTable key={t.title} title={t.title} rows={t.rows} />)}
      </div>
    </div>
  )
}
