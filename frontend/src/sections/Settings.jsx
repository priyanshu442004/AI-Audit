import React, { useState, useEffect, useRef } from 'react'
import { useStore } from '../store'

export default function Settings() {
  const { theme, toggleTheme } = useStore()
  const [profile, setProfile] = useState({
    name: '',
    email: '',
    mobile_number: '',
    profile_pic_url: ''
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const fileInputRef = useRef(null)

  const [activeTab, setActiveTab] = useState('profile') // 'profile' | 'sap' | 'security'

  // SAP ERP integration state (mockup)
  const [sapAccounts, setSapAccounts] = useState([
    { id: '1', systemName: 'SAP S/4HANA Production', client: '100', status: 'Connected', lastSync: '10 minutes ago' }
  ])
  const [showSapModal, setShowSapModal] = useState(false)
  const [newSapSys, setNewSapSys] = useState({ systemName: '', client: '' })

  const fetchProfile = async () => {
    try {
      const res = await fetch('/api/user-profile')
      if (res.ok) {
        const data = await res.json()
        setProfile({
          name: data.name || '',
          email: data.email || '',
          mobile_number: data.mobile_number || '',
          profile_pic_url: data.profile_pic_url || ''
        })
      }
    } catch (err) {
      console.error('Error fetching profile:', err)
      setError('Failed to load user profile.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProfile()

    const handleRefresh = () => {
      setLoading(true)
      fetchProfile()
    }

    window.addEventListener('refresh-settings', handleRefresh)
    return () => window.removeEventListener('refresh-settings', handleRefresh)
  }, [])

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const ext = file.name.split('.').pop().toLowerCase()
    if (!['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(ext)) {
      setError('Only image files (.png, .jpg, .jpeg, .gif, .webp) are supported.')
      return
    }
    setError('')
    setSelectedFile(file)
    setPreviewUrl(URL.createObjectURL(file))
  }

  const handleProfileSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')

    const formData = new FormData()
    formData.append('name', profile.name)
    formData.append('email', profile.email)
    formData.append('mobile_number', profile.mobile_number)
    if (selectedFile) {
      formData.append('profile_pic', selectedFile)
    }

    try {
      const res = await fetch('/api/user-profile', {
        method: 'POST',
        body: formData
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || 'Failed to update profile')
      }
      const data = await res.json()
      setProfile({
        name: data.name || '',
        email: data.email || '',
        mobile_number: data.mobile_number || '',
        profile_pic_url: data.profile_pic_url || ''
      })
      setSelectedFile(null)
      setPreviewUrl('')
      setSuccess('Profile updated successfully!')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      setError(err.message || 'An error occurred while saving profile changes.')
    } finally {
      setSaving(false)
    }
  }

  const removeSapAccount = (id) => {
    setSapAccounts(prev => prev.filter(acc => acc.id !== id))
  }

  const addSapAccount = (e) => {
    e.preventDefault()
    if (!newSapSys.systemName.trim()) return
    setSapAccounts(prev => [
      ...prev,
      {
        id: Date.now().toString(),
        systemName: newSapSys.systemName,
        client: newSapSys.client || '000',
        status: 'Connected',
        lastSync: 'Just now'
      }
    ])
    setNewSapSys({ systemName: '', client: '' })
    setShowSapModal(false)
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] space-y-4">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">Loading settings...</p>
      </div>
    )
  }

  const initials = profile.name
    ? profile.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
    : 'AD'
  const activeAvatar = previewUrl || profile.profile_pic_url

  const tabs = [
    {
      id: 'profile',
      label: 'Profile Details',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      )
    },
    {
      id: 'sap',
      label: 'SAP ERP Integration',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      )
    },
    {
      id: 'security',
      label: 'Preferences & Security',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      )
    }
  ]

  const renderProfileForm = () => {
    return (
      <form onSubmit={handleProfileSubmit} className="space-y-6">
        <div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-0.5">Profile Details</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">Update account contact details and user avatar.</p>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-6 pb-6 border-b border-slate-100 dark:border-slate-800/80">
          <div 
            onClick={() => fileInputRef.current?.click()}
            className="relative group w-20 h-20 rounded-full overflow-hidden bg-slate-100 dark:bg-slate-800 flex items-center justify-center border border-slate-200 dark:border-slate-700 cursor-pointer shadow-sm shrink-0"
            title="Upload new profile picture"
          >
            {activeAvatar ? (
              <img src={activeAvatar} alt="Profile Avatar" className="w-full h-full object-cover" />
            ) : (
              <span className="text-xl font-bold text-slate-400 dark:text-slate-500">{initials}</span>
            )}
            
            <div className="absolute inset-0 bg-slate-900/60 flex flex-col items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              </svg>
              <span className="text-[8px] font-bold mt-1 uppercase tracking-wider">Change</span>
            </div>
          </div>

          <input 
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
            accept="image/*"
          />

          <div className="space-y-1 text-center sm:text-left">
            <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">Avatar Image</h4>
            <p className="text-[11px] text-slate-400 dark:text-slate-500">
              Supports JPEG, PNG, or WebP. Saved on AWS S3 storage.
            </p>
            {selectedFile && (
              <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-400 border border-blue-100 dark:border-blue-900/40 mt-1">
                Selected: {selectedFile.name}
              </span>
            )}
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-800/30 text-rose-800 dark:text-rose-455 text-xs">
            {error}
          </div>
        )}

        {success && (
          <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800/30 text-emerald-800 dark:text-emerald-455 text-xs font-semibold">
            {success}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-1.5 sm:col-span-2">
            <label className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Full Name</label>
            <input 
              type="text"
              required
              value={profile.name}
              onChange={e => setProfile({...profile, name: e.target.value})}
              className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 transition shadow-inner"
              placeholder="Full Name"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Email Address</label>
            <input 
              type="email"
              required
              value={profile.email}
              onChange={e => setProfile({...profile, email: e.target.value})}
              className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 transition shadow-inner"
              placeholder="e.g. user@company.com"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">Mobile Number</label>
            <input 
              type="text"
              required
              value={profile.mobile_number}
              onChange={e => setProfile({...profile, mobile_number: e.target.value})}
              className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 transition shadow-inner"
              placeholder="e.g. +91 9876543210"
            />
          </div>
        </div>

        <div className="flex justify-end pt-4 border-t border-slate-100 dark:border-slate-800/80">
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-750 disabled:opacity-40 rounded-lg transition-colors duration-150 shadow flex items-center gap-1.5"
          >
            {saving ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </button>
        </div>
      </form>
    )
  }

  const renderSapIntegration = () => {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-0.5">SAP ERP Integrations</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">Configure connections to SAP S/4HANA instances to enable automatic live data ingestion.</p>
          </div>
          <span className="text-[10px] font-bold px-2 py-0.5 bg-blue-50 dark:bg-blue-955/20 text-blue-700 dark:text-blue-400 border border-blue-100 dark:border-blue-900/40 rounded-full">
            Enterprise Sync Enabled
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sapAccounts.map(acc => (
            <div key={acc.id} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200/80 dark:border-slate-800/80 flex items-start justify-between gap-4">
              <div className="space-y-1.5 min-w-0">
                <div className="text-xs font-bold text-slate-900 dark:text-white truncate flex items-center gap-1.5">
                  <svg className="w-4 h-4 text-blue-500 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                  {acc.systemName}
                </div>
                <div className="flex items-center gap-2 text-[10px] text-slate-500 font-semibold">
                  <span>Client ID: <span className="font-mono text-slate-700 dark:text-slate-350">{acc.client}</span></span>
                  <span>•</span>
                  <span className="inline-flex items-center gap-1 text-emerald-600">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    {acc.status}
                  </span>
                </div>
              </div>
              
              <button 
                onClick={() => removeSapAccount(acc.id)}
                className="p-1 hover:bg-rose-50 dark:hover:bg-rose-955/20 rounded text-slate-400 hover:text-rose-600 transition"
                title="Disconnect instance"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          ))}

          {sapAccounts.length === 0 && (
            <div className="col-span-2 py-8 text-center border border-dashed border-slate-200 dark:border-slate-800 rounded-xl text-slate-400 text-xs">
              No SAP connections configured.
            </div>
          )}
        </div>

        <div className="flex justify-start">
          <button
            onClick={() => setShowSapModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-700 dark:text-slate-300 rounded-lg text-xs font-semibold transition"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            Add SAP Connection
          </button>
        </div>
      </div>
    )
  }

  const renderSecurityPreferences = () => {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-0.5">Preferences & Security</h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">Configure visual themes, security parameters, and audit controls.</p>
        </div>

        <div className="space-y-4 divide-y divide-slate-100 dark:divide-slate-850">
          {/* Theme setting */}
          <div className="flex items-center justify-between py-3">
            <div>
              <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">Dark Mode Interface</h4>
              <p className="text-[11px] text-slate-400 dark:text-slate-500">Toggle dark mode visual layout.</p>
            </div>
            <button
              onClick={toggleTheme}
              className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                theme === 'dark' ? 'bg-blue-600' : 'bg-slate-200 dark:bg-slate-800'
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                  theme === 'dark' ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* Secure Audit Logs */}
          <div className="flex items-center justify-between py-4">
            <div>
              <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">Tamper-Proof Audit Logging</h4>
              <p className="text-[11px] text-slate-400 dark:text-slate-500">Log all actions to internal log ledger for security compliance.</p>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-900/40">
              Active
            </span>
          </div>

          {/* API Token Mockup */}
          <div className="flex flex-col gap-2 py-4">
            <div>
              <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200">Audit Trace API Key</h4>
              <p className="text-[11px] text-slate-400 dark:text-slate-500">Authenticate command-line tools or custom scripts to ingest audit logs.</p>
            </div>
            <div className="flex items-center gap-2 max-w-md">
              <input
                type="text"
                readOnly
                value="sk_live_512809df5fcbcfdbbba03d2e4a9e18e975d"
                className="w-full font-mono text-[10px] rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 px-3 py-1.5 text-slate-500 select-all"
              />
              <button 
                onClick={() => navigator.clipboard.writeText("sk_live_512809df5fcbcfdbbba03d2e4a9e18e975d")}
                className="px-3 py-1.5 text-[10px] font-bold rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-750 dark:text-slate-250 hover:bg-slate-50 dark:hover:bg-slate-850 transition"
              >
                Copy
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-16">
      {/* Title */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          System Settings
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Manage user profiles, ERP credentials, and system preferences.
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6 items-start">
        {/* Left Settings Sidebar */}
        <div className="w-full lg:w-60 shrink-0 flex flex-row lg:flex-col gap-1 overflow-x-auto lg:overflow-x-visible pb-2 lg:pb-0 border-b lg:border-b-0 lg:border-r border-slate-100 dark:border-slate-800/80 pr-0 lg:pr-6">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`flex items-center gap-2.5 px-3 py-2 text-xs font-semibold rounded-lg transition-all duration-150 whitespace-nowrap ${
                activeTab === t.id
                  ? 'bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/60'
              }`}
            >
              {t.icon}
              {t.label}
            </button>
          ))}
        </div>

        {/* Right Settings Content */}
        <div className="flex-1 w-full bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800/80 rounded-2xl p-6 shadow-sm min-h-[400px]">
          {activeTab === 'profile' && renderProfileForm()}
          {activeTab === 'sap' && renderSapIntegration()}
          {activeTab === 'security' && renderSecurityPreferences()}
        </div>
      </div>

      {/* Mockup SAP Connection Modal */}
      {showSapModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl overflow-hidden">
            <div className="p-6 pb-4 border-b border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
              <h4 className="text-base font-extrabold text-slate-900 dark:text-white">Add SAP Connection</h4>
              <button 
                onClick={() => setShowSapModal(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <form onSubmit={addSapAccount} className="p-6 space-y-4">
              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">System Identifier / Name</label>
                <input 
                  type="text"
                  required
                  placeholder="e.g. SAP S/4HANA Staging"
                  value={newSapSys.systemName}
                  onChange={e => setNewSapSys({...newSapSys, systemName: e.target.value})}
                  className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 transition shadow-inner"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">SAP Client</label>
                <input 
                  type="text"
                  placeholder="e.g. 100"
                  value={newSapSys.client}
                  onChange={e => setNewSapSys({...newSapSys, client: e.target.value})}
                  className="w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500 transition shadow-inner"
                />
              </div>

              <div className="flex items-center gap-3 justify-end pt-4">
                <button
                  type="button"
                  onClick={() => setShowSapModal(false)}
                  className="px-4 py-2 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-xl text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold shadow"
                >
                  Save Connection
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
