import React, { useState, useEffect } from 'react'
import { useStore } from '../store'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'

import Cover                from '../sections/Cover'
import Executive            from '../sections/Executive'
import PoStatus             from '../sections/PoStatus'
import GateEntry            from '../sections/GateEntry'
import PriceVarianceSame    from '../sections/PriceVarianceSame'
import PriceVarianceCross   from '../sections/PriceVarianceCross'
import GeToGrn              from '../sections/GeToGrn'
import GrnToAp              from '../sections/GrnToAp'
import GlBalances           from '../sections/GlBalances'
import PaymentAging         from '../sections/PaymentAging'
import PaymentAgingDomestic from '../sections/PaymentAgingDomestic'
import PaymentAgingForeign  from '../sections/PaymentAgingForeign'
import PaymentAgingRelated  from '../sections/PaymentAgingRelated'
import PaymentAgingMsme     from '../sections/PaymentAgingMsme'
import Msme                 from '../sections/Msme'
import VendorMaster         from '../sections/VendorMaster'
import VendorMasterNew      from '../sections/VendorMasterNew'
import ThreeWayMatching     from '../sections/ThreeWayMatching'
import ItemMaster           from '../sections/ItemMaster'
import DataMap              from '../sections/DataMap'
import Appendix             from '../sections/Appendix'
import History              from '../sections/History'
import Settings             from '../sections/Settings'
import UploadModal          from '../components/UploadModal'
import AuditTraceModal      from '../components/AuditTraceModal'

const SECTIONS = {
  cover:                Cover,
  executive:            Executive,
  postatus:             PoStatus,
  gateentry:            GateEntry,
  pricevariancesame:    PriceVarianceSame,
  pricevariancecross:   PriceVarianceCross,
  getogrn:              GeToGrn,
  grntoap:              GrnToAp,
  glbalances:           GlBalances,
  paymentaging:         PaymentAging,
  paymentagingdomestic: PaymentAgingDomestic,
  paymentagingforeign:  PaymentAgingForeign,
  paymentagingrelated:  PaymentAgingRelated,
  paymentagingmsme:     PaymentAgingMsme,
  vendormasternew:      VendorMasterNew,
  threewaymatching:     ThreeWayMatching,
  msme:                 Msme,
  vendormaster:         VendorMaster,
  itemmaster:           ItemMaster,
  datamap:              DataMap,
  appendix:             Appendix,
  history:              History,
  settings:             Settings,
}

export default function Dashboard() {
  const { activeSection, results, showUploadModal } = useStore()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  
  // Audit Trace State
  const [traceData, setTraceData] = useState(null)

  const Section = SECTIONS[activeSection] || Cover
  const sectionData = results?.[activeSection] || {}

  // Intercept all table cell clicks globally for tracing
  useEffect(() => {
    const handleCellClick = (e) => {
      // Find closest table cell
      const td = e.target.closest('td')
      if (!td) return

      // Don't intercept clicks on inputs, buttons, select dropdowns, or links inside the table
      if (e.target.closest('button, input, select, textarea, a')) return

      const tr = td.closest('tr')
      if (!tr) return

      const table = tr.closest('table')
      if (!table) return

      const value = td.textContent.trim()
      if (!value || value === '—' || value === 'None' || value === 'NaN') return

      // Find cell index
      const cells = Array.from(tr.children)
      const cellIdx = cells.indexOf(td)

      // Find corresponding table header
      const thead = table.querySelector('thead')
      if (!thead) return
      
      const ths = Array.from(thead.querySelectorAll('th'))
      if (ths.length === 0) return

      // If there are multiple header rows (e.g. grouped headers), find the header in the same column index
      const th = ths[cellIdx] || ths[ths.length - 1]
      const columnName = th ? th.textContent.trim().replace(/\s*\n\s*/g, ' ').replace(/↓|↑/g, '').trim() : 'Table Cell'

      // Collect all row cell values for context matching
      const rowValues = cells.map(c => c.textContent.trim())

      setTraceData({
        value,
        columnName,
        section: activeSection,
        rowValues
      })
    }

    document.addEventListener('click', handleCellClick)
    return () => document.removeEventListener('click', handleCellClick)
  }, [activeSection])

  return (
    <div className="app-bg flex">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 lg:ml-72 min-w-0">
        <Header onMenuClick={() => setSidebarOpen(true)} />
        <main className="px-4 py-5 sm:px-6 lg:px-10 lg:py-8 max-w-[1500px] mx-auto">
          <div className="page-section">
            <Section data={sectionData} results={results} />
          </div>
        </main>
      </div>

      {showUploadModal && <UploadModal />}

      {/* Global Audit Trace Modal */}
      {traceData && (
        <AuditTraceModal
          isOpen={!!traceData}
          onClose={() => setTraceData(null)}
          initialData={traceData}
        />
      )}
    </div>
  )
}
