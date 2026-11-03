import React, { useEffect, useState } from 'react'

const API = '/api/management-report'

async function request(path, token, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      ...(options.headers || {}),
      'X-Admin-Token': token
    }
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(body.detail || `Request failed (${response.status})`)
  }
  return body
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function statusClass(status) {
  if (status === 'completed' || status === 'sent' || status === 'green') {
    return 'text-emerald-700 bg-emerald-50 dark:text-emerald-300 dark:bg-emerald-950/40'
  }
  if (status === 'delivery_failed' || status === 'failed' || status === 'red') {
    return 'text-red-700 bg-red-50 dark:text-red-300 dark:bg-red-950/40'
  }
  if (status === 'amber' || status === 'sending') {
    return 'text-amber-700 bg-amber-50 dark:text-amber-300 dark:bg-amber-950/40'
  }
  return 'text-slate-600 bg-slate-100 dark:text-slate-300 dark:bg-slate-800'
}

export default function ManagementReportAdmin() {
  const [token, setToken] = useState('')
  const [status, setStatus] = useState(null)
  const [history, setHistory] = useState([])
  const [activeExecutionId, setActiveExecutionId] = useState('')
  const [loading, setLoading] = useState(false)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const refresh = async (authToken = token) => {
    if (!authToken) return
    setLoading(true)
    setError('')
    try {
      const [nextStatus, nextHistory] = await Promise.all([
        request('/status', authToken),
        request('/history?limit=30', authToken)
      ])
      setStatus(nextStatus)
      setHistory(nextHistory.executions || [])
    } catch (requestError) {
      setError(requestError.message || 'Unable to load management-report details.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!activeExecutionId || !token) return undefined
    let cancelled = false
    let timeout

    const poll = async () => {
      try {
        const execution = await request(`/executions/${encodeURIComponent(activeExecutionId)}`, token)
        if (cancelled) return
        if (['completed', 'failed', 'delivery_failed'].includes(execution.status)) {
          setRunning(false)
          setMessage(`Execution ${execution.status.replace('_', ' ')}.`)
          await refresh(token)
          return
        }
      } catch (requestError) {
        if (!cancelled) {
          setRunning(false)
          setError(requestError.message || 'Unable to read execution status.')
        }
        return
      }
      if (!cancelled) timeout = window.setTimeout(poll, 3000)
    }

    timeout = window.setTimeout(poll, 1500)
    return () => {
      cancelled = true
      window.clearTimeout(timeout)
    }
  }, [activeExecutionId, token])

  const handleRun = async () => {
    setRunning(true)
    setError('')
    setMessage('')
    try {
      const result = await request('/run', token, { method: 'POST' })
      setActiveExecutionId(result.execution_id)
      setMessage('Management summary queued.')
    } catch (requestError) {
      setRunning(false)
      setError(requestError.message || 'Unable to queue the report.')
    }
  }

  const downloadPdf = async (execution) => {
    setError('')
    try {
      const response = await fetch(`${API}/executions/${encodeURIComponent(execution.execution_id)}/pdf`, {
        headers: { 'X-Admin-Token': token }
      })
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body.detail || `Download failed (${response.status})`)
      }
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = execution.pdf_filename || 'P2P_Audit_Management_Summary.pdf'
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (downloadError) {
      setError(downloadError.message || 'Unable to download the report PDF.')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-bold text-slate-900 dark:text-white">Daily P2P Management Summary</h3>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Review the scheduler, delivery history, and three-page report. Manual generation requires the server-side administrator token.
        </p>
      </div>

      <form
        className="flex flex-col sm:flex-row gap-2"
        onSubmit={(event) => {
          event.preventDefault()
          refresh()
        }}
      >
        <label className="sr-only" htmlFor="management-report-admin-token">Administrator token</label>
        <input
          id="management-report-admin-token"
          type="password"
          autoComplete="off"
          value={token}
          onChange={(event) => setToken(event.target.value)}
          placeholder="Administrator token"
          className="flex-1 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-xs text-slate-900 dark:text-white"
        />
        <button
          type="submit"
          disabled={!token || loading}
          className="rounded-lg bg-slate-800 px-4 py-2 text-xs font-semibold text-white disabled:opacity-50 dark:bg-slate-700"
        >
          {loading ? 'Loading…' : 'Load report status'}
        </button>
      </form>

      {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">{error}</div>}
      {message && <div role="status" className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-xs text-blue-700 dark:border-blue-900 dark:bg-blue-950/40 dark:text-blue-300">{message}</div>}

      {status && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-slate-200 dark:border-slate-700 p-4">
              <p className="text-[10px] font-bold uppercase text-slate-500">Scheduler</p>
              <p className="mt-2 text-sm font-semibold text-slate-900 dark:text-white">{status.scheduler.enabled ? 'Enabled' : 'Disabled'}</p>
              <p className="mt-1 text-[10px] text-slate-500">{status.scheduler.cron} · {status.scheduler.timezone}</p>
            </div>
            <div className="rounded-xl border border-slate-200 dark:border-slate-700 p-4">
              <p className="text-[10px] font-bold uppercase text-slate-500">Next scheduled run</p>
              <p className="mt-2 text-xs font-semibold text-slate-900 dark:text-white">{formatDate(status.scheduler.next_run)}</p>
            </div>
            <div className="rounded-xl border border-slate-200 dark:border-slate-700 p-4">
              <p className="text-[10px] font-bold uppercase text-slate-500">Last successful run</p>
              <p className="mt-2 text-xs font-semibold text-slate-900 dark:text-white">{formatDate(status.last_successful_run?.completed_at)}</p>
            </div>
            <div className="rounded-xl border border-slate-200 dark:border-slate-700 p-4">
              <p className="text-[10px] font-bold uppercase text-slate-500">Last generated PDF</p>
              <p className="mt-2 break-all text-xs font-semibold text-slate-900 dark:text-white">{status.last_generated_pdf || 'Not generated yet'}</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h4 className="text-xs font-bold text-slate-900 dark:text-white">Execution history</h4>
              <p className="mt-1 text-[10px] text-slate-500">Email status is tracked separately for each recipient.</p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => refresh()}
                disabled={loading}
                className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 disabled:opacity-50 dark:border-slate-700 dark:text-slate-300"
              >
                Refresh
              </button>
              <button
                type="button"
                onClick={handleRun}
                disabled={!token || running}
                className="rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50"
              >
                {running ? 'Running…' : 'Run summary now'}
              </button>
            </div>
          </div>

          <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700">
            <table className="w-full min-w-[700px] text-left text-xs">
              <thead className="bg-slate-50 text-[10px] uppercase text-slate-500 dark:bg-slate-800/70">
                <tr>
                  <th className="px-3 py-2">Started</th>
                  <th className="px-3 py-2">Reporting period</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Email deliveries</th>
                  <th className="px-3 py-2">PDF</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {history.map((execution) => (
                  <tr key={execution.execution_id}>
                    <td className="px-3 py-3 text-slate-600 dark:text-slate-300">{formatDate(execution.started_at)}</td>
                    <td className="px-3 py-3 text-slate-600 dark:text-slate-300">{execution.reporting_period || '—'}</td>
                    <td className="px-3 py-3">
                      <span className={`rounded-full px-2 py-1 text-[10px] font-semibold ${statusClass(execution.status)}`}>
                        {execution.status}
                      </span>
                    </td>
                    <td className="px-3 py-3">
                      <div className="space-y-1">
                        {(execution.deliveries || []).map((delivery) => (
                          <div key={`${execution.execution_id}-${delivery.recipient}`} className="flex items-center gap-2">
                            <span className={`rounded-full px-2 py-1 text-[10px] font-semibold ${statusClass(delivery.status)}`}>{delivery.status}</span>
                            <span className="text-slate-600 dark:text-slate-300">{delivery.recipient}</span>
                          </div>
                        ))}
                        {(!execution.deliveries || execution.deliveries.length === 0) && <span className="text-slate-400">No delivery records</span>}
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      {execution.pdf_filename ? (
                        <button type="button" onClick={() => downloadPdf(execution)} className="font-semibold text-blue-600 hover:underline dark:text-blue-400">
                          Download
                        </button>
                      ) : <span className="text-slate-400">—</span>}
                    </td>
                  </tr>
                ))}
                {history.length === 0 && (
                  <tr><td colSpan="5" className="px-3 py-8 text-center text-slate-400">No report executions recorded.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
