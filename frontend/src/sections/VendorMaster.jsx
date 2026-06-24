import React from 'react'
import DonutChart from '../components/DonutChart'
import DataTable from '../components/DataTable'
import AiInsightBox from '../components/AiInsightBox'
import { BAR_COLORS } from '../theme'

export default function VendorMaster({ data }) {
  const kpis   = data?.kpis   || {}
  const charts = data?.charts || {}
  const tables = data?.tables || []

  const exc   = charts.exceptions_donut || { total: 0, segments: [] }
  const msmeBars = charts.msme_bars || []
  const msmeColors = ['bg-emerald-600', 'bg-blue-600', 'bg-amber-500', 'bg-slate-500']

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
          Vendor Master Validation
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Audits Business Partner (BP) master record consistency, focusing on duplicates, compliance tracking, and tax details.
        </p>
      </div>

      <AiInsightBox section="vendormaster" kpis={kpis} />

      {/* KPIs Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Audited Vendor Base', value: kpis.total_vendors, desc: 'BP Master record registry count' },
          { label: 'Duplicate Accounts', value: kpis.duplicates, color: 'text-rose-600 dark:text-rose-400', desc: 'Potential duplicate PAN/Name' },
          { label: 'Missing GSTIN Tax IDs', value: kpis.missing_gstin, color: 'text-amber-600 dark:text-amber-500', desc: 'Vulnerability in tax reporting' },
          { label: 'Missing PAN Records', value: kpis.missing_pan, color: 'text-amber-600 dark:text-amber-500', desc: 'Vulnerability in income tax filings' }
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

      {/* Details layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Master Data Exceptions</h3>
            <p className="text-xs text-slate-400 mt-0.5">Classification of database validation exceptions</p>
          </div>
          <div className="flex items-center justify-center my-6">
            <DonutChart
              segments={exc.segments || []}
              centerText={(exc.total || 0).toLocaleString()}
              centerSub="Exceptions"
            />
          </div>
          <div className="space-y-2 text-xs border-t border-slate-100 dark:border-slate-800/80 pt-3">
            {(exc.segments || []).map(s => (
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
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">MSME Registry Status</h3>
            <p className="text-xs text-slate-400 mt-0.5">Category classification of registered Business Partners</p>
          </div>
          <div className="space-y-4 my-6 flex-1 flex flex-col justify-center">
            {msmeBars.map((b, i) => (
              <div key={b.label} className="space-y-1">
                <div className="flex justify-between text-xs font-semibold text-slate-600 dark:text-slate-300">
                  <span>{b.label}</span>
                  <span className="font-bold text-slate-950 dark:text-white">{(b.value || 0).toLocaleString()} ({b.pct}%)</span>
                </div>
                <div className="bg-slate-100 dark:bg-slate-800 rounded-full h-5 overflow-hidden relative shadow-inner">
                  <div 
                    className={`h-full rounded-full ${msmeColors[i % 4]} flex items-center justify-end pr-2 transition-all duration-500`}
                    style={{ width: `${Math.max(b.pct, 1)}%` }} 
                  >
                    <span className="text-[9px] font-bold text-white leading-none z-10">{(b.value || 0).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="text-[10px] text-slate-400 border-t border-slate-100 dark:border-slate-800/80 pt-3 text-center">
            Accurate classification in BP Master is crucial for 45-day statutory compliance reports.
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
