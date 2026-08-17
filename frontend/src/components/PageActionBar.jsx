import React, { useState } from 'react'
import { RefreshCw, FileSpreadsheet } from 'lucide-react'
import ExportModal from './ExportModal'

export default function PageActionBar({
  title,
  subtitle,
  badgeText = 'Live Audit',
  onRefresh,
  refreshing = false,
  columns = [],
  data = [],
  filenamePrefix = 'Audit_Export',
  extraActions
}) {
  const [showExportModal, setShowExportModal] = useState(false)

  return (
    <>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-200/60 dark:border-slate-800/60">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              {title}
            </h2>
            {badgeText && (
              <span className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                {badgeText}
              </span>
            )}
          </div>
          {subtitle && (
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
              {subtitle}
            </p>
          )}
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {extraActions}

          {/* Refresh Button with proper Lucide React Icon */}
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 shadow-sm transition-all active:scale-95 disabled:opacity-50"
              title="Refresh page data"
            >
              <RefreshCw className={`w-4 h-4 text-blue-500 ${refreshing ? 'animate-spin' : ''}`} />
              <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
            </button>
          )}

          {/* Export to Excel Button */}
          <button
            onClick={() => setShowExportModal(true)}
            className="flex items-center gap-2 px-4 py-2 text-xs font-bold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm transition-all active:scale-95"
            title="Export page data to Excel"
          >
            <FileSpreadsheet className="w-4 h-4" />
            <span>Export to Excel</span>
          </button>
        </div>
      </div>

      {/* Export Modal Component */}
      <ExportModal
        isOpen={showExportModal}
        onClose={() => setShowExportModal(false)}
        title={`Export ${title} Data`}
        columns={columns}
        data={data}
        filenamePrefix={filenamePrefix}
      />
    </>
  )
}
