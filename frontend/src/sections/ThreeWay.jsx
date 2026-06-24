import React from 'react'
import DonutChart from '../components/DonutChart'
import DataTable from '../components/DataTable'
import AiInsightBox from '../components/AiInsightBox'

export default function ThreeWay({ data }) {
  const kpis   = data?.kpis   || {}
  const charts = data?.charts || {}
  const tables = data?.tables || []

  const donut  = charts.match_donut  || { total: 0, segments: [] }
  const pvg    = charts.po_vs_grpo   || {}

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
          Three-Way Match Verification
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Compares Purchase Order (PO), Goods Receipt (GRPO), and AP Invoice details to verify quantity and unit price alignment.
        </p>
      </div>

      <AiInsightBox section="threeway" kpis={kpis} />

      {/* KPIs Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Audited Records', value: kpis.total_records, desc: 'Matched transaction rows' },
          { label: 'Fully Matched (Perfect)', value: kpis.fully_matched, color: 'text-green-600 dark:text-green-400', desc: 'No price or quantity variance' },
          { label: 'Quantity Mismatch', value: kpis.qty_exceptions, color: 'text-rose-600 dark:text-rose-400', desc: 'Receipt qty != invoice qty' },
          { label: 'Pricing Mismatch', value: kpis.rate_exceptions, color: 'text-amber-600 dark:text-amber-500', desc: 'Unit rate difference found' }
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

      {/* Comparisons */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Three-Way Verification Outcomes</h3>
            <p className="text-xs text-slate-400 mt-0.5">Matching status breakdown of audited transactions</p>
          </div>
          <div className="flex items-center justify-center my-6">
            <DonutChart
              segments={donut.segments || []}
              centerText={(donut.total || 0).toLocaleString()}
              centerSub="Audited Invoices"
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
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Purchase Order vs Goods Receipt</h3>
            <p className="text-xs text-slate-400 mt-0.5">Comparison of order quantity against receipt quantity</p>
          </div>
          
          <div className="grid grid-cols-3 gap-3 my-4">
            {[
              { label: 'Exact Match', value: pvg.matched, bg: 'bg-green-50/50 dark:bg-green-950/20', text: 'text-green-700 dark:text-green-400' },
              { label: 'PO > GRPO (Short)', value: pvg.po_gt_grpo, bg: 'bg-rose-50/50 dark:bg-rose-950/20', text: 'text-rose-700 dark:text-rose-400' },
              { label: 'PO < GRPO (Excess)', value: pvg.po_lt_grpo, bg: 'bg-amber-50/50 dark:bg-amber-950/20', text: 'text-amber-700 dark:text-amber-400' }
            ].map(c => (
              <div key={c.label} className={`${c.bg} rounded-xl p-3 text-center border border-slate-100 dark:border-slate-800/80`}>
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">{c.label}</div>
                <div className={`text-base font-black ${c.text}`}>{(c.value || 0).toLocaleString()}</div>
              </div>
            ))}
          </div>

          <div className="rounded-xl border border-slate-100 dark:border-slate-800/80 p-4 space-y-2.5">
            <h4 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-1">Volume Metric Highlights</h4>
            {[
              { label: 'Total Ordered Volume', value: pvg.total_po_qty },
              { label: 'Total Received Volume', value: pvg.total_grpo_qty },
              { label: 'Short Receipts Delta', value: pvg.short_receipt, color: 'text-rose-600 dark:text-rose-400' }
            ].map(r => (
              <div key={r.label} className="flex items-center justify-between text-xs">
                <span className="text-slate-500 dark:text-slate-400 font-medium">{r.label}</span>
                <span className={`font-bold font-mono text-slate-900 dark:text-white ${r.color || ''}`}>
                  {(r.value || 0).toLocaleString()} units
                </span>
              </div>
            ))}
          </div>
          
          <div className="text-[10px] text-slate-400 border-t border-slate-100 dark:border-slate-800/80 pt-3 text-center">
            Short receipts may indicate outstanding supplier backorders or receipt errors.
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
