import React, { useState, useEffect, useRef } from 'react'

export default function Settings() {
  const [holidayFile, setHolidayFile] = useState(null)
  const [currentFile, setCurrentFile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef(null)

  const fetchHolidaysInfo = async () => {
    try {
      const res = await fetch('/api/holidays-info')
      if (res.ok) {
        const data = await res.json()
        if (data.has_file) {
          setCurrentFile(data.filename)
        } else {
          setCurrentFile('Default Holiday Calendar (STATIC_HOLIDAYS)')
        }
      }
    } catch (err) {
      console.error('Error fetching holidays info:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHolidaysInfo()
  }, [])

  const handleFileChange = (file) => {
    if (!file) return
    const ext = file.name.split('.').pop().toLowerCase()
    if (!['csv', 'xlsx', 'xls'].includes(ext)) {
      setError(`Invalid file format for ${file.name}. Only .csv, .xlsx, and .xls are supported.`)
      setSuccess('')
      return
    }
    setError('')
    setSuccess('')
    setHolidayFile(file)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragActive(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFileChange(file)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragActive(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setDragActive(false)
  }

  const handleUpload = async () => {
    if (!holidayFile) return
    setUploading(true)
    setError('')
    setSuccess('')

    const formData = new FormData()
    formData.append('file', holidayFile)

    try {
      const res = await fetch('/api/upload-holidays', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || 'Failed to upload holidays file')
      }

      const data = await res.json()
      setSuccess('Holiday calendar uploaded and applied successfully! Audit cache has been invalidated.')
      setCurrentFile(data.filename)
      setHolidayFile(null)
    } catch (err) {
      setError(err.message || 'An error occurred during upload.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-3xl">
          System Settings
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Configure and customize the P2P compliance engine settings.
        </p>
      </div>

      <div className="rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 p-6 shadow-sm space-y-6">
        <div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            Holiday Calendar Configuration
          </h3>
          <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
            Upload custom holiday sheets to override static lists. Dates in this sheet and Sundays are flagged as compliance holidays in the PO Status report.
          </p>
        </div>

        {/* Current File Info */}
        <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200/80 dark:border-slate-800/80 flex items-center justify-between">
          <div className="space-y-1">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Active Calendar File</div>
            <div className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              {loading ? (
                <span className="opacity-55">Loading calendar state...</span>
              ) : (
                currentFile
              )}
            </div>
          </div>
          <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${currentFile && currentFile !== 'Default Holiday Calendar (STATIC_HOLIDAYS)' ? 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400' : 'bg-slate-500/10 text-slate-600 dark:text-slate-400'}`}>
            {currentFile && currentFile !== 'Default Holiday Calendar (STATIC_HOLIDAYS)' ? 'Custom File' : 'System Default'}
          </span>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-800/30 text-rose-800 dark:text-rose-300 text-sm">
            {error}
          </div>
        )}

        {success && (
          <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/30 text-emerald-800 dark:text-emerald-300 text-sm font-medium">
            {success}
          </div>
        )}

        {/* Dropzone */}
        <div
          className={`relative border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center transition-all duration-200 cursor-pointer ${
            dragActive
              ? 'bg-indigo-500/5 border-indigo-500'
              : 'border-slate-200 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700 bg-slate-50/50 dark:bg-slate-950/10'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            className="hidden"
            accept=".csv,.xlsx,.xls"
            ref={fileInputRef}
            onChange={(e) => handleFileChange(e.target.files[0])}
          />

          <svg className="w-10 h-10 text-slate-400 mb-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>

          <div className="text-sm font-semibold text-slate-800 dark:text-slate-200">
            {holidayFile ? holidayFile.name : 'Select or drag holiday file here'}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Supports .xlsx, .xls, and .csv formats
          </div>
        </div>

        {/* Upload Button */}
        {holidayFile && (
          <div className="flex items-center gap-3 justify-end">
            <button
              onClick={() => setHolidayFile(null)}
              disabled={uploading}
              className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-xl transition-all"
            >
              Cancel
            </button>
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="px-5 py-2 text-xs font-bold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 rounded-xl shadow-md transition-all flex items-center gap-2"
            >
              {uploading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Uploading...
                </>
              ) : (
                'Upload and Apply Calendar'
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
