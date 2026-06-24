import React from 'react'
import DonutChart from '../components/DonutChart'
import DataTable from '../components/DataTable'
import AiInsightBox from '../components/AiInsightBox'
import { BAR_COLORS, CHART_COLORS } from '../theme'

export default function Msme({ data }) {
  const kpis   = data?.kpis   || {}
  const charts = data?.charts || {}
  const tables = data?.tables || []

  const donut    = charts.msme_donut     || { total: 0, segments: [] }
  const delayBars = charts.avg_delay_bars || []

  const catColors = { 
    MEDIUM: CHART_COLORS.info, 
    MICRO: CHART_COLORS.success, 
    N: CHART_COLORS.neutral, 
    SMALL: CHART_COLORS.warning 
  }

  const categoryLabels = {
    MICRO: 'Micro Enterprises',
    SMALL: 'Small Enterprises',
    MEDIUM: 'Medium Enterprises',
    N: 'Non-MSME Vendors'
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
          MSME Compliance Audit
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Strict regulatory check under Section 16 of the MSMED Act, enforcing a 45-day maximum credit term for registered Micro &amp; Small enterprises.
        </p>
      </div>

      <AiInsightBox section="msme" kpis={kpis} />

      {/* KPIs Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Micro Invoices', value: kpis.micro_invoices, desc: 'Registered Micro vendors' },
          { label: 'Small Invoices', value: kpis.small_invoices, desc: 'Registered Small vendors' },
          { label: 'Total MSME Invoices', value: kpis.total_msme, desc: 'Aggregated MSME registry rows' },
          { label: 'MSME Spend Value', value: `₹${kpis.msme_value_cr ?? 0} Cr`, desc: 'Total spend volume' },
          { label: '45-Day Rule Breaches', value: kpis.breaches, color: 'text-rose-600 dark:text-rose-400', desc: 'Invoices exceeding 45 days limit' },
          { label: 'Overdue Breach Spend', value: `₹${kpis.breach_val_cr ?? 0} Cr`, color: 'text-rose-600 dark:text-rose-400', desc: 'Breached total value' },
          { label: 'Indicative Interest Penalty', value: `₹${kpis.penalty_l ?? 0} L`, color: 'text-amber-600 dark:text-amber-500', desc: '3x RBI Bank Rate penalty' },
          { label: 'Breach Ratio', value: `${kpis.breach_rate ?? 0}%`, color: 'text-rose-600 dark:text-rose-400', desc: 'Percentage of breached bills' }
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

      {/* Graphs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">MSME Categorisation</h3>
            <p className="text-xs text-slate-400 mt-0.5">Classification of invoices by registered MSME status</p>
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
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: s.color || catColors[s.label] || '#94a3b8' }} />
                  {categoryLabels[s.label] || s.label}
                </span>
                <span className="font-semibold text-slate-950 dark:text-white">{(s.value || 0).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Average Payment Speed by Category</h3>
            <p className="text-xs text-slate-400 mt-0.5">Average payment delays relative to credit limits</p>
          </div>
          <div className="space-y-4 my-6 flex-1 flex flex-col justify-center">
            {delayBars.map((b, i) => {
              const rowColors = ['bg-emerald-600', 'bg-blue-600', 'bg-slate-500', 'bg-amber-500']
              const isBreaching = b['Avg Delay Days'] > 45
              return (
                <div key={b['MSME Category']} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold text-slate-600 dark:text-slate-300">
                    <span>{categoryLabels[b['MSME Category']] || b['MSME Category']}</span>
                    <span className={`font-bold ${isBreaching ? 'text-rose-600 dark:text-rose-400' : 'text-slate-900 dark:text-white'}`}>
                      {b['Avg Delay Days']} days
                    </span>
                  </div>
                  <div className="bg-slate-100 dark:bg-slate-800 rounded-full h-5 overflow-hidden relative shadow-inner">
                    <div 
                      className={`h-full rounded-full ${rowColors[i % 4]} flex items-center justify-end pr-2 transition-all duration-500`}
                      style={{ width: `${Math.max(b.pct, 2)}%` }} 
                    >
                      <span className="text-[9px] font-bold text-white leading-none z-10">{b['Avg Delay Days']}d</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
          <div className="text-[10px] text-slate-400 border-t border-slate-100 dark:border-slate-800/80 pt-3 text-center">
            Under the MSMED Act, compounding interest is calculated at 3x the RBI bank rate for delays above 45 days.
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
