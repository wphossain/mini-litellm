import { useState, useEffect } from 'react'
import { apiGet, apiPost, apiDelete } from '../api'

interface Provider {
  name: string; type: string; enabled: boolean; priority: number
  status: string; api_keys_count: number; models: string[]
  api_base: string; cost_weight: number; latency_weight: number
  consecutive_failures: number; avg_latency_ms: number
}

export default function Providers() {
  const [providers, setProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(true)
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ name: '', type: 'openai', api_base: '', api_key: '', enabled: true, priority: 10 })

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    try { setProviders(await apiGet('/admin/providers')) } catch {}
    setLoading(false)
  }

  async function toggle(name: string, enabled: boolean) {
    await apiPost('/admin/providers/toggle', { provider_name: name, enabled })
    load()
  }

  async function remove(name: string) {
    if (!confirm(`Delete provider "${name}"? This cannot be undone.`)) return
    await apiDelete(`/admin/providers/${name}`)
    load()
  }

  async function addProvider() {
    if (!form.name) return
    await apiPost('/admin/providers', {
      name: form.name, type: form.type, api_base: form.api_base,
      api_keys: form.api_key ? [form.api_key] : [],
      enabled: form.enabled, priority: form.priority,
    })
    setShowAdd(false)
    setForm({ name: '', type: 'openai', api_base: '', api_key: '', enabled: true, priority: 10 })
    load()
  }

  const PROVIDER_TYPES = [
    'openai', 'anthropic', 'gemini', 'openrouter', 'mistral', 'groq', 'deepseek',
    'azure', 'ollama', 'openai_compatible', 'vertex', 'bedrock', 'vllm', 'lm_studio', 'xinference'
  ]

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold dark:text-white">Providers</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{providers.length} total &middot; {providers.filter(p => p.enabled).length} enabled</p>
        </div>
        <button onClick={() => setShowAdd(!showAdd)} className="btn-primary">
          {showAdd ? '✕ Cancel' : '+ Add Provider'}
        </button>
      </div>

      {/* Add Provider Form */}
      {showAdd && (
        <div className="card mb-6 p-6">
          <h3 className="font-semibold mb-4 dark:text-white">New Provider</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Name</label>
              <input value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="my-provider" className="input" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Type</label>
              <select value={form.type} onChange={e => setForm({...form, type: e.target.value})} className="select">
                {PROVIDER_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">API Base URL</label>
              <input value={form.api_base} onChange={e => setForm({...form, api_base: e.target.value})} placeholder="https://api.openai.com/v1" className="input" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Priority</label>
              <input type="number" value={form.priority} onChange={e => setForm({...form, priority: parseInt(e.target.value) || 10})} className="input" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-xs font-medium text-gray-500 mb-1">API Key</label>
              <input value={form.api_key} onChange={e => setForm({...form, api_key: e.target.value})} placeholder="sk-..." className="input" />
            </div>
            <div className="flex items-end">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={form.enabled} onChange={e => setForm({...form, enabled: e.target.checked})} className="rounded border-gray-300" />
                <span className="text-sm">Enabled</span>
              </label>
            </div>
          </div>
          <button onClick={addProvider} className="btn-primary">Create Provider</button>
        </div>
      )}

      {/* Provider List */}
      {loading ? (
        <div className="flex justify-center py-12">
          <svg className="animate-spin h-8 w-8 text-blue-500" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
        </div>
      ) : (
        <div className="grid gap-4">
          {providers.map(p => (
            <div key={p.name} className="card p-5">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className={`w-2.5 h-2.5 rounded-full mt-2 ${
                    p.status === 'healthy' ? 'bg-green-500' :
                    p.status === 'degraded' ? 'bg-yellow-500' :
                    p.enabled ? 'bg-red-500' : 'bg-gray-400'
                  }`} />
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold dark:text-white">{p.name}</h3>
                      <span className="badge badge-gray">{p.type}</span>
                      <span className={`badge ${p.enabled ? 'badge-green' : 'badge-red'}`}>{p.enabled ? 'Enabled' : 'Disabled'}</span>
                      <span className={`badge ${
                        p.status === 'healthy' ? 'badge-green' :
                        p.status === 'degraded' ? 'badge-yellow' : 'badge-red'
                      }`}>{p.status}</span>
                    </div>
                    <div className="flex gap-4 mt-1 text-xs text-gray-500">
                      <span>Priority: {p.priority}</span>
                      <span>Keys: {p.api_keys_count}</span>
                      <span>Latency: {p.avg_latency_ms?.toFixed(0) || '-'}ms</span>
                      <span>Failures: {p.consecutive_failures}</span>
                    </div>
                    {p.api_base && <p className="text-xs text-gray-400 mt-1">{p.api_base}</p>}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => toggle(p.name, !p.enabled)} className={`btn-sm ${p.enabled ? 'btn-secondary' : 'btn-success'}`}>
                    {p.enabled ? 'Disable' : 'Enable'}
                  </button>
                  <button onClick={() => remove(p.name)} className="btn-sm btn-danger">Delete</button>
                </div>
              </div>
            </div>
          ))}
          {providers.length === 0 && (
            <div className="text-center py-12 text-gray-400">
              <p className="text-4xl mb-3">🔌</p>
              <p>No providers configured. Click "Add Provider" to get started.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
