import { useState, useEffect } from 'react'
import { apiGet } from '../api'

export default function Health() {
  const [health, setHealth] = useState<any[]>([])
  const [overall, setOverall] = useState<any>(null)

  useEffect(() => {
    apiGet('/health/providers').then(setHealth).catch(() => {})
    apiGet('/health').then(setOverall).catch(() => {})
  }, [])

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 dark:text-white">Health</h1>
      {overall && (
        <div className="card mb-6">
          <div className="flex items-center gap-3">
            <span className={`w-3 h-3 rounded-full ${overall.status === 'ok' ? 'bg-green-500' : 'bg-yellow-500'}`} />
            <span className="font-semibold dark:text-white">{overall.status.toUpperCase()}</span>
            <span className="text-gray-400 text-sm">Uptime: {Math.floor(overall.uptime_seconds)}s</span>
          </div>
        </div>
      )}
      <div className="grid gap-3">
        {health.map(h => (
          <div key={h.name} className="card flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className={`w-2.5 h-2.5 rounded-full ${h.status === 'healthy' ? 'bg-green-500' : h.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'}`} />
              <span className="font-semibold dark:text-white">{h.name}</span>
              <span className="text-sm text-gray-400">{h.avg_latency_ms?.toFixed(0)}ms</span>
            </div>
            <div className="flex gap-3 text-sm">
              <span className={`badge ${h.status === 'healthy' ? 'badge-green' : 'badge-red'}`}>{h.status}</span>
              <span className="text-gray-400">{h.consecutive_failures} failures</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
