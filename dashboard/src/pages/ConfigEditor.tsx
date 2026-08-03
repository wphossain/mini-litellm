import { useState, useEffect } from 'react'
import { apiGet, apiPut } from '../api'

export default function ConfigEditor() {
  const [yaml, setYaml] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')
  const [msgType, setMsgType] = useState<'success' | 'error'>('success')

  useEffect(() => { loadYaml() }, [])

  async function loadYaml() {
    setLoading(true)
    try {
      const d = await apiGet('/admin/config')
      setYaml(d.config || '# No configuration loaded')
    } catch (e: any) {
      setYaml('# Error loading config: ' + e.message)
    }
    setLoading(false)
  }

  async function saveYaml() {
    setSaving(true)
    try {
      await apiPut('/admin/config', { config: yaml })
      setMsg('Configuration saved and reloaded successfully!')
      setMsgType('success')
    } catch (e: any) {
      setMsg('Failed to save: ' + e.message)
      setMsgType('error')
    }
    setSaving(false)
    setTimeout(() => setMsg(''), 4000)
  }

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold dark:text-white">Config Editor</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Edit config.yaml — changes save directly to disk</p>
        </div>
        <div className="flex gap-2">
          <button onClick={loadYaml} className="btn-secondary" disabled={loading}>🔄 Load</button>
          <button onClick={saveYaml} className="btn-primary" disabled={saving || !yaml}>
            {saving ? (
              <><svg className="animate-spin h-4 w-4" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg> Saving...</>
            ) : '💾 Save'}
          </button>
        </div>
      </div>

      {msg && (
        <div className={`mb-4 px-4 py-3 rounded-lg text-sm font-medium ${
          msgType === 'success' ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-800' :
          'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
        }`}>
          {msgType === 'success' ? '✓ ' : '✕ '}{msg}
        </div>
      )}

      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-12">
            <svg className="animate-spin h-8 w-8 text-blue-500" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
          </div>
        ) : (
          <textarea
            value={yaml}
            onChange={e => setYaml(e.target.value)}
            className="w-full h-[70vh] p-4 font-mono text-sm bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-200 border-0 focus:outline-none resize-none"
            spellCheck={false}
          />
        )}
      </div>
    </div>
  )
}
