import React, { useState } from 'react'
import { useStore } from '../store'
import logo from '../assets/logo.jpeg'

const CORE_CAPABILITIES = [
  {
    title: 'Three-Way Match Automation',
    description: 'Continuous cross-referencing between Purchase Orders, Gate Entries, GRPOs, and AP Invoices.'
  },
  {
    title: 'Source-Aware Audit Tracing',
    description: 'Click-to-pivot data lineage mapping back to raw transactional file records.'
  },
  {
    title: 'Treasury & Vendor Compliance',
    description: 'MSME status validation, payment aging brackets, and cross-vendor price variation tracking.'
  }
]

export default function LoginPage() {
  const login = useStore(state => state.login)
  const loginError = useStore(state => state.loginError)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [localError, setLocalError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLocalError('')

    if (!email.trim() || !password.trim()) {
      setLocalError('Please fill in all fields.')
      return
    }

    setLoading(true)
    setTimeout(() => {
      const success = login(email.trim(), password.trim())
      setLoading(false)
      if (!success) {
        setLocalError('Invalid email or password.')
      }
    }, 600)
  }

  return (
    <div className="min-h-screen flex bg-white dark:bg-slate-950 text-slate-800 dark:text-slate-100 font-sans transition-colors duration-200">
      {/* LEFT PANEL: Enterprise Product Preview (Visible on desktop) */}
      <div className="hidden lg:flex lg:w-7/12 bg-slate-50 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex-col justify-between p-12 relative overflow-hidden transition-colors duration-200">
        {/* Subtle grid accent */}
        <div className="absolute inset-0 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] dark:bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-40 dark:opacity-15"></div>

        <div className="relative z-10 space-y-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded bg-white flex items-center justify-center overflow-hidden p-1 shadow-sm border border-slate-200 dark:border-slate-800">
              <img src={logo} alt="IKIO Logo" className="w-full h-full object-contain" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-slate-950 dark:text-white">IKIO Solutions</span>
              <span className="block text-[10px] text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider">Procure-to-Pay Audit System</span>
            </div>
          </div>

          <div className="space-y-4 max-w-lg pt-12">
            <h1 className="text-4xl font-extrabold tracking-tight text-slate-950 dark:text-white leading-tight">
              Automated compliance, validation, and risk analysis.
            </h1>
            <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed">
              Consolidate disparate procurement records into a unified audit trail. 
              Trace inventory transactions, gate logs, and invoice variances back to their original source files in one click.
            </p>
          </div>

          {/* Core Capabilities List */}
          <div className="pt-6 max-w-md space-y-4">
            {CORE_CAPABILITIES.map((cap, idx) => (
              <div key={idx} className="flex gap-3">
                <div className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-blue-600 mt-2"></div>
                <div className="space-y-1">
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-200">{cap.title}</h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 leading-normal">{cap.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10 text-xs text-slate-400 dark:text-slate-500 font-semibold tracking-wide">
          © {new Date().getFullYear()} IKIO Solutions Private Limited. All rights reserved.
        </div>
      </div>

      {/* RIGHT PANEL: Minimalist, High-Contrast Login Form */}
      <div className="w-full lg:w-5/12 flex flex-col justify-center px-6 sm:px-12 lg:px-20 py-12 bg-white dark:bg-slate-950 transition-colors duration-200">
        <div className="mx-auto w-full max-w-sm">
          {/* Mobile Brand Header */}
          <div className="flex lg:hidden items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded bg-white flex items-center justify-center p-0.5 border border-slate-200 dark:border-slate-800">
              <img src={logo} alt="IKIO Logo" className="w-full h-full object-contain" />
            </div>
            <span className="text-md font-bold text-slate-950 dark:text-white tracking-tight">IKIO P2P Audit</span>
          </div>

          <div className="space-y-2 mb-8">
            <h2 className="text-2xl font-bold tracking-tight text-slate-950 dark:text-white">Sign in to your account</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Enter your credentials to access the audit platform.</p>
          </div>

          {/* Validation Alerts */}
          {(localError || loginError) && (
            <div className="mb-6 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-md text-xs text-red-650 dark:text-red-400 font-semibold flex items-start gap-2.5 animate-in fade-in duration-200">
              <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>{localError || loginError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email Address */}
            <div className="space-y-1.5">
              <label htmlFor="email" className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-md text-sm text-slate-950 dark:text-white placeholder-slate-400 dark:placeholder-slate-600 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 transition"
                placeholder="name@company.com"
                autoComplete="email"
                required
              />
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label htmlFor="password" className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                  Password
                </label>
              </div>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-md text-sm text-slate-950 dark:text-white placeholder-slate-400 dark:placeholder-slate-600 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 transition"
                placeholder="••••••••"
                autoComplete="current-password"
                required
              />
            </div>

            {/* Sign In Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold rounded-md transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                  <span>Verifying...</span>
                </>
              ) : (
                <span>Sign In</span>
              )}
            </button>
          </form>

          {/* Secure Admin Access Banner */}
          <div className="mt-8 pt-6 border-t border-slate-200 dark:border-slate-900">
            <div className="p-4 bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800/80 rounded-md">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 block mb-1">
                Demo Workspace Access
              </span>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-normal mb-2">
                Identity federation is active. For demonstration purposes, authenticate using the default admin credentials:
              </p>
              <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400 space-y-0.5">
                <div>Email: <span className="text-slate-700 dark:text-slate-300 font-semibold select-all">admin@ikio.com</span></div>
                <div>Pass: <span className="text-slate-700 dark:text-slate-300 font-semibold select-all">admin</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
