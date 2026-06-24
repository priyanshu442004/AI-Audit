import React from 'react'
import DataTable from '../components/DataTable'
import AiInsightBox from '../components/AiInsightBox'
import { BAR_COLORS } from '../theme'

export default function PaymentAging({ data }) {
  const kpis   = data?.kpis   || {}
  const charts = data?.charts || {}
  const tables = data?.tables || []

  const bars     = charts.aging_bars      || []
  const ovdBars  = charts.overdue_amt_bars || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
          Payment Aging Analysis
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Audits accounts payable aging status, checking for delayed invoices and potential working capital leaks.
        </p>
      </div>

      <AiInsightBox section="paymentaging" kpis={kpis} />

      {/* KPIs Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Total Invoices Audited', value: kpis.total_invoices, desc: 'Processed purchase register rows' },
          { label: 'Early Settlement', value: kpis.early, color: 'text-green-600 dark:text-green-400', desc: 'Paid before terms limit' },
          { label: 'Paid On-Time', value: kpis.on_time, color: 'text-sky-600 dark:text-sky-400', desc: 'Paid exactly on terms' },
          { label: 'Paid Late', value: kpis.late, color: 'text-rose-600 dark:text-rose-400', desc: 'Paid after invoice due date' },
          { label: 'Unsettled (Not Due)', value: kpis.not_due, desc: 'Current liability under credit terms' },
          { label: 'Unsettled (Overdue)', value: kpis.overdue, color: 'text-rose-600 dark:text-rose-400', desc: 'Past due credit term threshold' },
          { label: 'Overdue Outstanding Amount', value: `₹${kpis.overdue_amt_l ?? 0} L`, color: 'text-rose-600 dark:text-rose-400', desc: 'Aggregated overdue amount' },
          { label: 'On-Time Ratio', value: `${kpis.on_time_pct ?? 0}%`, color: 'text-green-600 dark:text-green-400', desc: 'On-time invoice payment rate' }
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

      {/* Grid for aging bucket distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Invoices by Aging Category</h3>
            <p className="text-xs text-slate-400 mt-0.5">Classification of invoice lines by payment timing</p>
          </div>
          <div className="space-y-3.5 my-6 flex-1 flex flex-col justify-center">
            {bars.map(b => (
              <div key={b.label} className="space-y-1">
                <div className="flex justify-between text-xs font-semibold text-slate-600 dark:text-slate-300">
                  <span>{b.label}</span>
                  <span className="font-bold text-slate-950 dark:text-white">{(b.value || 0).toLocaleString()} ({b.pct}%)</span>
                </div>
                <div className="bg-slate-100 dark:bg-slate-800 rounded-full h-4 overflow-hidden relative shadow-inner">
                  <div 
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${Math.max(b.pct, 1)}%`, background: b.color }} 
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Overdue Age Breakdown</h3>
            <p className="text-xs text-slate-400 mt-0.5">Distribution of overdue trade payables value by aging brackets</p>
          </div>
          <div className="space-y-4 my-6 flex-1 flex flex-col justify-center">
            {ovdBars.map((b, i) => {
              const colors = ['bg-rose-500', 'bg-rose-600', 'bg-rose-700']
              return (
                <div key={b.label} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold text-slate-600 dark:text-slate-300">
                    <span>{b.label}</span>
                    <span className="font-bold text-slate-950 dark:text-white">₹{b.value_l} L</span>
                  </div>
                  <div className="bg-slate-100 dark:bg-slate-800 rounded-full h-4 overflow-hidden relative shadow-inner">
                    <div 
                      className={`h-full rounded-full ${colors[i % 3]} transition-all duration-500`}
                      style={{ width: `${Math.max(b.pct, 1)}%` }} 
                    />
                  </div>
                </div>
              )
            })}
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
