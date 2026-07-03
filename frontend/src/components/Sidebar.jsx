import React from 'react'
import { useStore } from '../store'
import ThemeToggle from './ThemeToggle'
import logo from '../assets/logo.jpeg'

const LINK_GROUPS = [
  {
    label: 'Overview',
    links: [
      { id: 'cover',        label: 'Report Cover',         icon: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z' },
      { id: 'executive',    label: 'Executive Summary',    icon: 'M13 10V3L4 14h7v7l9-11h-7z' },
      { id: 'history',      label: 'Audit History',        icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0' },
    ],
  },
  {
    label: 'Procurement Controls',
    links: [
      { id: 'postatus',     label: 'PO Status',            icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
      { id: 'gateentry',    label: 'Gate Entry Check',     icon: 'M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4' },
      { id: 'getogrn',     label: 'GE to GRN Check',  icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4' },
      { id: 'grntoap',     label: 'GRN to AP Invoice Check', icon: 'M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z' },
      { id: 'pricevariancesame', label: 'Price Var. (Same Vendor)', icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
      { id: 'pricevariancecross', label: 'Price Var. (Cross Vendor)', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
      { id: 'paymentagingdomestic', label: 'Payment Aging(Domestic)', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
      { id: 'paymentagingforeign', label: 'Foreign Vendor Aging', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
      { id: 'paymentagingmsme', label: 'MSME Compliance', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
      { id: 'paymentagingrelated', label: 'Related Party Aging', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
    ],
  },
  {
    label: 'Financial & Compliance',
    links: [
      { id: 'glbalances',   label: 'GL Vendor Balances',   icon: 'M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z' },
      { id: 'paymentaging', label: 'Payment Aging',        icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
      { id: 'msme',         label: 'MSME Compliance Audit', icon: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16' },
      { id: 'vendormaster', label: 'Vendor Master',        icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z' },
    ],
  },
  {
    label: 'Methodology',
    links: [
      { id: 'datamap',      label: 'Data Map & Logic',     icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2' },
      { id: 'appendix',     label: 'Appendix',             icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' },
    ],
  },
  {
    label: 'Configuration',
    links: [
      { id: 'settings',     label: 'System Settings',      icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' },
    ],
  },
]

export default function Sidebar({ open, onClose }) {
  const { activeSection, setActiveSection } = useStore()

  const handleClick = (id) => {
    setActiveSection(id)
    if (window.innerWidth < 1024) onClose()
  }

  return (
    <>
      <aside className={`sidebar-shell fixed inset-y-0 left-0 z-50 w-72 transform transition-transform duration-300 flex flex-col ${open ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0`}>
        <div className="px-6 py-5 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-white flex items-center justify-center overflow-hidden p-1">
              <img src={logo} alt="IKIO" className="w-full h-full object-contain" />
            </div>
            <div>
              <div className="text-sm font-semibold tracking-wide text-white">IKIO</div>
              <div className="text-[10px] text-slate-400 uppercase tracking-[0.16em]">P2P Audit Analytics</div>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav flex-1 px-3 py-5 overflow-y-auto">
          {LINK_GROUPS.map(group => (
            <div key={group.label} className="mb-5 last:mb-0">
              <div className="px-3 mb-2 text-[10px] font-semibold text-slate-500 uppercase tracking-[0.16em]">
                {group.label}
              </div>
              <div className="space-y-1">
                {group.links.map(link => (
                  <a
                    key={link.id}
                    href="#"
                    onClick={e => { e.preventDefault(); handleClick(link.id) }}
                    className={`sidebar-link flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-all${activeSection === link.id ? ' active' : ''}`}
                  >
                    <svg className="w-4 h-4 flex-shrink-0 opacity-80" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d={link.icon} />
                    </svg>
                    {link.label}
                  </a>
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className="px-5 py-4 border-t border-white/10">
          <ThemeToggle />
          <div className="mt-3 flex items-center justify-between">
            <div>
              <div className="text-[10px] text-slate-500 uppercase tracking-wider">Audit Period</div>
              <div className="text-xs text-slate-300 font-medium">FY 2026-27</div>
            </div>
            <div className="text-[10px] text-slate-500">Confidential</div>
          </div>
        </div>
      </aside>

      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onClose}
        />
      )}
    </>
  )
}
