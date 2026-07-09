import React from 'react'
import { useStore } from '../store'
import logo from '../assets/logo.jpeg'

const PHASES = [
  { id: 'ingestion', label: 'Data Ingestion & Cleaning', range: [0, 15] },
  { id: 'reconciliation', label: 'Transaction Reconciliation', range: [16, 40] },
  { id: 'analytical', label: 'Analytical Auditing', range: [41, 70] },
  { id: 'compliance', label: 'Compliance & Master Data', range: [71, 85] },
  { id: 'consolidation', label: 'Report Consolidation', range: [86, 100] }
]

export default function LoadingPage() {
  const { progress } = useStore()
  const { pct = 0, message = 'Preparing data…' } = progress

  return (
    <div className="app-bg flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/85 rounded-xl p-8 max-w-md w-full shadow-lg text-left">
        <div className="flex items-center gap-4 mb-6 pb-6 border-b border-slate-100 dark:border-slate-800/80">
          <img src={logo} alt="IKIO" className="w-12 h-12 object-contain rounded-lg border border-slate-100 dark:border-slate-800" />
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white">P2P Compliance Audit</h2>
            <p className="text-xs text-slate-400 dark:text-slate-500">Processing transactional datasets</p>
          </div>
          <div className="ml-auto text-right">
            <span className="text-xl font-black text-blue-600 dark:text-blue-400">{pct}%</span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-100 dark:bg-slate-800/80 rounded-full h-2 mb-8 overflow-hidden">
          <div
            className="bg-blue-600 h-full rounded-full transition-all duration-300 ease-out"
            style={{ width: `${pct}%` }}
          />
        </div>

        {/* Audit Phases */}
        <div className="space-y-4 mb-8">
          {PHASES.map((phase) => {
            const isCompleted = pct > phase.range[1]
            const isActive = pct >= phase.range[0] && pct <= phase.range[1]
            
            return (
              <div key={phase.id} className="flex items-center gap-3">
                <div className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                  {isCompleted ? (
                    <svg className="w-4 h-4 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  ) : isActive ? (
                    <div className="w-3.5 h-3.5 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
                  ) : (
                    <div className="w-2 h-2 rounded-full bg-slate-200 dark:bg-slate-700" />
                  )}
                </div>
                <span className={`text-xs font-semibold transition-colors duration-300 ${
                  isActive 
                    ? 'text-slate-900 dark:text-white font-bold' 
                    : isCompleted 
                    ? 'text-slate-400 dark:text-slate-500' 
                    : 'text-slate-300 dark:text-slate-600'
                }`}>
                  {phase.label}
                </span>
              </div>
            )
          })}
        </div>

        {/* Current Detailed Message */}
        <div className="bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800/50 rounded-xl p-3.5">
          <p className="text-[11px] font-mono text-slate-500 dark:text-slate-400 truncate text-center">
            {message}
          </p>
        </div>
      </div>
    </div>
  )
}
