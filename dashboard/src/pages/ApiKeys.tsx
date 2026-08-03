import { useState, useEffect } from 'react'
import { apiGet, apiPost } from '../api'

interface Provider { name: string; api_keys_count: number; type: string }

export default function ApiKeys() {
  const [providers, setProviders] = useState<Provider[]>([])
  const [selected, setSelected] = useState('')
  const [newKey, setNewKey] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try { setProviders(await apiGet('/admin/providers')) } catch {}
    setLoading(false)
  }

  async function addKey() {
    if (!selected || !newKey) return
    await apiPost('/admin/keys', { provider_name: selected, api_key: newKey })
    setNewKey('')
    load()
  }

  return (
    <div className="animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold dark:text-white">API Keys</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Manage API keys for each provider</p>
      </div>
      <div className="card p-6 mb-6">
        <h3 className="font-semibold mb-4 dark:text-white">Add New Key</h3>
        <div className="flex flex-col md:flex-row gap-3">
          <select value={selected} onChange={e => setSelected(e.target.value)} className="select md:w-48">
            <option value="">Select provider...</option>
            {providers.map(p => <option key={p.name} value={p.name}>{p.name} ({p.type})</option>)}
          </select>
          <input value={newKey} onChange={e => setNewKey(e.target.value)} placeholder="Enter API key (sk-...)" className="input flex-1" onKeyDown={e => e.key === 'Enter' && addKey()} />
          <button onClick={addKey} disabled={!selected || !newKey} className="btn-primary">+ Add Key</button>
        </div>
      </div>
      {loading ? (
        <div className="flex justify-center py-12"><svg className="animate-spin h-8 w-8 text-blue-500" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg></div>
      ) : (
        <div className="grid gap-3">
          {providers.map(p => (
            <div key={p.name} className="card p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-lg">🔑</span>
                <div><span className="font-medium dark:text-white">{p.name}</span><span className="text-xs text-gray-400 ml-2">{p.type}</span></div>
              </div>
              <span className={`badge ${p.api_keys_count > 0 ? 'badge-green' : 'badge-red'}`}>{p.api_keys_count} key{p.api_keys_count !== 1 ? 's' : ''}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
