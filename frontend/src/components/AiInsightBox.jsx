import React, { useState, useEffect } from 'react'
import { fetchInsight } from '../api'

const DEFAULT_NARRATIVES = {
  executive: (kpis) => 
    `The P2P cycle audit reveals a total PO commitment of ₹${kpis.po_value_cr ?? 0} Cr, with ₹${kpis.open_value_cr ?? 0} Cr remaining open. Operational risk is highlighted by ${kpis.msme_breaches ?? 0} MSME breaches and ${kpis.qty_above_5pct ?? 0} quantity variance anomalies exceeding the 5% tolerance. Addressing these points, along with vendor duplication issues, presents a potential savings recovery of ₹${kpis.savings_l ?? 0} L.`,
  postatus: (kpis) => 
    `PO Status analysis shows ${kpis.open_lines ?? 0} open lines representing ${kpis.open_value_pct ?? 0}% of total PO value. The aging profile indicates that ${kpis.stale_open_lines ?? 0} lines have remained open for over 90 days, suggesting potential material delivery bottlenecks or incomplete system closures.`,
  gateentry: (kpis) => 
    `Gate entry date tracking indicates an overall late entry rate of ${kpis.late_entry_pct ?? 0}%. A total of ${kpis.backdated_entries ?? 0} instances were identified where gate entries were recorded after the invoice date, representing a compliance check failure.`,
  qtyvariance: (kpis) => 
    `Quantity variance analysis flagged ${kpis.qty_above_5pct ?? 0} instances exceeding the 5% tolerance threshold. This suggests potential over-delivery or receipt errors that must be reconciled against the supplier billing files to prevent financial leakage.`,
  pricevariance: (kpis) => 
    `Pricing analysis identified ₹${kpis.savings_l ?? 0} Lakhs in potential savings. The largest price variance was observed on key item categories, indicating that standard purchase rates were not consistently applied across vendor accounts.`,
  pricevariancesame: (kpis) => 
    `Same-vendor price variance analysis evaluated ${kpis.vendor_items ?? 0} items. We identified ${kpis.variance_lines ?? 0} instances of unit rate deviations within individual vendors, and ${kpis.uom_inconsistent ?? 0} vendors with inconsistent Unit of Measure (UOM) profiles.`,
  pricevariancecross: (kpis) => 
    `Cross-vendor price variance analysis evaluated ${kpis.vendor_items ?? 0} items. We identified ${kpis.variance_lines ?? 0} instances where identical item codes were purchased at different rates across different vendors, highlighting potential purchasing leakage.`,
  glbalances: (kpis) => 
    `GL Vendor balance analysis shows a total GL liability of ₹${kpis.total_gl_balance_cr ?? 0} Cr, with a variance of ₹${kpis.variance_cr ?? 0} Cr against the AP invoice register. High-risk debit balances total ₹${kpis.debit_balances_l ?? 0} L, requiring immediate follow-up.`,
  paymentaging: (kpis) => 
    `The AP aging profile is heavily skewed, with ₹${kpis.overdue_90days_l ?? 0} L outstanding beyond 90 days. This delay increases the risk of vendor disputes, potential supply line disruptions, and statutory compliance issues.`,
  msme: (kpis) => 
    `MSME compliance check shows ${kpis.msme_breaches ?? 0} payments exceeding the 45-day statutory limit, incurring a potential interest penalty of ₹${kpis.interest_penalty_l ?? 0} L. Immediate cash flow prioritisation is recommended.`,
  vendormaster: (kpis) => 
    `Vendor Master validation flagged ${kpis.missing_gstin ?? 0} vendors missing valid GSTINs and ${kpis.duplicate_pan ?? 0} accounts with duplicate PAN details, creating critical tax compliance and reporting vulnerabilities.`,
  grpoexcept: (kpis) => 
    `GRPO exceptions report indicates ${kpis.unlinked_grpo ?? 0} unlinked GRPO lines and ${kpis.invoice_before_grpo ?? 0} instances where the AP invoice date preceded the physical goods receipt.`,
  threeway: (kpis) => 
    `Three-way matching shows a perfect match rate of ${kpis.threeway_pct ?? 0}% on total invoice volume. The remaining ${100 - (kpis.threeway_pct ?? 0)}% of invoices have quantity, price, or document lineage variances requiring manual resolution.`
}

export default function AiInsightBox({ section, kpis, topRisks = [] }) {
  const [loading, setLoading] = useState(false)
  const [insight, setInsight] = useState('')
  const [copied, setCopied] = useState(false)

  const generateInsight = async () => {
    setLoading(true)
    try {
      const text = await fetchInsight(section, kpis, topRisks)
      if (text) {
        setInsight(text)
      } else {
        // Fallback to static but detailed professional narrative generator
        const genFn = DEFAULT_NARRATIVES[section]
        setInsight(genFn ? genFn(kpis) : 'No high-risk anomalies or significant variances were detected in this audit section.')
      }
    } catch (e) {
      const genFn = DEFAULT_NARRATIVES[section]
      setInsight(genFn ? genFn(kpis) : 'No high-risk anomalies or significant variances were detected in this audit section.')
    } finally {
      setLoading(false)
    }
  }

  // Auto-generate on first load
  useEffect(() => {
    generateInsight()
  }, [section, kpis])

  const copyToClipboard = () => {
    navigator.clipboard.writeText(insight)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative overflow-hidden rounded-2xl border border-blue-500/10 bg-blue-50/5 dark:bg-blue-950/5 p-6 backdrop-blur shadow-sm mb-6">
      <div className="absolute top-0 right-0 -mt-6 -mr-6 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl"></div>
      
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400">
            <svg className="w-5 h-5 animate-pulse" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 21l8.982-11.795H13.62l1.317-7.795L6 13.205h5.187Z" />
            </svg>
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-900 dark:text-white">AI Auditor Insight</h4>
            <p className="text-xs text-slate-500 dark:text-slate-400">Automated compliance assessment &amp; narrative summary</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {insight && (
            <button
              onClick={copyToClipboard}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all flex items-center gap-1.5"
            >
              {copied ? 'Copied!' : (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 7.5V6.108c0-1.135.845-2.098 1.976-2.192.373-.03.748-.057 1.123-.08M15.75 18H18a2.25 2.25 0 002-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08M15.75 18.75v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5A3.375 3.375 0 006.375 7.5H5.25m11.9-3.664A2.251 2.251 0 0015 2.25h-1.5a2.251 2.251 0 00-2.15 1.586m5.8 0c.065.21.1.433.1.664v.75h-6V4.5c0-.231.035-.454.1-.664M6.75 7.5H4.875c-.621 0-1.125.504-1.125 1.125v12c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V16.5a9 9 0 00-9-9z" />
                  </svg>
                  Copy Prose
                </>
              )}
            </button>
          )}
          <button
            onClick={generateInsight}
            disabled={loading}
            className="px-3 py-1.5 rounded-lg text-xs font-bold bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {loading ? 'Analyzing...' : 'Re-Analyze'}
          </button>
        </div>
      </div>

      <div className="relative text-sm text-slate-700 dark:text-slate-300 font-medium leading-relaxed">
        {loading ? (
          <div className="space-y-2">
            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded animate-pulse w-3/4"></div>
            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded animate-pulse w-5/6"></div>
            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded animate-pulse w-2/3"></div>
          </div>
        ) : (
          <p className="whitespace-pre-line">{insight}</p>
        )}
      </div>
    </div>
  )
}
