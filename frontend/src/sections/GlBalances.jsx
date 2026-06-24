import React from 'react'
import DonutChart from '../components/DonutChart'
import DataTable from '../components/DataTable'
import AiInsightBox from '../components/AiInsightBox'

export default function GlBalances({ data }) {
  const kpis   = data?.kpis   || {}
  const charts = data?.charts || {}
  const tables = data?.tables || []

  const ps  = charts.payment_status || { total: 0, segments: [] }
  const ab  = charts.amount_bars    || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
          General Ledger Vendor Balances
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Detailed check of accounts payable ledger, outstanding commitments, advances paid, and net accounting liabilities.
        </p>
      </div>

      <AiInsightBox section="glbalances" kpis={kpis} />

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Outstanding Accounts', value: kpis.outstanding_cnt, color: 'text-rose-600 dark:text-rose-400', desc: 'Accounts with open balances' },
          { label: 'Settled Accounts', value: kpis.fully_paid_cnt, color: 'text-green-600 dark:text-green-400', desc: 'Fully matching paid accounts' },
          { label: 'Advances & Debits', value: kpis.advance_cnt, color: 'text-amber-600 dark:text-amber-500', desc: 'Debit balances (potential risk)' },
          { label: 'Total Audited Vendors', value: kpis.total_vendors, desc: 'BP accounts with transactions' }
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

      {/* Grid of chart and bars */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Vendor Accounting Status</h3>
            <p className="text-xs text-slate-400 mt-0.5">Distribution of vendor accounts by status category</p>
          </div>
          <div className="flex items-center justify-center my-6">
            <DonutChart
              segments={ps.segments || []}
              centerText={(ps.total || 0).toLocaleString()}
              centerSub="Total Vendors"
            />
          </div>
          <div className="space-y-2 text-xs border-t border-slate-100 dark:border-slate-800/80 pt-3">
            {(ps.segments || []).map(s => (
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
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Outstanding Balances</h3>
            <p className="text-xs text-slate-400 mt-0.5">Aggregated financial value by ledger status</p>
          </div>
          <div className="space-y-4 my-6 flex-1 flex flex-col justify-center">
            {ab.map(b => (
              <div key={b.label} className="space-y-1">
                <div className="flex justify-between text-xs font-semibold text-slate-600 dark:text-slate-300">
                  <span>{b.label} Value</span>
                  <span className="font-bold text-slate-950 dark:text-white">₹{b.value_cr} Cr</span>
                </div>
                <div className="bg-slate-100 dark:bg-slate-800 rounded-full h-4 overflow-hidden relative shadow-inner">
                  <div 
                    className={`h-full rounded-full ${b.label === 'Outstanding' ? 'bg-rose-600' : 'bg-amber-500'} transition-all duration-500`}
                    style={{ width: `${Math.max(b.pct, 1)}%` }} 
                  />
                </div>
              </div>
            ))}
            <div className="pt-4 border-t border-slate-100 dark:border-slate-800/80 mt-2">
              <div className="flex justify-between items-center">
                <div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white">Net Financial Liability</div>
                  <div className="text-[10px] text-slate-400">Total payables offset by debit advances</div>
                </div>
                <div className="text-lg font-black text-rose-600 dark:text-rose-400">
                  ₹{kpis.net_liability_cr} Cr
                </div>
              </div>
            </div>
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
