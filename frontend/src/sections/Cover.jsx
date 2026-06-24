import React from 'react'
import KpiCard from '../components/KpiCard'

const NAV_ITEMS = [
  { n: 1, c: 'blue', label: 'Cover & P2P Overview' },
  { n: 2, c: 'indigo', label: 'Executive Dashboard & Risk Analysis' },
  { n: 3, c: 'slate', label: 'Data Map & Source Lineage' },
  { n: 4, c: 'slate', label: 'PO Status & Lifecycle Check' },
  { n: 5, c: 'slate', label: 'Gate Entry Date Integrity' },
  { n: 6, c: 'slate', label: 'Quantity Variance Tolerance' },
  { n: 7, c: 'slate', label: 'Price Variance & Leakage' },
  { n: 8, c: 'slate', label: 'GL Balance Reconciliation' },
  { n: 9, c: 'slate', label: 'Aging & Working Capital' },
  { n: 10, c: 'slate', label: 'MSME Regulatory Compliance' },
  { n: 11, c: 'slate', label: 'Vendor Master Records Audit' },
  { n: 12, c: 'slate', label: 'GRPO Exception Mapping' },
  { n: 13, c: 'slate', label: 'Three-Way Match Verification' },
  { n: 14, c: 'slate', label: 'Appendix & Audit Glossary' }
]

export default function Cover({ data }) {
  const kpis = data?.kpis || {}

  const cards = [
    { label: 'Purchase Orders', value: (kpis.purchase_orders ?? 0).toLocaleString(), icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2', color: 'from-blue-500/10 to-indigo-500/10 text-blue-600 dark:text-blue-400' },
    { label: 'GRPO Documents', value: (kpis.grpo_documents ?? 0).toLocaleString(), icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', color: 'from-purple-500/10 to-pink-500/10 text-purple-600 dark:text-purple-400' },
    { label: 'Gate Entries', value: (kpis.gate_entries ?? 0).toLocaleString(), icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16', color: 'from-amber-500/10 to-orange-500/10 text-amber-600 dark:text-amber-400' },
    { label: 'AP Invoices', value: (kpis.ap_invoices ?? 0).toLocaleString(), icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2', color: 'from-emerald-500/10 to-teal-500/10 text-emerald-600 dark:text-emerald-400' },
    { label: 'GL Transactions', value: (kpis.gl_transactions ?? 0).toLocaleString(), icon: 'M7 12l3-3 3 3 4-4', color: 'from-sky-500/10 to-blue-500/10 text-sky-600 dark:text-sky-400' },
    { label: 'Vendor Registry', value: (kpis.vendor_records ?? 0).toLocaleString(), icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7', color: 'from-indigo-500/10 to-violet-500/10 text-indigo-600 dark:text-indigo-400' },
    { label: 'Active Vendors', value: (kpis.active_vendors ?? 0).toLocaleString(), icon: 'M15 7a3 3 0 11-6 0 3 3 0 016 0z', color: 'from-rose-500/10 to-red-500/10 text-rose-600 dark:text-rose-400' },
    { label: 'Report Sheets', value: '14 Modules', icon: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6z', color: 'from-teal-500/10 to-cyan-500/10 text-teal-600 dark:text-teal-400' }
  ]

  return (
    <div className="space-y-8">
      {/* Welcome Hero Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-slate-900 text-white p-8 sm:p-12 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-80 h-80 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full blur-3xl opacity-35"></div>
        <div className="absolute bottom-0 left-0 -mb-16 -ml-16 w-80 h-80 bg-gradient-to-tr from-emerald-600 to-teal-600 rounded-full blur-3xl opacity-20"></div>
        
        <div className="relative z-10 max-w-3xl space-y-4">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-300 ring-1 ring-inset ring-blue-500/30">
            System Status: Audit Complete
          </span>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight">
            IKIO Technologies Limited
          </h1>
          <p className="text-base sm:text-lg text-slate-300 font-medium">
            Procure-to-Pay (P2P) Comprehensive Compliance &amp; Transaction Integrity Audit
          </p>
          <div className="pt-4 flex flex-wrap gap-4 text-xs text-slate-400">
            <div>Audit Cycle: <span className="text-white font-medium">FY 2026-27</span></div>
            <div className="hidden sm:block">•</div>
            <div>Classification: <span className="text-white font-medium">Confidential Executive Document</span></div>
          </div>
        </div>
      </div>

      {/* Grid Statistics */}
      <div>
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Database Source Counts</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {cards.map(c => (
            <div key={c.label} className="group relative overflow-hidden rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-6 shadow-sm hover:shadow-md transition-all duration-200">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  {c.label}
                </span>
                <div className={`p-2 rounded-lg bg-gradient-to-br ${c.color}`}>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d={c.icon} />
                  </svg>
                </div>
              </div>
              <div className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                {c.value}
              </div>
              <div className="mt-1 text-xs text-slate-400">
                Verified records processed
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Navigation Map */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-6 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4">Audit Module Map</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {NAV_ITEMS.map(item => (
            <div key={item.n} className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800/30 hover:border-slate-300 dark:hover:border-slate-700 transition-all duration-150">
              <span className={`w-8 h-8 rounded-lg bg-slate-900 dark:bg-slate-800 text-white text-xs font-bold flex items-center justify-center flex-shrink-0 shadow-sm border border-slate-700`}>
                {item.n.toString().padStart(2, '0')}
              </span>
              <div className="min-w-0">
                <span className="text-xs font-medium text-slate-800 dark:text-slate-200 block truncate">{item.label}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
