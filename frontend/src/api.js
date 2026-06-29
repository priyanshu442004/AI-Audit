const BASE = '/api'

/**
 * Upload files with roles.
 * @param {Array<{role: string, file: File}>} items
 * @returns {Promise<{session_id: string, files: Array}>}
 */
export async function uploadFiles(items) {
  const fd = new FormData()
  items.forEach(({ file, role }) => {
    fd.append('files', file)
    fd.append('roles', role)
  })
  const res = await fetch(`${BASE}/upload`, { method: 'POST', body: fd })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Upload failed: ${res.status}`)
  }
  return res.json()
}

/**
 * Subscribe to SSE analysis stream.
 * onProgress({stage, pct, message}) called for progress events.
 * onResult(result) called when the final result arrives.
 * onError(msg) called on error.
 * Returns a cleanup function to close the EventSource.
 */
export function analyzeStream(sessionId, { onProgress, onResult, onError }) {
  const es = new EventSource(`${BASE}/analyze/${sessionId}`)

  es.onmessage = (e) => {
    const data = JSON.parse(e.data)
    if (data.stage === 'result') {
      es.close()
      onResult(data.result)
    } else if (data.stage === 'error') {
      es.close()
      onError(data.message || 'Analysis failed')
    } else {
      onProgress({ stage: data.stage, pct: data.pct, message: data.message })
    }
  }

  es.onerror = () => {
    es.close()
    onError('Connection to server lost.')
  }

  return () => es.close()
}

/**
 * Fetch AI narrative for a section.
 * @param {string} section
 * @param {object} kpis
 * @param {Array}  topRisks
 * @returns {Promise<string>}
 */
export async function fetchInsight(section, kpis, topRisks = []) {
  const res = await fetch(`${BASE}/insights/${section}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ kpis, top_risks: topRisks }),
  })
  if (!res.ok) return ''
  const data = await res.json()
  return data.narrative || ''
}

/**
 * Fetch same-vendor price variance.
 * @returns {Promise<{rows: Array, kpis: object}>}
 */
export async function fetchPriceVarianceSame() {
  const res = await fetch(`${BASE}/analysis/price-variance-same`)
  if (!res.ok) throw new Error('Failed to load same-vendor price variance')
  return res.json()
}

/**
 * Fetch cross-vendor price variance.
 * @returns {Promise<{rows: Array, kpis: object}>}
 */
export async function fetchPriceVarianceCross() {
  const res = await fetch(`${BASE}/analysis/price-variance-cross`)
  if (!res.ok) throw new Error('Failed to load cross-vendor price variance')
  return res.json()
}

/**
 * Fetch payment aging (domestic).
 * @returns {Promise<{rows: Array, kpis: object}>}
 */
export async function fetchPaymentAgingDomestic() {
  const res = await fetch(`${BASE}/analysis/payment-aging-domestic`)
  if (!res.ok) throw new Error('Failed to load payment aging (domestic) analysis')
  return res.json()
}

/**
 * Fetch payment aging (foreign).
 * @returns {Promise<{rows: Array, kpis: object}>}
 */
export async function fetchPaymentAgingForeign() {
  const res = await fetch(`${BASE}/analysis/payment-aging-foreign`)
  if (!res.ok) throw new Error('Failed to load payment aging (foreign) analysis')
  return res.json()
}

/**
 * Fetch payment aging (related).
 * @returns {Promise<{rows: Array, kpis: object}>}
 */
export async function fetchPaymentAgingRelated() {
  const res = await fetch(`${BASE}/analysis/payment-aging-related`)
  if (!res.ok) throw new Error('Failed to load payment aging (related) analysis')
  return res.json()
}



