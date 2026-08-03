import { useState, useEffect } from 'react'
import { apiGet, apiPost, apiDelete } from '../api'

interface Provider { name: string; type: string; enabled: boolean; priority: number; status: string; api_keys_count: number }

export default function Providers() {
  const [providers, setProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true)
    const data = await apiGet('/admin/providers')
    setProviders(data)
    setLoading(false)
  }

  async function toggle(name: string, enabled: boolean) {
    await apiPost('/admin/providers/toggle', { provider_name: name, enabled })
    load()
  }

  async function remove(name: string) {
    if (!confirm(`Delete provider "${name}"?`)) return
    await apiDelete(`/admin/providers/${name}`)
    load()
  }

  if (loading) return <div className="text-gray-500">Loading...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 dark:text-white">Providers</h1>
      <div className="grid gap-4">
        {providers.map(p => (
          <div key={p.name} className="card flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-lg dark:text-white">{p.name} <span className="text-sm text-gray-400">({p.type})</span></h3>
              <div className="flex gap-2 mt-1">
                <span className={`badge ${p.enabled ? 'badge-green' : 'badge-red'}`}>{p.enabled ? 'Enabled' : 'Disabled'}</span>
                <span className={`badge ${p.status === 'healthy' ? 'badge-green' : p.status === 'degraded' ? 'badge-yellow' : 'badge-red'}`}>{p.status}</span>
                <span className="badge badge-green">Keys: {p.api_keys_count}</span>
              </div>
            </div>
            <div className="flex gap-2">
              <button onClick={() => toggle(p.name, !p.enabled)} className={`btn ${p.enabled ? 'btn-outline' : 'btn-primary'}`}>
                {p.enabled ? 'Disable' : 'Enable'}
              </button>
              <button onClick={() => remove(p.name)} className="btn btn-outline text-red-500">Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
