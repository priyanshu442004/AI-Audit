import React from 'react'
import DonutChart from '../components/DonutChart'
import DataTable from '../components/DataTable'
import AiInsightBox from '../components/AiInsightBox'
import { BAR_COLORS, CHART_COLORS } from '../theme'

export default function GateEntry({ data }) {
  const kpis   = data?.kpis   || {}
  const charts = data?.charts || {}
  const tables = data?.tables || []

  const pve  = charts.pass_vs_exception || { total: 0, segments: [] }
  const checks = charts.detailed_checks || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
          Gate Entry Integrity
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Chronological validation of transaction dates: Vendor Bill Date ≤ Gate Entry (GE) Date ≤ Goods Receipt (GRPO) Date.
        </p>
      </div>

      <AiInsightBox section="gateentry" kpis={kpis} />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Gate Entries', value: kpis.gate_entries, desc: 'Logged entry items' },
          { label: 'GRPO Documents', value: kpis.grpo_docs, desc: 'Goods receipts processed' },
          { label: 'Anomalies / Errors', value: kpis.exceptions, color: 'text-rose-600 dark:text-rose-400', desc: 'Out-of-order date entries' },
          { label: 'Compliance Index', value: `${kpis.integrity_pct ?? 0}%`, color: 'text-green-600 dark:text-green-400', desc: 'Overall date match score' }
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

      {/* Charts section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Audit Pass vs Exception Ratio</h3>
            <p className="text-xs text-slate-400 mt-0.5">Chronology verification outcome</p>
          </div>
          <div className="flex items-center justify-center my-6">
            <DonutChart
              segments={(pve.segments || []).map(s => ({
                ...s, color: s.label === 'Pass' ? CHART_COLORS.success : CHART_COLORS.risk,
              }))}
              centerText={`${kpis.integrity_pct ?? 0}%`}
              centerSub="Valid Chronology"
            />
          </div>
          <div className="space-y-2 text-xs border-t border-slate-100 dark:border-slate-800/80 pt-3">
            {(pve.segments || []).map(s => (
              <div key={s.label} className="flex justify-between items-center">
                <span className="flex items-center gap-2 text-slate-600 dark:text-slate-300 font-medium">
                  <span className={`w-2.5 h-2.5 rounded-full ${s.label === 'Pass' ? 'bg-green-600' : 'bg-rose-600'}`} />
                  {s.label === 'Pass' ? 'Correct Date Sequence' : 'Sequence Discrepancy (GE > GRPO)'}
                </span>
                <span className="font-semibold text-slate-950 dark:text-white">{(s.value || 0).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Chronological Control Checks</h3>
            <p className="text-xs text-slate-400 mt-0.5">Performance of specific chronological validation rules</p>
          </div>
          <div className="space-y-4 my-6 flex-1 flex flex-col justify-center">
            {checks.map(c => {
              const colors = {
                'Total': 'bg-slate-500', 
                'GE = GRPO (same)': 'bg-emerald-600',
                'GE < GRPO (normal)': 'bg-blue-600', 
                'GE > GRPO (error)': 'bg-rose-600',
                'Missing GRPO Date': 'bg-amber-600', 
                'Missing Bill Date': 'bg-slate-400',
              }
              const progressColor = colors[c.label] || 'bg-slate-400'
              return (
                <div key={c.label} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold text-slate-600 dark:text-slate-300">
                    <span>{c.label}</span>
                    <span className="font-bold text-slate-950 dark:text-white">{(c.value || 0).toLocaleString()}</span>
                  </div>
                  <div className="bg-slate-100 dark:bg-slate-800 rounded-full h-3 overflow-hidden">
                    <div 
                      className={`h-full rounded-full ${progressColor} transition-all duration-500`}
                      style={{ width: `${Math.max(c.pct, 1)}%` }} 
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Details Table */}
      <div className="space-y-6">
        {tables.map(t => <DataTable key={t.title} title={t.title} rows={t.rows} />)}
      </div>
    </div>
  )
}
