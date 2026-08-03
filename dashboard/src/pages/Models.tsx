import { useState, useEffect } from 'react'
import { apiGet } from '../api'

interface Model { id: string; owned_by: string }

export default function Models() {
  const [models, setModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    apiGet('/v1/models').then(d => { setModels(d.data || []); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  const filtered = models.filter(m => m.id.toLowerCase().includes(search.toLowerCase()))
  const byProvider: Record<string, Model[]> = {}
  filtered.forEach(m => { const p = m.owned_by; if (!byProvider[p]) byProvider[p] = []; byProvider[p].push(m) })

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold dark:text-white">Models</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{models.length} models available</p>
        </div>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search models..." className="input max-w-xs" />
      </div>
      {loading ? (
        <div className="flex justify-center py-12"><svg className="animate-spin h-8 w-8 text-blue-500" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg></div>
      ) : (
        Object.entries(byProvider).map(([provider, models]) => (
          <div key={provider} className="card mb-4">
            <div className="card-header flex items-center gap-2"><span>{provider}</span><span className="badge badge-gray">{models.length}</span></div>
            <div className="p-4"><div className="flex flex-wrap gap-2">
              {models.map(m => <span key={m.id} className="px-3 py-1.5 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-xs font-mono dark:text-gray-200">{m.id}</span>)}
            </div></div>
          </div>
        ))
      )}
      {!loading && filtered.length === 0 && <div className="text-center py-12 text-gray-400"><p className="text-4xl mb-3">🧠</p><p>No models found.</p></div>}
    </div>
  )
}
