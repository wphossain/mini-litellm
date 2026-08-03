import { useState, useEffect } from 'react'
import { apiGet } from '../api'

interface Model { id: string; owned_by: string }

export default function Models() {
  const [models, setModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiGet('/v1/models').then(d => { setModels(d.data || []); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-gray-500">Loading...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 dark:text-white">Models ({models.length})</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {models.map(m => (
          <div key={m.id} className="card">
            <h3 className="font-semibold dark:text-white">{m.id}</h3>
            <p className="text-sm text-gray-400">{m.owned_by}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
