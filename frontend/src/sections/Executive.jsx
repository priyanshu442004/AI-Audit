import React from 'react'
import DonutChart from '../components/DonutChart'
import BarRow from '../components/BarRow'
import RiskTable from '../components/RiskTable'
import AiInsightBox from '../components/AiInsightBox'
import { BAR_COLORS, CHART_COLORS } from '../theme'

function Kpi({ label, value, sub, color, desc }) {
  return (
    <div className="group relative overflow-hidden rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm hover:shadow-md transition-all duration-200">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">{label}</span>
      </div>
      <div className={`text-2xl font-black tracking-tight ${color || 'text-slate-900 dark:text-white'}`}>
        {value ?? '—'}
      </div>
      {sub && <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 font-medium">{sub}</div>}
      {desc && <div className="text-[10px] text-slate-400 mt-0.5">{desc}</div>}
    </div>
  )
}

export default function Executive({ data }) {
  const kpis   = data?.kpis   || {}
  const charts = data?.charts || {}
  const risks  = data?.top_risks || []

  const poChart   = charts.po_status    || { total: 0, segments: [] }
  const twChart   = charts.three_way    || { total: 0, segments: [] }
  const agingBars = charts.payment_aging || []

  const poSegs = poChart.segments || []
  const twSegs = (twChart.segments || []).slice(0, 5)

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
            Executive Summary
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            High-level audit findings, financial risk metrics, and key performance graphs.
          </p>
        </div>
      </div>

      {/* AI Insights narrative */}
      <AiInsightBox section="executive" kpis={kpis} topRisks={risks} />

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Kpi 
          label="Purchase Order Value" 
          value={`₹${kpis.po_value_cr ?? 0} Cr`} 
          sub={`Open PO: ₹${kpis.open_value_cr ?? 0} Cr`} 
          desc="Total PO commitment analyzed" 
        />
        <Kpi 
          label="AP Outstanding" 
          value={`₹${kpis.ap_outstanding_cr ?? 0} Cr`} 
          sub={`Total Invoices: ${(kpis.ap_invoices ?? 0).toLocaleString()}`} 
          color="text-sky-600 dark:text-sky-400"
          desc="Open trade payables" 
        />
        <Kpi 
          label="MSME Breaches" 
          value={kpis.msme_breaches ?? 0} 
          sub="Violations of 45-Day Payment Rule" 
          color="text-rose-600 dark:text-rose-400"
          desc="Strict regulatory compliance check" 
        />
        <Kpi 
          label="Potential Recoveries" 
          value={`₹${kpis.savings_l ?? 0} L`} 
          sub="Price variance leakage identified" 
          color="text-emerald-600 dark:text-emerald-400"
          desc="Immediate savings opportunity" 
        />
        <Kpi 
          label="Overdue AP Invoices" 
          value={kpis.late_overdue ?? 0} 
          sub="Payments past due terms" 
          color="text-amber-600 dark:text-amber-500"
          desc="Aging ledger exceptions" 
        />
        <Kpi 
          label="Quantity Deviations" 
          value={kpis.qty_above_5pct ?? 0} 
          sub="Over 5% tolerance threshold" 
          color="text-rose-600 dark:text-rose-400"
          desc="GRPO vs PO quantity checks" 
        />
        <Kpi 
          label="Three-Way Matches" 
          value={kpis.threeway_perfect ?? 0} 
          sub={`Perfect Match Rate: ${kpis.threeway_pct ?? 0}%`} 
          desc="Fully verified document lineage" 
        />
        <Kpi 
          label="Master Data Flags" 
          value={kpis.vendor_issues ?? 0} 
          sub={`${kpis.duplicates ?? 0} Dup + ${kpis.missing_gstin ?? 0} Missing Tax IDs`} 
          color="text-amber-600 dark:text-amber-500"
          desc="BP Registry anomalies" 
        />
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* PO Status */}
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">PO Lifecycle Profile</h3>
            <p className="text-xs text-slate-400 mt-0.5">Distribution of PO line items by status</p>
          </div>
          <div className="flex items-center justify-center my-6">
            <DonutChart
              segments={poSegs.map(s => ({
                ...s,
                color: s.label === 'Open' ? CHART_COLORS.warning : CHART_COLORS.success
              }))}
              centerText={(poChart.total || 0).toLocaleString()}
              centerSub="Total Line Items"
            />
          </div>
          <div className="space-y-2 text-xs border-t border-slate-100 dark:border-slate-800/80 pt-3">
            {poSegs.map(s => {
              const col = s.label === 'Open' ? 'bg-amber-500' : 'bg-green-600'
              return (
                <div key={s.label} className="flex items-center justify-between">
                  <span className="flex items-center gap-2 text-slate-600 dark:text-slate-300 font-medium">
                    <span className={`w-2.5 h-2.5 rounded-full ${col}`} />
                    {s.label}
                  </span>
                  <span className="font-semibold text-slate-950 dark:text-white">{(s.value || 0).toLocaleString()}</span>
                </div>
              )
            })}
          </div>
        </div>

        {/* 3-Way matching */}
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">3-Way Match Verification</h3>
            <p className="text-xs text-slate-400 mt-0.5">Comparison of Purchase Orders, GRPO, and Invoices</p>
          </div>
          <div className="flex items-center justify-center my-6">
            <DonutChart
              segments={twSegs}
              centerText={(twChart.total || 0).toLocaleString()}
              centerSub="Audited Invoices"
            />
          </div>
          <div className="space-y-2 text-xs border-t border-slate-100 dark:border-slate-800/80 pt-3">
            {twSegs.map(s => (
              <div key={s.label} className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-slate-600 dark:text-slate-300 font-medium truncate max-w-[200px]">
                  <span className="w-2.5 h-2.5 rounded-md" style={{ background: s.color }} />
                  {s.label}
                </span>
                <span className="font-semibold text-slate-950 dark:text-white">{(s.value || 0).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Payment aging */}
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Accounts Payable Aging</h3>
            <p className="text-xs text-slate-400 mt-0.5">Distribution of outstanding payables by due date bracket</p>
          </div>
          <div className="space-y-3.5 my-6 flex-1 flex flex-col justify-center">
            {agingBars.map(b => (
              <BarRow key={b.label} label={b.label} value={b.value} pct={b.pct} color={BAR_COLORS.primary} />
            ))}
          </div>
          <div className="text-[10px] text-slate-400 border-t border-slate-100 dark:border-slate-800/80 pt-3 text-center">
            Total AP value matches the verified Purchase Register.
          </div>
        </div>
      </div>

      {/* Risks Table */}
      <RiskTable risks={risks} />
    </div>
  )
}
