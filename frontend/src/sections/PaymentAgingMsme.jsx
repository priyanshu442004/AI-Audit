import React, { useState, useEffect, useMemo } from 'react'
import { fetchPaymentAgingMsme } from '../api'
import AiInsightBox from '../components/AiInsightBox'
import { useStore } from '../store'
import TruncatedCell from '../components/TruncatedCell'
import useColumnOrder from '../hooks/useColumnOrder'

const formatCurrency = (val) => {
  if (val === null || val === undefined) return '—'
  const num = parseFloat(val)
  if (isNaN(num)) return val
  // Cumulative balance is negative for payables, display absolute value
  const absNum = Math.abs(num)
  if (absNum >= 10000000) return `₹${(absNum / 10000000).toFixed(2)} Cr`
  if (absNum >= 100000) return `₹${(absNum / 100000).toFixed(2)} L`
  return `₹${absNum.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
}

const parseDate = (dateStr) => {
  if (!dateStr || dateStr === '—') return null
  if (dateStr instanceof Date) return dateStr
  const s = String(dateStr).trim()
  if (!s || s.toLowerCase() === 'nan' || s.toLowerCase() === 'none') return null
  
  // Try YYYY-MM-DD
  const isoMatch = s.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/)
  if (isoMatch) {
    return new Date(parseInt(isoMatch[1], 10), parseInt(isoMatch[2], 10) - 1, parseInt(isoMatch[3], 10))
  }
  
  // Try DD-MM-YYYY or DD/MM/YY
  const dmyMatch = s.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})/)
  if (dmyMatch) {
    let year = parseInt(dmyMatch[3], 10)
    if (year < 100) year += 2000
    return new Date(year, parseInt(dmyMatch[2], 10) - 1, parseInt(dmyMatch[1], 10))
  }
  
  const parsed = Date.parse(s)
  return isNaN(parsed) ? null : new Date(parsed)
}

function SortIcon({ dir }) {
  if (!dir) return (
    <svg className="w-3 h-3 text-slate-300 dark:text-slate-600 ml-1 inline" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4" />
    </svg>
  )
  return (
    <svg className="w-3 h-3 text-blue-500 ml-1 inline" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
      {dir === 'asc'
        ? <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
        : <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />}
    </svg>
  )
}

const COLS = [
  { id: 'vendor_code', label: 'Vendor Code' },
  { id: 'vendor_name', label: 'Vendor Name' },
  { id: 'vendor_country', label: 'Country' },
  { id: 'vendor_group', label: 'Vendor Group' },
  { id: 'vendor_address', label: 'Vendor Address' },
  { id: 'company_type', label: 'Company Type' },
  { id: 'payment_terms', label: 'Payment Terms' },
  { id: 'payment_term_type', label: 'Term Type' },
  { id: 'term_days', label: 'Term Days' },
  { id: 'invoice_doc_number', label: 'Doc Number' },
  { id: 'document_date', label: 'Doc Date' },
  { id: 'posting_date', label: 'Posting Date' },
  { id: 'due_date_doc_term', label: 'Due Date(Doc+Term)' },
  { id: 'payment_date', label: 'Payment Date' },
  { id: 'days_late', label: 'Days Late' },
  { id: 'actual_paid', label: 'Actual Paid' },
  { id: 'outstanding', label: 'Outstanding' },
  { id: 'status', label: 'Status' },
  { id: 'aging_category', label: 'Aging Category' },
]
const ALL_COLS = COLS.map(c => c.id)
const COL_LABEL = Object.fromEntries(COLS.map(c => [c.id, c.label]))

const CELL_CLASS = {
  vendor_code: 'px-4 py-3 text-xs font-mono font-bold text-slate-900 dark:text-white',
  vendor_name: 'px-4 py-3 text-xs font-medium text-slate-700 dark:text-slate-300',
  vendor_country: 'px-4 py-3 text-xs text-slate-600 dark:text-slate-400',
  vendor_group: 'px-4 py-3 text-xs text-slate-600 dark:text-slate-400',
  vendor_address: 'px-4 py-3 text-xs text-slate-500 dark:text-slate-500 max-w-[150px]',
  company_type: 'px-4 py-3 text-xs text-slate-700 dark:text-slate-300 font-semibold',
  payment_terms: 'px-4 py-3 text-xs text-slate-600 dark:text-slate-400',
  payment_term_type: 'px-4 py-3 text-xs text-slate-600 dark:text-slate-400 font-semibold',
  term_days: 'px-4 py-3 text-xs font-mono text-slate-600 dark:text-slate-400',
  invoice_doc_number: 'px-4 py-3 text-xs font-mono text-slate-700 dark:text-slate-300',
  document_date: 'px-4 py-3 text-xs text-slate-600 dark:text-slate-400 font-mono',
  posting_date: 'px-4 py-3 text-xs text-slate-600 dark:text-slate-400 font-mono',
  due_date_doc_term: 'px-4 py-3 text-xs text-slate-600 dark:text-slate-400 font-mono',
  payment_date: 'px-4 py-3 text-xs text-slate-600 dark:text-slate-400 font-mono',
  days_late: 'px-4 py-3 text-xs font-mono text-slate-600 dark:text-slate-400',
  actual_paid: 'px-4 py-3 text-xs font-mono text-right text-slate-900 dark:text-white',
  outstanding: 'px-4 py-3 text-xs font-mono text-right text-slate-900 dark:text-white',
  status: 'px-4 py-3 text-xs text-center',
  aging_category: 'px-4 py-3 text-xs text-center',
}

function renderCell(colId, row) {
  switch (colId) {
    case 'actual_paid':
      return <TruncatedCell value={formatCurrency(row.actual_paid)} />
    case 'outstanding':
      return <TruncatedCell value={formatCurrency(row.outstanding)} />
    case 'status':
      return (
        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
          row.status === 'Fully paid'
            ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400'
            : row.status === 'Partially paid'
            ? 'bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400'
            : 'bg-rose-100 text-rose-700 dark:bg-rose-950/40 dark:text-rose-400'
        }`}>
          {row.status}
        </span>
      )
    case 'aging_category': {
      let catBadge = 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
      const ac = row.aging_category || ''
      if (ac.includes('16-30')) catBadge = 'bg-amber-50 text-amber-700 dark:bg-amber-950/20 dark:text-amber-400'
      else if (ac.includes('31-45')) catBadge = 'bg-orange-50 text-orange-700 dark:bg-orange-950/20 dark:text-orange-400'
      else if (ac.includes('46-60')) catBadge = 'bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400'
      else if (ac.includes('61-90')) catBadge = 'bg-red-50 text-red-700 dark:bg-red-950/20 dark:text-red-400'
      else if (ac.includes('>90')) catBadge = 'bg-rose-100 text-rose-700 dark:bg-rose-950/30 dark:text-rose-400 font-bold'
      return <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono ${catBadge}`}>{row.aging_category}</span>
    }
    default:
      return <TruncatedCell value={row[colId]} />
  }
}

export default function PaymentAgingMsme() {
  const { paymentAgingMsme, setPaymentAgingMsme } = useStore()
  const [loading, setLoading] = useState(!paymentAgingMsme)
  const [error, setError] = useState(null)

  // Filters and pagination state
  const [searchTerm, setSearchTerm] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [sortCol, setSortCol] = useState('vendor_code')
  const [sortDir, setSortDir] = useState('asc')
  const [currentPage, setCurrentPage] = useState(1)
  const ITEMS_PER_PAGE = 25

  const { order: colOrder, moveColumn } = useColumnOrder('payment-aging-msme', ALL_COLS)
  const [dragCol, setDragCol] = useState(null)
  const [dragOverCol, setDragOverCol] = useState(null)

  useEffect(() => {
    if (paymentAgingMsme) {
      setLoading(false)
      return
    }
    setLoading(true)
    fetchPaymentAgingMsme()
      .then(res => {
        setPaymentAgingMsme(res)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [paymentAgingMsme, setPaymentAgingMsme])

  const handleSearch = (e) => {
    setSearchTerm(e.target.value)
    setCurrentPage(1)
  }

  const handleSort = (col) => {
    if (sortCol === col) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortCol(col)
      setSortDir('asc')
    }
    setCurrentPage(1)
  }

  const rows = paymentAgingMsme?.rows || []

  // Filtered rows
  const filtered = useMemo(() => {
    let out = [...rows]
    const term = searchTerm.trim().toLowerCase()

    // 1. Search filter
    if (term) {
      out = out.filter(r => 
        String(r.vendor_code ?? '').toLowerCase().includes(term) ||
        String(r.vendor_name ?? '').toLowerCase().includes(term) ||
        String(r.vendor_group ?? '').toLowerCase().includes(term) ||
        String(r.company_type ?? '').toLowerCase().includes(term) ||
        String(r.invoice_doc_number ?? '').toLowerCase().includes(term) ||
        String(r.payment_terms ?? '').toLowerCase().includes(term) ||
        String(r.payment_term_type ?? '').toLowerCase().includes(term) ||
        String(r.status ?? '').toLowerCase().includes(term) ||
        String(r.aging_category ?? '').toLowerCase().includes(term)
      )
    }

    // 2. Date filter (ranges over posting_date or document_date)
    if (startDate || endDate) {
      const start = startDate ? new Date(startDate) : null
      if (start) start.setHours(0, 0, 0, 0)
      const end = endDate ? new Date(endDate) : null
      if (end) end.setHours(23, 59, 59, 999)

      out = out.filter(r => {
        const postDate = parseDate(r.posting_date)
        if (!postDate) return false
        if (start && postDate < start) return false
        if (end && postDate > end) return false
        return true
      })
    }

    // 3. Sorting
    if (sortCol) {
      out.sort((a, b) => {
        const av = a[sortCol] ?? ''
        const bv = b[sortCol] ?? ''
        const an = parseFloat(av)
        const bn = parseFloat(bv)

        let cmp = 0
        if (!isNaN(an) && !isNaN(bn)) {
          cmp = an - bn
        } else {
          cmp = String(av).localeCompare(String(bv), undefined, { numeric: true, sensitivity: 'base' })
        }
        return sortDir === 'asc' ? cmp : -cmp
      })
    }

    return out
  }, [rows, searchTerm, startDate, endDate, sortCol, sortDir])

  // Calculated metrics for top of page (KPI Cards)
  const metrics = useMemo(() => {
    const totalLines = filtered.length
    
    // Sum of actual paid
    let totalPaid = 0
    // Vendor unique balance aggregation (take last row's outstanding for each vendor)
    const vendorBalances = {}
    
    // Avg days late (paid): average of days_late considering payments made (actual_paid > 0)
    let lateDaysSumPaid = 0
    let lateDaysCountPaid = 0

    // Early Payments: count of payments done before the due date
    let earlyPayments = 0

    // Late Payments: count of payments done after the due date
    let latePayments = 0

    // Find the max posting date in the dataset to act as "today" for overdue check
    const dates = filtered.map(r => parseDate(r.posting_date)).filter(Boolean)
    const maxDate = dates.length > 0 
      ? new Date(dates.reduce((max, d) => {
          const t = d.getTime()
          return t > max ? t : max
        }, dates[0].getTime()))
      : new Date()

    // Overdue Amount check per vendor
    const vendorOverdue = {}

    // Advance term invoices: total unique vendors who are in advance payment term column
    const advanceVendorsSet = new Set()

    // On-Time/Early %: total percent of payments that were paid on time or early (days_late === 0)
    let totalPaidPaymentsCount = 0
    let onTimeEarlyPaidPaymentsCount = 0

    // Unique Vendor codes
    const uniqueVendorsSet = new Set()

    filtered.forEach(r => {
      totalPaid += r.actual_paid || 0
      
      const vcode = r.vendor_code
      if (vcode) {
        uniqueVendorsSet.add(vcode)
      }
      
      const bal = Math.abs(r.outstanding || 0)
      vendorBalances[vcode] = bal // will store the latest one processed since rows are sorted
      
      const isPayment = r.actual_paid > 0 || r.status === 'Fully paid' || r.status === 'Partially paid'
      const payDt = parseDate(r.payment_date)
      const dueDt = parseDate(r.due_date_doc_term)
      
      if (isPayment) {
        totalPaidPaymentsCount++
        
        // Avg days late (paid)
        lateDaysSumPaid += r.days_late || 0
        lateDaysCountPaid++

        // Early payments (payment date before due date)
        if (payDt && dueDt && payDt < dueDt) {
          earlyPayments++
        }
        
        // Late payments (payment date after due date)
        if (payDt && dueDt && payDt > dueDt) {
          latePayments++
        }

        // On-Time/Early count (paid and days_late === 0)
        if ((r.days_late || 0) === 0) {
          onTimeEarlyPaidPaymentsCount++
        }
      }

      // Overdue check
      if (r.status === 'Open' || r.status === 'Partially paid') {
        if (dueDt && dueDt < maxDate) {
          vendorOverdue[vcode] = true
        }
      }

      // Advance term check
      if (r.payment_term_type === 'Advance' && vcode) {
        advanceVendorsSet.add(vcode)
      }
    })

    const totalOutstanding = Object.values(vendorBalances).reduce((a, b) => a + b, 0)
    const avgDaysLatePaid = lateDaysCountPaid > 0 ? Math.round(lateDaysSumPaid / lateDaysCountPaid) : 0
    const onTimeEarlyPct = totalPaidPaymentsCount > 0 ? Math.round((onTimeEarlyPaidPaymentsCount / totalPaidPaymentsCount) * 100) : 0

    let overdueAmount = 0
    Object.keys(vendorBalances).forEach(vcode => {
      if (vendorOverdue[vcode]) {
        overdueAmount += vendorBalances[vcode]
      }
    })

    return {
      totalLines,
      totalOutstanding,
      totalPaid,
      avgDaysLatePaid,
      earlyPayments,
      latePayments,
      overdueAmount,
      advanceTermInvoices: advanceVendorsSet.size,
      onTimeEarlyPct,
      uniqueVendors: uniqueVendorsSet.size
    }
  }, [filtered])

  // Top Items: Top 5 Overdue Vendors
  const topOverdue = useMemo(() => {
    const vendorMap = {}
    filtered.forEach(r => {
      const vcode = r.vendor_code
      const vname = r.vendor_name
      const grp = r.vendor_group
      const outstanding = Math.abs(r.outstanding || 0)
      
      if (!vendorMap[vcode]) {
        vendorMap[vcode] = { code: vcode, name: vname, group: grp, outstanding: 0, maxLate: 0 }
      }
      // Since cumulative balance is running, the final balance is the last transaction's balance
      vendorMap[vcode].outstanding = outstanding
      if (r.days_late > vendorMap[vcode].maxLate) {
        vendorMap[vcode].maxLate = r.days_late
      }
    })

    return Object.values(vendorMap)
      .filter(v => v.outstanding > 1)
      .sort((a, b) => b.outstanding - a.outstanding)
      .slice(0, 5)
  }, [filtered])

  const totalPages = Math.max(1, Math.ceil(filtered.length / ITEMS_PER_PAGE))
  const paginated = filtered.slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE)
  const startRec = filtered.length === 0 ? 0 : (currentPage - 1) * ITEMS_PER_PAGE + 1
  const endRec = Math.min(currentPage * ITEMS_PER_PAGE, filtered.length)

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">
          Processing MSME Compliance Payment Aging analysis...
        </p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-800 rounded-xl">
        <h3 className="text-base font-bold text-rose-800 dark:text-rose-400 mb-1">Error Loading Data</h3>
        <p className="text-sm text-rose-700 dark:text-rose-400/80">{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            MSME Compliance
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Audit payments and track credit term compliance for small and micro vendors (MSME Registration values: Small, Micro, or Y).
          </p>
        </div>
        <span className="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800 text-[11px] font-semibold text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
          <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
          MSME Vendors
        </span>
      </div>

      {/* AI Insight Box */}
      <AiInsightBox section="paymentagingmsme" kpis={{
        total_lines: metrics.totalLines,
        unique_vendors: metrics.uniqueVendors,
        total_outstanding: metrics.totalOutstanding,
        overdue_amount: metrics.overdueAmount,
        total_paid: metrics.totalPaid,
        avg_days_late: metrics.avgDaysLatePaid,
        on_time_early_pct: metrics.onTimeEarlyPct,
        early_payments: metrics.earlyPayments,
        late_payments: metrics.latePayments,
        advance_term_invoices: metrics.advanceTermInvoices
      }} />

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {[
          { label: 'Audited Transactions', value: metrics.totalLines, accent: 'blue', desc: 'Total ledger entries processed' },
          { label: 'Unique Vendor Codes', value: metrics.uniqueVendors, accent: 'blue', desc: 'Count of unique vendor codes' },
          { label: 'Total Outstanding Balance', value: formatCurrency(metrics.totalOutstanding), accent: 'rose', desc: 'Net trade payables liability' },
          { label: 'Overdue Amount', value: formatCurrency(metrics.overdueAmount), accent: 'rose', desc: 'Total overdue balance' },
          { label: 'Total Paid (Actual)', value: formatCurrency(metrics.totalPaid), accent: 'green', desc: 'Total payments cleared' },
          { label: 'Avg Days Late (Paid)', value: `${metrics.avgDaysLatePaid} Days`, accent: metrics.avgDaysLatePaid > 15 ? 'amber' : 'blue', desc: 'Mean payment delay of paid invoices' },
          { label: 'On-Time/Early %', value: `${metrics.onTimeEarlyPct}%`, accent: metrics.onTimeEarlyPct > 80 ? 'green' : 'amber', desc: 'Percent of payments on-time or early' },
          { label: 'Early Payments', value: metrics.earlyPayments, accent: 'green', desc: 'Payments done before the due date' },
          { label: 'Late Payments', value: metrics.latePayments, accent: metrics.latePayments > 0 ? 'rose' : 'blue', desc: 'Payments done after the due date' },
          { label: 'Advance Term Invoices', value: metrics.advanceTermInvoices, accent: 'blue', desc: 'Unique vendors with advance terms' }
        ].map(card => {
          const isRose = card.accent === 'rose'
          const isAmber = card.accent === 'amber'
          const isGreen = card.accent === 'green'
          const barColor = isRose ? 'bg-rose-500' : (isAmber ? 'bg-amber-500' : (isGreen ? 'bg-emerald-500' : 'bg-blue-500'))
          const textColor = isRose ? 'text-rose-600 dark:text-rose-400' : (isAmber ? 'text-amber-600 dark:text-amber-400' : (isGreen ? 'text-emerald-600 dark:text-emerald-400' : 'text-blue-600 dark:text-blue-400'))
          
          return (
            <div key={card.label} className="relative bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden">
              <div className={`absolute top-0 left-0 right-0 h-0.5 ${barColor}`} />
              <p className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest leading-tight mb-2">
                {card.label}
              </p>
              <p className={`text-xl font-black tracking-tight leading-none ${textColor}`}>
                {typeof card.value === 'number' ? card.value.toLocaleString() : card.value}
              </p>
              {card.desc && <p className="text-[9px] text-slate-400 dark:text-slate-500 mt-2">{card.desc}</p>}
            </div>
          )
        })}
      </div>

      {/* Top Items Section (Dynamically Calculated) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-3">Top 5 Overdue MSME Vendors</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-800 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                  <th className="py-2">Vendor Code</th>
                  <th className="py-2">Vendor Name</th>
                  <th className="py-2">Vendor Group</th>
                  <th className="py-2 text-right">Outstanding Balance</th>
                  <th className="py-2 text-right">Max Days Late</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-medium">
                {topOverdue.map((v, i) => (
                  <tr key={i} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                    <td className="py-2.5 font-mono font-bold text-slate-950 dark:text-white"><TruncatedCell value={v.code} /></td>
                    <td className="py-2.5 text-slate-700 dark:text-slate-300"><TruncatedCell value={v.name} /></td>
                    <td className="py-2.5 text-slate-500 dark:text-slate-500"><TruncatedCell value={v.group} /></td>
                    <td className="py-2.5 text-right font-mono font-bold text-rose-600 dark:text-rose-400">{formatCurrency(v.outstanding)}</td>
                    <td className="py-2.5 text-right font-mono text-slate-700 dark:text-slate-300">{v.maxLate} days</td>
                  </tr>
                ))}
                {topOverdue.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-4 text-center text-slate-400">No overdue MSME vendors found</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Small Breakdown Card */}
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">MSME Status Distribution</h3>
            <p className="text-xs text-slate-400 mt-0.5">Summary of ledger line status flags</p>
          </div>
          <div className="space-y-3.5 my-4">
            {['Fully paid', 'Partially paid', 'Open'].map(st => {
              const count = filtered.filter(r => r.status === st).length
              const pct = filtered.length > 0 ? ((count / filtered.length) * 100).toFixed(1) : '0'
              const color = st === 'Fully paid' ? 'bg-emerald-500' : (st === 'Partially paid' ? 'bg-amber-500' : 'bg-rose-500')
              const textColor = st === 'Fully paid' ? 'text-emerald-600 dark:text-emerald-400' : (st === 'Partially paid' ? 'text-amber-600 dark:text-amber-400' : 'text-rose-600 dark:text-rose-400')
              return (
                <div key={st} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold text-slate-600 dark:text-slate-300">
                    <span className="flex items-center gap-1.5">
                      <span className={`w-2 h-2 rounded-full ${color}`} />
                      {st}
                    </span>
                    <span className="font-bold text-slate-950 dark:text-white">{count.toLocaleString()} ({pct}%)</span>
                  </div>
                  <div className="bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden relative shadow-inner">
                    <div 
                      className={`h-full rounded-full ${color} transition-all duration-500`}
                      style={{ width: `${pct}%` }} 
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Bottom Table Section */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        {/* Table Toolbar */}
        <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-800 flex flex-col gap-3">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Reconciled Ledger Invoices</h3>
              <p className="text-xs text-slate-400 mt-0.5">Detail level aging status for each MSME vendor ledger transaction</p>
            </div>

            <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
              {/* Search input */}
              <div className="relative">
                <svg className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  placeholder="Search table..."
                  value={searchTerm}
                  onChange={handleSearch}
                  className="pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 w-44 transition"
                />
              </div>

              {/* Date Filters */}
              <div className="flex items-center gap-1.5 text-xs">
                <input
                  type="date"
                  value={startDate}
                  onChange={e => { setStartDate(e.target.value); setCurrentPage(1) }}
                  className="px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <span className="text-slate-400">to</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={e => { setEndDate(e.target.value); setCurrentPage(1) }}
                  className="px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                {(startDate || endDate) && (
                  <button
                    onClick={() => { setStartDate(''); setEndDate(''); setCurrentPage(1) }}
                    className="text-xs text-rose-500 hover:underline font-bold"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Responsive Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse min-w-[2200px]">
            <thead>
              <tr className="bg-slate-50/50 dark:bg-slate-800/40 border-b border-slate-100 dark:border-slate-800">
                {colOrder.map(colId => (
                  <th
                    key={colId}
                    draggable
                    onDragStart={(e) => { e.dataTransfer.effectAllowed = 'move'; setDragCol(colId) }}
                    onDragOver={(e) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; if (dragOverCol !== colId) setDragOverCol(colId) }}
                    onDragLeave={() => setDragOverCol(prev => (prev === colId ? null : prev))}
                    onDrop={(e) => { e.preventDefault(); if (dragCol && dragCol !== colId) moveColumn(dragCol, colId); setDragCol(null); setDragOverCol(null) }}
                    onDragEnd={() => { setDragCol(null); setDragOverCol(null) }}
                    onClick={() => handleSort(colId)}
                    title="Click to sort · Drag to reorder"
                    className={`px-4 py-3 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider cursor-grab active:cursor-grabbing select-none transition-colors hover:bg-slate-100/50 dark:hover:bg-slate-800/60 ${dragCol === colId ? 'opacity-40' : ''} ${dragOverCol === colId && dragCol !== colId ? 'bg-blue-100/70 dark:bg-blue-900/30 border-l-2 border-l-blue-500' : ''}`}
                  >
                    <div className="flex items-center font-bold">
                      {COL_LABEL[colId]}
                      <SortIcon dir={sortCol === colId ? sortDir : null} />
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {paginated.map((row, i) => (
                <tr key={i} className="hover:bg-slate-50/40 dark:hover:bg-slate-800/20 transition-colors duration-150">
                  {colOrder.map(colId => (
                    <td key={colId} className={CELL_CLASS[colId] || 'px-4 py-3 text-xs text-slate-700 dark:text-slate-300'}>
                      {renderCell(colId, row)}
                    </td>
                  ))}
                </tr>
              ))}
              {paginated.length === 0 && (
                <tr>
                  <td colSpan={colOrder.length} className="px-6 py-10 text-center text-sm text-slate-400 dark:text-slate-500">
                    No matching records found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Toolbar */}
        <div className="px-5 py-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <div>
            Showing <span className="font-semibold text-slate-700 dark:text-white">{startRec}</span> to{' '}
            <span className="font-semibold text-slate-700 dark:text-white">{endRec}</span> of{' '}
            <span className="font-semibold text-slate-700 dark:text-white">{filtered.length}</span> entries
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage(1)}
              disabled={currentPage === 1}
              className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40"
            >
              First
            </button>
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40"
            >
              Prev
            </button>
            <span className="px-2 py-1">
              Page <span className="font-semibold text-slate-700 dark:text-white">{currentPage}</span> of{' '}
              <span className="font-semibold text-slate-700 dark:text-white">{totalPages}</span>
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40"
            >
              Next
            </button>
            <button
              onClick={() => setCurrentPage(totalPages)}
              disabled={currentPage === totalPages}
              className="px-2 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40"
            >
              Last
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
