import React from 'react'
import DonutChart from '../components/DonutChart'
import DataTable from '../components/DataTable'
import AiInsightBox from '../components/AiInsightBox'
import { CHART_COLORS } from '../theme'

export default function PoStatus({ data }) {
  const kpis   = data?.kpis   || {}
  const charts = data?.charts || {}
  const tables = data?.tables || []

  const ps = charts.po_status || { total: 0, segments: [] }
  const pv = charts.po_value  || { closed: {}, open: {} }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
          Purchase Order Status
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Analysis of open versus closed purchase order commitments and aging.
        </p>
      </div>

      <AiInsightBox section="postatus" kpis={kpis} />

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Unique POs', value: kpis.unique_pos, desc: 'Distinct purchase order sheets' },
          { label: 'Total Lines', value: kpis.total_lines, desc: 'Individual line items' },
          { label: 'Open Lines', value: kpis.open_lines, color: 'text-amber-600 dark:text-amber-400', desc: 'Awaiting delivery or closure' },
          { label: 'Closed Lines', value: kpis.closed_lines, color: 'text-green-600 dark:text-green-400', desc: 'Fully delivered/invoiced' },
          { label: 'Total PO Value', value: `₹${kpis.total_value_cr ?? 0} Cr`, desc: 'Aggregated PO value' },
          { label: 'Open PO Value', value: `₹${kpis.open_value_cr ?? 0} Cr`, color: 'text-amber-600 dark:text-amber-400', desc: 'Outstanding exposure' },
          { label: 'Open Value Ratio', value: `${kpis.pct_open_value ?? 0}%`, desc: 'Percentage of total value open' },
          { label: 'Top Vendor Open', value: `${kpis.top_vendor_open ?? 0} POs`, desc: 'Largest single vendor count' }
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

      {/* Charts Block */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">PO Status Distribution</h3>
            <p className="text-xs text-slate-400 mt-0.5">Ratio of open lines to closed lines</p>
          </div>
          <div className="flex items-center justify-center my-6">
            <DonutChart
              segments={(ps.segments || []).map(s => ({
                ...s, color: s.label === 'Open' ? CHART_COLORS.warning : CHART_COLORS.success,
              }))}
              centerText={(ps.total || 0).toLocaleString()}
              centerSub="Total Lines"
            />
          </div>
          <div className="space-y-2 text-xs border-t border-slate-100 dark:border-slate-800/80 pt-3">
            {(ps.segments || []).map(s => (
              <div key={s.label} className="flex justify-between items-center">
                <span className="flex items-center gap-2 text-slate-600 dark:text-slate-300 font-medium">
                  <span className={`w-2.5 h-2.5 rounded-full ${s.label === 'Open' ? 'bg-amber-500' : 'bg-green-600'}`} />
                  {s.label} Lines
                </span>
                <span className="font-semibold text-slate-950 dark:text-white">
                  {(s.value || 0).toLocaleString()} ({s.label === 'Open'
                    ? `${kpis.open_lines && kpis.total_lines ? ((kpis.open_lines / kpis.total_lines) * 100).toFixed(1) : 0}%`
                    : `${kpis.closed_lines && kpis.total_lines ? ((kpis.closed_lines / kpis.total_lines) * 100).toFixed(1) : 0}%`})
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">PO Value Exposure</h3>
            <p className="text-xs text-slate-400 mt-0.5">Financial value locked in closed versus open PO states</p>
          </div>
          <div className="space-y-5 my-6 flex-1 flex flex-col justify-center">
            <div>
              <div className="flex justify-between text-xs font-semibold mb-1 text-slate-600 dark:text-slate-300">
                <span>Closed Value</span>
                <span className="font-bold text-slate-900 dark:text-white">₹{pv.closed?.value_cr ?? 0} Cr</span>
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 rounded-full h-6 overflow-hidden relative shadow-inner">
                <div 
                  className="h-full rounded-full bg-gradient-to-r from-emerald-600 to-green-500 flex items-center justify-end pr-3 transition-all duration-500"
                  style={{ width: `${pv.closed?.pct ?? 0}%` }}
                >
                  <span className="text-[10px] font-bold text-white z-10">{pv.closed?.pct ?? 0}%</span>
                </div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs font-semibold mb-1 text-slate-600 dark:text-slate-300">
                <span>Open Value</span>
                <span className="font-bold text-slate-900 dark:text-white">₹{pv.open?.value_cr ?? 0} Cr</span>
              </div>
              <div className="bg-slate-100 dark:bg-slate-800 rounded-full h-6 overflow-hidden relative shadow-inner">
                <div 
                  className="h-full rounded-full bg-gradient-to-r from-amber-500 to-orange-500 flex items-center justify-end pr-3 transition-all duration-500"
                  style={{ width: `${Math.max(pv.open?.pct ?? 0, 1)}%` }}
                >
                  <span className="text-[10px] font-bold text-white z-10">{pv.open?.pct ?? 0}%</span>
                </div>
              </div>
            </div>
          </div>
          <div className="text-[10px] text-slate-400 border-t border-slate-100 dark:border-slate-800/80 pt-3 text-center">
            Open PO commitments represent potential incoming raw material and cash outflows.
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
