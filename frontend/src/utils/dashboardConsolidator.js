export function calculateConsolidatedMetrics(store) {
  const {
    results,
    priceVarianceSame,
    priceVarianceCross,
    paymentAgingDomestic,
    paymentAgingForeign,
    paymentAgingRelated,
    paymentAgingMsme,
    vendorMasterNew,
    threeWayMatching,
    backgroundStates,
  } = store

  const execKpis = { ...(results?.executive?.kpis || {}) }

  // helper function to parse dates
  const parseDate = (dateStr) => {
    if (!dateStr || dateStr === '—') return null
    const s = String(dateStr).trim()
    if (!s || s.toLowerCase() === 'nan' || s.toLowerCase() === 'none') return null
    const isoMatch = s.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/)
    if (isoMatch) return new Date(parseInt(isoMatch[1], 10), parseInt(isoMatch[2], 10) - 1, parseInt(isoMatch[3], 10))
    const dmyMatch = s.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})/)
    if (dmyMatch) {
      let year = parseInt(dmyMatch[3], 10)
      if (year < 100) year += 2000
      return new Date(year, parseInt(dmyMatch[2], 10) - 1, parseInt(dmyMatch[1], 10))
    }
    const parsed = Date.parse(s)
    return isNaN(parsed) ? null : new Date(parsed)
  }

  // 1. Master Data Flags
  if (backgroundStates?.vendorMasterNew === 'success' && vendorMasterNew?.kpis) {
    const kpis = vendorMasterNew.kpis
    execKpis.vendor_issues = (kpis.same_gstin_multi_codes || 0) + (kpis.missing_gstin_domestic || 0) + (kpis.missing_gstin_foreign || 0)
    execKpis.duplicates = kpis.same_gstin_multi_codes || 0
    execKpis.missing_gstin = (kpis.missing_gstin_domestic || 0) + (kpis.missing_gstin_foreign || 0)
  }

  // 2. Potential Recoveries Subtext & Calculation
  let recoveriesSubtext = 'Price variance leakage identified'
  if (backgroundStates?.priceVarianceSame === 'success' || backgroundStates?.priceVarianceCross === 'success') {
    const sameLines = priceVarianceSame?.kpis?.variance_lines || 0
    const crossLines = priceVarianceCross?.kpis?.variance_lines || 0
    
    if (backgroundStates?.priceVarianceSame === 'success' && backgroundStates?.priceVarianceCross === 'success') {
      recoveriesSubtext = `${sameLines} same-vendor + ${crossLines} cross-vendor flags`
    } else if (backgroundStates?.priceVarianceSame === 'success') {
      recoveriesSubtext = `${sameLines} same-vendor flags`
    } else {
      recoveriesSubtext = `${crossLines} cross-vendor flags`
    }

    let totalSavings = 0
    if (priceVarianceSame?.rows) {
      priceVarianceSame.rows.forEach(r => {
        if (r.variance_flag === 1) {
          const avg = parseFloat(r.avg_price) || 0
          const min = parseFloat(r.min_price) || 0
          const qty = parseFloat(r.ordered_qty) || 0
          const saving = (avg - min) * qty
          if (saving > 0) totalSavings += saving
        }
      })
    }
    if (priceVarianceCross?.rows) {
      priceVarianceCross.rows.forEach(r => {
        if (r.variance_flag === 1) {
          const rate = parseFloat(r.rate_inr) || 0
          const min = parseFloat(r.item_min_rate) || 0
          const qty = parseFloat(r.ordered_qty) || 0
          const saving = (rate - min) * qty
          if (saving > 0) totalSavings += saving
        }
      })
    }
    execKpis.savings_l = parseFloat((totalSavings / 1e5).toFixed(1))
  }

  // 3. AP Outstanding, Total Invoices, and Overdue AP Invoices
  let totalOverdueCount = 0
  let isAgingLoaded = false
  let totalOutstandingAmt = 0
  let totalInvoicesCount = 0
  
  const countOverdueInRows = (rows) => {
    if (!rows) return 0
    const dates = rows.map(r => parseDate(r.posting_date || r.document_date)).filter(Boolean)
    const maxDate = dates.length > 0 
      ? new Date(dates.reduce((max, d) => {
          const t = d.getTime()
          return t > max ? t : max
        }, dates[0].getTime()))
      : new Date()

    let count = 0
    rows.forEach(r => {
      const isOverdue = r.status === 'Open' || r.status === 'Partially paid'
      const dueDt = parseDate(r.due_date_doc_term || r.due_date)
      if (isOverdue && dueDt && dueDt < maxDate) {
        count++
      }
    })
    return count
  }

  const processAgingRows = (rows) => {
    if (!rows) return
    rows.forEach(r => {
      const amt = parseFloat(r.outstanding) || 0
      if (amt > 0 && (r.status === 'Open' || r.status === 'Partially paid')) {
        totalOutstandingAmt += amt
      }
      totalInvoicesCount++
    })
  }

  const domesticOverdue = backgroundStates?.paymentAgingDomestic === 'success' ? countOverdueInRows(paymentAgingDomestic?.rows) : null
  const foreignOverdue = backgroundStates?.paymentAgingForeign === 'success' ? countOverdueInRows(paymentAgingForeign?.rows) : null
  const relatedOverdue = backgroundStates?.paymentAgingRelated === 'success' ? countOverdueInRows(paymentAgingRelated?.rows) : null
  const msmeOverdue = backgroundStates?.paymentAgingMsme === 'success' ? countOverdueInRows(paymentAgingMsme?.rows) : null

  if (backgroundStates?.paymentAgingDomestic === 'success' && paymentAgingDomestic?.rows) {
    processAgingRows(paymentAgingDomestic.rows)
  }
  if (backgroundStates?.paymentAgingForeign === 'success' && paymentAgingForeign?.rows) {
    processAgingRows(paymentAgingForeign.rows)
  }
  if (backgroundStates?.paymentAgingRelated === 'success' && paymentAgingRelated?.rows) {
    processAgingRows(paymentAgingRelated.rows)
  }
  if (backgroundStates?.paymentAgingMsme === 'success' && paymentAgingMsme?.rows) {
    processAgingRows(paymentAgingMsme.rows)
  }

  const loadedSegments = []
  if (domesticOverdue !== null) {
    totalOverdueCount += domesticOverdue
    loadedSegments.push('Domestic')
    isAgingLoaded = true
  }
  if (foreignOverdue !== null) {
    totalOverdueCount += foreignOverdue
    loadedSegments.push('Foreign')
    isAgingLoaded = true
  }
  if (relatedOverdue !== null) {
    totalOverdueCount += relatedOverdue
    loadedSegments.push('Related')
    isAgingLoaded = true
  }
  if (msmeOverdue !== null) {
    totalOverdueCount += msmeOverdue
    loadedSegments.push('MSME')
    isAgingLoaded = true
  }

  let overdueSubtext = 'Payments past due terms'
  if (loadedSegments.length > 0) {
    overdueSubtext = `Overdue in: ${loadedSegments.join(', ')}`
  }

  if (isAgingLoaded) {
    const allAgingLoaded = 
      backgroundStates?.paymentAgingDomestic === 'success' &&
      backgroundStates?.paymentAgingForeign === 'success' &&
      backgroundStates?.paymentAgingRelated === 'success' &&
      backgroundStates?.paymentAgingMsme === 'success'
    
    if (allAgingLoaded) {
      execKpis.late_overdue = totalOverdueCount
    }
  }

  if (backgroundStates?.paymentAgingDomestic === 'success' || 
      backgroundStates?.paymentAgingForeign === 'success' || 
      backgroundStates?.paymentAgingRelated === 'success' || 
      backgroundStates?.paymentAgingMsme === 'success') {
    execKpis.ap_outstanding_cr = parseFloat((totalOutstandingAmt / 1e7).toFixed(2))
    execKpis.ap_invoices = totalInvoicesCount
  }

  // 4. MSME Breaches
  if (backgroundStates?.paymentAgingMsme === 'success' && paymentAgingMsme?.rows) {
    const countMsmeBreaches = (rows) => {
      if (!rows) return 0
      const dates = rows.map(r => parseDate(r.posting_date || r.document_date)).filter(Boolean)
      const maxDate = dates.length > 0 
        ? new Date(dates.reduce((max, d) => {
            const t = d.getTime()
            return t > max ? t : max
          }, dates[0].getTime()))
        : new Date()

      let breaches = 0
      rows.forEach(r => {
        const docDt = parseDate(r.document_date || r.posting_date)
        if (!docDt) return

        const isPaid = r.status === 'Fully paid' || (r.payment_date && r.payment_date !== '—')
        if (isPaid) {
          const payDt = parseDate(r.payment_date)
          if (payDt) {
            const diffDays = Math.round((payDt - docDt) / (1000 * 60 * 60 * 24))
            if (diffDays > 45) {
              breaches++
            }
          }
        } else {
          const diffDays = Math.round((maxDate - docDt) / (1000 * 60 * 60 * 24))
          if (diffDays > 45) {
            breaches++
          }
        }
      })
      return breaches
    }
    execKpis.msme_breaches = countMsmeBreaches(paymentAgingMsme.rows)
  }

  // 5. Quantity Deviations (>5% tolerance threshold)
  if (backgroundStates?.threeWayMatching === 'success' && threeWayMatching?.rows) {
    let countAbove5 = 0
    threeWayMatching.rows.forEach(r => {
      const poQty = parseFloat(r.po_qty) || 0
      const grpoQty = parseFloat(r.grpo_qty) || 0
      if (poQty > 0) {
        const variancePct = (Math.abs(poQty - grpoQty) / poQty) * 100
        if (variancePct > 5.0) {
          countAbove5++
        }
      }
    })
    execKpis.qty_above_5pct = countAbove5
  }

  // 6. Three-Way Matches
  if (backgroundStates?.threeWayMatching === 'success' && threeWayMatching?.kpis) {
    const kpis = threeWayMatching.kpis
    execKpis.threeway_perfect = kpis.perfect_match_qty || 0
    execKpis.threeway_total = kpis.total_grpo_lines || 0
    execKpis.threeway_pct = kpis.total_grpo_lines > 0
      ? ((kpis.perfect_match_qty / kpis.total_grpo_lines) * 100).toFixed(1)
      : '0.0'
  }

  return {
    execKpis,
    recoveriesSubtext,
    overdueSubtext,
  }
}
