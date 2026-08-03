import { useState, useEffect } from 'react'
import { apiGet, apiPost } from '../api'

interface Provider { name: string; api_keys_count: number }

export default function ApiKeys() {
  const [providers, setProviders] = useState<Provider[]>([])
  const [selected, setSelected] = useState('')
  const [newKey, setNewKey] = useState('')
  const [msg, setMsg] = useState('')

  useEffect(() => { apiGet('/admin/providers').then(setProviders) }, [])

  async function addKey() {
    if (!selected || !newKey) return
    await apiPost('/admin/keys', { provider_name: selected, api_key: newKey })
    setMsg(`Key added to ${selected}`)
    setNewKey('')
    apiGet('/admin/providers').then(setProviders)
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 dark:text-white">API Keys</h1>
      {msg && <p className="text-green-500 mb-4">{msg}</p>}
      <div className="card mb-6">
        <h3 className="font-semibold mb-3 dark:text-white">Add Key</h3>
        <div className="flex gap-3">
          <select value={selected} onChange={e => setSelected(e.target.value)} className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 dark:text-white">
            <option value="">Select provider...</option>
            {providers.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
          </select>
          <input value={newKey} onChange={e => setNewKey(e.target.value)} placeholder="sk-..." className="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 dark:text-white" />
          <button onClick={addKey} className="btn btn-primary">Add</button>
        </div>
      </div>
      <div className="grid gap-3">
        {providers.map(p => (
          <div key={p.name} className="card flex justify-between items-center">
            <span className="font-semibold dark:text-white">{p.name}</span>
            <span className="badge badge-green">{p.api_keys_count} keys</span>
          </div>
        ))}
      </div>
    </div>
  )
}
