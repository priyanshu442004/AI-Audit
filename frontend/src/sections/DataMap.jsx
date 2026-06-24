import React from 'react'

const SOURCE_FILES = [
  { file: 'AP Credit Note.csv',     purpose: 'AP Credit Notes booked',    records: '1,250',  keys: 'DocEntry, CardCode, ItemCode, Quantity, Price' },
  { file: 'AP Invoice Report.csv',  purpose: 'AP invoices booked (purchase register)', records: '9,997',  keys: 'DocEntry, CardCode, ItemCode, Quantity, Price, DocDate' },
  { file: 'BP Master.csv',          purpose: 'Business Partner registry', records: '1,498',  keys: 'CardCode, CardName, MSMEStatus, GSTRegNum' },
  { file: 'Gate Entry Report.csv',  purpose: 'Security vehicle gate logs', records: '2,323',  keys: 'GateEntryNo, InvoiceNo, InvoiceDate, LinkedGRPO' },
  { file: 'General Ledger.csv',     purpose: 'Financial ledger ledger postings', records: '4,211',  keys: 'CardCode, Debit, Credit, PostingDate' },
  { file: 'GRPO Report.csv',        purpose: 'Goods Receipt PO receipts',  records: '12,384', keys: 'DocEntry, BaseEntry, CardCode, ItemCode, Quantity' },
  { file: 'Item Master.csv',        purpose: 'Material registry',         records: '6,200',  keys: 'ItemCode, ItemName, ItemGroup' },
  { file: 'Purchase Order Report.csv', purpose: 'Authorized PO commitments', records: '7,250',  keys: 'DocEntry, CardCode, ItemCode, Quantity, Price, OpenQty' },
  { file: 'Purchase Register.csv',  purpose: 'Purchase booking registry', records: '9,997',  keys: 'InvoiceNo, Date, VendorCode, LineTotal, TaxCode' },
]

const JOINS = [
  { id: 'J1', a: 'Purchase Order', b: 'GRPO Report', key: 'PO Line (DocEntry) = GRPO Base (BaseEntry)' },
  { id: 'J2', a: 'GRPO Report', b: 'Gate Entry Report', key: 'GRPO No (DocEntry) = Gate Entry Linked GRPO' },
  { id: 'J3', a: 'GRPO Report', b: 'AP Invoice Report', key: 'Invoice Line (DocEntry) = GRPO Line' },
  { id: 'J4', a: 'AP Invoice Report', b: 'General Ledger', key: 'InvoiceNo + CardCode + DocDate' },
  { id: 'J5', a: 'All Transactions', b: 'BP Master', key: 'Vendor Code (CardCode)' },
  { id: 'J6', a: 'All Transactions', b: 'Item Master', key: 'Item Number (ItemCode)' },
]

const AUDIT_RULES = [
  { id: 'A', title: 'PO Status Lifecycle', desc: 'OPEN vs CLOSED status validation against physical delivery balances.' },
  { id: 'B', title: 'Chronology Verification', desc: 'Ensures transaction sequence integrity: Invoice Date ≤ Gate Entry Date ≤ GRPO Date ≤ AP Posting Date.' },
  { id: 'C', title: 'Quantity Variance', desc: 'Validates received (GRPO) vs ordered (PO) quantities against 5% tolerances.' },
  { id: 'D', title: 'Price Variance', desc: 'Calculates spread difference between maximum and minimum unit prices for identical items.' },
  { id: 'E', title: 'Savings Potential', desc: 'Quantifies leakage: (Average Price - Minimum Price) multiplied by cumulative purchased volume.' },
  { id: 'F', title: 'GL Vendor Balance Reconciliation', desc: 'Matches AP ledger balances against sub-ledger open invoices to flag net liabilities.' },
  { id: 'G', title: 'Payment Aging Profile', desc: 'Buckets trade payables by age of due date (0-30, 31-60, 61-90, 90+ days).' },
  { id: 'H', title: 'MSME Breach Assessment', desc: 'Flags payments exceeding the statutory 45-day MSMED Act limit to calculate penalty interest.' },
  { id: 'I', title: 'Master Data Consistency', desc: 'Flags incomplete records, missing GSTINs/PANs, and duplicate registry files.' },
  { id: 'J', title: 'Three-Way Match Check', desc: 'Simultaneous cross-validation of PO Unit Price, GRPO Quantities, and AP Invoice billing.' },
]

const PROCESS_FLOW = [
  { n: 1, color: 'from-blue-600 to-indigo-600', title: 'Purchase Order', desc: 'Creation of purchase commitment and standard terms' },
  { n: 2, color: 'from-indigo-600 to-violet-600', title: 'Gate Entry', desc: 'Security vehicle check and physical manifest recording' },
  { n: 3, color: 'from-violet-600 to-fuchsia-600', title: 'Goods Receipt (GRPO)', desc: 'Store room verification, physical receipt booking, and stock updates' },
  { n: 4, color: 'from-fuchsia-600 to-pink-600', title: 'AP Invoice', desc: 'Booking of supplier invoice against physical receipts' },
  { n: 5, color: 'from-pink-600 to-rose-600', title: 'General Ledger Posting', desc: 'Accrual posting, ledger balancing, and payment release' },
  { n: 6, color: 'from-rose-600 to-emerald-600', title: '3-Way Reconciliation', desc: 'Continuous compliance checks and variance reviews' },
]

export default function DataMap() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
          Audit Model, Joins &amp; Rules
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Detailed technical reference of files mapped, relational joins, business flow stages, and rule configurations.
        </p>
      </div>

      {/* Source Files Register */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm overflow-hidden">
        <div className="px-6 py-4.5 border-b border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">Audit Source Register</h3>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400">
            9 Mandatory Schemas
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 dark:bg-slate-800/40 border-b border-slate-100 dark:border-slate-800/80">
                <th className="px-6 py-3 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">File Name</th>
                <th className="px-6 py-3 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Mapping Purpose</th>
                <th className="px-6 py-3 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider text-right">Row Count</th>
                <th className="px-6 py-3 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider hidden lg:table-cell">Key Columns Reference</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {SOURCE_FILES.map(r => (
                <tr key={r.file} className="hover:bg-slate-50/40 dark:hover:bg-slate-800/20 transition-colors duration-150">
                  <td className="px-6 py-3.5 text-xs font-mono font-bold text-slate-900 dark:text-white">{r.file}</td>
                  <td className="px-6 py-3.5 text-xs text-slate-600 dark:text-slate-400">{r.purpose}</td>
                  <td className="px-6 py-3.5 text-right text-xs font-bold text-slate-900 dark:text-white font-mono">{r.records}</td>
                  <td className="px-6 py-3.5 text-xs font-mono text-slate-500 dark:text-slate-500 hidden lg:table-cell text-left">{r.keys}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Relational model / Process */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* P2P Process Flow */}
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-3">Procure-to-Pay (P2P) Pipeline Flow</h3>
          <p className="text-xs text-slate-400 mb-4">Linear transaction lifecycle audited by the pipeline engine.</p>
          <div className="space-y-3">
            {PROCESS_FLOW.map(s => (
              <div key={s.n} className="flex items-center gap-4 p-3 bg-slate-50/50 dark:bg-slate-800/20 border border-slate-100 dark:border-slate-800/60 rounded-xl">
                <span className={`w-8 h-8 rounded-xl bg-gradient-to-br ${s.color} text-white text-xs font-black flex items-center justify-center flex-shrink-0 shadow-sm`}>
                  {s.n.toString().padStart(2, '0')}
                </span>
                <div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white">{s.title}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">{s.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Joins mapping */}
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm overflow-hidden flex flex-col justify-between">
          <div>
            <div className="px-6 py-4.5 border-b border-slate-100 dark:border-slate-800/80">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Pipeline Relation Joins</h3>
              <p className="text-xs text-slate-400 mt-0.5">Primary and foreign key mappings used during data staging</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50/50 dark:bg-slate-800/40 border-b border-slate-100 dark:border-slate-800/80">
                    <th className="px-6 py-2.5 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider w-12">ID</th>
                    <th className="px-6 py-2.5 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Source Table</th>
                    <th className="px-6 py-2.5 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Target Table</th>
                    <th className="px-6 py-2.5 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider hidden md:table-cell">Relation Key</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {JOINS.map(j => (
                    <tr key={j.id} className="hover:bg-slate-50/40 dark:hover:bg-slate-800/20 transition-colors duration-150">
                      <td className="px-6 py-3 text-xs font-mono font-bold text-blue-600 dark:text-blue-400">{j.id}</td>
                      <td className="px-6 py-3 text-xs font-semibold text-slate-900 dark:text-white">{j.a}</td>
                      <td className="px-6 py-3 text-xs text-slate-600 dark:text-slate-400">{j.b}</td>
                      <td className="px-6 py-3 text-xs font-mono text-slate-500 dark:text-slate-500 hidden md:table-cell">{j.key}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="text-[10px] text-slate-400 p-4 border-t border-slate-100 dark:border-slate-800/80 text-center">
            Mismatches or orphans during staging are redirected to the Exceptions bucket.
          </div>
        </div>
      </div>

      {/* Audit Rules */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-1">Standard Audit Logic Reference</h3>
        <p className="text-xs text-slate-400 mb-4">Detailed definitions of programmatic rules applied by the audit engine.</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {AUDIT_RULES.map(r => (
            <div key={r.id} className="flex items-start gap-3 p-3 bg-slate-50/50 dark:bg-slate-800/20 border border-slate-100 dark:border-slate-800/60 rounded-xl">
              <span className="w-6 h-6 rounded-lg bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-300 text-xs font-black flex items-center justify-center flex-shrink-0">
                {r.id}
              </span>
              <div>
                <div className="text-xs font-bold text-slate-900 dark:text-white">{r.title}</div>
                <div className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">{r.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
