import React, { useState } from 'react'
import { useStore } from '../store'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'

import Cover        from '../sections/Cover'
import Executive    from '../sections/Executive'
import PoStatus     from '../sections/PoStatus'
import GateEntry    from '../sections/GateEntry'
import PriceVarianceSame from '../sections/PriceVarianceSame'
import PriceVarianceCross from '../sections/PriceVarianceCross'
import GeToGrn     from '../sections/GeToGrn'
import GrnToAp     from '../sections/GrnToAp'
import QtyVariance  from '../sections/QtyVariance'
import PriceVariance from '../sections/PriceVariance'
import GlBalances   from '../sections/GlBalances'
import PaymentAging from '../sections/PaymentAging'
import Msme         from '../sections/Msme'
import VendorMaster from '../sections/VendorMaster'
import DataMap      from '../sections/DataMap'
import Appendix     from '../sections/Appendix'
import History      from '../sections/History'
import UploadModal  from '../components/UploadModal'

const SECTIONS = {
  cover:              Cover,
  executive:          Executive,
  postatus:           PoStatus,
  gateentry:          GateEntry,
  pricevariancesame:  PriceVarianceSame,
  pricevariancecross: PriceVarianceCross,
  glbalances:         GlBalances,
  paymentaging:       PaymentAging,
  msme:               Msme,
  vendormaster:       VendorMaster,
  datamap:            DataMap,
  appendix:           Appendix,
  history:            History,
  cover:         Cover,
  executive:     Executive,
  postatus:      PoStatus,
  gateentry:     GateEntry,
  getogrn:       GeToGrn,
  grntoap:       GrnToAp,
  qtyvariance:   QtyVariance,
  pricevariance: PriceVariance,
  glbalances:    GlBalances,
  paymentaging:  PaymentAging,
  msme:          Msme,
  vendormaster:  VendorMaster,
  grpoexcept:    GrpoExcept,
  threeway:      ThreeWay,
  datamap:       DataMap,
  appendix:      Appendix,
  history:       History,
}

export default function Dashboard() {
  const { activeSection, results, showUploadModal } = useStore()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const Section = SECTIONS[activeSection] || Cover
  const sectionData = results?.[activeSection] || {}

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
    </div>
  )
}
