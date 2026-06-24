import React from 'react'
import DonutChart from '../components/DonutChart'
import DataTable from '../components/DataTable'
import AiInsightBox from '../components/AiInsightBox'
import { BAR_COLORS, CHART_COLORS } from '../theme'

export default function QtyVariance({ data }) {
  const kpis   = data?.kpis   || {}
  const charts = data?.charts || {}
  const tables = data?.tables || []

  const vb  = charts.variance_buckets   || { total: 0, within_pct: 0, segments: [] }
  const gs  = charts.goods_vs_services  || []

  const gsColors = ['bg-emerald-600', 'bg-rose-600', 'bg-blue-600', 'bg-amber-600']

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
          Quantity Variance Analysis
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Identifies discrepancies between Purchase Order quantities and actual physical Receipts (GRPO).
        </p>
      </div>

      <AiInsightBox section="qtyvariance" kpis={kpis} />

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Audited Lines', value: kpis.total_lines, desc: 'Total transaction lines checked' },
          { label: 'Within Tolerance', value: kpis.within_tol, color: 'text-green-600 dark:text-green-400', desc: 'Acceptable 0-5% difference' },
          { label: 'Tolerance Breaches', value: kpis.above_tol, color: 'text-rose-600 dark:text-rose-400', desc: 'Anomalies exceeding 5% variance' },
          { label: 'Anomalous Rate', value: `${kpis.exception_rate ?? 0}%`, color: 'text-rose-600 dark:text-rose-400', desc: 'Percentage of faulty receipts' }
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

      {/* Graph and breakdown card */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Quantity Variance Buckets</h3>
            <p className="text-xs text-slate-400 mt-0.5">Tolerance classification of receipt quantities</p>
          </div>
          <div className="flex items-center justify-center my-6">
            <DonutChart
              segments={(vb.segments || []).map(s => ({
                ...s, color: s.label?.includes('Within') ? CHART_COLORS.success : CHART_COLORS.risk,
              }))}
              centerText={`${vb.within_pct ?? 0}%`}
              centerSub="Within Tolerance"
            />
          </div>
          <div className="space-y-2 text-xs border-t border-slate-100 dark:border-slate-800/80 pt-3">
            {(vb.segments || []).map(s => (
              <div key={s.label} className="flex justify-between items-center">
                <span className="flex items-center gap-2 text-slate-600 dark:text-slate-300 font-medium">
                  <span className={`w-2.5 h-2.5 rounded-full ${s.label?.includes('Within') ? 'bg-green-600' : 'bg-rose-600'}`} />
                  {s.label}
                </span>
                <span className="font-semibold text-slate-950 dark:text-white">{(s.value || 0).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Material Categories (Goods vs Services)</h3>
            <p className="text-xs text-slate-400 mt-0.5">Breakdown of line items by physical material and services</p>
          </div>
          <div className="space-y-4 my-6 flex-1 flex flex-col justify-center">
            {gs.map((item, i) => (
              <div key={item.label} className="space-y-1">
                <div className="flex justify-between text-xs font-semibold text-slate-600 dark:text-slate-300">
                  <span>{item.label}</span>
                  <span className="font-bold text-slate-950 dark:text-white">{(item.value || 0).toLocaleString()} ({item.pct}%)</span>
                </div>
                <div className="bg-slate-100 dark:bg-slate-800 rounded-full h-4 overflow-hidden relative shadow-inner">
                  <div 
                    className={`h-full rounded-full ${gsColors[i % 4]} transition-all duration-500`}
                    style={{ width: `${Math.max(item.pct, 1)}%` }} 
                  />
                </div>
              </div>
            ))}
          </div>
          <div className="text-[10px] text-slate-400 border-t border-slate-100 dark:border-slate-800/80 pt-3 text-center">
            Service codes are prefixed by "SV" in accordance with company ledger policies.
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
