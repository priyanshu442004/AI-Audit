import React, { useState } from 'react'
import { X, FileText, Truck, Calendar, Layers, CheckCircle2, AlertTriangle, ExternalLink } from 'lucide-react'

export default function LineItemSourceTraceModal({ isOpen, onClose, selectedRow }) {
  const [activeTab, setActiveTab] = useState('po') // 'po' | 'grpo' | 'holiday'

  if (!isOpen || !selectedRow) return null

  const row = selectedRow

  const poNo = row['PO No'] || '—'
  const grnNo = row['GRN No'] || '—'
  const itemCode = row['Item Code'] || '—'
  const itemDesc = row['Item Description'] || '—'
  const vendorName = row['Vendor Name'] || row['Vendor Code'] || '—'
  const postDate = row['Posting Date'] || row['Document Date'] || '—'
  const holidayFlag = row['Holiday & Sunday Exception'] || 'Normal Working Day'

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xl max-w-4xl w-full overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95 duration-150">
        
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-200/80 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/80 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400">
                <Layers className="w-4 h-4" />
              </span>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Data Lineage & Source Inspection
              </h3>
              <span className="text-[10px] font-bold text-slate-500 bg-slate-200/70 dark:bg-slate-800 px-2 py-0.5 rounded-md">
                3 Input Sheets Audit Trace
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Tracing source fields for PO <strong className="text-slate-700 dark:text-slate-200">{poNo}</strong> (Item: {itemCode}) across raw S3 input sheets.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Row Context Banner */}
        <div className="bg-blue-950/5 dark:bg-blue-950/20 px-6 py-3 border-b border-slate-200/60 dark:border-slate-800/80 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold">PO Number & Key</div>
            <div className="font-extrabold text-blue-600 dark:text-blue-400">{poNo}</div>
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Vendor Name</div>
            <div className="font-semibold text-slate-800 dark:text-slate-200 truncate">{vendorName}</div>
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Item Description</div>
            <div className="font-semibold text-slate-800 dark:text-slate-200 truncate">{itemDesc}</div>
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Posting Date</div>
            <div className="font-semibold text-slate-800 dark:text-slate-200">{postDate}</div>
          </div>
        </div>

        {/* Tabs Bar */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 bg-slate-100/50 dark:bg-slate-900/50 px-6 pt-2">
          <button
            onClick={() => setActiveTab('po')}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 transition ${
              activeTab === 'po'
                ? 'border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400 bg-white dark:bg-slate-900 rounded-t-lg shadow-xs'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>1. Purchase Order Sheet</span>
          </button>
          <button
            onClick={() => setActiveTab('grpo')}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 transition ${
              activeTab === 'grpo'
                ? 'border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400 bg-white dark:bg-slate-900 rounded-t-lg shadow-xs'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <Truck className="w-3.5 h-3.5" />
            <span>2. GRPO Report Sheet</span>
          </button>
          <button
            onClick={() => setActiveTab('holiday')}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 transition ${
              activeTab === 'holiday'
                ? 'border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400 bg-white dark:bg-slate-900 rounded-t-lg shadow-xs'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <Calendar className="w-3.5 h-3.5" />
            <span>3. Holidays Reference Sheet</span>
          </button>
        </div>

        {/* Modal Tab Contents */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          
          {/* TAB 1: PO SHEET */}
          {activeTab === 'po' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-500">Source Input File: <code className="text-blue-600 dark:text-blue-400">Purchase Order Report-ITL.xls (S3)</code></span>
                <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-100 dark:bg-emerald-950/60 dark:text-emerald-400 px-2 py-0.5 rounded-full">
                  <CheckCircle2 className="w-3 h-3" /> Record Loaded
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs">
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">PO Series & Status</span>
                  <div className="font-bold text-slate-900 dark:text-white mt-0.5">{row['PO Series'] || '—'} | Status: {row['Document Status']}</div>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Branch / Plant</span>
                  <div className="font-bold text-slate-900 dark:text-white mt-0.5">{row['Branch'] || '—'}</div>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Vendor Group & Code</span>
                  <div className="font-bold text-slate-900 dark:text-white mt-0.5">{row['Vendor Group']} ({row['Vendor Code']})</div>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Item Group & UOM</span>
                  <div className="font-bold text-slate-900 dark:text-white mt-0.5">{row['Item Group']} | {row['UOM']}</div>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">PO Qty & Open Qty</span>
                  <div className="font-bold text-slate-900 dark:text-white mt-0.5">{row['PO Qty']} / Open: {row['Open Qty']}</div>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">PO Unit Price</span>
                  <div className="font-bold text-slate-900 dark:text-white mt-0.5">₹{row['PO Price']}</div>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Line Total Value</span>
                  <div className="font-bold text-slate-900 dark:text-white mt-0.5">₹{row['Line Total']}</div>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Currency & Rate</span>
                  <div className="font-bold text-slate-900 dark:text-white mt-0.5">{row['Document Currency']} (Rate: {row['Document Rate']})</div>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Canceled Status</span>
                  <div className="font-bold text-slate-900 dark:text-white mt-0.5">{row['Canceled Status']}</div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: GRPO SHEET */}
          {activeTab === 'grpo' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-500">Source Input File: <code className="text-blue-600 dark:text-blue-400">new GRPO Report-ITL1.xls (S3)</code></span>
                {grnNo && grnNo !== '—' && grnNo !== '0' ? (
                  <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-100 dark:bg-emerald-950/60 dark:text-emerald-400 px-2 py-0.5 rounded-full">
                    <CheckCircle2 className="w-3 h-3" /> GRN Matched: {grnNo}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[10px] font-bold text-amber-700 bg-amber-100 dark:bg-amber-950/60 dark:text-amber-400 px-2 py-0.5 rounded-full">
                    <AlertTriangle className="w-3 h-3" /> Pending Receipt
                  </span>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs">
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">GRN Receipt Number</span>
                  <div className="font-bold text-slate-900 dark:text-white mt-0.5">{grnNo}</div>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">GRN Qty Received</span>
                  <div className="font-bold text-slate-900 dark:text-white mt-0.5">{row['GRN Qty']}</div>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">GRN Unit Price</span>
                  <div className="font-bold text-slate-900 dark:text-white mt-0.5">₹{row['GRN Price']}</div>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">GRN Total Line Value</span>
                  <div className="font-bold text-slate-900 dark:text-white mt-0.5">₹{row['GRN Line Total']}</div>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Quantity Variance Audit</span>
                  <div className={`font-bold mt-0.5 ${row['QTY Difference'] === 'Exception' ? 'text-rose-600' : 'text-slate-900 dark:text-white'}`}>
                    Excess: {row['Excess QTY']} ({row['Excess Qty Variation %']}%)
                  </div>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold uppercase">Price Variance Audit</span>
                  <div className={`font-bold mt-0.5 ${row['Line Total Difference'] === 'Exception' ? 'text-rose-600' : 'text-slate-900 dark:text-white'}`}>
                    Excess: ₹{row['Excess Price']} ({row['Excess Price Variation %']}%)
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: HOLIDAY SHEET */}
          {activeTab === 'holiday' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-500">Source Input File: <code className="text-blue-600 dark:text-blue-400">HOLIDAY-2026.xlsx (S3)</code></span>
                {holidayFlag && holidayFlag !== 'Normal Working Day' ? (
                  <span className="inline-flex items-center gap-1 text-[10px] font-bold text-rose-700 bg-rose-100 dark:bg-rose-950/60 dark:text-rose-400 px-2 py-0.5 rounded-full">
                    <AlertTriangle className="w-3 h-3" /> Flagged: {holidayFlag}
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-100 dark:bg-emerald-950/60 dark:text-emerald-400 px-2 py-0.5 rounded-full">
                    <CheckCircle2 className="w-3 h-3" /> Verified Working Day
                  </span>
                )}
              </div>

              <div className="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200/60 dark:border-slate-800 space-y-3 text-xs">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <span className="text-[10px] text-slate-400 font-semibold uppercase">PO Posting Date</span>
                    <div className="font-bold text-slate-900 dark:text-white mt-0.5">{postDate}</div>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-semibold uppercase">Holiday Calendar Result</span>
                    <div className="font-bold text-slate-900 dark:text-white mt-0.5">{holidayFlag}</div>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 font-semibold uppercase">Compliance Assessment</span>
                    <div className={`font-bold mt-0.5 ${holidayFlag !== 'Normal Working Day' ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                      {holidayFlag !== 'Normal Working Day' ? 'Non-Working Day Creation Exception' : 'Compliant Calendar Creation'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-slate-200/80 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/80 flex items-center justify-between text-xs">
          <span className="text-slate-400 font-medium">Reconciled via key: <code className="text-slate-600 dark:text-slate-300 font-bold">{poNo}-{itemCode}</code></span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-bold rounded-xl bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition"
          >
            Close Trace Modal
          </button>
        </div>

      </div>
    </div>
  )
}
