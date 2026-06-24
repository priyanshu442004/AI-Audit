import React from 'react'

const GLOSSARY = [
  { term: 'PO',          def: 'Purchase Order – buyer\'s formal request to supply goods or services.' },
  { term: 'GRPO',        def: 'Goods Receipt against PO – the receiving document booked when goods enter stock.' },
  { term: 'Gate Entry',  def: 'Security record at the factory gate when material physically arrives.' },
  { term: 'AP Invoice',  def: 'Accounts Payable Invoice – supplier\'s bill, posted in accounts.' },
  { term: 'GL',          def: 'General Ledger – chronological record of every accounting transaction.' },
  { term: 'GSTIN',       def: '15-character Goods & Services Tax Identification Number.' },
  { term: 'PAN',         def: '10-character Permanent Account Number (Income-Tax).' },
  { term: 'MSME',        def: 'Micro, Small and Medium Enterprise – per MSMED Act, 2006.' },
  { term: 'FIFO',        def: 'First-In-First-Out – matching the earliest invoice to the earliest payment.' },
  { term: '3-Way Match', def: 'Reconciliation of PO ↔ GRPO ↔ Invoice for Qty and Price.' },
  { term: 'Variance %',  def: '( Difference ÷ Original Value ) × 100 — expressed as a percentage.' },
  { term: 'Aging Bucket',def: 'Range of days an invoice has been pending past due date.' },
  { term: 'NIL Balance', def: 'A vendor for whom Total Credit equals Total Debit – fully paid.' },
  { term: 'Days Late',   def: 'Whole-number difference between Payment Date and Due Date (no decimals).' },
]

const REGULATIONS = [
  { title: 'MSMED Act, 2006, Sections 15 & 16', desc: '45-day payment rule and compound interest for Micro & Small Enterprises.' },
  { title: 'CGST Act, 2017', desc: 'Levy of tax, ITC eligibility, tax invoice format guidelines.' },
  { title: 'Income-Tax Act, 1961, Section 206AA', desc: 'Higher TDS rate where PAN is not furnished.' },
  { title: 'Companies Act, 2013, Section 143', desc: 'Auditor responsibility on internal financial controls.' },
  { title: 'CARO 2020, Clause 3(ii)(b)', desc: 'Auditor reporting on inventory and procurement controls.' },
  { title: 'RBI Master Direction on Bank Rate', desc: 'Reference rate for MSME penal interest (3 × Bank Rate).' },
]

export default function Appendix() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
          Appendix &amp; Technical Notes
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Methodology, definitions, compliance framework, and operational rules governing the P2P audit.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Legend */}
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-3">Risk Classification Framework</h3>
          <div className="space-y-3.5">
            {[
              { level: 'High Risk / Exception', bg: 'bg-rose-500/10 border-rose-500/20 text-rose-700 dark:text-rose-400', dot: 'bg-rose-500', desc: 'Critical exceptions needing immediate action (e.g., 45-day MSME breaches, invoice without gate entry).' },
              { level: 'Medium Risk / Warning', bg: 'bg-amber-500/10 border-amber-500/20 text-amber-700 dark:text-amber-400', dot: 'bg-amber-500', desc: 'Significant data gaps requiring process improvement (e.g., missing GSTIN/PAN, rate mismatches).' },
              { level: 'Operational Metric', bg: 'bg-blue-500/10 border-blue-500/20 text-blue-700 dark:text-blue-400', dot: 'bg-blue-500', desc: 'Trends to track over time (e.g., early payment by SME category, payment aging distribution).' },
            ].map(r => (
              <div key={r.level} className={`flex items-start gap-3 p-3.5 rounded-xl border ${r.bg}`}>
                <span className={`w-2.5 h-2.5 rounded-full ${r.dot} shrink-0 mt-1.5`} />
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider">{r.level}</span>
                  <p className="text-xs text-slate-600 dark:text-slate-300 font-medium mt-1 leading-relaxed">{r.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Data Sources */}
        <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-3">Audited Data Registers</h3>
          <p className="text-xs text-slate-400 mb-4">Input data feeds mapped directly from company records.</p>
          <div className="space-y-2 text-xs">
            {[
              { label: 'AP Credit Note', name: 'AP Credit Note-ITL.csv' },
              { label: 'AP Invoice Report', name: 'AP Invoice Report ITL.csv' },
              { label: 'BP Master', name: 'BP Master-ITL.csv' },
              { label: 'Gate Entry Report', name: 'Gate Entry Report-ITL.csv' },
              { label: 'General Ledger', name: 'General Ledger ITL.csv' },
              { label: 'GRPO Report', name: 'GRPO Report ITL.csv' },
              { label: 'Item Master', name: 'Item Master-ITL.csv' },
              { label: 'Purchase Order Report', name: 'Purchase Order Report-ITL.csv' },
              { label: 'Purchase Register', name: 'Purchase Register -ITL.csv' },
            ].map(d => (
              <div key={d.label} className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80 pb-2">
                <span className="font-semibold text-slate-600 dark:text-slate-400">{d.label}</span>
                <span className="font-mono text-[11px] text-slate-900 dark:text-white">{d.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Audit Methodology */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-6 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4">Audit Methodology &amp; Staging Rules</h3>
        <div className="space-y-6">
          {[
            { n: 1, title: 'Data Extraction', body: 'All nine mandatory ERP datasets (AP Credit Note, AP Invoice, BP Master, Gate Entry, GL, GRPO, Item Master, Purchase Order, Purchase Register) parsed in multi-part form arrays.' },
            { n: 2, title: 'Cleaning & Normalisation', bullets: [
              'Standardized date strings parsing into local ISO (dd-mm-yyyy) format.',
              'Vendor identifiers normalized for duplicate, PAN, and tax master mapping.',
              'GSTIN syntax checking against 15-character statutory standards.',
              'General Ledger hierarchical debit/credit balances parsed into single transactional lines.',
              'All calculated payment delay numbers rounded to whole integers.',
            ]},
            { n: 3, title: 'Staging & Pipeline Rules', bullets: [
              'Pricing variances calculated with 5% standard tolerance limits.',
              'Quantity receipt variance divided by within-tolerance (0-5%) and exceeding-tolerance (>5%).',
              'Physical materials and services separation via "SV" item code prefixes.',
              'FIFO chronological clearing logic matching outstanding invoices against payment logs.',
              'Statutory MSME calculations matching dates against the 45-day limit.',
            ]},
            { n: 4, title: 'Audit Scope & Limits', bullets: [
              'Based purely on historical snapshot files; does not represent live bank balances.',
              'Penalty interest calculated indicatively based on standard 3x RBI bank rate (approx. 27.00% p.a.).',
              'Categorization assumes standard company prefixes are consistently maintained by buyers.',
            ]}
          ].map(step => (
            <div key={step.n} className="flex gap-4">
              <span className="w-8 h-8 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs font-black flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
                0{step.n}
              </span>
              <div>
                <div className="text-xs font-bold text-slate-900 dark:text-white mb-1">{step.title}</div>
                {step.body && <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed font-medium">{step.body}</p>}
                {step.bullets && (
                  <ul className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed space-y-1 mt-1 font-medium list-none">
                    {step.bullets.map(b => (
                      <li key={b} className="flex gap-2">
                        <span className="text-blue-500 font-bold">•</span>
                        <span>{b}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Glossary */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 shadow-sm overflow-hidden">
        <div className="px-6 py-4.5 border-b border-slate-100 dark:border-slate-800/80">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">Glossary of Procurement Terms</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 dark:bg-slate-800/40 border-b border-slate-100 dark:border-slate-800/80">
                <th className="px-6 py-3 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider w-40">Acronym / Term</th>
                <th className="px-6 py-3 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Operational Definition</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {GLOSSARY.map(g => (
                <tr key={g.term} className="hover:bg-slate-50/40 dark:hover:bg-slate-800/20 transition-colors duration-150">
                  <td className="px-6 py-3 text-xs font-bold text-slate-900 dark:text-white">{g.term}</td>
                  <td className="px-6 py-3 text-xs text-slate-600 dark:text-slate-400 font-medium leading-relaxed">{g.def}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Regulations */}
      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4">Statutory &amp; Regulatory Context</h3>
        <div className="space-y-3">
          {REGULATIONS.map(r => (
            <div key={r.title} className="flex gap-3 p-3 bg-slate-50/50 dark:bg-slate-800/20 border border-slate-100 dark:border-slate-800/60 rounded-xl">
              <span className="text-blue-500 font-bold text-xs mt-0.5 shrink-0">•</span>
              <div>
                <span className="text-xs font-bold text-slate-900 dark:text-white">{r.title}</span>
                <p className="text-xs text-slate-400 mt-0.5 font-medium">{r.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-5 shadow-sm text-xs flex justify-between items-center text-slate-500 dark:text-slate-400 font-medium">
        <span>Report Staged &amp; Generated for current snapshot period.</span>
        <span>FY 2025-26</span>
      </div>
    </div>
  )
}
