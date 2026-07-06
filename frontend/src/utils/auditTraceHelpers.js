export const SECTION_LABELS = {
  cover: 'Cover',
  executive: 'Executive Summary',
  postatus: 'PO Status',
  gateentry: 'Gate Entry',
  pricevariancesame: 'Price Variance (Same Vendor)',
  pricevariancecross: 'Price Variance (Cross Vendor)',
  getogrn: 'Gate Entry to GRN',
  grntoap: 'GRN to AP Invoice',
  glbalances: 'GL Balances',
  paymentaging: 'Payment Aging',
  paymentagingdomestic: 'Payment Aging (Domestic)',
  paymentagingforeign: 'Payment Aging (Foreign)',
  paymentagingrelated: 'Payment Aging (Related)',
  paymentagingmsme: 'Payment Aging (MSME)',
  vendormasternew: 'Vendor Master Validation',
  threewaymatching: '3-Way Matching',
  msme: 'MSME Compliance',
  vendormaster: 'Vendor Master',
  itemmaster: 'Item Master',
}

export function getSectionRows(sectionKey, storeState) {
  if (!storeState) return []
  if (sectionKey === 'paymentagingdomestic') return storeState.paymentAgingDomestic?.rows || []
  if (sectionKey === 'paymentagingforeign') return storeState.paymentAgingForeign?.rows || []
  if (sectionKey === 'paymentagingrelated') return storeState.paymentAgingRelated?.rows || []
  if (sectionKey === 'paymentagingmsme') return storeState.paymentAgingMsme?.rows || []
  if (sectionKey === 'vendormasternew') return storeState.vendorMasterNew?.rows || []
  if (sectionKey === 'threewaymatching') return storeState.threeWayMatching?.rows || []
  if (sectionKey === 'pricevariancesame') return storeState.priceVarianceSame?.rows || []
  if (sectionKey === 'pricevariancecross') return storeState.priceVarianceCross?.rows || []

  const res = storeState.results?.[sectionKey]
  if (res?.tables && res.tables.length > 0) {
    return res.tables[0].rows || []
  }
  return []
}

export function getCrossReferences(value, storeState) {
  const normalizedVal = String(value).trim().toLowerCase()
  if (!normalizedVal) return {}

  const results = {}
  const sectionsToScan = [
    'postatus', 'gateentry', 'getogrn', 'grntoap', 'pricevariancesame', 
    'pricevariancecross', 'glbalances', 'paymentaging', 'paymentagingdomestic', 
    'paymentagingforeign', 'paymentagingrelated', 'paymentagingmsme', 
    'vendormasternew', 'threewaymatching', 'msme', 'vendormaster', 'itemmaster'
  ]

  sectionsToScan.forEach(sec => {
    const rows = getSectionRows(sec, storeState)

    const matched = rows.filter(r => {
      return Object.values(r).some(cellVal => {
        if (cellVal === null || cellVal === undefined) return false
        return String(cellVal).trim().toLowerCase() === normalizedVal
      })
    })

    if (matched.length > 0) {
      results[sec] = matched
    }
  })

  return results
}

export function findMatchedRow(rows, value, rowValues) {
  const normalizedVal = String(value).trim().toLowerCase()
  const possible = rows.filter(r => {
    return Object.entries(r).some(([k, v]) => String(v).trim().toLowerCase() === normalizedVal)
  })
  if (possible.length === 0) return null
  if (possible.length === 1) return possible[0]

  // Best match based on DOM row values intersection
  let bestMatch = possible[0]
  let maxMatches = -1
  possible.forEach(r => {
    let matches = 0
    Object.values(r).forEach(v => {
      if (rowValues && rowValues.includes(String(v).trim())) matches++
    })
    if (matches > maxMatches) {
      maxMatches = matches
      bestMatch = r
    }
  })
  return bestMatch
}

export function getRowVal(row, ...keys) {
  if (!row) return undefined
  for (const k of keys) {
    if (row[k] !== undefined) return row[k]
  }
  const normalizedKeys = keys.map(k => String(k).replace(/[\s_-]/g, '').toLowerCase())
  for (const [rowKey, rowVal] of Object.entries(row)) {
    const normRowKey = rowKey.replace(/[\s_-]/g, '').toLowerCase()
    if (normalizedKeys.includes(normRowKey)) return rowVal
  }
  return undefined
}

/**
 * Look up the calculated_fields metadata for a given section + column name.
 * Scans all tables in the section's results for matching calculated_fields.
 *
 * @param {string} section - The section key (e.g. 'postatus', 'getogrn')
 * @param {string} columnName - The column name to look up
 * @param {object} storeState - The full Zustand store state
 * @returns {object|null} The calculated field descriptor, or null if not a calculated field
 */
export function getCalculatedField(section, columnName, storeState) {
  if (!section || !columnName || !storeState) return null

  // 1. Check dedicated section state objects (priceVarianceSame, etc.)
  const sectionStateMap = {
    pricevariancesame: 'priceVarianceSame',
    pricevariancecross: 'priceVarianceCross',
    paymentagingdomestic: 'paymentAgingDomestic',
    paymentagingforeign: 'paymentAgingForeign',
    paymentagingrelated: 'paymentAgingRelated',
    paymentagingmsme: 'paymentAgingMsme',
    vendormasternew: 'vendorMasterNew',
    threewaymatching: 'threeWayMatching',
  }

  const stateKey = sectionStateMap[section]
  if (stateKey) {
    const data = storeState[stateKey]
    if (data?.tables) {
      for (const table of data.tables) {
        if (table.calculated_fields && table.calculated_fields[columnName]) {
          return table.calculated_fields[columnName]
        }
      }
    }
    return null
  }

  // 2. Check main results object
  const results = storeState.results
  if (!results) return null

  const sectionData = results[section]
  if (!sectionData?.tables) return null

  for (const table of sectionData.tables) {
    if (table.calculated_fields && table.calculated_fields[columnName]) {
      return table.calculated_fields[columnName]
    }
  }

  return null
}

export function evaluateKpiContributions(section, row) {
  if (!row) return []

  const list = []
  const getNum = (v) => {
    if (v === null || v === undefined) return 0
    const n = parseFloat(v)
    return isNaN(n) ? 0 : n
  }
  const isFlag = (v) => {
    return v === 1 || v === '1' || v === true || String(v).toLowerCase() === 'true'
  }

  const sectionNorm = String(section).toLowerCase()

  if (sectionNorm.startsWith('paymentaging') || sectionNorm === 'msme') {
    const daysLate = getNum(getRowVal(row, 'days_late', 'Days Late'))
    const isPaid = String(getRowVal(row, 'status', 'Status') || '').toLowerCase() === 'paid'
    const amt = getNum(getRowVal(row, 'outstanding', 'Outstanding', 'amount', 'Amount'))
    const term = String(getRowVal(row, 'payment_term_type', 'Payment Term Type', 'payment_term', 'Payment Terms') || '')
    const code = getRowVal(row, 'vendor_code', 'Vendor Code', 'vendor')

    list.push({
      kpi: 'Avg days late(paid)',
      matched: isPaid && daysLate > 0,
      detail: isPaid && daysLate > 0 ? `Paid transaction delayed by ${daysLate} days` : 'Not a late paid transaction'
    })
    list.push({
      kpi: 'Early Payments',
      matched: isPaid && daysLate <= 0,
      detail: isPaid && daysLate <= 0 ? `Paid early or on-time (${Math.abs(daysLate)} days difference)` : 'Not paid early/on-time'
    })
    list.push({
      kpi: 'Late Payments',
      matched: isPaid && daysLate > 0,
      detail: isPaid && daysLate > 0 ? `Paid late by ${daysLate} days` : 'Not a late paid transaction'
    })
    list.push({
      kpi: 'Overdue Amount',
      matched: !isPaid && amt > 0,
      detail: !isPaid && amt > 0 ? `Outstanding balance: ₹${amt.toLocaleString()}` : 'No outstanding/overdue balance'
    })
    list.push({
      kpi: 'Advance term invoices',
      matched: term.toLowerCase() === 'advance',
      detail: term.toLowerCase() === 'advance' ? 'Belongs to Advance payment terms' : 'Not an advance term invoice'
    })
    list.push({
      kpi: 'Unique Vendor codes',
      matched: !!code,
      detail: code ? `Contributes to vendor code: ${code}` : 'No vendor code found'
    })
  } else if (sectionNorm === 'vendormasternew' || sectionNorm === 'vendormaster') {
    const sameGst = isFlag(getRowVal(row, 'same_gst_multi_code', 'Same GSTIN Multi Code'))
    const isDormant = String(getRowVal(row, 'active', 'Status', 'active_dormant') || '').toLowerCase() === 'dormant'
    const name = getRowVal(row, 'vendor_name', 'Vendor Name', 'name')
    const code = getRowVal(row, 'vendor_code', 'Vendor Code', 'vendor')
    const gstin = getRowVal(row, 'gstin', 'GSTIN', 'GST Number')

    list.push({
      kpi: 'Total suppliers',
      matched: true,
      detail: `Supplier record: ${name || code || 'Unnamed'}`
    })
    list.push({
      kpi: 'Same GSTIN on Multiple codes',
      matched: sameGst,
      detail: sameGst ? `GSTIN ${gstin} is registered to multiple codes` : 'GSTIN is unique or not applicable'
    })
    list.push({
      kpi: 'Dormant duplicate codes',
      matched: sameGst && isDormant,
      detail: sameGst && isDormant ? 'Inactive duplicate code with shared GSTIN' : 'Not a dormant duplicate code'
    })
    list.push({
      kpi: 'Missing GSTIN(domestic)',
      matched: isFlag(getRowVal(row, 'missing_gstin', 'Missing GSTIN Flag')),
      detail: isFlag(getRowVal(row, 'missing_gstin', 'Missing GSTIN Flag')) ? 'Domestic vendor with missing GSTIN details' : 'Not a missing domestic GSTIN'
    })
    list.push({
      kpi: 'Missing GSTIN(foreign)',
      matched: isFlag(getRowVal(row, 'foreign_w_gstin', 'Foreign w/ GSTIN Flag')),
      detail: isFlag(getRowVal(row, 'foreign_w_gstin', 'Foreign w/ GSTIN Flag')) ? 'Foreign vendor with invalid domestic format' : 'Not a foreign w/ GSTIN flag'
    })
    list.push({
      kpi: 'Rows flagged',
      matched: isFlag(getRowVal(row, 'missing_gstin', 'Missing GSTIN Flag')) || isFlag(getRowVal(row, 'foreign_w_gstin', 'Foreign w/ GSTIN Flag')),
      detail: (isFlag(getRowVal(row, 'missing_gstin', 'Missing GSTIN Flag')) || isFlag(getRowVal(row, 'foreign_w_gstin', 'Foreign w/ GSTIN Flag')) ? 'Flagged for compliance review' : 'No flag registered')
    })
  } else if (sectionNorm === 'postatus') {
    const docStatus = String(getRowVal(row, 'doc_status', 'Doc Status', 'status', 'Status') || '').toUpperCase()
    const isOpen = docStatus === 'OPEN'
    const recvQty = getNum(getRowVal(row, 'received_qty', 'Received Qty.', 'Recv Qty'))
    const ordQty = getNum(getRowVal(row, 'ordered_qty', 'Ordered Qty.', 'Total Qty', 'Total Qty.'))
    const recvPct = ordQty > 0 ? (recvQty / ordQty) * 100 : 0
    const isFlagged = isFlag(getRowVal(row, 'pending_flag', 'Pending Flag')) || 
                      isFlag(getRowVal(row, 'open_90d_no_receipt', 'Open>90d & No receipt')) || 
                      isFlag(getRowVal(row, 'recv_less_50', 'Recv<50%')) || 
                      isFlag(getRowVal(row, 'holiday_flag', 'Holiday flag'))
    const poNum = getRowVal(row, 'po_number', 'PO Number', 'PO No', 'po_no')

    list.push({
      kpi: 'Unique POs',
      matched: true,
      detail: `PO Number: ${poNum || 'Unknown'}`
    })
    list.push({
      kpi: 'Open Lines',
      matched: isOpen,
      detail: isOpen ? 'PO line item is still open' : 'PO line item is closed'
    })
    list.push({
      kpi: 'Recv < 50%',
      matched: ordQty > 0 && recvPct < 50,
      detail: ordQty > 0 && recvPct < 50 ? `Received ${recvPct.toFixed(1)}% of ordered quantity` : 'Received >= 50%'
    })
    list.push({
      kpi: 'Flagged POs',
      matched: isFlagged,
      detail: isFlagged ? 'Contains active compliance flags' : 'No flags detected'
    })
  } else if (sectionNorm === 'threewaymatching' || sectionNorm === 'threeway') {
    const matchStatus = getRowVal(row, 'match_status', 'Match Status')
    const hasVariance = matchStatus === 'Variance'
    const excess = isFlag(getRowVal(row, 'excess_over_5', 'Excess Over 5%'))

    list.push({
      kpi: 'Perfect match',
      matched: matchStatus === 'Perfect match',
      detail: matchStatus === 'Perfect match' ? 'Quantities and rates perfectly match' : 'Variance detected'
    })
    list.push({
      kpi: 'Variance',
      matched: hasVariance,
      detail: hasVariance ? 'Variance in quantity or rates' : 'Perfect match'
    })
    list.push({
      kpi: 'Excess > 5%',
      matched: excess,
      detail: excess ? 'Invoice quantity exceeds GRN by >5%' : 'No excess variance'
    })
  }

  return list
}
