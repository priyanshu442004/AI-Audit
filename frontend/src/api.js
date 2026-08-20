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
  let isDone = false
  const es = new EventSource(`${BASE}/analyze/${sessionId}`)

  const fetchFinalResult = async (retries = 5) => {
    if (isDone) return
    try { es.close() } catch (_) {}

    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const res = await fetch(`${BASE}/result/${sessionId}`, {})
        if (res.ok) {
          const data = await res.json()
          if (data && typeof data === 'object' && Object.keys(data).length > 0) {
            isDone = true
            onResult(data)
            return
          }
        }
      } catch (e) {
        console.error(`Attempt ${attempt + 1} error fetching final result:`, e)
      }
      if (attempt < retries - 1) {
        await new Promise(r => setTimeout(r, 600))
      }
    }
    isDone = true
    onError('Analysis completed, but failed to load results. Please refresh.')
  }

  es.onmessage = (e) => {
    if (isDone) return
    try {
      const data = JSON.parse(e.data)
      if (data.stage === 'result') {
        isDone = true
        try { es.close() } catch (_) {}
        if (data.result) {
          onResult(data.result)
        } else {
          fetchFinalResult()
        }
      } else if (data.stage === 'error') {
        isDone = true
        try { es.close() } catch (_) {}
        onError(data.message || 'Analysis failed')
      } else {
        if (data.pct !== undefined || data.message) {
          onProgress({ stage: data.stage || '', pct: data.pct || 0, message: data.message || '' })
        }
        if (data.pct === 100 && data.stage === 'done') {
          setTimeout(() => {
            if (!isDone) fetchFinalResult()
          }, 500)
        }
      }
    } catch (err) {
      console.warn('SSE message parse error:', err)
      fetchFinalResult()
    }
  }

  es.onerror = (e) => {
    if (isDone) return
    console.warn('SSE connection error/closed, attempting result fallback...', e)
    fetchFinalResult()
  }

  return () => {
    isDone = true
    try { es.close() } catch (_) {}
  }
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
  const res = await fetch(`${BASE}/analysis/price-variance-same`, {})
  if (!res.ok) throw new Error('Failed to load same-vendor price variance')
  return res.json()
}

/**
 * Fetch cross-vendor price variance.
 * @returns {Promise<{rows: Array, kpis: object}>}
 */
export async function fetchPriceVarianceCross() {
  const res = await fetch(`${BASE}/analysis/price-variance-cross`, {})
  if (!res.ok) throw new Error('Failed to load cross-vendor price variance')
  return res.json()
}

/**
 * Fetch payment aging (domestic).
 * @returns {Promise<{rows: Array, kpis: object}>}
 */
export async function fetchPaymentAgingDomestic() {
  const res = await fetch(`${BASE}/analysis/payment-aging-domestic`, {})
  if (!res.ok) throw new Error('Failed to load payment aging (domestic) analysis')
  return res.json()
}

/**
 * Fetch payment aging (foreign).
 * @returns {Promise<{rows: Array, kpis: object}>}
 */
export async function fetchPaymentAgingForeign() {
  const res = await fetch(`${BASE}/analysis/payment-aging-foreign`, {})
  if (!res.ok) throw new Error('Failed to load payment aging (foreign) analysis')
  return res.json()
}

/**
 * Fetch payment aging (msme).
 * @returns {Promise<{rows: Array, kpis: object}>}
 */
export async function fetchPaymentAgingMsme() {
  const res = await fetch(`${BASE}/analysis/payment-aging-msme`, {})
  if (!res.ok) throw new Error('Failed to load payment aging (msme) analysis')
  return res.json()
}

/**
 * Fetch payment aging (related).
 * @returns {Promise<{rows: Array, kpis: object}>}
 */
export async function fetchPaymentAgingRelated() {
  const res = await fetch(`${BASE}/analysis/payment-aging-related`, {})
  if (!res.ok) throw new Error('Failed to load payment aging (related) analysis')
  return res.json()
}

/**
 * Fetch vendor master new.
 * @returns {Promise<{rows: Array, kpis: object}>}
 */
export async function fetchVendorMasterNew() {
  const res = await fetch(`${BASE}/analysis/vendor-master-new`, {})
  if (!res.ok) throw new Error('Failed to load vendor master new analysis')
  return res.json()
}

/**
 * Fetch three-way matching analysis.
 * @returns {Promise<{rows: Array, kpis: object}>}
 */
export async function fetchThreeWayMatching() {
  const res = await fetch(`${BASE}/analysis/three-way-matching`, {})
  if (!res.ok) throw new Error('Failed to load three-way matching analysis')
  return res.json()
}/**
 * Fetch the list of system action and audit logs.
 * @param {number} limit
 * @returns {Promise<Array>}
 */
export async function fetchLogs(limit = 100) {
  const res = await fetch(`${BASE}/logs?limit=${limit}`, {})
  if (!res.ok) throw new Error('Failed to load logs')
  return res.json()
}

/**
 * Perform a real-time search across raw source DataFrames.
 * @param {string} query
 * @returns {Promise<object>}
 */
export async function searchAuditTrace(query) {
  const res = await fetch(`${BASE}/audit-trace/search?query=${encodeURIComponent(query)}`, {})
  if (!res.ok) throw new Error('Failed to search audit trace raw files')
  return res.json()
}

